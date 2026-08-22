# N-KÖPRÜ v1.3.2 — Kompakt Teknik Panel ve Katman Bazlı Performans

## Sorunlar

v1.3.1 Teknik Doğrulama kartları ana analiz ekranlarına ait 560 piksellik
minimum yüksekliği miras aldığı için sağ panelde büyük boş alanlar oluşuyordu.
Ayrıca ekrandaki `0 Transformer çıkarımı` yalnızca 20 örnekli görüş doğrulama
setini anlatıyor, aynı demo analizinde İddia Radarı'nın ayrıca çalıştırdığı
Transformer kararını göstermiyordu.

## Uygulanan çözüm

- Sadece teknik sağ panel kartlarına `min-height: auto` uygulandı; ana sekmelerin
  ve diğer modüllerin mevcut kart davranışı değişmedi.
- Her gerçek demo analizi sırasında altı ardışık katman yüksek çözünürlüklü
  zamanlayıcıyla ayrı ölçülür:
  1. Görüş sınıflandırması
  2. İddia Radarı
  3. Cevapsız Sorular
  4. Ortak Zemin
  5. Görüş Haritası
  6. Köprü Oluştur
- Her katmanın örnekleri, medyanı, minimumu, ortalaması, maksimumu, P95 değeri,
  toplam içindeki payı ve gerçek çıkarım adedi API yanıtında saklanır.
- En yavaş katman o anki gerçek medyanlarla seçilir; önceki ekran değerinden veya
  sabit metinden türetilmez.
- Hazırlık, gösterge üretimi, özet ve sonuç nesnesi süreleri kalan süre olarak
  ayrıca açıklanır.
- İç set görüş çıkarımı, iç set İddia Radarı çıkarımı, demo görüş çıkarımı ve
  demo İddia Radarı çıkarımı ayrı raporlanır.
- Demo yorum #8 gerçekten modelle incelendiğinde ilgili yorum numarası, analiz
  başına çıkarım ve tüm tekrarların toplamı birlikte gösterilir.

## CPU/CUDA tanısı

- Hazır modelin gerçekten kullandığı cihaz açıklanır.
- Kurulu PyTorch sürümü ve varsa PyTorch CUDA derlemesi gösterilir.
- CUDA erişimi ve doğrulanmış CUDA aygıt adı yalnızca gerçekten okunmuşsa görünür.
- CPU derlemesi ile CUDA destekli fakat kullanılamayan kurulum ayrı durumdur.
- Fiziksel GPU varlığı doğrulanmadan ekran kartı bulunmadığı iddia edilmez.
- Donanım tanısı modeli otomatik yüklemez, indirme başlatmaz veya paket kurmaz.

## Geriye uyumluluk ve SQLite

- v1.3.1'in son ölçümü mevcut SQLite kaydından okunmaya devam eder.
- Eski kayıtta ölçülmemiş katman ve İddia Radarı sayaçları sıfırmış gibi
  gösterilmez; `Ölçülmedi` denir ve yeni ölçüm önerilir.
- Eski kayıt yalnızca okunurken yeniden yazılmaz; kullanıcının ölçüm geçmişi
  ve diğer uygulama kayıtları korunur.
- Teknik çalışma bildirim, snapshot, profil, mesaj, yer imi veya liste üretmez.

## Doğrulama

- Önceki v1.3.1 regresyonları: 497/497.
- Yeni testler: 36 profil/model/SQLite + 15 CPU/CUDA + 24 arayüz = 75/75.
- Toplam: 572/572 unittest, 36 test paketi.
- Python `compileall`, TypeScript `tsc --noEmit` ve Next.js production build.
- SOURCE ZIP: `.venv`, `node_modules`, `.next`, `.env`, SQLite `.db` dosyaları
  ve `__pycache__` içermez.
