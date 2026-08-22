# N-KÖPRÜ v1.4.0 — Çok Senaryolu Teknik Doğrulama

v1.4.0, mevcut 20 cümlelik referans ölçümünü ve donanımdan bağımsız İddia
Radarı önbelleğini değiştirmeden, dört farklı tartışma konusunda 80 yeni
elle etiketlenmiş cümleyi gerçekten değerlendirir. Sonuçlar bağımsız bir dış
veri kümesi veya akademik benchmark olarak sunulmaz; yanlış sınıflandırmalar
konu, zorluk ve beklenen/tahmin edilen görüş bilgisiyle açıkça gösterilir.

## v1.4.0 ile gelenler

- Akademik yapay zekâ, okulda telefon kullanımı, kampüste gece ulaşımı ve
  uzaktan çalışma için 20'şer gerçek sınıflandırma örneği; toplam 80 cümle.
- Destekleyen, Karşı / Sınırlayıcı, Koşullu / Dengeli ve Soru / Tarafsız
  sınıflarının her biri toplam 20, her konuda 5 örnekle dengeli temsil edilir.
- 32 temel ve 48 zor örnek; olumsuzlamalı destek, örtük kısıtlama, sınırlı
  kullanım, gerekçeli itiraz ve soru işaretsiz kaynak eleştirisi ayrıca ölçülür.
- Genel doğruluk, Macro-F1, dört konu için ayrı başarı, temel/zor kırılımı,
  sınıf başına precision/recall/F1 ve gerçek 80 örnek karışıklık matrisi.
- Hatalı yorumlar saklanmaz: başlık, yorum metni, beklenen sınıf, gerçek
  tahmin, zorluk türü ve yalnızca varsa gerçek model güveni gösterilir.
- Yapay zekâ dışındaki başlıklarda Transformer, yapay zekâya özgü hipotezler
  yerine konu-bağımsız dört görüş hipoteziyle çalışır; eski demo korunur.
- Çok senaryolu test ayrı düğmeyle ve isteğe bağlı başlatılır; beş tekrarlı
  mevcut hızlı performans/önbellek ölçümünü veya soğuk/sıcak sayacını bozmaz.
- Her ölçüm kendi SQLite `app_meta` anahtarında tutulur; eski sonuç, kullanıcı
  tartışmaları, profil, analiz geçmişi, bildirimler, mesajlar, yer imleri ve
  listeler değiştirilmez.
- Aktif kullanıcı tartışmasının gerçek yorum, tekil yorum, iddia ve soru
  sayıları referans verisinden ayrı gösterilir; etiketsiz kullanıcı içeriğine
  doğruluk veya F1 değeri uydurulmaz.
- Dar ana sayfa başlığında `N-KÖPRÜ` artık iki satıra bölünmez; üst eylemler
  gerektiğinde kendi alanlarında düzgünce sarılır.
- GPU zorunlu değildir. CPU ve uyumlu GPU aynı davranışı kullanır; bilgisayar
  modeline özgü koşul eklenmez.

## Kurulum

1. Çalışan backend ve frontend'i `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine çıkar. `.venv`,
   `node_modules`, `.next`, `.env`, `.db` ve `__pycache__` pakette olmadığı
   için kurulu bağımlılıklar ve SQLite kullanıcı verileri korunur.
3. Backend'i çalıştır:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Ayrı terminalde frontend'i çalıştır:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://localhost:8000/health` adresinde `version: 1.4.0` ve
   `storage: sqlite` görünmelidir.

## Elle test

1. Ana Sayfa'da `N-KÖPRÜ` başlığının tek satırda kaldığını doğrula.
2. `AI Modelini Hazırla`, ardından demo tartışmayı analiz et.
3. `Teknik Doğrulama` ekranında önce `Gerçek Ölçümü Başlat`; 20 cümlelik
   referans, 80 ham/20 tekil demo, `%25` kaynak farkındalığı, dokuz değişmez
   ve soğuk/sıcak önbellek sonuçları önceki sürümdeki gibi çalışmalıdır.
4. `Çok Senaryolu Doğrulamayı Başlat`; 80 gerçek örneğin sınıflandırılması,
   özellikle CPU üzerinde, 20 cümlelik referanstan daha uzun sürebilir.
5. Sol kartta 4 konu/80 örnek, genel doğruluk, Macro-F1, model çıkarımı,
   yapısal karar sayısı ve dört konuya ayrı başarı oranı görünmelidir.
6. Sağ panelde `Temel ifadeler` ile `Zor ve örtük ifadeler` skorlarını,
   dört konunun ayrı kartlarını ve 80 örnekli karışıklık matrisini incele.
7. `Gerçek sınıflandırma hataları` varsa yorum, beklenen görüş ve gerçekleşen
   tahmin açıkça listelenmelidir; skorlar model/ortama göre değişebilir.
8. Ana Sayfa'da yeni yorum ekle, Teknik Doğrulama'ya dön ve `Aktif kullanıcı
   tartışması` altında gerçek toplamın değiştiğini doğrula; 80 senaryo sabit
   kalmalı ve kullanıcı yorumuna sahte doğruluk/F1 atanmamalıdır.
9. Sayfayı yenile veya backend'i yeniden başlat; hem referans hem çok
   senaryolu sonucun SQLite üzerinden ayrı ayrı geri geldiğini doğrula.
10. Bildirim dedup, Profil, Mesajlar, Yer İmleri, Listeler ve 8 analiz adımı
    çalışmaya devam etmelidir.

## Test durumu

- **808/808 unittest; 43 test paketi.**
- Önceki regresyonlar: **700/700**.
- Yeni kontroller: **48 senaryo/veri/model + 24 SQLite kalıcılığı ve ürün
  izolasyonu + 36 arayüz sözleşmesi = 108/108**.
- TypeScript tam typecheck ve optimize Next.js production build başarılı.

---

# N-KÖPRÜ v1.3.3 — Donanımdan Bağımsız İddia Radarı Önbelleği

v1.3.3 aynı belirsiz yorumun model kararını tekrar tekrar üretmez. İddia
Radarı'nın doğrulanmış model sonucu sınırlı süreç belleğinde tutulur; yorum,
tartışma başlığı, model veya aktif cihaz değiştiğinde karar otomatik olarak
yeniden hesaplanır. CPU ve GPU üzerinde aynı ürün davranışı korunur.

## v1.3.3 ile gelenler

- İlk analizde belirsiz iddia adayı gerçekten mevcut modele gönderilir.
- Aynı tartışma yeniden analiz edildiğinde değişmeyen yorumun model kararı
  önbellekten gelir; ikinci Transformer çıkarımı yapılmaz.
- Yeni belirsiz bir yorum eklenirse yalnızca yeni yorum modele gönderilir;
  daha önce değerlendirilmiş yorumlar tekrar çalıştırılmaz.
- Önbellek anahtarı model adı, gerçek model nesnesi, aktif cihaz, tartışma
  başlığı, tam yorum metni, aday etiketler, hipotez şablonu ve karar eşiğini
  kapsar. Ham yorum metni yerine SHA-256 özet anahtarı kullanılır.
- Sonuçlar en fazla 512 girdilik, en az kullanılanı atan süreç-içi önbellekte
  tutulur. SQLite'a yorum önbelleği veya ek tablo yazılmaz; backend yeniden
  başlatılırsa önbellek güvenli biçimde temizlenir.
- Eşzamanlı aynı istek tek model çalıştırmasına indirgenir. Hatalı, eksik veya
  geçersiz model çıktısı kaydedilmez. Olumsuz model kararları da doğru biçimde
  yeniden kullanılır.
- Teknik Doğrulama ilk gerçek soğuk analizi, tekrar analizlerinin gerçek sıcak
  medyanını, hızlanma oranını, önbellek isabetlerini ve önlenen çıkarımları
  ayrı gösterir.
- Altı analiz katmanında ilk ve tekrar süreleri karşılaştırılır; ilk analiz
  darboğazı ile normal tekrar darboğazı gerçek ölçümlerden hesaplanır.
- İddia Radarı kartı `AI + Önbellek`, yeni Transformer kararı ve önbellek
  kararı sayılarını dürüstçe ayırır.
- Eski v1.3.1 ve v1.3.2 SQLite teknik sonuçları silinmeden açılır; eksik yeni
  ölçümler uydurulmaz ve yeni gerçek ölçümle tamamlanır.
- GPU zorunlu değildir; herhangi bir bilgisayardaki mevcut çalışma ortamı
  aynen kullanılır. Hazır ve uyumlu GPU varsa mevcut model seçimi korunur;
  yoksa CPU üzerinde aynı önbellek iyileştirmesi çalışır.

## Kurulum

1. Çalışan backend/frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine aç. `.venv`,
   `node_modules`, `.next`, `.env`, `.db` ve `__pycache__` ZIP içinde olmadığı
   için mevcut kurulumlar ve SQLite kayıtları korunur.
3. Backend'i çalıştır:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Ayrı terminalde frontend'i çalıştır:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://localhost:8000/health` yanıtında `version: 1.3.3` ve
   `storage: sqlite` görünmelidir.

## Elle test

1. Ana Sayfa'da gerçek AI modelini hazırla ve demo tartışmayı analiz et.
2. `4 · İddia Radarı` kartında ilk analizde `1 yeni Transformer kararı`
   görünmelidir. Aynı tartışmayı tekrar analiz ettiğinde `0 yeni Transformer
   kararı`, `1 önbellek kararı` ve `AI + Önbellek` görünmelidir.
3. Demo tartışmaya `Bazı öğrenciler farklı araçlarla bütün projelerini
   hazırlatıyor.` yorumunu ekle. Eski yorum önbellekten kullanılmalı; yalnızca
   yeni belirsiz yorum için `1 yeni Transformer kararı` oluşmalıdır.
4. Sol menüde `Teknik Doğrulama` → `Gerçek Ölçümü Başlat` düğmesini kullan.
5. `İlk analiz ve tekrar analizi` kartında soğuk süre ile sıcak tekrar
   medyanını karşılaştır. Beş tekrar için `1 yeni İddia Radarı çıkarımı` ve
   `4 yeniden kullanılan model kararı` beklenir.
6. Sağ panelde `Ne kadar model işi önlendi?` kartında `4` önlenen çıkarım,
   `4` önbellek isabeti, `1` yeni model çıkarımı ve `%80` yeniden kullanım
   görülmelidir. Model yüklenmediyse sayaçlar dürüstçe `0` kalır.
7. `Analiz süresi nereye gidiyor?` bölümünde İddia Radarı'nın ilk çalışma ve
   tekrar çalışma sürelerini ayrı kontrol et.
8. `%25` kaynak farkındalığı, iki açık soru, 28 kelime Köprü sınırı ve dokuz
   demo değişmezi korunmalıdır.
9. Aynı analizi yeniden çalıştırırken mükerrer bildirim oluşmamalı; silinmiş
   bildirimler geri gelmemeli. Profil, Mesajlar, Yer İmleri ve Listeler
   çalışmaya devam etmelidir.

## Test durumu

- **700/700 unittest; 40 test paketi.**
- Korunan önceki regresyonlar: **572/572**.
- Yeni testler: **44 önbellek motoru + 36 soğuk/sıcak ölçüm + 20 gerçek
  API/SQLite kalıcılığı + 28 arayüz sözleşmesi = 128/128**.
- Tam TypeScript typecheck ve optimize Next.js production build başarılı.

---

# N-KÖPRÜ v1.3.2 — Kompakt Teknik Panel ve Katman Bazlı Performans

v1.3.2, Teknik Doğrulama ekranındaki gereksiz boşlukları giderir ve gerçek
analiz süresini altı ayrı işlem katmanında ölçer. İç doğrulama setinin görüş
çıkarımı, demo görüş çıkarımı ve demo İddia Radarı çıkarımı artık birbirine
karıştırılmaz. Mevcut SQLite kayıtları ve önceki ölçümler korunur.

## v1.3.2 ile gelenler

- Teknik Doğrulama sağ panelindeki kartlar artık diğer analiz ekranlarının 560
  piksellik minimum yüksekliğini devralmaz; yalnızca içerikleri kadar yer kaplar.
- Görüş sınıflandırması, İddia Radarı, Cevapsız Sorular, Ortak Zemin, Görüş
  Haritası ve Köprü Oluştur her gerçek demo tekrarında ayrı ayrı zamanlanır.
- Her katman için gerçek örnek süreleri, medyan, ortalama, minimum, maksimum,
  P95, toplam süre içindeki pay ve varsa gerçek Transformer çıkarımı hesaplanır.
- En yavaş katman ölçülen değerlerle belirlenir; sabit bir darboğaz uydurulmaz.
- İç set görüş çıkarımı, iç set iddia çıkarımı, demo görüş çıkarımı ve demo
  İddia Radarı çıkarımı ayrı gösterilir. Demo #8 modelle incelenmişse yorum
  numarası ve beş tekrardaki gerçek çıkarım sayısı görünür.
- PyTorch sürümü, CUDA destekli derleme, CUDA erişimi, aktif cihaz ve yalnızca
  gerçekten algılanmış ekran kartı adı gösterilir. CPU derlemesinden fiziksel
  ekran kartının olmadığı sonucu çıkarılmaz.
- v1.3.1'den kalan teknik ölçümler silinmeden açılır. Saklanmamış eski süreler
  ve model sayaçları `Ölçülmedi` olarak belirtilir; yeniden ölçümle güncellenir.
- Teknik ölçüm bildirim, analiz geçmişi, profil, mesaj, yer imi, liste ve kayıtlı
  tartışmalara dokunmaz; yalnızca son sonuç mevcut SQLite `app_meta` kaydına
  yazılır.

## Kurulum

1. Çalışan backend/frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine aç. `.venv`,
   `node_modules`, `.next`, `.env`, `.db` ve `__pycache__` ZIP içinde olmadığı
   için mevcut Python/Node kurulumu ve SQLite kayıtların korunur.
3. Backend'i başlat:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Ayrı terminalde frontend'i başlat:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://localhost:8000/health` çıktısında `version: 1.3.2` ve
   `storage: sqlite` görünmelidir.

## Elle test

1. Önce sol menüden `Teknik Doğrulama`yı aç: varsa önceki v1.3.1 sonucu
   silinmeden görünmeli; yeni katman alanı yeniden ölçüm isteyebilir.
2. Ana Sayfa'ya dönüp modeli hazırla, sonra Teknik Doğrulama'da `Gerçek Ölçümü
   Başlat` düğmesine bas.
3. Sağ panelde `Analiz süresi nereye gidiyor?` bölümünde altı katmanı, ölçülen
   süreleri, yüzde paylarını ve gerçek en yavaş katmanı kontrol et.
4. Sol tarafta `İç doğrulama seti` ile `Demo · analiz başına` bloklarını
   karşılaştır. Demo model çıkarımı gerçekleşmişse `#8` ve İddia Radarı sayacı
   görünmeli; görüş sayacı sıfır olabilir.
5. `CPU / CUDA durumu` kartında PyTorch sürümünü, CUDA derlemesini, CUDA erişimini
   ve modelin gerçekte CPU'da mı GPU'da mı çalıştığını incele.
6. Sağ paneldeki süre, katman, karışıklık matrisi ve sınıf kartları arasında
   artık büyük boş alanlar olmamalı.
7. Dokuz demo değişmezinin, `%25` kaynak farkındalığının, iki açık sorunun ve
   Köprü kelime sınırının korunduğunu doğrula.
8. Profil, Bildirimler, Mesajlar, Yer İmleri ve Listeler'i aç. Ölçüm yeni analiz
   geçmişi veya bildirim üretmemeli.

## Test durumu

- **572/572 unittest; 36 test paketi.**
- Korunan v1.3.1 regresyonları: **497/497**.
- Yeni testler: **36 katman/model ve geriye uyumluluk + 15 CPU/CUDA + 24
  kompakt arayüz = 75/75**.
- Python `compileall`, tam TypeScript typecheck ve optimize Next.js production
  build başarılı.

---

# N-KÖPRÜ v1.3.1 — Gerçek Teknik Ölçüm ve Şeffaf Doğrulama

v1.3.1, mevcut ürün özelliklerini korurken ayrı bir **Teknik Doğrulama** alanı
ekler. Bu alan sınıflandırma doğruluğunu, sınıf bazlı skorları ve analiz
gecikmesini gerçekten çalıştırarak ölçer; değerleri hazır metin olarak
göstermez.

## v1.3.1 ile gelenler

- Sol menüdeki `Teknik Doğrulama` bölümünden `Gerçek Ölçümü Başlat` çalıştırılır.
- Dört görüş sınıfından beşer adet, toplam 20 elle etiketlenmiş Türkçe iç örnek
  mevcut analiz motoruyla gerçekten sınıflandırılır.
- Doğruluk, Macro-F1, sınıf bazlı precision/recall/F1, karışıklık matrisi ve
  örnek bazında beklenen / tahmin edilen etiketler gösterilir.
- Sabit demo tartışması beş kez gerçekten analiz edilir; medyan, P95, minimum,
  maksimum ve örnek çalışma süreleri mevcut bilgisayarda yeniden ölçülür.
- 80 ham → 20 benzersiz yorum, `%25` kaynak farkındalığı, iki açık soru, yüksek
  öncelikli iddia, kısa Köprü ve #7/#11 semantik korumaları doğrulanır.
- Model hazır değilse kendiliğinden yüklenmez; heuristik yedeğin gerçek sonucu
  gösterilir. Model hazır olsa da Transformer çıkarımı yapılmadığında model
  kullanılmış veya model güveni ölçülmüş gibi davranılmaz.
- Ölçüm tartışmalara, analiz geçmişine, bildirimlere ve profil istatistiklerine
  dokunmaz. Yalnızca son ölçüm SQLite üzerinde saklanır.
- 20 örnek küçük, elle etiketlenmiş iç doğrulama verisidir; bağımsız benchmark
  veya genellenebilir akademik sonuç değildir.

## Kurulum

1. Çalışan backend/frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine aç. `.venv`,
   `node_modules`, `.env` ve `backend/data/nkopru.db` ZIP içinde olmadığı için
   mevcut yerel kurulumun ve kayıtların korunur.
3. Backend:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Frontend:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://localhost:8000/health` sonucunda `version: 1.3.1` ve
   `storage: sqlite` görmelisin.

## Elle test

1. Ana sayfada istersen önce `AI Modelini Hazırla` ile hibrit modeli belleğe al.
2. Sol menüden `Teknik Doğrulama` bölümünü aç.
3. `Gerçek Ölçümü Başlat` düğmesine bas. Sol tarafta iç set doğruluğunu,
   Macro-F1'i, medyan/P95 sürelerini ve dokuz ürün davranışı kontrolünü incele.
4. Sağ tarafta beş ayrı süre örneğini, karışıklık matrisini, sınıf bazlı skorları
   ve açılır etiketli örnekleri kontrol et.
5. AI modelini hazırlamadan denersen `Heuristik yedek` sonucu görünür. Hatalı
   örnekler gizlenmez. Model hazırsa hibrit yol ayrıca belirtilir.
6. Ölçüm öncesi ve sonrası `Profil` bölümündeki toplam analiz sayısını ve
   `Bildirimler` sayısını karşılaştır: artmamalı.
7. Backend'i kapatıp yeniden başlat; `Teknik Doğrulama` son sonucu SQLite'tan
   yeniden açmalıdır.

## Test durumu

- **497/497 unittest başarılı; 33 test paketi.**
- Önceki v1.3.0 regresyonları: **436/436**.
- Yeni testler: **32 ölçüm + 11 SQLite/izolasyon + 18 UI sözleşmesi = 61/61**.
- Python `compileall`, tam TypeScript `tsc --noEmit` ve Next.js production build
  başarılı.

---

# N-KÖPRÜ v1.3.0 — Canlı Tartışma ve Gerçek Değişim Takibi

v1.3.0, açık olan bir tartışmaya yeni yorum ekleme ve aynı işlem içinde kalıcı yeni analiz anlık görüntüsü üretme özelliğini getirir. Demo, Keşfet ve kullanıcının oluşturduğu tartışmalar aynı güvenli SQLite akışını kullanır. v1.2.3'ün analiz tutarlılığı ve v1.1.2'nin Bildirim Dedup davranışı korunur.

## v1.3.0 ile gelenler

- Gönderi kartındaki `Tartışmaya yeni yorum ekle` alanından 1200 karaktere kadar yeni katkı girilebilir.
- `Yorumu Ekle ve Analizi Güncelle` işlemi yorumu SQLite'a kaydeder, tartışmayı yeniden analiz eder, snapshot oluşturur ve arayüzü yeni sonuçla günceller.
- İşlem tamamlandığında arayüz doğrudan `Ben Yokken Ne Değişti?` adımını açar.
- Aynı metin sosyal akışta ayrı yorum olarak saklanabilir; analizde tekrar olarak tekilleştirildiği için sahte yeni görüş, iddia, soru veya bildirim oluşturmaz.
- Yeni soru yalnızca soru/kaynak olayını, yeni iddia yalnızca iddia olayını üretir. Gerçekten değişen görüş, ortak zemin veya Köprü ayrıca kendi ilgili bildirimini üretebilir.
- Daha önce aynı yüksek öncelikli iddia için oluşturulan uyarı tekrarlanmaz; kullanıcı tarafından silinen olay yeniden doğmaz.
- Demo ve Keşfet sabit kaynakları bellekte değiştirilmez. Yerel değişiklikler SQLite'taki kalıcı gönderi kopyasında tutulur.
- Eş zamanlı yorum ekleme işlemleri `BEGIN IMMEDIATE` ile sıralanır; yorum kimliği çakışması ve kayıp güncelleme engellenir.
- v1.2.x'ten kalan Listeler bileşeni TypeScript prop uyumsuzluğu giderildi; çalışma davranışı değiştirilmedi.

## Kurulum

1. Backend ve frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine aç. Mevcut `.venv`, `node_modules`, `.env` ve `backend/data/nkopru.db` dosyan korunur; SOURCE ZIP bunları içermez.
3. Backend'i başlat:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Frontend'i ayrı terminalde başlat:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://localhost:8000/health` yanıtında `version: 1.3.0` ve `storage: sqlite` görmelisin.

## Elle doğrulama

1. Demo tartışmasını analiz et ve Bildirim sayısını not et.
2. Sol gönderi kartındaki canlı yorum alanına `Bu yasak öğrencilerin ruh sağlığını nasıl etkiler?` yazıp `Yorumu Ekle ve Analizi Güncelle` düğmesine bas.
3. İşlem sonunda `Ben Yokken Ne Değişti?` açılmalı; `1 yeni benzersiz yorum` ve `1 yeni cevapsız soru` değişimleri görünmelidir.
4. `Cevapsız Sorular` adımında yeni soru kartını, Bildirimler'de yalnızca ilgili yeni kaynak/soru bildirimini kontrol et.
5. Aynı cümleyi ikinci kez ekle. Ham yorum sayısı artar; benzersiz analiz sayısı, değişim listesi ve bildirim sayısı artmamalıdır.
6. Backend'i kapatıp yeniden aç. `Örneğe Dön` sonrasında eklenen yorumların korunması gerekir.
7. İstersen `Yeni Tartışma` veya Keşfet'teki bir tartışmada da aynı canlı yorum akışını dene.

## Test durumu

- **436/436 unittest başarılı; 30 test paketi.**
- Önceki v1.2.3 regresyonları: **383/383**.
- Yeni v1.3.0 testleri: **24 canlı akış + 13 SQLite/eş zamanlılık/dedup + 16 UI sözleşmesi = 53/53**.
- Yanıt Koçu: **29/29 unittest + 552 ek senaryo kontrolü**.
- Python `compileall`, TypeScript `tsc --noEmit` ve Next.js 15.4.6 optimize production build başarılı.

---

# N-KÖPRÜ v1.2.3 — Tutarlı Analiz Özeti ve Gerçek Görüş Ayrışması

Bu sürüm, v1.2.2 doğrulama ekran görüntülerinde saptanan üç tutarsızlığı düzeltir: model çıkarımı yapılmadığında yapılmış gibi anlatan özet, yalnızca en yüksek oranlı iki kümeye bakarak yasakçı azınlığı dışarıda bırakan Köprü ve soru etki metnindeki eski teknik görüş adları.

## v1.2.3 ile gelen düzeltme

- Demo tartışmasında 20 yapısal karar ve 0 Transformer çıkarımı varsa özet artık `Görüş katmanı hibrit analiz motorunun yapısal Türkçe sinyalleriyle çıkarıldı; bu analizde Transformer çıkarımı gerekmedi.` der.
- Gerçek Transformer çıkarımı olan başka tartışmalarda yapısal karar ve model çıkarımı sayıları ayrı belirtilir; model kullanımı veya güveni uydurulmaz.
- Ana özet, kontrollü kullanım `%50`, kullanım alanlarını koruma `%20` ve tam yasak `%10` yaklaşımlarını birlikte gösterir.
- `Tam yasak veya güçlü sınırlama` %10 ile azınlıkta olsa da tartışmanın gerçek politika karşıtlığı olduğu için Köprü kapsamından çıkarılmaz.
- Asıl ayrışma artık tam yasaklama + kontrollü kullanım + yararlı kullanım alanlarını koruma seçeneklerini birlikte açıklar.
- Köprü kartında `Karşılaştırılan yaklaşımlar` altında üç görüş adı ayrı etiketlerle gösterilir.
- Demo Köprü sorusu 24 kelimedir ve 28 kelimelik üst sınırı korur.
- Soru #6 ve #13'ün etki metinlerinde `Koşullu / Dengeli`, `Karşı / Sınırlayıcı` gibi teknik adlar yerine görünür kart adları kullanılır. İç olay/snapshot kimlikleri değiştirilmez.
- Yasak içermeyen genel tartışmalara yapay yasaklama dili taşınmaz; soru/tarafsız küme karar tarafı gibi gösterilmez.

## Kurulum ve elle doğrulama

1. Çalışan backend ve frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörü üzerine aç; mevcut `.venv`, `node_modules`, `.env` ve `backend/data/nkopru.db` korunur.
3. Backend: `cd D:\NKOPRU\backend`, `.\.venv\Scripts\Activate.ps1`, `uvicorn app.main:app --reload --port 8000`.
4. Frontend: `cd D:\NKOPRU\frontend`, `npm run dev`.
5. `/health` yanıtında `version: 1.2.3` ve `storage: sqlite` kontrol et.
6. AI hazırken demoyu analiz et; **Tartışmayı Anla** özetinde `Transformer çıkarımı gerekmedi` ve üç gerçek politika yaklaşımının `%50`, `%20`, `%10` oranlarını kontrol et.
7. **Köprü Oluştur** ekranında `Asıl ayrışma` alanının tam yasaklama, kontrollü kullanım ve kullanım alanlarını korumayı birlikte anlattığını doğrula. `Karşılaştırılan yaklaşımlar` üç etiket göstermelidir.
8. Köprü sorusunda `Tam yasak, kontrollü kullanım ve kullanım alanlarını koruma` ifadesini gör; soru 28 kelimeden kısa kalmalıdır.
9. **Cevapsız Sorular** kartlarında #6 ve #13'ün etki açıklamalarında görünür görüş adlarını kontrol et; teknik canonical adlar görünmemelidir.
10. **Görüş Haritası** bölümünde #7, #11, `%50/%20/%20/%10` dağılımı ve `20 yapısal / 0 Transformer` sonucu korunmalıdır.
11. **Tartışmayı Anla** ekranındaki kaynak farkındalığı `%25` olmalıdır.
12. Eski v1.2.2 sonucundan ilk geçişte Köprü sorusu gerçekten değiştiği için bir kez Köprü bildirimi oluşabilir; sonraki aynı analizler yeni bildirim üretmemelidir.

## Test durumu

- **383/383 unittest başarılı; 27 ayrı test paketi.**
- Önceki v1.2.2 regresyonları: **330/330**.
- Yeni v1.2.3 testleri: **30 analiz tutarlılığı + 12 arayüz sözleşmesi + 11 SQLite/bildirim = 53/53**.
- Yanıt Koçu: **29/29 unittest + 552 ek senaryo kontrolü**.
- Python `compileall` ve `frontend/lib/types.ts`, `frontend/lib/api.ts` Node TypeScript sözdizimi kontrolleri başarılı.
- Bu çalışma ortamında frontend bağımlılıkları bulunmadığından tam TypeScript kontrolü ve Next.js production build çalıştırılmadı.

---

# N-KÖPRÜ v1.2.2 — Görüş Tutarlılığı ve Kompakt Görüş Haritası

Bu sürüm, v1.2.1 Görüş Haritası ekran görüntülerinde yakalanan iki gerçek sınıflandırma hatasını düzeltir ve uzun görüş kartlarını açılır, okunabilir özetlere dönüştürür. Profil, analiz geçmişi, SQLite kalıcılığı, Bildirim Dedup, Mesajlar, Yer İmleri, Listeler, Cevapsız Sorular ve kısa Köprü sorusu korunur.

## v1.2.2 ile düzeltilen davranış

- #7 Selin Aksoy: `Ben ders çalışırken açıklama almak için kullanıyorum, ödevimi ona yazdırmıyorum.` artık yasakçı kümeye değil `Kontrollü ve kurallı kullanım` kümesine bağlanır.
- #11 Pelin Öz: `Kaynak belirtilmediği sürece yüzde vermek çok anlamlı değil.` artık yasakçı kümeye değil `Kanıt talebi / tarafsız değerlendirme` kümesine bağlanır.
- Sınırlı kişisel kullanım ile başkasının bütün ödevini yapay zekâya yaptırmasına yönelik eleştiri birbirine karıştırılmaz.
- Kaynaksız yüzde/iddia eleştirisi, kaynak göstermeden yapay zekâ kullanımının akademik riskinden ayrı değerlendirilir.
- Koruma hem gerçek hibrit AI akışında hem heuristik yedek akışta çalışır; gerçek model güveni uydurulmaz.
- Hibrit demo dağılımı: `10 / %50 kontrollü`, `2 / %10 tam yasak`, `4 / %20 yasağa karşı`, `4 / %20 kanıt/tarafsız`.
- Demo görüş katmanında `20 yapısal karar + 0 Transformer çıkarımı + 2 anlam tutarlılığı koruması` beklenir. AI modelinin hazır olması korunur; gereksiz sınıflandırma çıkarımı atlanır.
- Her kart önce görüş adını, yorum sayısını, oranı ve kısa gerekçesini gösterir. Temalar, ilişkiler, temsilci yorumlar, düzeltilen yorumlar, kümedeki tüm yorum numaraları ve soru/iddia bağlantıları `Görüş ayrıntıları ve temsilci yorumlar` satırından açılır.
- Tekrar eden `AI sınıflandırma örnekleri` bölümü de varsayılan olarak kapalıdır.
- Yasakçı görüş açıklamasındaki `risk ... riskler` tekrarı giderilir.

## Kurulum ve elle doğrulama

1. Backend ve frontend terminallerini `Ctrl+C` ile durdur.
2. ZIP içeriğini mevcut `D:\NKOPRU` klasörü üzerine aç. Mevcut `backend/data/nkopru.db`, `.venv`, `node_modules` ve `.env` korunur; teslim paketinde bunlar bulunmaz.
3. Backend: `cd D:\NKOPRU\backend`, `.\.venv\Scripts\Activate.ps1`, `uvicorn app.main:app --reload --port 8000`.
4. Frontend: `cd D:\NKOPRU\frontend`, `npm run dev`.
5. `http://localhost:8000/health` sonucunda `version: 1.2.2` ve `storage: sqlite` gör.
6. Gerçek AI hazırken demo tartışmasını analiz et ve **3. Görüş Haritası** bölümünü aç.
7. `%50 / %10 / %20 / %20` dağılımını, `20 yapısal sinyal`, `0 Transformer çıkarımı` ve `2 yorum anlam tutarlılığı kontrolü` açıklamasını doğrula.
8. Kontrollü kartta `Anlam tutarlılığıyla doğrulanan yorumlar` altında #7'yi; tarafsız karttaki aynı bölümde #11'i kontrol et. Her kartta `Kümedeki tüm yorumlar` da görünür; kartlar ilk açılışta kapalı olmalıdır.
9. **Tartışmayı Anla** ekranında `%25` kaynak farkındalığını; **Cevapsız Sorular** ekranında #6 ve #13'ü; **Köprü Oluştur** ekranında kısa Köprü sorusunu doğrula.
10. Aynı tartışmayı yeniden analiz et: snapshot geçmişi büyür, fakat anlamlı yeni değişiklik yoksa bildirim sayısı artmaz. Eski v1.2.1 sonucundan ilk geçişte düzeltilen gerçek görüş oranları bir defalık anlamlı değişiklik sayılabilir.

## v1.2.2 test sonucu

- **330/330 unittest başarılı; 24 ayrı test paketi.**
- Önceki v1.2.1 regresyonları: **282/282**.
- Yeni v1.2.2 testleri: **26 anlamsal tutarlılık + 14 kompakt arayüz + 8 SQLite/bildirim = 48/48**.
- Yanıt Koçu: **29/29 unittest + 552 ek güvenlik/senaryo kontrolü**.
- Python `compileall` ve `frontend/lib/types.ts`, `frontend/lib/api.ts` Node TypeScript sözdizimi kontrolleri başarılı.
- Frontend bağımlılıkları çalışma ortamında bulunmadığından tam TypeScript kontrolü ve Next.js production build çalıştırılmadı; başarılı oldukları iddia edilmez.

---

# N-KÖPRÜ v1.2.1 — Açıklanabilir ve Bağlama Duyarlı Görüş Haritası

Bu sürüm, kullanıcının doğruladığı **v1.2.0 semantik Cevapsız Sorular + v1.1.2 Bildirim Dedup + SQLite kalıcılık** tabanını korur. Görüş Haritası artık yalnızca dört genel etiket ve yüzde göstermez: her görüşün tartışmada neyi savunduğunu, kaç yoruma dayandığını, hangi yorumlarla temsil edildiğini ve diğer kümelerle nasıl ilişkilendiğini açıklar.

Mevcut `backend/data/nkopru.db` kaynak ZIP'ine dahil edilmez. Paketi mevcut `D:\NKOPRU` üzerine açtığında profil, analiz geçmişi, bildirim, mesaj, yer imi ve liste kayıtları korunur. Önceki v1.0–v1.2.0 snapshot'ları yeni Görüş Haritası alanları için geriye uyumlu varsayılanlarla açılabilir.

## v1.2.1 ile gelen geliştirme

### Görüş etiketi artık neyin desteklendiğini açıkça söyler

- Yasaklama ve düzenleme tartışmalarında `Koşullu / Dengeli`, `Kontrollü ve kurallı kullanım` olarak görünür.
- `Karşı / Sınırlayıcı` kümesi `Tam yasak veya güçlü sınırlama` biçiminde açıklanır.
- `Destekleyen` kümesi, yasaklamayı destekliyormuş gibi anlaşılmaması için `Yasağa karşı / kullanım alanlarını koruma` olarak gösterilir.
- Soru/kanıt isteyen veya kararsız yorumlar ayrı gösterilir; karar tarafı gibi sunulmaz.
- Yasakla ilgisiz tartışmalara yapay yasak etiketleri taşınmaz.

### Her görüş kartı kaynak yorumlarına geri bağlanır

- Yüzdeyle birlikte gerçek benzersiz yorum sayısı gösterilir.
- Ana gerekçe, kümedeki yorumlarda bulunan öğrenme, risk, kural, fayda, kanıt veya şeffaflık temalarıyla açıklanır.
- Temsilci yorumlarda gerçek yorum numarası, yazar, metin ve kararın yapısal/model kaynağı görünür.
- Ayrıştığı görüşler, ortak zemin temaları, ilgili İddia Radarı ve soru bağlantıları gösterilir.
- Küme başına yapısal karar ve Transformer çıkarımı ayrı sayılır.
- Model güveni yalnızca Transformer tarafından sınıflandırılan yorumlar içindir; görüşün haklılığı veya bütün tartışmanın doğruluğu anlamına gelmez.

### Snapshot ve Bildirim Dedup uyumluluğu

- `Viewpoint.name` alanındaki eski canonical kimlik korunur; yeni görünen ad `display_name` alanındadır.
- Yalnızca sunum adı/gerekçe değişti diye eski snapshot'lar yeni görüş veya bildirim üretmez.
- Zengin Görüş Haritası SQLite snapshot'larında saklanır ve backend yeniden başlatıldıktan sonra geri açılır.
- Kullanıcının sildiği görüş bildirimi aynı analizde yeniden oluşturulmaz.
- v1.2.0 soru türleri, tekrar birleştirme, retorik ayrımı ve cevap bağlantıları korunur.

## v1.2.1 hızlı kontrol

1. Backend/frontend'i başlat; `/health` yanıtında `version: 1.2.1` ve `storage: sqlite` kontrol et.
2. AI modelini hazırla, demo tartışmasını analiz et ve **3. Görüş Haritası** bölümünü aç.
3. `Kontrollü ve kurallı kullanım`, `Tam yasak veya güçlü sınırlama`, `Yasağa karşı / kullanım alanlarını koruma` ve `Kanıt talebi / tarafsız değerlendirme` başlıklarını kontrol et.
4. Her kartta yorum sayısı + yüzde, ana gerekçe, temsilci yorum, diğer görüşlerle ilişki ve varsa soru/iddia bağlantısını doğrula.
5. Model güveni notunun yalnızca Transformer yorumlarını kapsadığını kontrol et.
6. **Cevapsız Sorular** bölümünde #6 ve #13'ü, **Tartışmayı Anla** bölümünde kaynak farkındalığının %25 olduğunu ve **Köprü Oluştur** ekranında kısa soruyu yeniden doğrula.
7. Aynı demo tartışmasını değişiklik olmadan yeniden analiz et; analiz geçmişi artmalı, bildirim sayısı artmamalıdır.

## v1.2.1 test durumu

- **282/282 unittest metodu başarılı**
- Yeni Görüş Haritası: **22/22 semantik + 10/10 SQLite/snapshot/dedup + 14/14 UI**
- Önceki tüm regresyonlar: **236/236**
- Yanıt Koçu: **29/29 + 552 ek senaryo kontrolü**
- Python `compileall`: başarılı
- `frontend/lib/types.ts` ve `frontend/lib/api.ts`: Node TypeScript sözdizimi kontrolü başarılı
- Frontend bağımlılıkları bu ortamda bulunmadığı ve npm ağ yetkisi engellendiği için tam `tsc --noEmit` ve Next.js production build çalıştırılmadı; başarılı olduğu iddia edilmez.

---

# N-KÖPRÜ v1.2.0 — Semantik Cevapsız Sorular

Bu paket, doğrulanmış **v1.1.2 Bildirim Dedup + v1.1.1 semantik analiz + v1.0 SQLite** tabanını korur. v1.2.0'ın hedefi, Cevapsız Sorular bölümünü basit soru işareti taramasından çıkarıp tartışmadaki gerçek bilgi ve kanıt boşluklarını açıklayan çalışan bir analiz katmanına dönüştürmektir.

Mevcut `backend/data/nkopru.db` kaynak ZIP'ine dahil edilmez. Paketi mevcut `D:\NKOPRU` üzerine açtığında profil, analiz geçmişi, bildirim, mesaj, yer imi ve liste verilerin korunur. Eski snapshot JSON'ları yeni soru alanları için geriye uyumlu varsayılanlarla açılır.

## v1.2.0 ile gelen geliştirme

### Cevapsız Sorular artık soru işareti listesi değildir

- Bilgi/açıklama sorusu, uygulama/karar sorusu ve açık kaynak/kanıt talebi ayrılır.
- “Nasıl kullanılacağını öğretmeli” gibi içinde soru sözcüğü geçen öneri cümleleri soru sayılmaz.
- Soru işareti bulunmasa bile “Bu yüzde için güvenilir kaynak paylaşılmalı” gibi açık kanıt talepleri yakalanır.
- Retorik/meydan okuyan sorular ayrı tutulur ve cevapsız soru sayısına eklenmez.
- Aynı anlamdaki tekrar sorular tek kartta birleştirilir; dayanak yorum numaraları korunur.
- Sonraki ilgili yorumlarda yanıt bağlantısı aranır ve durum `Cevapsız`, `Kısmen cevaplandı` veya `Cevaplandı` olarak gösterilir.
- Her kartta soru türü, durum, öncelik, dayanak yorumlar, yanıt bağlantıları, etkilediği görüş kümeleri ve “Bu soru cevaplanırsa ne değişebilir?” açıklaması bulunur.
- Soru güveni, ifadenin ilgili soru türüne ait olduğuna ilişkin tespit güvenidir; sorunun veya yanıtın doğruluk olasılığı değildir.

### Snapshot ve Bildirim Dedup uyumluluğu

- Soru kartlarının yeni alanları analiz snapshot JSON'unda SQLite üzerinde kalıcı saklanır.
- Eski v1.0–v1.1.2 snapshot'ları açılmaya devam eder.
- Bir sorunun yanıt durumundaki gerçek değişiklik “Ben Yokken Ne Değişti?” karşılaştırmasına yansır.
- Yanıtlanmış ve retorik sorular yeni kaynak talebi bildirimi üretmez.
- Aynı sorunun semantik tekrarı yeni soru olayı sayılmaz.
- Değişmeyen yeniden analiz ve silinen bildirim korumaları v1.1.2 mantığıyla devam eder.

## v1.2.0 hızlı kontrol

1. Backend ve frontend'i başlat; `/health` yanıtında sürümün `1.2.0`, depolamanın `sqlite` olduğunu kontrol et.
2. Demo tartışmasını analiz et ve **Cevapsız Sorular** adımını aç.
3. Demo veride yorum #6 ve #13'ün yüksek öncelikli `Kaynak / Kanıt Talebi` olarak göründüğünü kontrol et.
4. Kartlarda durum, dayanak yorum, etkilediği görüşler, yanıt bağlantısı ve etki açıklamasının göründüğünü doğrula.
5. Aynı tartışmayı değişiklik olmadan yeniden analiz et; snapshot sayısı artarken bildirim rozeti artmamalıdır.
6. Profilden eski bir snapshot aç; kaydedilmiş sonuç yeni analiz çalıştırılmadan açılmalıdır.

## v1.2.0 test durumu

- **236/236 unittest metodu başarılı**
- Yeni Cevapsız Sorular: **15/15 semantik + 8/8 SQLite/snapshot/dedup + 10/10 UI**
- Bildirim: **22/22 backend + 11/11 UI**
- Yanıt Koçu: **29/29 + 552 senaryo kontrolü**
- Semantik analiz: **20/20 backend + 10/10 UI**
- Python `compileall`: başarılı
- Tam `npm ci`, ağ yetki sınırı nedeniyle bu çalışma ortamında tamamlanamadı; bu nedenle tam `tsc --noEmit` ve Next.js production build geçtiği iddia edilmez.

---

## v1.1.2 — Anlamlı Bildirim ve Dedup Düzeltmesi

Bu paket, **v1.1.1 semantik analiz + v1.0 SQLite/Profil/Analiz Geçmişi** tabanını korur. v1.1.2'nin hedefi, snapshot geçmişi büyürken Bildirimler merkezinin aynı olaylarla şişmesini engellemektir.

Mevcut `backend/data/nkopru.db` kaynak ZIP'ine dahil edilmez. Paketi mevcut `D:\NKOPRU` üzerine açtığında profil, analiz geçmişi, bildirim, mesaj, yer imi ve liste verilerin korunur.

## v1.1.2 ile gelen düzeltme

### Bildirim artık “analiz çalıştı” değil, “anlamlı bir şey değişti” demektir

- Aynı tartışmayı tekrar analiz edip snapshot karşılaştırmasında değişiklik bulunmazsa **yeni bildirim oluşmaz**.
- Sonraki analizlerde yalnızca yeni görüş/değişen görüş oranı, yeni iddia, yeni cevapsız soru-kaynak talebi, değişen ortak zemin veya değişen Köprü sorusu bildirim üretir.
- İlk analizde başlangıç bildirimleri korunur.
- Yeni bildirimlerin tekilleştirme kimliği görünür başlıktan değil **olayın gerçek içeriğinden** üretilir. Aynı olay + aynı içerik tekrar bildirim oluşturmaz.
- Kullanıcının sildiği aynı olay yeniden doğmaz.

### Önceki sürümlerden kalan mükerrer otomatik bildirimler bir kez temizlenir

v1.1.2 ilk backend açılışında eski otomatik analiz bildirimlerini tek seferlik denetler. Aynı olay ailesinde birden çok aktif eski kopya varsa en yeni kayıt tutulur, eski kopyalar soft-delete edilir. Eşdeğer kopyalardan biri okunmuşsa kalan kayıt da okunmuş tutulur.

Bu nedenle v1.1.1'de örneğin `13` görünen bildirim rozeti, v1.1.2'yi ilk çalıştırdığında daha düşük bir sayıya inebilir. Bu beklenen davranıştır; eski mükerrer otomatik olaylar birleştirilir.

### Bildirim ekranı açıklaması güncellendi

Arayüz artık açıkça şunu belirtir: **“Aynı tartışmayı değişiklik olmadan yeniden analiz etmek yeni bildirim üretmez.”** Okundu/okunmadı, tek silme, Okunanları temizle ve 5 saniyelik Geri Al akışı aynen devam eder.

## v1.1.2 hızlı kontrol

1. Backend'i v1.1.2 ile ilk kez başlat. Eski mükerrer otomatik bildirimlerin varsa rozetin bir kez düşmesi beklenir.
2. Demo tartışmasını analiz et ve Bildirimler sayısını not et.
3. Hiçbir yorum/veri değişmeden aynı tartışmayı tekrar analiz et. Bildirim sayısı **artmamalı**; Profilde analiz/snapshot sayısı ise artmaya devam etmelidir.
4. Bildirimler ekranının alt notunda “değişiklik olmadan yeniden analiz etmek yeni bildirim üretmez” açıklamasını kontrol et.
5. Okundu/okunmadı, tek silme, Okunanları temizle ve Geri Al işlemlerinin çalıştığını doğrula.

## v1.1.2 test durumu

- **203/203 unittest metodu başarılı**
- Bildirim: **22/22 backend + 11/11 UI**
- Yanıt Koçu: **29/29 + 552 senaryo kontrolü**
- Semantik analiz: **20/20 backend + 10/10 UI**
- Python `compileall`: başarılı
- `page.tsx`, `layout.tsx`, `api.ts`, `types.ts`: TS/TSX syntax-transpile başarılı
- Tam `tsc --noEmit` çalıştırılmadı; tam tip kontrolü geçtiği iddia edilmez.

---

## v1.1.1 — Kaynak Farkındalığı ve Kısa Köprü Düzeltmesi

Bu paket, **v1.0.0 SQLite + Profil + Analiz Geçmişi** tabanını korur ve analiz çekirdeğinin üç önemli bölümünü güçlendirir: **İddia Radarı**, **Ortak Zemin** ve **Köprü Oluştur**.

Mevcut `backend/data/nkopru.db` veritabanı kaynak ZIP'ine dahil edilmez. Bu nedenle paketi mevcut `D:\NKOPRU` üzerine açarken v1.0'da oluşmuş profil, analiz geçmişi, bildirim, mesaj, yer imi ve liste verilerin korunur.


## v1.1.1 ile gelen düzeltmeler

### 1. Kaynak farkındalığı artık gerçek kanıt sinyallerini ölçer

Önceki sürümde **Kaynak farkındalığı** yalnızca İddia Radarı'ndaki adayların doğrudan kaynak/atıf işareti taşıyıp taşımamasına göre hesaplanıyordu. Bu nedenle tartışmada açıkça “güvenilir bir araştırma var mı?” veya “dayandığı veri nedir?” gibi sağlıklı kaynak talepleri bulunsa bile gösterge `%0` olabiliyordu.

v1.1.1'de metrik, benzersiz yorumların içinde **kaynak, araştırma, veri, kanıt, istatistik veya ölçüm** ihtiyacını açıkça gündeme getiren yorumların oranı olarak hesaplanır. Kaynak sunmak kadar **kaynak istemek de kanıt farkındalığı** kabul edilir. Demo tartışmasında 20 benzersiz yorumun 5'inde bu sinyaller bulunduğu için gösterge `%25` olur; ayrıca 2 açık kaynak/veri talebi ayrı olarak motor meta verisinde tutulur.

Arayüzde metriğin ne anlama geldiği kısa bir açıklamayla görünür hâle getirildi; böylece yüzde, iddiaların doğruluk puanı veya kaynakların güvenilirlik puanı gibi yorumlanmaz.

### 2. Köprü sorusu kısa/öz biçim kuralına bağlandı

Köprü Oluştur, ortak zemin + ana ayrışma + eksik kanıt mantığını korur; fakat soru artık tartışma başlığını ve ayrıntı kartlarını tekrar eden uzun bir paragraf üretmez. Sorular **en fazla 28 kelimelik** kontrollü şablona bağlandı. Dinamik tema beklenmedik biçimde uzarsa yarım cümle kırpmak yerine tam ve kısa bir yedek soru üretilir.

Demo tartışmasında yeni Köprü sorusu:

> Sert kısıtlama ile kontrollü kullanım seçeneklerini öğrenme etkisinin ölçülmesi açısından hangi ortak ölçütlerle karşılaştırmalı ve bu ölçütleri hangi güvenilir verilerle sınamalıyız?

Bu soru 21 kelimedir ve önceki sürümdeki aynı bilgiyi daha kısa biçimde taşır. Kelime sayısı backend meta verisinde kalite kontrolü için tutulur; kullanıcı arayüzünde teknik sayaç olarak gösterilmez.

---

## v1.1.0 ile gelen ana değişiklikler

### 1. İddia Radarı — hibrit doğrulanabilirlik analizi

İddia Radarı artık tek bir anahtar sözcük listesiyle çalışmaz.

- Sayısal / istatistiksel iddiaları ayırır.
- Etki / nedensellik iddialarını ayırır.
- Karşılaştırmalı iddiaları ayırır.
- Yaygınlık / davranış genellemelerini ayırır.
- Salt politika önerisi, değer yargısı ve kişisel deneyimi doğrulanabilir iddiadan ayırmaya çalışır.
- Soru biçimindeki yüzde/kaynak taleplerini yanlışlıkla iddia olarak işaretlemez.
- Her iddiaya **Yüksek / Orta / Düşük doğrulama önceliği** verir.
- Her iddia için hangi tür kanıtın gerekli olduğunu açıklar.
- Kaynak işareti olup olmadığını gösterir.
- Yapısal karar belirsizse ve mDeBERTa-XNLI modeli zaten yüklüyse aynı Transformer katmanını ikinci karar katmanı olarak kullanabilir.

Demo tartışmasında yapısal yedek motor üç net doğrulanabilir aday çıkarır: yorum #10'daki `%70` iddiası ile yorum #1 ve #4'teki etki iddiaları. Salt yönerge önerileri veya kişisel kullanım deneyimi iddia olarak şişirilmez.

### 2. Ortak Zemin — görüş kümeleri arası çapraz-tema analizi

Ortak Zemin artık sabit metin değildir. Analiz, aynı temanın **birden fazla görüş kümesinde** tekrar edip etmediğini kontrol eder.

Örnek ortak temalar:

- öğrenme etkisinin ölçülmesi,
- kurallı ve bağlama duyarlı kullanım,
- şeffaflık ve kaynak kullanımı,
- yapay zekâ okuryazarlığı ve rehberlik.

Her ortak zemin kartında:

- kaç görüş kümesinden sinyal geldiği,
- kaç yorumun dayanak olduğu,
- dayanak yorum numaraları,
- güven puanı

gösterilir. Belirgin içerik uzlaşısı yoksa sistem bunu yüksek güvenli uzlaşı gibi sunmaz; düşük güvenli **ortak değerlendirme ölçütleri** zemini üretir.

### 3. Köprü Oluştur — kanıta dayalı sentez

Köprü sorusu artık ilk cevapsız sorunun kopyası değildir. Sistem birlikte değerlendirir:

1. ortak kabul / çapraz-tema,
2. iki ana görüş arasındaki asıl ayrışma,
3. kaynak veya veri açığı,
4. en ilgili cevapsız araştırma sorusu,
5. görüş kümelerini temsil eden yorumlar.

Sonuçta Köprü kartı:

- ortak kabul,
- asıl ayrışma,
- eksik bilgi / doğrulama ihtiyacı,
- dayanak yorum numaraları,
- güven puanı,
- yeni sentezlenmiş Köprü sorusu

gösterir.

### 4. v1.0 kalıcılık ve geçmiş sistemi korunur

Aşağıdaki v1.0 özellikleri değişmeden devam eder:

- SQLite kalıcı depolama,
- Profil,
- analiz geçmişi / snapshot,
- Ben Yokken Ne Değişti? karşılaştırması,
- Bildirimler,
- Mesajlar,
- Yer İmleri,
- Listeler,
- Keşfet,
- Yanıt Koçu.

Eski v1.0 snapshot JSON'larında yeni semantik alanlar bulunmadığı için model alanları geriye dönük varsayılanlarla tanımlanmıştır. **v1.0 analiz geçmişi v1.1.1'de açılmaya devam eder.**

## Çalıştırma

Backend:

```powershell
cd D:\NKOPRU\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd D:\NKOPRU\frontend
npm run dev
```

Ardından `http://localhost:3000` adresini aç.

## Güncelleme

ZIP'i doğrudan mevcut `D:\NKOPRU` üzerine açabilirsin. Kaynak paketinde şu çalışma zamanı klasör/dosyaları yoktur:

- `.venv`
- `node_modules`
- `.next`
- `__pycache__`
- `backend/data/nkopru.db`

Bu yüzden mevcut sanal ortam, npm bağımlılıkların ve SQLite verilerin üzerine yazılmaz.

## v1.1.1 hızlı kontrol akışı

1. Ana Sayfa'da demo tartışmasını analiz et; Tartışmayı Anla ekranında Kaynak farkındalığının demo veride `%25` olduğunu ve açıklama satırında 5 yorum sinyali / 2 açık kaynak-veri talebi bulunduğunu kontrol et.
2. **İddia Radarı**'na geç; iddia türü, öncelik ve “Doğrulama için” alanlarını kontrol et.
3. **Ortak Zemin**'e geç; görüş kümesi / yorum sinyali / dayanak yorum numaralarını kontrol et.
4. **Köprü Oluştur**'a geç; “Kanıta Dayalı Köprü Sentezi”, güven puanı ve dayanak yorumları kontrol et. Köprü sorusunun tek cümle ve kısa olduğunu doğrula.
5. Profilden eski bir v1.0 snapshot'ı aç; geçmiş kayıt açılırken yeni analiz çalıştırılmadığını doğrula.

## Test durumu

v1.1.1 kaynak paketinde **198/198 unittest metodu** başarılıdır.

Yanıt Koçu regresyon seti ayrıca **552 senaryo kontrolü** içerir.

Ek kontroller:

- Python `compileall`: başarılı.
- `page.tsx`, `layout.tsx`, `api.ts`, `types.ts` TS/TSX syntax-transpile: başarılı.
- v1.0 snapshot şeması → v1.1.1 model geriye uyumluluk testi: başarılı.
- Tam `tsc --noEmit`, kaynak ZIP'te `node_modules` bulunmadığı için bu çalışma ortamında çalıştırılmamıştır; tam tip kontrolü geçtiği iddia edilmemektedir.

## Sonraki ürün adımları

v1.1.1 ile semantik analiz katmanındaki iki tutarsızlık kapatıldı. Sonraki büyük ürün adımları:

- gerçek N'Sosyal veri adaptörü,
- çok kullanıcılı kimlik doğrulama/yetkilendirme,
- kaynak URL'lerini gerçekten çözümleyip doğrulayan retrieval/fact-check katmanı,
- değerlendirme veri seti ile claim / ortak zemin / Köprü kalite benchmark'ı.
