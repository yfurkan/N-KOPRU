# N-KÖPRÜ v1.0.0 — Son Kaynak Kod Denetimi

## Sonuç

v0.9.2 PRE-V1 Stable tabanı v1.0.0'a taşındı. Bu sürümde kullanıcıya ait çalışma verisi artık yalnızca süreç belleğinde tutulmuyor; SQLite ile backend yeniden başlatmaları arasında korunuyor. Profil ve analiz geçmişi gerçek backend verisinden besleniyor ve "Ben Yokken Ne Değişti?" çıktısı aynı tartışmanın ardışık analiz snapshot'ları karşılaştırılarak oluşturuluyor.

## v1.0.0'da tamamlananlar

- **SQLite veri katmanı:** Bildirimler, Mesajlar, Yer İmleri, Listeler, özel tartışmalar, analiz geçmişi ve profil kalıcı hale getirildi.
- **Profil:** görünen ad, kullanıcı adı ve açıklama düzenlenebilir; tüm sayaçlar gerçek SQLite kayıtlarından türetilir.
- **Analiz geçmişi:** her analiz ayrı snapshot olarak saklanır. Profilde son analizler listelenir ve geçmiş snapshot yeni analiz çalıştırmadan açılır.
- **Ben Yokken Ne Değişti?:** önceki snapshot ile yeni snapshot arasında yorum sayısı, görüş kümeleri/yüzdeleri, yeni iddialar, cevapsız sorular, ortak zemin ve Köprü sorusu değişimleri karşılaştırılır.
- **Bildirimler:** okundu/okunmadı, tek silme, okunanları temizleme, geri alma ve okunmamış rozet mantığı SQLite üzerinde korunur.
- **Mesajlar:** gönderilen mesajlar ve paylaşılan Köprü kartları kalıcıdır.
- **Yer İmleri:** Tartışma/İddia/Köprü kayıtları kalıcı ve idempotenttir.
- **Listeler:** listeler ve liste öğeleri kalıcı; varsayılan listeler silindikten sonra kendiliğinden geri oluşmaz.
- **Özel tartışmalar:** kullanıcı tarafından analiz edilen özel tartışmalar backend yeniden başlatıldığında tekrar açılabilir.

## Snapshot karşılaştırmasının doğrulanması

Regresyon testinde aynı `post_id` için önce temel tartışma, sonra yeni yorum eklenmiş ikinci sürüm analiz edildi. İkinci snapshot; yeni benzersiz yorum, görünür hale gelen görüş kümesi, görüş yüzdesi değişimi, yeni cevapsız soru ve güncellenen Köprü sorusu gibi değişim notlarını üretti. Aynı veri tekrar analiz edildiğinde ise sistem ölçülebilir değişim olmadığını belirtir.

## Test sonucu

- **168/168 test metodu başarılı.**
- **13/13 test betiği başarılı.**
- Yanıt Koçu testleri içinde ayrıca **552 senaryo kontrolü** başarılı.
- Python `compileall`: başarılı.
- Frontend `page.tsx`, `layout.tsx`, `api.ts`, `types.ts` TS/TSX syntax-transpile kontrolü: başarılı.
- Aynı SQLite dosyasını kullanan iki ayrı Python işlemi ile restart kalıcılık probu: başarılı.

Tam TypeScript `tsc --noEmit` doğrulaması test konteynerinde npm bağımlılık kurulumunun zaman aşımına uğraması nedeniyle tamamlanamadı; bu rapor bu kontrolü yapılmış gibi göstermemektedir.

## Bilinçli olarak v1.0.0 kapsamı dışında kalan ürün katmanları

1. **Çok kullanıcılı kimlik doğrulama:** v1.0.0 tek yerel kullanıcı çalışma alanıdır; gerçek hesap/oturum sistemi yoktur.
2. **N'Sosyal canlı veri adaptörü:** Keşfet ve demo tartışmaları kontrollü yerel veridir. Canlı platform entegrasyonu ayrı adaptör gerektirir.
3. **İddia Radarı AI zenginleştirmesi:** mevcut claim tespiti çalışır ancak daha gelişmiş kaynak doğrulama/NER/claim-confidence katmanı sonraki ürünleştirme adımıdır.
4. **Ortak Zemin ve Köprü üretiminin AI doğrulaması:** mevcut çıkarım çalışır; kontrollü üretken AI + anlam koruma doğrulaması daha ileri sürümde güçlendirilebilir.
5. **Gerçek zamanlı arka plan senkronizasyonu:** snapshot karşılaştırıcı hazırdır; fakat statik demo veri kendi kendine değişmez. Canlı N'Sosyal adaptörü yeni yorumları getirdiğinde aynı mekanizma değişimleri doğrudan karşılaştırabilir.

## Kalıcı veri dosyası

Normal yerel kullanımda veritabanı ilk çalıştırmada şu yolda oluşturulur:

`backend/data/nkopru.db`

Kaynak ZIP bu çalışma zamanı veritabanını **içermez**. Bu nedenle sonraki kaynak kod güncellemeleri mevcut `nkopru.db` dosyasını üzerine yazmadan uygulanabilir.
