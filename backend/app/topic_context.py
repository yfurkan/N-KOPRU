"""Görüş kartı, özet ve Köprü için ortak, cihazdan bağımsız konu bağlamı.

Kanonik görüş adları burada değiştirilmez. Üretilen metinler yalnızca
kullanıcının gördüğü açıklamaları özelleştirir; kayıtlı olay kimlikleri,
snapshot karşılaştırması ve bildirim parmak izleri aynı kalır.
"""
from __future__ import annotations

from dataclasses import dataclass


SUPPORT = 'Destekleyen'
RESTRICT = 'Karşı / Sınırlayıcı'
CONDITIONAL = 'Koşullu / Dengeli'
NEUTRAL = 'Soru / Tarafsız'
OTHER = 'Diğer / Nötr'


@dataclass(frozen=True)
class TopicContext:
    key: str
    subject: str
    support_name: str
    restriction_name: str
    conditional_name: str
    support_position: str
    restriction_position: str
    conditional_position: str
    decision_criteria: tuple[str, ...] = ('etki', 'uygulanabilirlik', 'adil erişim')
    common_ground_text: str = ''
    evidence_focus: str = 'karar seçeneklerinin gerçek etkisini gösteren güvenilir veri'

    @property
    def is_specific(self) -> bool:
        return self.key not in {'generic', 'academic-ai'}

    def display_name(self, canonical_name: str) -> str | None:
        if not self.is_specific:
            return None
        names = {
            SUPPORT: self.support_name,
            RESTRICT: self.restriction_name,
            CONDITIONAL: self.conditional_name,
            NEUTRAL: f'{self.subject.capitalize()} için kanıt / tarafsız değerlendirme',
            OTHER: f'{self.subject.capitalize()} için ek değerlendirme',
        }
        return names.get(canonical_name)

    def position(self, canonical_name: str) -> str | None:
        return {
            SUPPORT: self.support_position,
            RESTRICT: self.restriction_position,
            CONDITIONAL: self.conditional_position,
        }.get(canonical_name)

    def contrast(self, labels: list[str]) -> str | None:
        if not self.is_specific:
            return None
        positions = [self.position(label) for label in labels]
        visible = [position for position in positions if position]
        if len(visible) < 2:
            return None
        if len(visible) == 2:
            return f'{visible[0]} ile {visible[1]}'
        return f'{visible[0]}, {visible[1]} ve {visible[2]}'

    @property
    def criteria_phrase(self) -> str:
        values = [item.strip() for item in self.decision_criteria if item.strip()]
        if not values:
            return 'ortak etkiler'
        if len(values) == 1:
            return values[0]
        return f'{", ".join(values[:-1])} ve {values[-1]}'


_GENERIC_CONTEXT = TopicContext(
    key='generic',
    subject='tartışma konusu',
    support_name='',
    restriction_name='',
    conditional_name='',
    support_position='',
    restriction_position='',
    conditional_position='',
)

_ACADEMIC_AI_CONTEXT = TopicContext(
    key='academic-ai',
    subject='yapay zekâ kullanımı',
    support_name='',
    restriction_name='',
    conditional_name='',
    support_position='',
    restriction_position='',
    conditional_position='',
    decision_criteria=('öğrenme etkisi', 'akademik dürüstlük', 'adil erişim'),
    common_ground_text='Farklı yaklaşımlar, öğrenme etkisi ve akademik dürüstlüğün açık ölçütlerle değerlendirilmesi ihtiyacında buluşuyor.',
    evidence_focus='öğrenme, başarı ve akademik güvenilirlik üzerindeki etkileri gösteren güvenilir veri',
)

_PROFILES: tuple[tuple[tuple[str, ...], TopicContext], ...] = (
    (
        ('uzaktan çalış', 'evden çalış', 'hibrit çalış', 'uzaktan çalışma'),
        TopicContext(
            key='remote-work',
            subject='uzaktan çalışma',
            support_name='Uzaktan çalışmanın devamını savunanlar',
            restriction_name='Ofis zorunluluğu veya daha güçlü sınırlama',
            conditional_name='Kurallı veya hibrit çalışma',
            support_position='uzaktan çalışmanın sürmesi',
            restriction_position='ofis zorunluluğu',
            conditional_position='kurallı veya hibrit çalışma',
            decision_criteria=('verimlilik', 'ekip koordinasyonu', 'çalışan esnekliği'),
            common_ground_text='Farklı görüşler, verimlilik, ekip koordinasyonu ve çalışan esnekliğinin birlikte ölçülmesini ortak bir karar zemini olarak görüyor.',
            evidence_focus='verimlilik, ekip koordinasyonu ve çalışan esnekliği üzerindeki etkileri gösteren güvenilir veri',
        ),
    ),
    (
        ('telefon', 'cep telefonu', 'kişisel cihaz'),
        TopicContext(
            key='phone-use',
            subject='telefon kullanımı',
            support_name='Telefon erişimini ve iletişimi savunanlar',
            restriction_name='Telefon kullanımına karşı çıkanlar',
            conditional_name='Zamanı ve alanı belirlenmiş telefon kullanımı',
            support_position='telefon erişiminin sürmesi',
            restriction_position='telefon kullanımının sınırlanması',
            conditional_position='kurallı telefon kullanımı',
            decision_criteria=('öğrenme odağı', 'iletişim ihtiyacı', 'dijital güvenlik'),
            common_ground_text='Farklı görüşler, öğrenme odağı, iletişim ihtiyacı ve dijital güvenliğin birlikte gözetilmesi gerektiği değerlendirmesinde kesişiyor.',
            evidence_focus='öğrenme odağı, iletişim ve güvenlik sonuçlarını karşılaştıran güvenilir veri',
        ),
    ),
    (
        ('kantin', 'şekerli ürün', 'şekerli gıda', 'okul beslen'),
        TopicContext(
            key='school-canteen',
            subject='okul kantinindeki ürünler',
            support_name='Kantindeki ürün seçeneklerini savunanlar',
            restriction_name='Şekerli ürünlere sınırlama isteyenler',
            conditional_name='Yaşa ve içeriğe göre kontrollü satış',
            support_position='ürün seçeneklerinin korunması',
            restriction_position='şekerli ürünlerin sınırlanması',
            conditional_position='kontrollü ve dengeli satış',
            decision_criteria=('sağlık etkisi', 'öğrenci seçimi', 'uygulanabilir denetim'),
            common_ground_text='Farklı görüşler, öğrenci sağlığı ile seçme imkânının uygulanabilir bir denetimle birlikte değerlendirilmesi gerektiği noktasında kesişiyor.',
            evidence_focus='sağlık etkisi, tüketim davranışı ve denetim uygulanabilirliğini gösteren güvenilir veri',
        ),
    ),
    (
        ('geri dönüş', 'geri kazan', 'atık ayrıştır', 'atık yönet'),
        TopicContext(
            key='recycling',
            subject='geri dönüşüm uygulaması',
            support_name='Geri dönüşüm uygulamasını destekleyenler',
            restriction_name='Zorunlu ayrıştırmaya karşı çıkanlar',
            conditional_name='Erişilebilir ve aşamalı geri dönüşüm',
            support_position='geri dönüşümün yaygınlaştırılması',
            restriction_position='zorunlu uygulamanın sınırlanması',
            conditional_position='aşamalı ve erişilebilir uygulama',
            decision_criteria=('çevresel etki', 'erişilebilirlik', 'uygulama maliyeti'),
            common_ground_text='Farklı görüşler, çevresel etkinin erişilebilirlik ve uygulama maliyetiyle birlikte ölçülmesi gerektiği değerlendirmesinde kesişiyor.',
            evidence_focus='çevresel kazanım, katılım ve uygulama maliyetini birlikte gösteren güvenilir veri',
        ),
    ),
    (
        ('kütüphane', 'kitaplık', 'okuma salon'),
        TopicContext(
            key='library-access',
            subject='kütüphane erişimi',
            support_name='Kütüphane erişiminin sürmesini savunanlar',
            restriction_name='Kütüphane saatlerini sınırlamak isteyenler',
            conditional_name='İhtiyaca ve personele göre kütüphane erişimi',
            support_position='kütüphane erişiminin genişlemesi',
            restriction_position='çalışma saatlerinin sınırlanması',
            conditional_position='ihtiyaca göre planlı erişim',
            decision_criteria=('erişim ihtiyacı', 'personel güvenliği', 'işletme kapasitesi'),
            common_ground_text='Farklı görüşler, erişim ihtiyacı ile personel güvenliği ve işletme kapasitesinin birlikte değerlendirilmesini ortak zemin olarak görüyor.',
            evidence_focus='erişim talebi, güvenlik ve işletme kapasitesini gösteren güvenilir veri',
        ),
    ),
    (
        ('dijital oyun', 'ekran süresi', 'oyun süresi', 'çevrim içi oyun'),
        TopicContext(
            key='digital-play',
            subject='dijital oyun süresi',
            support_name='Çocukların oyun ve erişim hakkını savunanlar',
            restriction_name='Dijital oyun süresini kısıtlamak isteyenler',
            conditional_name='Yaşa uygun ve dengeli oyun süresi',
            support_position='oyun ve erişim hakkının korunması',
            restriction_position='oyun süresinin kısıtlanması',
            conditional_position='yaşa uygun dengeli kullanım',
            decision_criteria=('çocuk iyi oluşu', 'yaşa uygunluk', 'aile rehberliği'),
            common_ground_text='Farklı görüşler, çocukların iyi oluşu, yaşa uygunluk ve aile rehberliğinin birlikte gözetilmesi gerektiği noktasında kesişiyor.',
            evidence_focus='yaşa göre iyi oluş, öğrenme ve kullanım süresi etkilerini gösteren güvenilir veri',
        ),
    ),
    (
        ('mahalle park', 'parkı', 'parklar', 'yeşil alan', 'kent park'),
        TopicContext(
            key='neighborhood-park',
            subject='mahalle parkı',
            support_name='Parkın kullanımını ve erişimini savunanlar',
            restriction_name='Park kullanımına sınırlama isteyenler',
            conditional_name='Saat ve güvenlik koşullarına bağlı park kullanımı',
            support_position='park erişiminin sürmesi',
            restriction_position='park kullanımının sınırlandırılması',
            conditional_position='saat ve güvenlik koşulları',
            decision_criteria=('erişim hakkı', 'çevre huzuru', 'güvenlik'),
            common_ground_text='Farklı görüşler, parka erişim ile çevre huzuru ve güvenliğin aynı karar ölçütlerinde ele alınması gerektiği noktasında kesişiyor.',
            evidence_focus='kullanım yoğunluğu, güvenlik olayları ve çevre şikâyetlerini gösteren güvenilir veri',
        ),
    ),
    (
        ('bisiklet yolu', 'bisiklet şeridi', 'bisiklet ulaşım'),
        TopicContext(
            key='bicycle-access',
            subject='bisiklet yolu',
            support_name='Bisiklet yolu erişimini savunanlar',
            restriction_name='Bisiklet yolu genişlemesine karşı çıkanlar',
            conditional_name='Güvenlik ve bütçeye göre bisiklet yolu',
            support_position='bisiklet yolu erişiminin genişlemesi',
            restriction_position='projenin sınırlandırılması',
            conditional_position='güvenlik ve bütçe koşulları',
            decision_criteria=('ulaşım güvenliği', 'erişim', 'bütçe etkisi'),
            common_ground_text='Farklı görüşler, güvenli ulaşım, erişim ve bütçe etkisinin birlikte değerlendirilmesi gerektiği noktasında kesişiyor.',
            evidence_focus='güvenlik, kullanım talebi ve bütçe etkisini karşılaştıran güvenilir veri',
        ),
    ),
    (
        ('ulaşım', 'servis', 'otobüs', 'gece hatt'),
        TopicContext(
            key='public-transport',
            subject='ulaşım hizmeti',
            support_name='Ulaşım hizmetinin sürmesini savunanlar',
            restriction_name='Hizmet kapsamına sınırlama isteyenler',
            conditional_name='Talep ve güvenliğe göre planlı ulaşım',
            support_position='ulaşım hizmetinin sürmesi',
            restriction_position='hizmetin sınırlandırılması',
            conditional_position='talebe göre planlı hizmet',
            decision_criteria=('erişim', 'güvenlik', 'hizmet verimliliği'),
            common_ground_text='Farklı görüşler, erişim, güvenlik ve hizmet verimliliğinin birlikte ölçülmesini ortak bir karar zemini olarak görüyor.',
            evidence_focus='yolcu talebi, güvenlik ve hizmet maliyetini birlikte gösteren güvenilir veri',
        ),
    ),
)


def resolve_topic_context(title: str) -> TopicContext:
    folded = title.casefold().strip()
    turkish_folded = title.replace('I', 'ı').replace('İ', 'i').casefold().strip()
    variants = (folded, turkish_folded)
    if any(signal in variant for variant in variants for signal in ('yapay zek', 'üretken ai', 'generative ai')):
        # Sabit TEKNOFEST demosunun etiketleri, Köprü sorusu ve olay kimliği
        # v1.1.1'den beri doğrulanmış sözleşmedir; aynen korunur.
        return _ACADEMIC_AI_CONTEXT
    for signals, profile in _PROFILES:
        if any(signal in variant for variant in variants for signal in signals):
            return profile
    return _GENERIC_CONTEXT
