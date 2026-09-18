"""Proje içi, elle etiketlenmiş ve konu bakımından dengeli doğrulama seti.

Bu cümleler bağımsız bir araştırma veri kümesi değildir. Amaç; aynı ürün
sınıflandırıcısının farklı tartışma başlıklarında, olumsuzlama içeren
ifadelerde ve örtük tutumlarda nasıl davrandığını açıkça incelemektir.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioCase:
    text: str
    expected_label: str
    difficulty: str
    challenge: str


@dataclass(frozen=True)
class ValidationScenario:
    key: str
    title: str
    topic: str
    description: str
    cases: tuple[ScenarioCase, ...]


def _case(text: str, label: str, difficulty: str, challenge: str) -> ScenarioCase:
    return ScenarioCase(text, label, difficulty, challenge)


SUPPORT = 'Destekleyen'
RESTRICT = 'Karşı / Sınırlayıcı'
CONDITIONAL = 'Koşullu / Dengeli'
NEUTRAL = 'Soru / Tarafsız'


SCENARIOS: tuple[ValidationScenario, ...] = (
    ValidationScenario(
        key='akademik-yapay-zeka',
        title='Üniversite ödevlerinde üretken yapay zekâ kullanımı nasıl düzenlenmeli?',
        topic='Akademik yapay zekâ',
        description='Eğitimde yarar, yasak, kontrollü kullanım ve kanıt ihtiyacı.',
        cases=(
            _case('Üretken yapay zekâ öğrencilerin öğrenmesi için faydalı bir araçtır.', SUPPORT, 'temel', 'açık destek'),
            _case('Öğrencilerin bu araçları kullanması serbest olmalı.', SUPPORT, 'temel', 'açık destek'),
            _case('Yapay zekâ kullanımının tamamen yasaklanmasına karşıyım.', SUPPORT, 'zor', 'olumsuzlamalı destek'),
            _case('Tamamen yasaklamak yanlış, öğrenciler araçlardan yararlanabilmeli.', SUPPORT, 'zor', 'karşıt ifade'),
            _case('Bu araçlara erişimin devam etmesinden yanayım.', SUPPORT, 'zor', 'örtük destek'),
            _case('Ödevlerde yapay zekâ kullanımı kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Bütün ödevi yapay zekâya yaptırmak ciddi sorun.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Hazır metin teslim etmek akademik güvenilirliğe zarar veriyor.', RESTRICT, 'zor', 'gerekçeli kısıtlama'),
            _case('Ödevin tamamını yapay zekâya yaptırmak ciddi problem.', RESTRICT, 'zor', 'sonuç odaklı kısıtlama'),
            _case('Sınav salonunda bu araçlara erişim kapatılmalı.', RESTRICT, 'zor', 'örtük kısıtlama'),
            _case('Kontrollü kullanım ve açık kurallar birlikte belirlenmeli.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Kaynak gösterme şartıyla yapay zekâdan yararlanılabilir.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Yasak yerine etik kullanım yönergesi hazırlanmalı.', CONDITIONAL, 'zor', 'yasak yerine koşul'),
            _case('Denetim ve şeffaflık sağlanırsa sınırlı kullanıma izin verilebilir.', CONDITIONAL, 'zor', 'çoklu koşul'),
            _case('Ben ders çalışırken açıklama almak için kullanıyorum, ödevimi ona yazdırmıyorum.', CONDITIONAL, 'zor', 'sınırlı kişisel kullanım'),
            _case('Bu araçların öğrenmeye etkisini gösteren araştırma var mı?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Başarı düzeyi hangi yöntemle karşılaştırılacak?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Bu oranın kaynağı hangi araştırmaya dayanıyor?', NEUTRAL, 'zor', 'kaynak sorgulaması'),
            _case('Yasak kararının etkisini ölçen veri yayımlandı mı?', NEUTRAL, 'zor', 'tarafsız kanıt talebi'),
            _case('Kaynak belirtilmediği sürece yüzde vermek çok anlamlı değil.', NEUTRAL, 'zor', 'sorusuz kanıt eleştirisi'),
        ),
    ),
    ValidationScenario(
        key='okulda-telefon',
        title='Okullarda öğrencilerin telefon kullanımı yasaklanmalı mı?',
        topic='Okulda telefon kullanımı',
        description='İletişim yararı, ders disiplini, sınırlı izin ve ölçülebilir etki.',
        cases=(
            _case('Acil durumda aileyle iletişim için telefon faydalı olabilir.', SUPPORT, 'temel', 'açık destek'),
            _case('Öğrencilerin teneffüste telefon kullanması serbest olmalı.', SUPPORT, 'temel', 'açık destek'),
            _case('Telefonların okulda tamamen yasaklanmasına karşıyım.', SUPPORT, 'zor', 'olumsuzlamalı destek'),
            _case('Telefonu tamamen yasaklamak yanlış, erişim devam etmeli.', SUPPORT, 'zor', 'karşıt ifade'),
            _case('Ders aralarında iletişim hakkının sürmesini istiyorum.', SUPPORT, 'zor', 'örtük destek'),
            _case('Ders sırasında telefon kullanımı kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Sürekli ekranla uğraşmak öğrencilerin dikkatine zarar veriyor.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Sınavda telefonla mesajlaşmak ciddi sorun oluşturuyor.', RESTRICT, 'zor', 'gerekçeli kısıtlama'),
            _case('Dersin tamamında telefona bakmak ciddi problem.', RESTRICT, 'zor', 'sonuç odaklı kısıtlama'),
            _case('Sınav salonuna kişisel cihaz alınmamalı.', RESTRICT, 'zor', 'örtük kısıtlama'),
            _case('Telefonlar öğretmen denetimi altında kullanılabilir.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Ders dışı saatlerde açık kurallarla izin verilmeli.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Tam yasak yerine yaşa göre kontrollü kullanım düşünülmeli.', CONDITIONAL, 'zor', 'yasak yerine koşul'),
            _case('Acil iletişim şartıyla kullanım belirli alanlarda serbest olabilir.', CONDITIONAL, 'zor', 'çoklu koşul'),
            _case('Kullanım amacı ve okulun yönergesi birlikte değerlendirilmelidir.', CONDITIONAL, 'zor', 'bağlamsal koşul'),
            _case('Telefon yasağının dikkat düzeyine etkisini ölçen çalışma var mı?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Acil durumlarda ailelere nasıl ulaşılacak?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Paylaşılan başarı oranının güvenilir kaynağı nedir?', NEUTRAL, 'zor', 'kaynak sorgulaması'),
            _case('Telefon kullanımı ile ders başarısı arasında karşılaştırmalı veri var mı?', NEUTRAL, 'zor', 'tarafsız kanıt talebi'),
            _case('Araştırma paylaşılmalı; aksi halde verilen oran doğrulanamaz.', NEUTRAL, 'zor', 'sorusuz kanıt eleştirisi'),
        ),
    ),
    ValidationScenario(
        key='kampus-ulasimi',
        title='Kampüste gece ücretsiz ulaşım hizmeti sürdürülmeli mi?',
        topic='Kampüs gece ulaşımı',
        description='Erişim yararı, bütçe itirazı, saat koşulları ve maliyet verisi.',
        cases=(
            _case('Gece ulaşımı öğrencilerin güvenliği için faydalı bir hizmettir.', SUPPORT, 'temel', 'açık destek'),
            _case('Öğrencilerin gece servisinden yararlanması serbest olmalı.', SUPPORT, 'temel', 'açık destek'),
            _case('Gece servisinin tamamen yasaklanmasına karşıyım.', SUPPORT, 'zor', 'olumsuzlamalı destek'),
            _case('Servisi tamamen yasaklamak yanlış, güvenli erişim sürmeli.', SUPPORT, 'zor', 'karşıt ifade'),
            _case('Gece hattının hizmet vermeye devam etmesini savunuyorum.', SUPPORT, 'zor', 'örtük destek'),
            _case('Tehlikeli güzergâhta izinsiz servis kullanımı kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Boş araçların sürekli çalışması çevreye zarar veriyor.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Denetimsiz sürücü kullanılması ciddi sorun oluşturuyor.', RESTRICT, 'zor', 'gerekçeli kısıtlama'),
            _case('Güvenlik kaydı olmayan araçların çalışması ciddi problem.', RESTRICT, 'zor', 'sonuç odaklı kısıtlama'),
            _case('Gece vardiyasındaki araç sayısı azaltılmalı.', RESTRICT, 'zor', 'örtük kısıtlama'),
            _case('Servis kontrollü güzergâhlarda hizmet vermeli.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Güvenlik denetimi ve açık kurallar uygulanmalı.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Tam iptal yerine kullanım saatleri için yönerge hazırlanmalı.', CONDITIONAL, 'zor', 'yasak yerine koşul'),
            _case('Talep oluşması şartıyla belirli saatlerde ücretsiz servis olabilir.', CONDITIONAL, 'zor', 'çoklu koşul'),
            _case('Bağlama göre rota ve yolcu sayısı sınırlandırılmalı.', CONDITIONAL, 'zor', 'bağlamsal koşul'),
            _case('Gece servisinin gerçek maliyeti ne kadar?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Hangi güzergâhta kaç öğrenci taşınıyor?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Güvenlik karşılaştırmasının kaynağı hangi raporda?', NEUTRAL, 'zor', 'kaynak sorgulaması'),
            _case('Servis kaldırılırsa güvenlik olaylarını gösteren veri var mı?', NEUTRAL, 'zor', 'tarafsız kanıt talebi'),
            _case('Kaynak belirtilmeden açıklanan yolcu oranı güvenilir sayılmaz.', NEUTRAL, 'zor', 'sorusuz kanıt eleştirisi'),
        ),
    ),
    ValidationScenario(
        key='uzaktan-calisma',
        title='Şirketlerde uzaktan çalışma uygulaması sürdürülmeli mi?',
        topic='Uzaktan çalışma',
        description='Esneklik yararı, ekip riski, hibrit koşullar ve verimlilik kanıtı.',
        cases=(
            _case('Uzaktan çalışma çalışanların yaşam dengesi için faydalı.', SUPPORT, 'temel', 'açık destek'),
            _case('Uygun görevlerde evden çalışma serbest olmalı.', SUPPORT, 'temel', 'açık destek'),
            _case('Uzaktan çalışmanın tamamen yasaklanmasına karşıyım.', SUPPORT, 'zor', 'olumsuzlamalı destek'),
            _case('Evden çalışmayı yasaklamak yanlış, esnek seçenekler sürmeli.', SUPPORT, 'zor', 'karşıt ifade'),
            _case('Çalışanların mekân seçimini korumasından yanayım.', SUPPORT, 'zor', 'örtük destek'),
            _case('Gizli belgelerin ortak ağda paylaşılması kesinlikle yasaklanmalı.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Sürekli erişilebilir olma baskısı çalışan sağlığına zarar veriyor.', RESTRICT, 'temel', 'açık kısıtlama'),
            _case('Güvenliksiz bağlantı üzerinden müşteri bilgisi işlemek ciddi sorun.', RESTRICT, 'zor', 'gerekçeli kısıtlama'),
            _case('Mesai sınırının tamamen ortadan kalkması ciddi problem.', RESTRICT, 'zor', 'sonuç odaklı kısıtlama'),
            _case('Kritik ekip toplantıları yalnızca ofiste yapılmalı.', RESTRICT, 'zor', 'örtük kısıtlama'),
            _case('Uzaktan çalışma açık kurallarla uygulanmalı.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Veri güvenliği denetimi altında hibrit çalışma sürdürülebilir.', CONDITIONAL, 'temel', 'açık koşul'),
            _case('Tam yasak yerine ekip ihtiyacına göre yönerge belirlenmeli.', CONDITIONAL, 'zor', 'yasak yerine koşul'),
            _case('Müşteri verisi korunması şartıyla evden çalışmaya izin verilebilir.', CONDITIONAL, 'zor', 'çoklu koşul'),
            _case('Görevin niteliğine ve bağlama göre kontrollü geçiş yapılmalı.', CONDITIONAL, 'zor', 'bağlamsal koşul'),
            _case('Uzaktan çalışmanın verimliliğe etkisi nasıl ölçüldü?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Ofis ve ev giderlerini karşılaştıran veri var mı?', NEUTRAL, 'temel', 'açık bilgi sorusu'),
            _case('Paylaşılan verimlilik oranının güvenilir kaynağı nedir?', NEUTRAL, 'zor', 'kaynak sorgulaması'),
            _case('Ekip bağlılığına ilişkin bağımsız araştırma yayımlandı mı?', NEUTRAL, 'zor', 'tarafsız kanıt talebi'),
            _case('Veri olmadan açıklanan başarı oranı tek başına yeterli değil.', NEUTRAL, 'zor', 'sorusuz kanıt eleştirisi'),
        ),
    ),
)


SCENARIO_DATASET_NAME = 'N-KÖPRÜ çok konulu elle etiketlenmiş iç doğrulama seti'
SCENARIO_DATASET_VERSION = '2026.08.22-v1'
SCENARIO_LIMITATION = (
    'Bu değerlendirme dört konu için proje ekibince hazırlanmış 80 elle '
    'etiketli Türkçe cümleyle sınırlıdır. Bağımsız dış veri seti, akademik '
    'benchmark, gerçek kullanıcı başarısı veya bilimsel genelleme değildir.'
)
SCENARIO_CALIBRATION_NOTE = (
    'Önceki proje içi sınıflandırma hataları konu-bağımsız dil kurallarını '
    'iyileştirmek için incelenmiştir. Bu nedenle aynı 80 örnekte elde edilen '
    'sonuç bağımsız tutma testi veya dış benchmark olarak yorumlanamaz.'
)


def scenario_dataset_info() -> dict:
    cases = [case for scenario in SCENARIOS for case in scenario.cases]
    labels = (SUPPORT, RESTRICT, CONDITIONAL, NEUTRAL)
    return {
        'name': SCENARIO_DATASET_NAME,
        'version': SCENARIO_DATASET_VERSION,
        'sample_count': len(cases),
        'scenario_count': len(SCENARIOS),
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
            for scenario in SCENARIOS
        ],
        'is_external_benchmark': False,
        'contains_user_content': False,
        'limitation': SCENARIO_LIMITATION,
        'calibration_note': SCENARIO_CALIBRATION_NOTE,
    }
