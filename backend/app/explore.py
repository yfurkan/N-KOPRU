from __future__ import annotations

import unicodedata
from typing import Iterable

from .models import Comment, ExploreTopic, Post


def _comments(rows: list[tuple[str, str, int]]) -> list[Comment]:
    return [
        Comment(id=i + 1, author=author, text=text, created_at=f'{4 + i * 3} dk', likes=likes)
        for i, (author, text, likes) in enumerate(rows)
    ]


EXPLORE_POSTS: list[tuple[ExploreTopic, Post]] = [
    (
        ExploreTopic(
            id=101,
            category='AI & Eğitim',
            title='Üniversitelerde yapay zekâ kullanımı ders türüne göre düzenlenmeli mi?',
            summary='Serbest kullanım, sınav kısıtları, kaynak gösterme ve akademik dürüstlük arasında nasıl bir denge kurulmalı?',
            badge='Trend',
            tags=['yapay zekâ', 'üniversite', 'akademik etik'],
            comment_count=10,
        ),
        Post(
            id=101,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Üniversitelerde yapay zekâ kullanımı ders türüne göre düzenlenmeli mi?',
            created_at='8 dk',
            comments=_comments([
                ('Ada Yılmaz', 'Tamamen yasaklamak yerine dersin amacına göre farklı kurallar olmalı.', 21),
                ('Berk Can', 'Sınavlarda yasaklanmalı ama araştırma ve fikir geliştirmede serbest olabilir.', 18),
                ('Ceren Ak', 'Kullanılan yapay zekâ aracının ve katkısının açıkça belirtilmesi yeterli olabilir.', 16),
                ('Deniz Efe', 'Geçen dönem bölümümüzde öğrencilerin yaklaşık %60\'ı en az bir üretken yapay zekâ aracı kullandı.', 11),
                ('Eylül Naz', 'Bu %60 oranının dayandığı anket veya kayıt nedir?', 14),
                ('Fırat Aras', 'Kaynak göstermeden üretilen metnin ödev olarak kabul edilmemesi gerektiğini düşünüyorum.', 20),
                ('Gizem Su', 'Birinci sınıfta rehberlik daha sıkı, üst sınıflarda daha esnek olabilir.', 13),
                ('Hakan Ali', 'Yasak koymak öğrenciyi araçtan uzaklaştırmaz, yalnızca kullanımı görünmez hâle getirir.', 17),
                ('İpek Nur', 'Hangi kullanım biçimlerinin öğrenmeyi güçlendirdiğine dair güvenilir bir çalışma var mı?', 19),
                ('Kaan Alp', 'Üniversiteler ortak ilkeler belirlesin ama ders hocası ek kural koyabilsin.', 15),
            ]),
        ),
    ),
    (
        ExploreTopic(
            id=102,
            category='Dijital Etik',
            title='Sosyal platformlar kişiselleştirilmiş öneriler için hangi verileri kullanabilmeli?',
            summary='Kullanıcı deneyimi ile mahremiyet arasında veri minimizasyonu, açık rıza ve şeffaflık sınırları tartışılıyor.',
            badge='Yeni',
            tags=['mahremiyet', 'veri', 'algoritma'],
            comment_count=9,
        ),
        Post(
            id=102,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Sosyal platformlar kişiselleştirilmiş öneriler için hangi verileri kullanabilmeli?',
            created_at='18 dk',
            comments=_comments([
                ('Lale Kır', 'İçerik tercihleri kullanılabilir ama özel mesaj içerikleri öneri sistemi için işlenmemeli.', 24),
                ('Mert Uğur', 'Kullanıcı hangi veri türünün neden kullanıldığını tek ekranda görebilmeli.', 19),
                ('Nehir Gül', 'Konum verisi yalnızca kullanıcı açıkça izin verdiğinde ve sınırlı süreyle kullanılmalı.', 17),
                ('Ozan Ay', 'Kişiselleştirme için her veriyi toplamak gereksiz; veri minimizasyonu esas olmalı.', 22),
                ('Pınar Ela', 'Öneri kalitesi düşecekse kullanıcı isterse daha fazla veri paylaşmayı seçebilmeli.', 12),
                ('Rüzgar Eren', 'Açık rıza kutusunun gerçekten anlaşılır olup olmadığını kim denetleyecek?', 15),
                ('Sena İl', 'Reklam hedefleme ile içerik önerisi için kullanılan veriler ayrı izinlere bağlanmalı.', 18),
                ('Tuna Arda', '18 yaş altı kullanıcılar için kişiselleştirme varsayılan olarak daha sınırlı olmalı.', 20),
                ('Yağmur Ece', 'Kullanıcı geçmişini tek tuşla sıfırlayabilmeli ve algoritmayı yeniden başlatabilmeli.', 23),
            ]),
        ),
    ),
    (
        ExploreTopic(
            id=103,
            category='Gençlik & Sosyal Medya',
            title='Genç kullanıcılar için gece bildirimleri varsayılan olarak kapatılmalı mı?',
            summary='Dijital iyi oluş, ebeveyn kontrolü ve gençlerin özerkliği açısından bildirim tasarımı tartışılıyor.',
            badge='Tartışılıyor',
            tags=['gençlik', 'bildirim', 'dijital iyi oluş'],
            comment_count=8,
        ),
        Post(
            id=103,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Genç kullanıcılar için gece bildirimleri varsayılan olarak kapatılmalı mı?',
            created_at='31 dk',
            comments=_comments([
                ('Aylin Ece', 'Gece 23.00 ile 07.00 arasında bildirimler varsayılan olarak sessize alınabilir.', 16),
                ('Bora Eren', 'Varsayılan kapalı olsun ama genç kullanıcı isterse kendisi açabilsin.', 14),
                ('Cansu Nil', 'Aileye değil kullanıcıya kontrol vermek daha doğru; aksi hâlde mahremiyet sorunu çıkar.', 18),
                ('Doruk Ata', 'Gece bildirimlerinin uyku süresine etkisini gösteren güvenilir bir araştırma var mı?', 20),
                ('Elif Su', 'Acil mesajlar için favori kişilerden gelen bildirimler açık kalabilmeli.', 11),
                ('Ferhat Can', 'Platformlar kullanım süresini azaltmak istemez; bu nedenle varsayılan tasarım önemli.', 15),
                ('Gökçe Ada', '16 yaş altı ve üstü için aynı kural uygulanmamalı.', 13),
                ('Hazar Alp', 'Bildirim yerine ekran süresi sınırı daha etkili olabilir.', 9),
            ]),
        ),
    ),
    (
        ExploreTopic(
            id=104,
            category='İklim Teknolojileri',
            title='Belediyeler elektrikli araç şarj altyapısına doğrudan yatırım yapmalı mı?',
            summary='Kamu yatırımı, özel sektör rekabeti, erişilebilirlik ve şebeke kapasitesi açısından farklı görüşler var.',
            badge='Öneri',
            tags=['iklim', 'ulaşım', 'enerji'],
            comment_count=9,
        ),
        Post(
            id=104,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Belediyeler elektrikli araç şarj altyapısına doğrudan yatırım yapmalı mı?',
            created_at='42 dk',
            comments=_comments([
                ('Işıl Mina', 'Özel sektörün gitmediği düşük gelirli bölgelerde belediye yatırım yapmalı.', 18),
                ('Koray Efe', 'Belediye işletmeci olmak yerine alan tahsis edip rekabeti kolaylaştırmalı.', 15),
                ('Mina Eylül', 'Şarj noktalarının engelli erişimine uygunluğu ihale şartı olmalı.', 17),
                ('Onur Alp', 'Şebeke kapasitesi ölçülmeden çok sayıda hızlı şarj noktası kurulması sorun çıkarabilir.', 16),
                ('Sarp Can', 'Kamu yatırımı fiyatları düşürür mü, buna dair karşılaştırmalı veri var mı?', 13),
                ('Selma Naz', 'Toplu taşıma elektrifikasyonu bireysel araç şarjından önce gelmeli.', 20),
                ('Umut Aras', 'Merkezde özel sektör yeterli, çevre ilçelerde kamu desteği mantıklı.', 14),
                ('Vera Su', 'Yeni otopark ruhsatlarında belirli oranda şarj altyapısı zorunlu olabilir.', 12),
                ('Yalın Ege', 'Yatırım maliyeti belediyenin başka hizmetlerini aksatmayacak şekilde planlanmalı.', 10),
            ]),
        ),
    ),
    (
        ExploreTopic(
            id=105,
            category='AI & Eğitim',
            title='Öğrencilerin yapay zekâ ile hazırladığı ödevlerde kullanım beyanı zorunlu olmalı mı?',
            summary='Şeffaflık, değerlendirme adaleti ve öğrencinin gerçek katkısının görünür kılınması üzerine bir tartışma.',
            badge='Yükseliyor',
            tags=['ödev', 'şeffaflık', 'değerlendirme'],
            comment_count=8,
        ),
        Post(
            id=105,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Öğrencilerin yapay zekâ ile hazırladığı ödevlerde kullanım beyanı zorunlu olmalı mı?',
            created_at='55 dk',
            comments=_comments([
                ('Zehra Lina', 'Kullanım beyanı zorunlu olmalı; hangi bölümde ne için kullanıldığı kısaca yazılabilir.', 22),
                ('Ali Eren', 'Sadece dil düzeltme için kullanılan araçları ayrıca belirtmek gereksiz olabilir.', 11),
                ('Buse Ada', 'Ödevin büyük kısmını model ürettiyse bunun gizlenmesi değerlendirme adaletini bozar.', 19),
                ('Cem Arda', 'Beyan sistemi varsa öğretim elemanı da hangi kullanımı kabul ettiğini önceden açıklamalı.', 16),
                ('Duru Ela', 'Beyan vermenin öğrencilerin dürüstlüğünü gerçekten artırdığına dair veri var mı?', 14),
                ('Emir Alp', 'Her ders için aynı beyan formu yerine kısa ve ders özelinde bir yöntem olmalı.', 13),
                ('Funda Su', 'Kaynak üretmek için yapay zekâ kullanıldıysa kaynakların ayrıca doğrulanması şart.', 20),
                ('Gürkan Efe', 'Beyan cezalandırma aracı değil, öğrenme sürecini görünür kılma aracı olmalı.', 18),
            ]),
        ),
    ),
    (
        ExploreTopic(
            id=106,
            category='Dijital Etik',
            title='Yapay zekâ ile üretilmiş siyasi içeriklerde görünür etiket zorunlu olmalı mı?',
            summary='İfade özgürlüğü, manipülasyon riski ve kullanıcıların içerik kökenini anlayabilmesi arasında sınır aranıyor.',
            badge='Gündem',
            tags=['yapay zekâ', 'şeffaflık', 'içerik etiketi'],
            comment_count=9,
        ),
        Post(
            id=106,
            author='N-KÖPRÜ Gündem',
            handle='@nkopru_gundem',
            text='Yapay zekâ ile üretilmiş siyasi içeriklerde görünür etiket zorunlu olmalı mı?',
            created_at='1 sa',
            comments=_comments([
                ('İdil Ece', 'Gerçek bir kişiyi taklit eden yapay görüntü ve seslerde etiket zorunlu olmalı.', 24),
                ('Kuzey Aras', 'Her yapay zekâ desteğini etiketlemek fazla geniş olur; anlamlı ölçüde üretilen içerik hedeflenmeli.', 18),
                ('Leyla Su', 'Etiket kolayca gözden kaçıyorsa hiçbir işe yaramaz, görünür bir standart gerekli.', 17),
                ('Mete Can', 'Platformların yanlış etiket kararına itiraz mekanizması bulunmalı.', 14),
                ('Nisa Eylül', 'Etiketli içeriğin daha az yayıldığını gösteren güvenilir bir çalışma var mı?', 13),
                ('Ömer Alp', 'Seçim döneminde kurallar daha sıkı uygulanabilir.', 16),
                ('Rana Ada', 'Kullanıcıların kendi hiciv içerikleri yanlışlıkla manipülasyon diye sınıflandırılmamalı.', 12),
                ('Sinem Ela', 'Kaynağı bilinmeyen sentetik ses kayıtları özellikle riskli.', 19),
                ('Toprak Efe', 'Etiket tek başına yetmez; içerik kökeni ve düzenleme geçmişi de görülebilmeli.', 21),
            ]),
        ),
    ),
]


_BY_ID = {topic.id: (topic, post) for topic, post in EXPLORE_POSTS}


def _fold(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', text)
    stripped = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.casefold().replace('ı', 'i')


def list_topics(category: str | None = None, q: str | None = None) -> list[ExploreTopic]:
    items: Iterable[tuple[ExploreTopic, Post]] = EXPLORE_POSTS
    if category and category != 'Tümü':
        wanted = _fold(category)
        items = [(topic, post) for topic, post in items if _fold(topic.category) == wanted]
    if q and q.strip():
        needle = _fold(q.strip())
        items = [
            (topic, post)
            for topic, post in items
            if needle in _fold(' '.join([
                topic.title, topic.summary, topic.category, *topic.tags,
                *(comment.text for comment in post.comments),
            ]))
        ]
    return [topic for topic, _ in items]


def get_post(topic_id: int) -> Post | None:
    pair = _BY_ID.get(topic_id)
    return pair[1] if pair else None


def get_topic(topic_id: int) -> ExploreTopic | None:
    pair = _BY_ID.get(topic_id)
    return pair[0] if pair else None


def categories() -> list[str]:
    return sorted({topic.category for topic, _ in EXPLORE_POSTS})
