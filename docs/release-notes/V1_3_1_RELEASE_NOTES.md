# N-KÖPRÜ v1.3.1 — Gerçek Teknik Ölçüm ve Şeffaf Doğrulama

## Amaç

Bu sürüm, N-KÖPRÜ'nün analiz kalitesini ve çalışma süresini sabit rakamlar
göstermeden, kullanıcının kendi bilgisayarında yeniden ölçülebilir hâle getirir.
Yeni `Teknik Doğrulama` alanı ürün demoları ve teknik rapor için gözlemlenebilir
kanıt sağlar.

## Gerçek ölçüm kapsamı

- Dört görüş sınıfından beşer örnek içeren, toplam 20 elle etiketlenmiş Türkçe
  iç doğrulama cümlesi gerçekten sınıflandırılır.
- Doğruluk, Macro-F1, sınıf bazlı precision/recall/F1 ve karışıklık matrisi
  üretilen gerçek tahminlerden hesaplanır.
- 80 ham / 20 benzersiz yorum içeren değişmemiş demo senaryosu beş kez gerçekten
  analiz edilir; minimum, medyan, ortalama, P95 ve maksimum süreler gösterilir.
- Tekilleştirme, kaynak farkındalığı `%25`, iki açık soru, yüksek öncelikli iddia,
  28 kelimelik Köprü sınırı, azınlık görüşü ve #7/#11 semantik korumaları olmak
  üzere dokuz davranış kontrolü çalıştırılır.
- Hazır olmayan Transformer otomatik indirilmez veya yüklenmez. Bu durumda
  heuristik yedek gerçekten ölçülür ve düşük sonuçlar gizlenmez.
- Model hazırsa hibrit yol kullanılır. Bir cümle yüksek kesinlikli yapısal
  kararla çözüldüğünde Transformer çıkarımı yapılmış ya da model güveni
  üretilmiş gibi gösterilmez.

## Dürüstlük sınırı

20 örnek proje içi, küçük ve elle etiketlenmiş bir doğrulama kümesidir. Sonuçlar
bağımsız akademik benchmark, dış test veri seti, gerçek kullanıcı araştırması
veya genellenebilir model başarısı olarak sunulmaz. Ekranda ve API yanıtında bu
sınırlılık açıkça belirtilir.

## SQLite ve kullanıcı verilerinin korunması

- Son teknik ölçüm mevcut `app_meta` tablosunda ayrı bir anahtar altında saklanır.
- Ölçüm; analiz geçmişine snapshot eklemez, bildirim oluşturmaz, profil sayılarını
  değiştirmez ve tartışma/mesaj/yer imi/liste kayıtlarına dokunmaz.
- Kullanıcının değiştirdiği demo korunur; davranış kontrolleri ayrı, sabit demo
  tanımı üzerinden yürütülür.
- Kaynak ZIP herhangi bir SQLite veritabanı içermez.

## API

- `GET /api/evaluation`: iç set tanımı, güncel model durumu ve son kayıtlı ölçüm.
- `POST /api/evaluation/run`: `{ "iterations": 5, "use_ai": true }` ile gerçek
  değerlendirme. Tekrar sayısı 1–10 aralığıyla sınırlıdır.

## Doğrulama

- Önceki v1.3.0 testleri: 436/436.
- Yeni testler: 32 backend ölçüm + 11 SQLite/izolasyon + 18 arayüz = 61/61.
- Toplam: 497/497 unittest, 33 test paketi.
- Python `compileall`, tam TypeScript typecheck ve optimize Next.js production
  build başarılı.
