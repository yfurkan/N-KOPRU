# N-KÖPRÜ v1.2.1 — Açıklanabilir Görüş Haritası

## Amaç

Kullanıcı tarafından doğrulanmış v1.2.0 tabanında Görüş Haritasını tartışma bağlamına, gerçek yorumlara ve kanıt bağlantılarına dayanan anlaşılır bir analiz modülüne dönüştürmek.

## Ana değişiklikler

- Yeni `backend/app/viewpoint_engine.py` modülü, stable görüş kümesi kimliğini bozmadan bağlama uygun görünen isim üretir.
- Yasak/düzenleme tartışmalarında kontrollü kullanım, güçlü sınırlama, yasağa karşı kullanım ve tarafsız kanıt talebi birbirinden açık biçimde ayrılır.
- Yasak bağlamı bulunmayan tartışmalarda genel destek/itiraz/koşul etiketleri korunur.
- Her küme gerçek tekilleştirilmiş yorum sayısı, ana gerekçe, baskın tema, en fazla iki temsilci yorum ve bütün dayanak yorum kimlikleriyle zenginleştirilir.
- Karşıt kümeler, ortak zemin, ilgili iddia ve ilgili soru bağlantıları aynı kartta gösterilir.
- Yapısal sınıflandırma ve gerçek Transformer çıkarımı ayrı sayılır; model güveni yalnızca gerçek model çıkarımlarından hesaplanır.
- Cevapsız Sorular kartları ile AI sınıflandırma örnekleri de aynı bağlama uygun görünen isimleri kullanır.

## Geriye uyumluluk ve SQLite

- `Viewpoint.name` değişmez; history karşılaştırması, Köprü sentezi ve bildirim olay imzaları aynı kimlikle çalışır.
- Yeni alanların tamamı Pydantic varsayılanına sahiptir; v1.0–v1.2.0 snapshot JSON'u açılabilir.
- Eski bir snapshot sonrasında ilk v1.2.1 analizi yalnızca yeni sunum alanları eklendiği için sahte değişiklik veya bildirim üretmez.
- Silinen görüş bildirimi yeniden analizle doğmaz.
- Zengin küme verileri SQLite üzerinde saklanır ve gerçek process restart testinde doğrulanır.

## Doğrulama

- Toplam: 282/282 test.
- Yeni anlamsal motor: 22/22.
- Yeni SQLite/snapshot/bildirim entegrasyonu: 10/10.
- Yeni frontend UI sözleşmesi: 14/14.
- Önceki tüm modüller: 236/236.
- Yanıt Koçu ek güvenlik/davranış senaryoları: 552.

Tam npm/Next.js production build bu ortamda bağımlılıklar ve ağ yetkisi bulunmadığı için çalıştırılmamıştır.
