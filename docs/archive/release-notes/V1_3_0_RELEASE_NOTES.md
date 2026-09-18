# N-KÖPRÜ v1.3.0 — Canlı Tartışma ve Gerçek Değişim Takibi

## Amaç

Bu sürüm, N-KÖPRÜ'nün yalnızca hazır tartışmaları analiz etmesi yerine bir tartışmanın zaman içindeki gelişimini canlı olarak izlemesini sağlar. Kullanıcı mevcut gönderiye yorum eklediğinde kayıt, analiz, snapshot karşılaştırması ve bildirim seçimi tek kullanıcı işlemi içinde tamamlanır.

## Çalışan akış

1. `POST /api/posts/{post_id}/comments` yorum metnini ve AI tercihini alır.
2. Yorum, yerel profil adıyla ve çakışmayan yeni yorum kimliğiyle SQLite'a kaydedilir.
3. Demo, Keşfet veya özel tartışmanın güncel kalıcı kopyası analiz edilir.
4. Yeni analiz `analysis_history` tablosuna post ve analiz JSON'larıyla kaydedilir.
5. Önceki snapshot ile benzersiz yorum, görüş, iddia, soru, ortak zemin ve Köprü farkları hesaplanır.
6. Bildirim sistemi yalnızca gerçek yeni olayları içerik tabanlı kimlikle bir kez oluşturur.
7. Frontend gönderiyi ve analizi günceller, sonucu `Ben Yokken Ne Değişti?` adımında açar.

## Kalıcılık ve yarış koşulu koruması

- Demo ve Keşfet kaynak sabitleri değiştirilmez; yerel güncel kopya `custom_posts` tablosunda tutulur.
- Özel tartışmalar mevcut kayıt kimliğiyle güncellenir.
- SQLite `BEGIN IMMEDIATE`, aynı anda gelen eklemelerin aynı yorum kimliğini almasını ve son yazanın önceki yorumu silmesini engeller.
- Kaynak ZIP veritabanı içermez; mevcut yerel veritabanı üzerine kurulumda kullanıcı kayıtları korunur.

## Bildirim davranışı

- Yalnızca benzersiz yorum sayısının artması tek başına otomatik bildirim oluşturmaz.
- Yeni soru/kaynak talebi, yeni doğrulanabilir iddia, anlamlı görüş değişimi, ortak zemin değişimi veya Köprü değişimi kendi ilgili olayını oluşturabilir.
- Aynı yorum tekrar eklendiğinde ham gönderide saklanır, analizde tekilleştirilir ve ikinci bildirim üretmez.
- Aynı yüksek öncelikli iddia tekrar uyarılmaz.
- Kullanıcının sildiği olay soft-delete kaydı ve benzersiz imzası sayesinde yeniden üretilmez.

## Geriye uyumluluk

- Profil, Analiz Geçmişi, Bildirimler, Mesajlar, Yer İmleri, Listeler ve sekiz analiz adımı korunur.
- Eski snapshot'lar yeni yorum alanı gerektirmeden açılır.
- Demo analizi değişiklik yapılmadan önce v1.2.3 ile aynı 20 benzersiz yorum, `%25` kaynak farkındalığı ve en fazla 28 kelimelik Köprü kuralını korur.

## Doğrulama özeti

- 436/436 unittest, 30 paket.
- Önceki 383 testin tamamı geçti.
- 53 yeni test: 24 backend canlı akış, 13 SQLite/kalıcılık/eş zamanlılık/dedup, 16 UI sözleşmesi.
- Yanıt Koçu 29 test ve 552 ek senaryo kontrolü.
- Python compileall, tam TypeScript typecheck ve Next.js production build başarılı.
