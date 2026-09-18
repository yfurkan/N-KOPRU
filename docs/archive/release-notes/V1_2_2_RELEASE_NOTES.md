# N-KÖPRÜ v1.2.2 — Görüş Tutarlılığı ve Kompakt Arayüz

## Düzeltilen iki doğrulanmış sınıflandırma hatası

1. Demo yorum #7, sorumlu ve sınırlı kişisel yapay zekâ kullanımı anlattığı hâlde gerçek Transformer tarafından yasakçı görüşe atanabiliyordu. Yeni anlamsal koruma, birinci tekil kullanım + öğrenme/açıklama amacı veya ödevi araca yaptırmama birlikteliğini `Koşullu / Dengeli` olarak sabitler.
2. Demo yorum #11, kaynak belirtilmeyen yüzdeye karşı kanıt eleştirisi olduğu hâlde aynı yasakçı kümeye atanabiliyordu. Yeni koruma, kaynak/veri açığı + iddia/yüzde/istatistik bağlamını `Soru / Tarafsız` olarak sabitler.

Koruma `_structural_label` içinde Transformer çağrısından önce ve `classify_viewpoint_heuristic` içinde heuristik karar öncesinde uygulanır. Başkasının ödevini yapay zekâya yaptırdığına yönelik eleştiri yasakçı; kaynak göstermeden kullanımın akademik güvenilirliğe zarar verdiği ifadesi koşullu kalır.

## Beklenen hibrit demo sonucu

| Görüş | Yorum | Oran |
| --- | ---: | ---: |
| Kontrollü ve kurallı kullanım | 10 | %50 |
| Tam yasak veya güçlü sınırlama | 2 | %10 |
| Yasağa karşı / kullanım alanlarını koruma | 4 | %20 |
| Kanıt talebi / tarafsız değerlendirme | 4 | %20 |

20 demo yorumu yapısal olarak çözüldüğü için görüş sınıflandırmasında 0 Transformer çıkarımı gerekir. Bu, model yüklenmediği veya gerçek AI kullanılamadığı anlamına gelmez; yalnızca belirsiz yorum kalmadığını gösterir. Farklı tartışmalardaki belirsiz ifadeler hâlâ mevcut Transformer katmanına gönderilir.

## Arayüz

- Görüş adı, yorum sayısı, yüzde, dağılım çubuğu ve ana gerekçe ilk bakışta görünür.
- Temalar, diğer görüşlerle ilişki, temsilci yorumlar, İddia Radarı ve soru bağlantıları erişilebilir HTML `details/summary` içinde açılır.
- Tutarlılık korumasıyla düzeltilen #7 ve #11, temsilci seçiminde öne çıkmasalar bile ilgili kartta kendi metinleriyle ayrıca gösterilir; kümedeki tüm yorum numaraları listelenir.
- AI sınıflandırma örnekleri ayrı bir açılır ayrıntıya taşınır.
- Kart boşlukları azaltılır; tüm görüşlerin karşılaştırılması için gereken kaydırma düşer.
- Kısıtlayıcı görüş gerekçesindeki `risk ... riskler` tekrarı kaldırılır.

## SQLite ve bildirim uyumluluğu

- Canonical `Viewpoint.name` alanı değişmez; snapshot ve olay kimlikleri korunur.
- `semantic_guardrail_count` motor bilgisinde saklanır ve SQLite snapshot üzerinden geri okunabilir.
- Değişmeyen yeniden analiz ikinci bildirim üretmez; silinen bildirimler yeniden oluşturulmaz.
- v1.2.1'den ilk yükseltmede iki yanlış görüşün gerçek düzelmesi oran farkı olarak bir defaya mahsus bildirim oluşturabilir. Sonraki aynı analizler tekrar bildirim üretmez.
- Kullanıcının mevcut `.db`, `.venv`, `node_modules` ve `.env` dosyaları SOURCE ZIP içine alınmaz.

## Doğrulama

- 330/330 unittest, 24 test paketi.
- 282/282 önceki regresyon testi.
- 26/26 yeni görüş tutarlılığı testi.
- 14/14 yeni kompakt arayüz sözleşmesi testi.
- 8/8 yeni SQLite, snapshot ve Bildirim Dedup testi.
- Yanıt Koçu: 29/29 ve 552 senaryo kontrolü.
- Demo kaynak farkındalığı %25; yüksek öncelikli soru yorumları #6 ve #13; Köprü sorusu en fazla 28 kelime.
- Tam Next.js production build ve `tsc --noEmit`, bu çalışma ortamında frontend bağımlılıkları bulunmadığı için çalıştırılmamıştır.
