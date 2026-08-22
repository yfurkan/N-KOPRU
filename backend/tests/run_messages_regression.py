import unittest

from fastapi.testclient import TestClient

from app.main import app


class MessagesRegression(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_health_version(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['version'], '1.4.0')

    def test_02_conversations_available(self):
        r = self.client.get('/api/messages')
        self.assertEqual(r.status_code, 200)
        rows = r.json()['conversations']
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(any(row['title'] == 'Ekip görüşmesi' for row in rows))

    def test_03_open_conversation_marks_read(self):
        before = self.client.get('/api/messages').json()['conversations']
        system = next(row for row in before if row['id'] == 1)
        self.assertGreaterEqual(system['unread_count'], 0)
        r = self.client.get('/api/messages/1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['conversation']['unread_count'], 0)

    def test_04_unknown_conversation_is_404(self):
        r = self.client.get('/api/messages/99999')
        self.assertEqual(r.status_code, 404)

    def test_05_send_message(self):
        text = 'Ekip için test mesajı.'
        r = self.client.post('/api/messages/2', json={'text': text})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['text'], text)
        self.assertTrue(r.json()['is_mine'])
        detail = self.client.get('/api/messages/2').json()
        self.assertTrue(any(item['text'] == text for item in detail['messages']))

    def test_06_empty_message_rejected(self):
        r = self.client.post('/api/messages/2', json={'text': ''})
        self.assertEqual(r.status_code, 422)

    def test_07_share_bridge_card(self):
        payload = {
            'conversation_id': 2,
            'post_id': 1,
            'title': 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?',
            'summary': 'Örnek özet',
            'common_acceptance': 'Kaynak ve gerekçe önemli.',
            'main_divergence': 'Yasaklama düzeyi.',
            'missing_information': 'Etkilere dair karşılaştırmalı kanıt.',
            'bridge_question': 'Hangi kullanım koşulları kabul edilebilir?',
        }
        r = self.client.post('/api/messages/bridge/share', json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsNotNone(data['attachment'])
        self.assertEqual(data['attachment']['kind'], 'bridge')
        self.assertEqual(data['attachment']['post_id'], 1)
        self.assertEqual(data['attachment']['tab_index'], 7)
        self.assertEqual(data['attachment']['bridge_question'], payload['bridge_question'])

    def test_08_bridge_persists_in_session(self):
        detail = self.client.get('/api/messages/2').json()
        attachments = [m['attachment'] for m in detail['messages'] if m.get('attachment')]
        self.assertTrue(any(a['kind'] == 'bridge' for a in attachments))

    def test_09_conversation_preview_updates_after_send(self):
        text = 'Son mesaj önizleme testi.'
        self.client.post('/api/messages/2', json={'text': text})
        rows = self.client.get('/api/messages').json()['conversations']
        demo = next(row for row in rows if row['id'] == 2)
        self.assertEqual(demo['last_message'], text)
        self.assertEqual(demo['last_time'], 'Şimdi')

    def test_10_unknown_send_is_404(self):
        r = self.client.post('/api/messages/99999', json={'text': 'test'})
        self.assertEqual(r.status_code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
