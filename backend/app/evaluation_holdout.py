"""Önceki kalibrasyon örneklerinden ayrılmış, dürüst proje içi kontrol.

Bu dosya bilimsel dış benchmark değildir. Konular ve bütün cümleler önceki
80 örnekten farklıdır; kesişim ile içerik parmak izi çalıştırılmadan önce
hesaplanır ve kullanıcıya açıkça gösterilir.
"""
from __future__ import annotations

import hashlib
import json
import re

from .evaluation_scenarios import (
    CONDITIONAL,
    NEUTRAL,
    RESTRICT,
    SCENARIO_DATASET_VERSION,
    SCENARIOS,
    SUPPORT,
    ScenarioCase,
    ValidationScenario,
)


def _case(text: str, label: str, difficulty: str, challenge: str) -> ScenarioCase:
    return ScenarioCase(text, label, difficulty, challenge)


HOLDOUT_SCENARIOS: tuple[ValidationScenario, ...] = (
    ValidationScenario(
        key='ayri-mahalle-parki',
        title='Mahalle parkları akşam saatlerinde açık kalmalı mı?',
        topic='Mahalle parkı erişimi',
        description='Kamusal alan erişimi, güvenlik sınırları, saat koşulları ve ölçüm.',
        cases=(
            _case('Mahalle parkının açık kalması aileler için faydalı olur.', SUPPORT, 'temel', 'açık kamusal alan desteği'),
            _case('Vatandaşların parktan akşam yararlanması serbest olmalı.', SUPPORT, 'temel', 'açık erişim desteği'),
            _case('Park erişiminin devam etmesinden yanayım.', SUPPORT, 'zor', 'kamusal erişim sürekliliği'),
            _case('Parkı tamamen yasaklamak yanlış; mahalleli alanı kullanabilmeli.', SUPPORT, 'zor', 'olumsuzlamalı park desteği'),
            _case('Parkta gece yüksek sesli etkinlikler kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık gürültü kısıtlaması'),
            _case('Kontrolsüz gece gürültüsü mahalle sakinlerine zarar veriyor.', RESTRICT, 'temel', 'zarar odaklı park itirazı'),
            _case('Denetimsiz park kullanımı mahalle güvenliği için ciddi sorun.', RESTRICT, 'zor', 'olumsuz denetim ve risk'),
            _case('Gece boyunca aydınlatmasız alanların açık olması ciddi problem.', RESTRICT, 'zor', 'gerekçeli park sınırlaması'),
            _case('Parklar kontrollü ve belirli saatlerde kullanılabilir.', CONDITIONAL, 'temel', 'açık saat koşulu'),
            _case('Güvenlik denetimi ve açık kurallar birlikte uygulanmalı.', CONDITIONAL, 'temel', 'açık güvenlik koşulu'),
            _case('Aydınlatma sağlanması şartıyla akşam park kullanımı sürdürülebilir.', CONDITIONAL, 'zor', 'aydınlatmaya bağlı erişim'),
            _case('Tam kapatma yerine mahalle ihtiyaçlarına uygun yönerge hazırlanmalı.', CONDITIONAL, 'zor', 'yasak yerine yerel kural'),
            _case('Parkların gece açık kalmasının güvenliğe etkisi ölçüldü mü?', NEUTRAL, 'temel', 'park güvenliği sorusu'),
            _case('Akşam saatlerinde parkı kaç kişi ziyaret ediyor?', NEUTRAL, 'temel', 'park kullanım verisi'),
            _case('Gürültü şikâyetlerinin kaynağı hangi belediye raporuna dayanıyor?', NEUTRAL, 'zor', 'park kaynak sorgulaması'),
            _case('Ölçüm verisi paylaşılmalı; açıklanan şikâyet oranı doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz park kanıt talebi'),
        ),
    ),
    ValidationScenario(
        key='ayri-okul-kantini',
        title='Okul kantinlerinde şekerli ürün satışı sürmeli mi?',
        topic='Okul kantini beslenmesi',
        description='Ürün seçimi, çocuk sağlığı, yaşa uygun satış ve beslenme verisi.',
        cases=(
            _case('Kantinde sağlıklı seçeneklerin bulunması öğrenciler için faydalı.', SUPPORT, 'temel', 'açık kantin seçeneği desteği'),
            _case('Öğrencilerin uygun kantin ürünlerini seçmesi serbest olmalı.', SUPPORT, 'temel', 'açık ürün seçimi'),
            _case('Kantin hizmetinin devam etmesinden yanayım.', SUPPORT, 'zor', 'kantin hizmeti sürekliliği'),
            _case('Kantindeki bütün seçenekleri tamamen yasaklamak yanlış.', SUPPORT, 'zor', 'olumsuzlamalı ürün desteği'),
            _case('Çocuklara yüksek şekerli içecek satışı kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık şekerli ürün kısıtı'),
            _case('Aşırı şeker tüketimi çocukların sağlığına zarar veriyor.', RESTRICT, 'temel', 'çocuk sağlığı riski'),
            _case('Denetimsiz enerji içeceği satılması ciddi sorun oluşturuyor.', RESTRICT, 'zor', 'denetimsiz kantin satışı'),
            _case('Etiketsiz ürünlerin çocuklara sunulması ciddi problem.', RESTRICT, 'zor', 'etiketsiz ürün itirazı'),
            _case('Kantin satışı yaşa uygun açık kurallarla düzenlenmeli.', CONDITIONAL, 'temel', 'açık beslenme kuralı'),
            _case('Ürünler okul denetimi altında kontrollü biçimde satılabilir.', CONDITIONAL, 'temel', 'açık kantin denetimi'),
            _case('Şeker içeriği belirtilmesi şartıyla belirli ürünler sunulabilir.', CONDITIONAL, 'zor', 'ürün etiketine bağlı izin'),
            _case('Tam yasak yerine diyetisyen onaylı kantin yönergesi hazırlanmalı.', CONDITIONAL, 'zor', 'yasak yerine beslenme kuralı'),
            _case('Kantin ürünlerinin öğrenci sağlığına etkisini gösteren veri var mı?', NEUTRAL, 'temel', 'kantin sağlık etkisi sorusu'),
            _case('Şeker tüketimi hangi yaş gruplarında karşılaştırıldı?', NEUTRAL, 'temel', 'yaş grubu karşılaştırması'),
            _case('Paylaşılan obezite oranının güvenilir kaynağı hangi çalışma?', NEUTRAL, 'zor', 'beslenme araştırması sorgusu'),
            _case('Araştırma verisi sunulmalı; verilen tüketim oranı doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz beslenme kanıtı'),
        ),
    ),
    ValidationScenario(
        key='ayri-geri-donusum',
        title='Kentte geri dönüşüm ayrıştırması yaygınlaştırılmalı mı?',
        topic='Kentte geri dönüşüm',
        description='Çevresel yarar, zorunluluk riski, erişilebilir uygulama ve ölçüm.',
        cases=(
            _case('Geri dönüşümün yaygınlaşması çevre için faydalı olur.', SUPPORT, 'temel', 'açık çevresel destek'),
            _case('Mahallelerin geri dönüşüm hizmetinden yararlanması serbest olmalı.', SUPPORT, 'temel', 'açık geri dönüşüm erişimi'),
            _case('Geri dönüşüm hizmetinin devam etmesinden yanayım.', SUPPORT, 'zor', 'geri dönüşüm sürekliliği'),
            _case('Geri dönüşüm kutularını tamamen yasaklamak yanlış.', SUPPORT, 'zor', 'olumsuzlamalı geri dönüşüm desteği'),
            _case('İzinsiz atık dökümü kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık atık kısıtlaması'),
            _case('Karışık atıkların denize bırakılması çevreye zarar veriyor.', RESTRICT, 'temel', 'açık çevresel zarar'),
            _case('Denetimsiz atık toplama araçları ciddi sorun oluşturuyor.', RESTRICT, 'zor', 'denetimsiz atık yönetimi'),
            _case('Korumasız tehlikeli atık taşınması ciddi problem.', RESTRICT, 'zor', 'tehlikeli atık sınırlaması'),
            _case('Atık ayrıştırması açık kurallar ve denetimle uygulanmalı.', CONDITIONAL, 'temel', 'açık ayrıştırma koşulu'),
            _case('Geri dönüşüm kontrollü ve erişilebilir noktalarda yapılabilir.', CONDITIONAL, 'temel', 'erişilebilir uygulama'),
            _case('Mahalleye yeterli kutu sağlanması şartıyla ayrıştırma yaygınlaşabilir.', CONDITIONAL, 'zor', 'altyapıya bağlı ayrıştırma'),
            _case('Ceza yerine bilgilendirme ve uygulama yönergesi hazırlanmalı.', CONDITIONAL, 'zor', 'ceza yerine açıklayıcı kural'),
            _case('Geri dönüşüm oranının gerçekten arttığını gösteren veri var mı?', NEUTRAL, 'temel', 'geri dönüşüm etkisi sorusu'),
            _case('Ayrıştırılan atıklar hangi tesiste değerlendiriliyor?', NEUTRAL, 'temel', 'atık tesisi sorusu'),
            _case('Belediyenin açıkladığı kazanım oranının kaynağı hangi rapor?', NEUTRAL, 'zor', 'atık verisinin kaynağı'),
            _case('Örneklem açıklanmalı; paylaşılan geri dönüşüm oranı doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz çevre verisi talebi'),
        ),
    ),
    ValidationScenario(
        key='ayri-halk-kutuphanesi',
        title='Halk kütüphaneleri hafta sonu açık kalmalı mı?',
        topic='Halk kütüphanesi erişimi',
        description='Bilgiye erişim, bütçe ve personel sınırı, planlı saatler ve veri.',
        cases=(
            _case('Kütüphanenin hafta sonu açık kalması öğrenciler için faydalı.', SUPPORT, 'temel', 'açık kütüphane desteği'),
            _case('Vatandaşların hafta sonu kütüphane kullanması serbest olmalı.', SUPPORT, 'temel', 'açık bilgi erişimi'),
            _case('Kütüphane erişiminin devam etmesinden yanayım.', SUPPORT, 'zor', 'bilgi erişimi sürekliliği'),
            _case('Kütüphane hizmetini tamamen yasaklamak yanlış.', SUPPORT, 'zor', 'olumsuzlamalı kütüphane desteği'),
            _case('Kütüphanede izinsiz kişisel veri paylaşımı kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık kütüphane gizliliği kısıtı'),
            _case('Yetersiz personelle sürekli açık kalmak hizmet kalitesine zarar veriyor.', RESTRICT, 'temel', 'personel yetersizliği riski'),
            _case('Denetimsiz gece girişleri ziyaretçiler için ciddi sorun.', RESTRICT, 'zor', 'denetimsiz kütüphane girişi'),
            _case('Gözetimsiz çocukların binada kalması ciddi problem.', RESTRICT, 'zor', 'gözetimsiz erişim riski'),
            _case('Kütüphane kontrollü saatlerde ve açık kurallarla kullanılabilir.', CONDITIONAL, 'temel', 'açık kütüphane saatleri'),
            _case('Hafta sonu hizmeti personel denetimi altında sürdürülebilir.', CONDITIONAL, 'temel', 'açık personel koşulu'),
            _case('Yeterli görevli bulunması şartıyla okuma salonu açık kalabilir.', CONDITIONAL, 'zor', 'personele bağlı kütüphane erişimi'),
            _case('Tam kapatma yerine kütüphane kullanım yönergesi hazırlanmalı.', CONDITIONAL, 'zor', 'kapatma yerine planlı erişim'),
            _case('Hafta sonu kütüphaneyi kaç kişi kullanıyor?', NEUTRAL, 'temel', 'kütüphane ziyaretçi sorusu'),
            _case('Ek çalışma saatlerinin gerçek maliyeti ne kadar?', NEUTRAL, 'temel', 'kütüphane maliyet sorusu'),
            _case('Kullanım artışını gösteren verinin güvenilir kaynağı nedir?', NEUTRAL, 'zor', 'kütüphane veri kaynağı'),
            _case('Ziyaretçi verisi paylaşılmalı; açıklanan doluluk oranı doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz kütüphane ölçümü'),
        ),
    ),
    ValidationScenario(
        key='ayri-dijital-oyun',
        title='Çocukların dijital oyun süresi nasıl belirlenmeli?',
        topic='Çocuklarda dijital oyun',
        description='Oyun hakkı, gelişim riski, yaşa uygun süre ve araştırma ihtiyacı.',
        cases=(
            _case('Yaşa uygun dijital oyunlar çocukların öğrenmesi için faydalı olabilir.', SUPPORT, 'temel', 'açık dijital oyun desteği'),
            _case('Çocukların güvenli dijital oyunlardan yararlanması serbest olmalı.', SUPPORT, 'temel', 'açık oyun erişimi'),
            _case('Çocukların oyun hakkının devam etmesinden yanayım.', SUPPORT, 'zor', 'çocuk oyun hakkı sürekliliği'),
            _case('Dijital oyunların tamamını yasaklamak yanlış.', SUPPORT, 'zor', 'olumsuzlamalı oyun desteği'),
            _case('Şiddet içeren oyunlara denetimsiz erişim kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık çocuk güvenliği kısıtı'),
            _case('Gece boyunca ekrana bakmak çocukların uyku düzenine zarar veriyor.', RESTRICT, 'temel', 'açık uyku etkisi'),
            _case('Denetimsiz çevrim içi iletişim çocuk güvenliği için ciddi sorun.', RESTRICT, 'zor', 'denetimsiz dijital iletişim'),
            _case('Yaş sınırı olmayan satın alma seçenekleri ciddi problem.', RESTRICT, 'zor', 'oyun içi satın alma riski'),
            _case('Dijital oyun süresi kontrollü ve yaşa uygun olmalı.', CONDITIONAL, 'temel', 'açık yaş ve süre koşulu'),
            _case('Aile denetimi ve açık kurallar birlikte uygulanmalı.', CONDITIONAL, 'temel', 'açık ebeveyn denetimi'),
            _case('Uyku düzeni korunması şartıyla sınırlı oyun süresi tanınabilir.', CONDITIONAL, 'zor', 'uykuya bağlı oyun izni'),
            _case('Tam yasak yerine aileyle birlikte oyun yönergesi hazırlanmalı.', CONDITIONAL, 'zor', 'yasak yerine aile kuralı'),
            _case('Oyun süresinin çocuk gelişimine etkisini inceleyen araştırma var mı?', NEUTRAL, 'temel', 'çocuk gelişimi sorusu'),
            _case('Yaş gruplarına göre önerilen ekran süresi nedir?', NEUTRAL, 'temel', 'ekran süresi sorusu'),
            _case('Paylaşılan bağımlılık oranının güvenilir kaynağı hangi çalışma?', NEUTRAL, 'zor', 'çocuk araştırması sorgusu'),
            _case('Araştırma örneklemi açıklanmalı; verilen bağımlılık oranı doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz çocuk verisi eleştirisi'),
        ),
    ),
)

HOLDOUT_DATASET_NAME = 'N-KÖPRÜ önceki örneklerden ayrılmış yeni proje içi kontrol seti'
HOLDOUT_DATASET_VERSION = '2026.08.24-heldout-v1'
HOLDOUT_LIMITATION = (
    'Bu kontrol seti önceki 80 kalibrasyon örneğiyle aynı cümleleri veya '
    'tartışma konularını paylaşmaz; yine proje ekibince hazırlanmış 80 Türkçe '
    'ifadeyle sınırlıdır. Bağımsız dış veri, akademik benchmark, gerçek '
    'kullanıcı performansı veya bilimsel genelleme değildir.'
)


def _normalized(value: str) -> str:
    return re.sub(r'\s+', ' ', value.casefold()).strip()


def holdout_dataset_info() -> dict:
    cases = [case for scenario in HOLDOUT_SCENARIOS for case in scenario.cases]
    labels = (SUPPORT, RESTRICT, CONDITIONAL, NEUTRAL)
    old_texts = {
        _normalized(case.text)
        for scenario in SCENARIOS
        for case in scenario.cases
    }
    new_texts = {_normalized(case.text) for case in cases}
    old_topics = {_normalized(scenario.topic) for scenario in SCENARIOS}
    new_topics = {_normalized(scenario.topic) for scenario in HOLDOUT_SCENARIOS}
    fingerprint_payload = [
        {
            'scenario': scenario.key,
            'title': scenario.title,
            'text': case.text,
            'expected': case.expected_label,
            'difficulty': case.difficulty,
        }
        for scenario in HOLDOUT_SCENARIOS
        for case in scenario.cases
    ]
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        ).encode('utf-8')
    ).hexdigest()
    text_overlap = len(old_texts.intersection(new_texts))
    topic_overlap = len(old_topics.intersection(new_topics))
    return {
        'name': HOLDOUT_DATASET_NAME,
        'version': HOLDOUT_DATASET_VERSION,
        'sample_count': len(cases),
        'scenario_count': len(HOLDOUT_SCENARIOS),
        'label_count': len(labels),
        'label_distribution': {
            label: sum(case.expected_label == label for case in cases)
            for label in labels
        },
        'difficulty_distribution': {
            level: sum(case.difficulty == level for case in cases)
            for level in ('temel', 'zor')
        },
        'scenarios': [
            {
                'key': scenario.key,
                'title': scenario.title,
                'topic': scenario.topic,
                'description': scenario.description,
                'sample_count': len(scenario.cases),
            }
            for scenario in HOLDOUT_SCENARIOS
        ],
        'is_external_benchmark': False,
        'contains_user_content': False,
        'dataset_role': 'separate-project-internal-control',
        'calibration_dataset_version': SCENARIO_DATASET_VERSION,
        'calibration_sample_overlap_count': text_overlap,
        'calibration_topic_overlap_count': topic_overlap,
        'is_disjoint_from_calibration': text_overlap == 0 and topic_overlap == 0,
        'frozen_sha256': fingerprint,
        'limitation': HOLDOUT_LIMITATION,
        'calibration_note': (
            'Önceki 80 örnekle metin/konu çakışması hesaplanır ve içerik '
            'SHA-256 ile sabitlenir. Bu ayrım projeye içkindir; bağımsız '
            'akademik doğrulama yerine geçmez.'
        ),
    }
