from .models import Comment, Post

BASE_COMMENTS = [
    ("Elif Demir", "Kesinlikle yasaklanmalı. Öğrenciler düşünmeyi bırakıyor."),
    ("Ahmet Yılmaz", "Doğru kullanılırsa çok faydalı. Tamamen yasaklamak yanlış olur."),
    ("Zeynep Arslan", "Sorun yasaklamak değil, nasıl kullandığımız."),
    ("Mert Kaya", "Yapay zekâ kaynak göstermeden kullanılırsa akademik güvenilirlik zarar görüyor."),
    ("Derya Aydın", "Üniversitelerin ortak bir kullanım yönergesi hazırlaması daha mantıklı."),
    ("Kerem Tunç", "Bu konuda öğrencilerin başarı düzeyini karşılaştıran güvenilir bir araştırma var mı?"),
    ("Selin Aksoy", "Ben ders çalışırken açıklama almak için kullanıyorum, ödevimi ona yazdırmıyorum."),
    ("Bora Şen", "Bazı öğrenciler bütün ödevi yapay zekâya yaptırıyor, bu ciddi problem."),
    ("Sude Çelik", "Yasak yerine öğretmenler nasıl kullanılacağını öğretmeli."),
    ("Emre Koç", "Geçen dönem sınıfımızın %70'i en az bir kez üretken yapay zekâ kullandı."),
    ("Pelin Öz", "Kaynak belirtilmediği sürece yüzde vermek çok anlamlı değil."),
    ("Oğuz Han", "Yapay zekâ okuryazarlığı dersleri zorunlu olabilir."),
    ("Deniz Acar", "Öğrenmeyi azaltıyor diyenlerin dayandığı veri nedir?"),
    ("İrem Şahin", "Bence sınavlarda yasak, öğrenme sürecinde kontrollü serbest olmalı."),
    ("Can Polat", "Her teknolojide olduğu gibi burada da kullanım amacı önemli."),
    ("Nazlı Kurt", "Üniversite öğrencisini tamamen engellemek gerçekçi değil."),
    ("Baran Işık", "AI ile hazırlanan ödev açıkça belirtilmeli."),
    ("Ece Uslu", "Asıl mesele etik kullanım ve şeffaflık."),
    ("Tolga Güneş", "Bunu yasaklamaya çalışmak interneti yasaklamaya benziyor."),
    ("Melis Kara", "Hangi kullanım biçimlerinin öğrenmeyi gerçekten güçlendirdiğini ölçmeliyiz."),
]

def make_demo_comments():
    comments = []
    cid = 1
    for cycle in range(4):
        for author, text in BASE_COMMENTS:
            suffix = "" if cycle == 0 else [
                " Bu ayrımın yönetmelikte açık olması gerekir.",
                " Özellikle birinci sınıflarda bunun etkisi daha çok tartışılmalı.",
                " Öğretim elemanlarının da ortak ölçütlere ihtiyacı var."
            ][(cycle - 1) % 3]
            comments.append(
                Comment(
                    id=cid,
                    author=author,
                    text=text + suffix,
                    created_at=f"{10 + (cid % 48)} dk",
                    likes=(cid * 7) % 31,
                )
            )
            cid += 1
    return comments

DEMO_POST = Post(
    id=1,
    author="Mehmet Kaya",
    handle="@mkaya",
    text="Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?",
    created_at="12 sn",
    comments=make_demo_comments(),
)
