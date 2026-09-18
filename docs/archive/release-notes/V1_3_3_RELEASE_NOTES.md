# N-KÖPRÜ v1.3.3 — İddia Radarı Sonuç Önbelleği

## Ürün amacı

Aynı belirsiz yorumu her yeniden analizde modele göndermeden, aynı analiz
sonucunu donanımdan bağımsız biçimde daha hızlı üretmek.

## Güvenli önbellek

- Saklama: yalnızca backend süreç belleği; en fazla 512 LRU girdisi.
- Anahtar: SHA-256(model adı + model nesnesi + cihaz + başlık + tam yorum +
  aday etiketler + hipotez şablonu + doğrulama eşiği).
- Kaydedilen veri: doğrulanmış olgusal karar ve gerçek model güveni.
- Model, cihaz, başlık veya metin değiştiğinde sonuç yeniden hesaplanır.
- Aynı anda gelen aynı istekler ikinci model çıkarımı oluşturmaz.
- Bozuk/eksik/NaN model cevabı kaydedilmez ve mevcut yapısal yedek korunur.
- Olumsuz model kararı da tekrar kullanılabilir.
- Aynı toplu çağrıdaki aynı yorum yalnızca bir kez modele gönderilir.
- Yeni yorum eklenirse yalnızca yeni belirsiz yorum yeniden çalıştırılır.
- GPU, CUDA, belirli ekran kartı veya kullanıcı bilgisayarı şart değildir.

## Şeffaf ölçüm

- İlk demo örneği gerçekten soğuk başlatılır.
- Sonraki demo örnekleri sıcak önbellekle gerçekten ölçülür.
- İlk süre, sıcak medyan, sıcak P95, hızlanma ve örnek etiketleri gösterilir.
- Gerçek model çıkarımı ve önbellek isabeti ayrı sayaçlardır.
- İddia Radarı için soğuk/sıcak katman süreleri ayrı görünür.
- İlk analiz darboğazı ve tekrar darboğazı gerçek katmanlardan belirlenir.
- Eski ölçümler silinmez; olmayan yeni veriler üretilmiş gibi gösterilmez.

## Korunan davranışlar

- İddia kartı, güven puanı, ortak zemin, görüş kümeleri, sorular ve Köprü
  soğuk ve sıcak analizlerde aynı kalır.
- SQLite kullanıcı verileri, snapshot geçmişi, bildirim dedup/silme koruması,
  Mesajlar, Yer İmleri, Listeler ve Profil mevcut sözleşmeleriyle korunur.
- Kaynak farkındalığı %25, iki açık soru, bir yüksek öncelikli iddia, Köprü
  üst sınırı 28 kelime ve dokuz teknik değişmez geçerlidir.

## Doğrulama

- 44 önbellek motoru testi.
- 36 gerçek soğuk/sıcak teknik ölçüm testi.
- 20 API/SQLite/bildirim/snapshot regresyonu.
- 28 arayüz sözleşme testi.
- Toplam 128 yeni test; 700/700 tüm testler ve production build.
