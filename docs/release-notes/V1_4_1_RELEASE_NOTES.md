# N-KÖPRÜ v1.4.1 — Bağlama Duyarlı Görüş Koruması

Bu sürüm, `v1.4.0-teknofest-final` teslim etiketini değiştirmeden sonraki
ürün geliştirmesini ayrı ve geri uyumlu biçimde sürdürür.

## Neler düzeltildi?

1. Erişimin, iletişim hakkının ve hizmetin sürmesini savunan örtük destek
   cümleleri yanlışlıkla kısıtlama görüşüne gönderilmez.
2. `denetimsiz`, `kuralsız` ve `şartsız` ifadeleri olumlu
   denetim/kural/şart sinyaliyle karıştırılmaz.
3. Soru işareti bulunmayan araştırma, kaynak ve veri talepleri tarafsız
   kanıt ihtiyacı olarak belirlenir.
4. Uzaktan çalışmada yalnızca ofiste bulunma zorunluluğu başlık bağlamıyla
   birlikte değerlendirilir; başka tartışmalara taşınmaz.
5. Açık yasak veya açık serbesti içeren bir cümlede kanıt talebi gerçek
   görüşü gizlemez.
6. Gerçek koşulla sürdürülen hizmet sınırsız destek olarak sunulmaz.
7. `uygulama` içindeki `ama` heceleri bağlaç sanılmaz.
8. Hem gerçek hibrit model yolu hem modelsiz yedek motor aynı anlam
   korumalarını kullanır.

## Doğrulama

- Önceki 808 testin tamamı korunmuştur.
- Daha önce kullanılmamış 42 cümle her iki motor yolunda ayrı ayrı
  denenmiştir; öncelik ve olumsuzlama kontrolleriyle bu pakette 108 test vardır.
- Kalıcılık, eski SQLite sonuçları, gerçek sayaçlar ve merkezi sürüm için
  38 değerlendirme testi eklenmiştir.
- Arayüz geriye uyumluluğu ve dürüstlük beyanları için 26 test eklenmiştir.
- Toplam: **46 paket, 980 / 980 başarılı test**.
- TypeScript tipi ve Next.js üretim derlemesi ayrıca doğrulanır.

Aynı 80 proje içi örnekte 77 yapısal karar, 3 model gerektiren yorum ve
13 açıklanabilir anlam koruması vardır. Kalan 3 yorum deterministik bir test
modeliyle doğru sınıflandırıldığında kontrollü sonuç 80 / 80'dir; kullanıcının
gerçek sonucu kendi mDeBERTa model çıktısına bağlıdır.

Önceki hatalar dil kurallarını iyileştirmek için incelendiğinden bu 80 örneğin
yeniden değerlendirilmesi **bağımsız test veya dış benchmark değildir**.
Sabit `v1.4.0` yarışma raporu ve GitHub teslim etiketi değiştirilmez.

## Korunan davranışlar

- FastAPI + Next.js + SQLite mimarisi.
- Sekiz analiz adımı ve tüm kalıcı ürün modülleri.
- Bildirim tekilleştirme, silinmiş bildirimlerin yeniden oluşmaması.
- İddia Radarı içerik önbelleği ve soğuk/sıcak çalışma davranışı.
- Demo kaynak farkındalığı %25, iki açık soru ve en fazla 28 kelimelik
  Köprü sorusu.
- CPU/GPU'dan ve belirli bilgisayar modellerinden bağımsız çalışma.
