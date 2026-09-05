# N-KÖPRÜ v1.4.2 — Konuya Duyarlı Analiz ve Ayrılmış İç Kontrol

Bu geliştirme yalnızca yerel SOURCE paketinde yapılmıştır. GitHub deposu,
yarışma etiketi ve sabit `v1.4.0-teknofest-final` teslimi değiştirilmez.

## 1. Tartışmanın konusunu gerçekten yansıtan görüş dili

Görüş Haritası, Tartışmayı Anla ve Köprü Oluştur ortak ve deterministik bir
konu bağlamı kullanır. Örneğin `Şirketlerde uzaktan çalışma sürmeli mi?`
başlığında kullanıcı artık şu gerçek pozisyonları görür:

- Uzaktan çalışmanın devamını savunanlar.
- Ofis zorunluluğu veya daha güçlü sınırlama.
- Kurallı veya hibrit çalışma.

Köprü ayrışması aynı pozisyonları kullanır; soru en fazla 28 kelimedir.
Telefon, park, okul kantini, geri dönüşüm, kütüphane, dijital oyun,
bisiklet ve ulaşım konuları da kendi bağlamlarında adlandırılır.

Kanonik görüş adları değiştirilmediği için bildirim parmak izleri, SQLite
geçmişi ve snapshot karşılaştırması geriye uyumludur. Sabit akademik yapay
zekâ demosunun doğrulanmış etiketleri ve metinleri özellikle korunmuştur.

## 2. Önceki 80 örnekten ayrılmış yeni kontrol

Teknik Doğrulama ekranındaki `Ayrılmış Yeni Kontrolü Başlat` düğmesi,
önceki dört konulu veri üzerinde kalibre edilen motoru beş ayrı konuda
80 yeni ifadeyle gerçekten çalıştırır:

1. Mahalle parkı erişimi — 16 ifade.
2. Okul kantini beslenmesi — 16 ifade.
3. Kentte geri dönüşüm — 16 ifade.
4. Halk kütüphanesi erişimi — 16 ifade.
5. Çocuklarda dijital oyun — 16 ifade.

Her konuda dört görüş sınıfı eşit temsil edilir; toplam 40 temel ve 40 zor
ifade vardır. Önceki veriyle 0 metin ve 0 konu çakışır. Sabit parmak izi:

`1b4e8cb55023d1a1b99e32a2029ff3fd5c0a00f55dd79be6fb937453011fbdcf`

Modelin yüklenmediği gerçek yedek motor koşusunda 70 / 80 doğru, %87,5
doğruluk, %90,18 Macro-F1 ve 10 gerçek hata ölçülmüştür. Gerçek mDeBERTa
modeli hazır olduğunda sonuç o cihazdaki gerçek model kararına bağlıdır.

Hatalar bu sürümde kuralları yeni sete uydurmak için kullanılmamıştır.
Doğrulama bağımsız bir dış benchmark, bilimsel genelleme veya gerçek
kullanıcı başarısı değildir; önceki kalibrasyondan ayrılmış proje içi
kontroldür. Bütün hatalar, sınıf metrikleri ve matris arayüzde görünür.

## 3. Geriye uyum ve ölçüm izolasyonu

- 20 örnekli eski referans ölçümü korunur.
- Dört konulu eski 80 örnekli ölçüm korunur.
- Yeni beş konulu 80 örnekli kontrol ayrı SQLite anahtarına yazılır.
- Ölçümler kayıtlı tartışmaları, profil geçmişini, bildirimleri, mesajları,
  yer imlerini veya listeleri değiştirmez.
- Kullanıcı tarafından silinmiş bildirimler tekrar oluşturulmaz.
- Kaynak farkındalığı %25, iki açık kaynak sorusu ve 28 kelimelik Köprü
  sınırı mevcut demo için aynen korunur.
- CPU yeterlidir; belirli GPU, ekran kartı veya bilgisayar modeli gerekmez.

## 4. Test sonucu

- Önceki sürümden korunan: **980 test**.
- Konu bağlamı ve demo geriye uyumu: **51 test**.
- Ayrılmış veri seti ve gerçek ölçüm: **51 test**.
- SQLite kalıcılığı ve ürün izolasyonu: **38 test**.
- Yeni ekran ve API arayüz sözleşmesi: **44 test**.
- Toplam: **50 pakette 1.164 / 1.164 başarılı test**.
- TypeScript `--noEmit` ve Next.js 15.4.6 üretim derlemesi başarılıdır.

## 5. Mevcut Windows kurulumu üzerine güncelleme

1. Backend ve frontend terminallerini `Ctrl+C` ile durdur.
2. SOURCE ZIP içeriğini mevcut `D:\NKOPRU` klasörünün üzerine çıkar.
   `.venv`, `node_modules`, `.next`, `.env`, `.db` ve `__pycache__` ZIP
   içinde olmadığı için yerel kurulum ve SQLite kayıtları korunur.
3. Backend terminalinde:

   ```powershell
   cd D:\NKOPRU\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```

4. Ayrı frontend terminalinde:

   ```powershell
   cd D:\NKOPRU\frontend
   npm run dev
   ```

5. `http://127.0.0.1:8000/health` yanıtında sürüm `1.4.2` olmalıdır.

## 6. Elle deneme sırası

1. Sabit demo tartışmada kaynak farkındalığının %25, açık soru sayısının
   2 ve bildirim tekilleştirmenin çalışır kaldığını doğrula.
2. `Yeni Tartışma` ile `Şirketlerde uzaktan çalışma sürmeli mi?` başlığını
   aç; devamı savunan, ofis zorunluluğu isteyen ve hibrit çalışmayı savunan
   üç gerçek yorum ekle.
3. `1 · Tartışmayı Anla`, `3 · Görüş Haritası` ve `8 · Köprü Oluştur`
   sekmelerinde aynı konuya özgü üç görüşün tutarlı göründüğünü kontrol et.
4. `Teknik Doğrulama` altında eski referans ve dört konulu testin ayrı
   çalıştığını doğrula.
5. `Ayrılmış Yeni Kontrolü Başlat` düğmesine bas; beş yeni konu, 80 örnek,
   0 ortak cümle, 0 ortak konu, SHA-256 ve gerçek sonuçlar görünmelidir.
6. Sağ panelde yeni konu skorları, karışıklık matrisi, Precision/Recall/F1
   ve varsa gizlenmeyen bütün hataları incele.
7. Sayfayı yenile veya backend'i yeniden başlat; üç ölçüm sonucunun ayrı
   ayrı SQLite üzerinden geri geldiğini doğrula.
