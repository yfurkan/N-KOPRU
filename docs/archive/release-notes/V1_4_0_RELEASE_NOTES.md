# N-KÖPRÜ v1.4.0 — Çok Senaryolu Teknik Doğrulama

## Doğrulama kapsamı

- 4 ayrı tartışma konusu, her biri 20 yorum: toplam 80 proje içi cümle.
- 4 görüş sınıfı; her sınıfta toplam 20 ve her konuda 5 örnek.
- 32 temel, 48 zor örnek; örtük tutum, olumsuzlama, koşul ve kaynak eleştirisi.
- Genel doğruluk, Macro-F1, konu başına doğruluk, zorluk başına doğruluk,
  sınıf başına precision/recall/F1 ve gerçek karışıklık matrisi.
- Hatalı tahminler, beklenen/gerçek sınıflarla birlikte gizlenmeden gösterilir.
- Bu veri seti proje içidir; bağımsız benchmark, bilimsel genelleme veya
  kullanıcı başarısı olarak sunulmaz.

## Uyum ve ürün davranışı

- Eski 20 örnekli referans ve 5 tekrarlı soğuk/sıcak ölçüm ayrı korunur.
- Yeni senaryo çalıştırma uç noktası: `POST /api/evaluation/scenarios/run`.
- Sonuçlar mevcut SQLite `app_meta` tablosunda ayrı bir anahtara kaydedilir;
  yeni ürün tablosu oluşturulmaz.
- Kullanıcı tartışmaları, kayıtlı yorumlar, snapshot geçmişi, bildirimler,
  mesajlar, yer imleri, listeler ve profil değerlendirmeyle değiştirilmez.
- Etiketsiz aktif kullanıcı tartışmaları referans setinden ayrı gösterilir.
- Yapay zekâ dışındaki konularda model hipotezleri konu-bağımsız seçilir.
- `N-KÖPRÜ` ana sayfa başlığı dar alanlarda bölünmez.
- CPU/GPU bağımsızdır; fiziksel cihaz modeline özel gereksinim yoktur.

## Doğrulama

- 808/808 unittest, 43 paket.
- Önceki 700 regresyon + 108 yeni test.
- TypeScript typecheck, Python compileall ve Next.js production build.
