# N-KÖPRÜ v1.2.3 — Tutarlı Özet ve Gerçek Görüş Ayrışması

## Gerçek çalıştırma yöntemine uygun özet

v1.2.2'de model hazır olduğu anda özet sabit olarak `hibrit Transformer görüş analizi` diyordu; oysa demo tartışmasının 20 yorumu yapısal olarak çözüldüğü için gerçek Transformer çıkarımı sayısı sıfırdı. Yeni sürüm, her yorumun gerçekten kullanılan yöntemini sayar ve dört yürütme durumunu ayrı raporlar:

- `structural-only`: hibrit motor hazır, görüşler yapısal Türkçe sinyalleriyle çözüldü.
- `hybrid-structural-transformer`: yapısal kararlar ile gerçek Transformer çıkarımları birlikte kullanıldı.
- `transformer-only`: bütün görüş kararları model çıkarımından geldi.
- `heuristic-fallback`: model yerine heuristik yedek kullanıldı.

Hazır model, kullanılmış model ve model güveni ayrı kavramlar olarak korunur.

## Azınlık görüşünü dışlamayan Köprü

Önceki Köprü, en yüksek oranlı iki görüşü aldığı için `%50 kontrollü kullanım` ve `%20 kullanım alanlarını koruma` kümelerini karşılaştırıyor; `%10 tam yasak` kümesini dışarıda bırakıyordu. Yeni politika-spektrumu seçimi üç gerçek karar yaklaşımını birlikte kapsar:

1. Tam yasak veya güçlü sınırlama.
2. Kontrollü ve kurallı kullanım.
3. Yasağa karşı / kullanım alanlarını koruma.

Asıl ayrışma, Köprü sorusu, temsilci kanıt yorumları ve yeni `Karşılaştırılan yaklaşımlar` etiketleri aynı üçlü karşılaştırmayı kullanır. Tarafsız/kanıt isteyen küme yapay karar tarafı gibi sunulmaz. Genel tartışmalara yasaklama dili taşınmaz. Demo Köprü sorusu 24 kelimedir; üst sınır 28 kelime olarak korunur.

## Soru metinlerinde ortak görünür adlar

#6 ve #13 soru kartlarının `affected_viewpoints` alanı geriye uyumlu canonical kimlikleri taşımaya devam eder. Yalnızca kullanıcıya gösterilen `impact` metnindeki adlar aynı tartışmanın Görüş Haritası başlıklarıyla değiştirilir. Böylece SQLite kayıtları, snapshot karşılaştırması, soru kimlikleri ve Bildirim Dedup bozulmaz.

## Yükseltme ve kalıcılık

- Yalnızca özet veya soru sunum metninin değişmesi bildirim oluşturmaz.
- Köprü sorusundaki gerçek içerik değişimi en fazla bir yeni Köprü bildirimi üretebilir.
- Aynı analiz sonraki çalıştırmalarda yeni bildirim üretmez.
- Kullanıcının sildiği Köprü bildirimi yeniden oluşturulmaz.
- Eski snapshot'larda yeni karşılaştırma alanları bulunmasa bile kayıtlar açılır.
- `.venv`, `node_modules`, `.next`, `.env`, `.db` ve `__pycache__` SOURCE ZIP içinde bulunmaz.

## Doğrulama

- 383/383 unittest; 27 test paketi.
- Önceki 330/330 regresyon testi.
- 30/30 yeni analiz tutarlılığı testi.
- 12/12 yeni arayüz sözleşmesi testi.
- 11/11 yeni SQLite, snapshot ve Bildirim Dedup testi.
- Yanıt Koçu: 29/29 ve 552 ek senaryo.
- Demo kaynak farkındalığı %25; soru #6/#13 korunur; #7 koşullu, #11 tarafsız kümededir.
- Tam Next.js production build ve `tsc --noEmit`, frontend bağımlılıkları bu ortamda bulunmadığı için çalıştırılmamıştır.
