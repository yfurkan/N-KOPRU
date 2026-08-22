from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v120_questions_persistence.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.analyzer import analyze_post
from app.database import reset_database_for_tests
from app.history import record_analysis_snapshot
from app.main import app
from app.models import Comment, Post
from app.notifications import list_notifications, record_analysis


def make_post(post_id: int, texts: list[str]) -> Post:
    return Post(
        id=post_id,
        author='Kalıcı Soru Testi',
        handle='@kalici_soru',
        text='Gece bildirimlerinin etkisi nasıl değerlendirilmelidir?',
        created_at='şimdi',
        comments=[
            Comment(id=index + 1, author=f'K{index + 1}', text=text, created_at='şimdi', likes=0)
            for index, text in enumerate(texts)
        ],
    )


class QuestionPersistenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_database_for_tests()

    def test_01_health_reports_v120_and_sqlite(self):
        data = self.client.get('/health').json()
        self.assertEqual(data['version'], '1.4.0')
        self.assertEqual(data['storage'], 'sqlite')

    def test_02_question_contract_is_saved_in_history(self):
        payload = {
            'title': 'Gece bildirimleri uyku düzenini etkiler mi?',
            'comments': [
                'Gece bildirimleri varsayılan olarak sessize alınmalı.',
                'Bu etkinin dayandığı güvenilir araştırma var mı?',
                'Kullanıcı isterse bildirimleri yeniden açabilmeli.',
            ],
            'use_ai': False,
        }
        analyzed = self.client.post('/api/analyze-discussion', json=payload)
        self.assertEqual(analyzed.status_code, 200)
        post_id = analyzed.json()['post']['id']
        item = analyzed.json()['analysis']['unanswered_questions'][0]
        self.assertEqual(item['question_type'], 'Kaynak / Kanıt Talebi')
        self.assertEqual(item['answer_status'], 'Cevapsız')

        history = self.client.get('/api/history', params={'post_id': post_id}).json()['analyses'][0]
        reopened = self.client.get(f"/api/history/{history['id']}").json()['analysis']['unanswered_questions'][0]
        self.assertEqual(reopened['identity_key'], item['identity_key'])
        self.assertEqual(reopened['evidence_comment_ids'], item['evidence_comment_ids'])

    def test_03_identical_reanalysis_keeps_question_notification_dedup(self):
        payload = {
            'title': 'Kaynak sorusu bulunan tartışma',
            'comments': ['Kontrollü kullanım yararlı olabilir.', 'Tam yasak gerekli olabilir.', 'Bu karar hangi veriye dayanıyor?'],
            'use_ai': False,
        }
        analyzed = self.client.post('/api/analyze-discussion', json=payload).json()
        post_id = analyzed['post']['id']
        first = [item for item in self.client.get('/api/notifications').json()['notifications'] if item['post_id'] == post_id]
        self.client.get(f'/api/analyze/{post_id}', params={'use_ai': 'false'})
        second = [item for item in self.client.get('/api/notifications').json()['notifications'] if item['post_id'] == post_id]
        self.assertEqual([(item['kind'], item['text']) for item in first], [(item['kind'], item['text']) for item in second])

    def test_04_answered_question_does_not_create_source_request_notification(self):
        payload = {
            'title': 'Yanıt bağlantısı testi',
            'comments': [
                'Gece bildirimleri neden uyku düzenini bozuyor?',
                'Çünkü gece bildirimleri uykuyu bölüyor ve yeniden uyumayı geciktiriyor.',
                'Sessize alma seçeneği kullanıcıda kalmalı.',
            ],
            'use_ai': False,
        }
        analyzed = self.client.post('/api/analyze-discussion', json=payload).json()
        post_id = analyzed['post']['id']
        self.assertEqual(analyzed['analysis']['unanswered_questions'][0]['answer_status'], 'Cevaplandı')
        rows = [item for item in self.client.get('/api/notifications').json()['notifications'] if item['post_id'] == post_id]
        self.assertFalse(any(item['kind'] == 'source_request' for item in rows))

    def test_05_rhetorical_question_does_not_create_source_request_notification(self):
        payload = {
            'title': 'Retorik soru testi',
            'comments': ['Bu nasıl saçmalık?', 'Kurallı kullanım mümkün.', 'Tam yasak gerekli değil.'],
            'use_ai': False,
        }
        analyzed = self.client.post('/api/analyze-discussion', json=payload).json()
        post_id = analyzed['post']['id']
        self.assertEqual(analyzed['analysis']['unanswered_questions'], [])
        self.assertEqual(len(analyzed['analysis']['rhetorical_questions']), 1)
        rows = [item for item in self.client.get('/api/notifications').json()['notifications'] if item['post_id'] == post_id]
        self.assertFalse(any(item['kind'] == 'source_request' for item in rows))

    def test_06_answer_status_change_is_recorded_without_new_source_alert(self):
        base = make_post(8220, [
            'Gece bildirimleri neden uyku düzenini bozuyor?',
            'Bildirimler varsayılan olarak kapatılabilir.',
            'Kullanıcı kontrolü korunmalı.',
        ])
        first = analyze_post(base, use_ai=False)
        first, first_id = record_analysis_snapshot(base, first)
        record_analysis(base, first, history_id=first_id)
        before_ids = {item.id for item in list_notifications()}

        changed = base.model_copy(deep=True)
        changed.comments.append(Comment(
            id=4,
            author='K4',
            text='Çünkü gece bildirimleri uykuyu bölüyor ve yeniden uyumayı geciktiriyor.',
            created_at='şimdi',
            likes=0,
        ))
        second = analyze_post(changed, use_ai=False)
        second, second_id = record_analysis_snapshot(changed, second)
        record_analysis(changed, second, history_id=second_id)

        self.assertEqual(second.unanswered_questions[0].answer_status, 'Cevaplandı')
        self.assertTrue(any('yanıtlandığına ilişkin bağlantı' in note for note in second.changes_since_last_visit))
        new_rows = [item for item in list_notifications() if item.id not in before_ids]
        self.assertFalse(any(item.kind == 'source_request' for item in new_rows))

    def test_07_new_semantic_repeat_is_not_a_new_question_event(self):
        base = make_post(8221, [
            'Yasaklamanın öğrenci başarısına etkisini gösteren güvenilir bir araştırma var mı?',
            'Kontrollü kullanım yararlı olabilir.',
            'Tam yasak gerekli olabilir.',
        ])
        first = analyze_post(base, use_ai=False)
        first, first_id = record_analysis_snapshot(base, first)
        record_analysis(base, first, history_id=first_id)
        before_ids = {item.id for item in list_notifications()}

        changed = base.model_copy(deep=True)
        changed.comments.append(Comment(
            id=4,
            author='K4',
            text='Yapay zekâ yasağının başarı üzerindeki etkisine dair bir çalışma bulunuyor mu?',
            created_at='şimdi',
            likes=0,
        ))
        second = analyze_post(changed, use_ai=False)
        second, second_id = record_analysis_snapshot(changed, second)
        record_analysis(changed, second, history_id=second_id)

        self.assertEqual(len(second.unanswered_questions), 1)
        self.assertEqual(second.unanswered_questions[0].repeated_comment_ids, [4])
        self.assertFalse(any('yeni cevapsız soru' in note.casefold() for note in second.changes_since_last_visit))
        new_rows = [item for item in list_notifications() if item.id not in before_ids]
        self.assertFalse(any(item.kind == 'source_request' for item in new_rows))

    def test_08_question_fields_survive_real_process_restart(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='nkopru_v120_restart_') as temp_dir:
            db_path = Path(temp_dir) / 'restart.db'
            env = os.environ.copy()
            env['N_KOPRU_DB_PATH'] = str(db_path)
            env['PYTHONPATH'] = str(root)
            create_code = """
import json
from fastapi.testclient import TestClient
from app.database import reset_database_for_tests
from app.main import app
reset_database_for_tests()
client = TestClient(app)
payload = {
  'title': 'Restart soru testi',
  'comments': ['Kontrollü kullanım olabilir.', 'Tam yasak düşünülebilir.', 'Bu karar hangi veriye dayanıyor?'],
  'use_ai': False,
}
created = client.post('/api/analyze-discussion', json=payload).json()
history = client.get('/api/history', params={'post_id': created['post']['id']}).json()['analyses'][0]
print(json.dumps({'history_id': history['id'], 'identity_key': created['analysis']['unanswered_questions'][0]['identity_key']}))
"""
            first = subprocess.run([sys.executable, '-c', create_code], cwd=root, env=env, text=True, capture_output=True, check=True)
            created = json.loads(first.stdout.strip().splitlines()[-1])
            read_code = f"""
import json
from fastapi.testclient import TestClient
from app.main import app
item = TestClient(app).get('/api/history/{created['history_id']}').json()['analysis']['unanswered_questions'][0]
print(json.dumps(item))
"""
            second = subprocess.run([sys.executable, '-c', read_code], cwd=root, env=env, text=True, capture_output=True, check=True)
            reopened = json.loads(second.stdout.strip().splitlines()[-1])
            self.assertEqual(reopened['identity_key'], created['identity_key'])
            self.assertEqual(reopened['answer_status'], 'Cevapsız')
            self.assertEqual(reopened['question_type'], 'Kaynak / Kanıt Talebi')


if __name__ == '__main__':
    unittest.main(verbosity=2)
