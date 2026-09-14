# N-KÖPRÜ — Jüri Teknik Sunum Metni V3

**TEKNOFEST 2026 · N’Sosyal İnovasyon Yarışması · Finalist · Teknik rapor: 98/100**

> Bu metin, jüri sunumunda kullanılacak tam anlatım metnidir. Teknik sonuçlar kapsamı ve sınırlılıklarıyla birlikte yazılmıştır. Kullanıcı etkisi, bağımsız benchmark veya canlı Qwen inference sonucu ölçülmemişse kesin sonuç olarak sunulmaz.

## Slayt 1 — N-KÖPRÜ
**Alt başlık:** Yapay Zekâ Destekli Sosyal Tartışma Zekâsı Sistemi
**Üst bilgi:** TEKNOFEST 2026 · N’Sosyal İnovasyon Yarışması · Finalist

### Slayt içeriği
- **Teknik rapor:** 98 / 100
- **Çalışan prototip:** v1.4.0 · sekiz analiz modülü
- **Sunumun amacı:** Problemden ölçüme, mimariden sorumlu kullanım sınırlarına kadar projenin tamamını göstermek.

### Jüriye anlatım
Bu sunumda N-KÖPRÜ’yü yalnızca bir fikir veya slogan olarak değil; çalışan prototipi, teknik mimarisi, testleri, ölçüm sınırları ve canlı demo akışıyla birlikte anlatacağız.

## Slayt 2 — Jürinin 90 saniyede bilmesi gerekenler
**Alt başlık:** Değerlendirmeyi üç soruya ayırıyoruz: hangi problem, çalışan hangi çözüm, hangi kanıt?

### Slayt içeriği
- **Problem:** Uzun tartışmalarda bağlam, görüş, iddia, kanıt ihtiyacı ve cevapsız sorular birbirine karışıyor. Kullanıcı çoğu zaman karşı görüşü anlamadan cevap veriyor.
- **Çözüm:** N-KÖPRÜ tartışmayı sekiz adımda bilgi haritasına dönüştürüyor: görüşleri, ortak zemini, iddiaları, soruları, değişiklikleri ve yapıcı yanıtı görünür kılıyor.
- **Kanıt ve sınır:** 80 proje içi elle etiketli örnekte 74/80 doğru ve %92,5 doğruluk/Macro-F1; v1.4.0 regresyonunda 808/808 test başarılı. Bu sonuçlar dış benchmark veya kullanıcı etkisi değildir.
- **Ne değil?:** Otomatik hakem, sansür filtresi veya doğruluk/fact-checking motoru değildir. Model güveni, iddianın doğru olduğu anlamına gelmez.

### Jüriye anlatım
Jüri açısından en önemli çerçeve şu: Sistem tartışmayı susturmuyor; tartışmanın yapısını anlaşılır hâle getiriyor. Teknik sonucu da sınırlarıyla birlikte sunuyoruz.

## Slayt 3 — Problemi tarif ediyoruz: tartışma metni karar verilebilir bilgiye dönüşmüyor
**Alt başlık:** Tartışmanın hacmi arttıkça içerik değil, içerik arasındaki ilişki kayboluyor.

### Slayt içeriği
- **Girdi:** Tekrarlanan yorumlar, karşıt görüşler, koşullu öneriler, kişisel saldırılar, sayısal iddialar ve soru biçimindeki katkılar aynı akışta ilerliyor.
- **Kayıp:** Kim neyi destekliyor? Hangi gerekçeye dayanıyor? Hangi iddia kaynak istiyor? Hangi soru hâlâ cevapsız? Bu sorular kullanıcıya hazır bir harita olarak görünmüyor.
- **Sonuç:** Yanıtlar kişiye yöneliyor; aynı nokta tekrar tekrar tartışılıyor; kanıtsız iddialar ile gerçek görüşler ayırt edilemiyor; yapıcı bir sonraki adım üretilemiyor.

### Jüriye anlatım
Buradaki problem yalnızca olumsuz duygu değildir. Aynı tartışmanın içinde farklı görüş türleri ve farklı kanıt ihtiyaçları vardır. N-KÖPRÜ bu ilişkileri ayırmayı hedefler.

## Slayt 4 — Neden klasik duygu analizi yetmez?
**Alt başlık:** N-KÖPRÜ’nün çıktısı yalnızca olumlu/olumsuz etiketi değildir.

### Slayt içeriği

### Tablo
| Boyut | Klasik duygu analizi | N-KÖPRÜ |
| :--: | :--: | :--: |
| Temel etiket | Olumlu / olumsuz / nötr | Destekleyen / karşı-sınırlayıcı / koşullu-dengeli / soru-tarafsız |
| İçerik | Duygusal ton | Görüş, iddia, gerekçe ve kanıt ihtiyacı |
| İlişki | Yorumun tek başına skoru | Görüş kümeleri, temsilci yorumlar ve karşıtlık ilişkileri |
| Eylem | Duyguya göre sınıflama | Cevapsız soruyu bulma, Yanıt Koçu ve Köprü Oluştur |
| Zaman | Anlık metin | Snapshot karşılaştırması ve anlamlı değişiklik bildirimi |

### Jüriye anlatım
Duygu analizi bir duygu sinyali verebilir; ancak jüriye göstermek istediğimiz ürün davranışı daha yapısaldır: görüş yönü, kanıt ihtiyacı, sorunun durumu ve sonraki yapıcı adım.

## Slayt 5 — Hedef, kapsam ve sınır
**Alt başlık:** Sistemin ne yaptığı kadar ne yapmadığını da tasarımın parçası kabul ediyoruz.

### Slayt içeriği
- **Hedefler:** Görüşleri ve dayanaklarını görünür kılmak; ortak zemini bulmak; doğrulama gerektiren iddiaları işaretlemek; cevapsız soruları önceliklendirmek; kişisel saldırıyı yapıcı bir mesaja dönüştürmek.
- **Kapsam dışı:** Bir iddianın gerçekliğine tek başına karar vermek; tartışmanın kazananını seçmek; kullanıcı adına görüş değiştirmek; konuşmayı otomatik susturmak; kaynak, istatistik veya sonuç uydurmak.
- **Tasarım ilkeleri:** Görünürlük · belirsizlikte dürüstlük · anlamı koruma · açıklanabilir işlem adımları · ölçülebilirlik · yerel kontrol.

### Jüriye anlatım
Bu sınırlar jüri için bir eksiklik değil, güvenilirlik ölçütüdür. Sistem kendisini fact-checker gibi sunmuyor; doğrulanması gereken noktayı göstermekle yetiniyor.

## Slayt 6 — Bir tartışmayı nasıl işleriz?
**Alt başlık:** Tek bir analiz çağrısı, farklı motorların ürettiği çıktıları tek bir sonuçta birleştirir.

### Slayt içeriği
- **Motor yaklaşımı:** Yüksek güvenli Türkçe yapısal sinyaller hızlı yolu oluşturur. Belirsiz görüş ve iddia örneklerinde isteğe bağlı mDeBERTa-XNLI devreye girer. Qwen yalnızca isteğe bağlı Yanıt Koçu üretken katmanıdır.
- **Kalıcı çıktı:** Analiz sonucu geçmişe snapshot olarak kaydedilir; yeni ve anlamlı değişiklikler içerik tabanlı bildirim kimliğiyle izlenir.

### Akış
1. Tartışma metni → 2. Normalize + tekilleştir → 3. Görüş ve görüş haritası → 4. İddia + kanıt ihtiyacı → 5. Sorular + ortak zemin → 6. Yanıt Koçu + Köprü Oluştur → 7. SQLite geçmişi / bildirim

### Jüriye anlatım
İş akışındaki önemli ayrım şu: Her adım aynı modele bırakılmıyor. Deterministik ve açıklanabilir olan bölüm hızlı çalışıyor; belirsiz bölüm gerektiğinde modele devrediliyor.

## Slayt 7 — Örnek tartışma: tek bir soru, sekiz farklı ihtiyacı açığa çıkarıyor
**Alt başlık:** Demo konusu: “Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?”

### Slayt içeriği

### Tablo
| Örnek katkı | Sistemin gördüğü ihtiyaç |
| :--: | :--: |
| “Kesinlikle yasaklanmalı; öğrenciler düşünmeyi bırakıyor.” | Karşı / sınırlayıcı görüş + gerekçe |
| “Tamamen yasaklamak yanlış; doğru kullanılırsa faydalı.” | Koşullu veya destekleyici görüş |
| “Sorun yasaklamak değil, nasıl kullandığımız.” | Çerçeveleme / ara pozisyon |
| “Kaynak göstermeden kullanılırsa güvenilirlik zarar görüyor.” | İddia + kaynak/kanıt ihtiyacı |
| “Başarı düzeyini karşılaştıran güvenilir araştırma var mı?” | Kaynak / kanıt talebi |
| “Sınavlarda yasak, öğrenme sürecinde kontrollü serbest olmalı.” | Koşullu görüş + bağlam korunmalı |
| “Geçen dönem sınıfımızın %70’i kullandı.” | Sayısal/doğrulanabilir iddia |
| “Hangi kullanım biçimleri öğrenmeyi güçlendiriyor?” | Ölçülebilir cevapsız soru |

## Slayt 8 — Modül 1 · Tartışmayı Anla
**Alt başlık:** İlk aşama, akışın genel yapısını kullanıcıya özetler.

### Slayt içeriği
- **Girdi:** Tartışma başlığı, yorumlar, yazar bilgisi, zaman ve etkileşim verileri.
- **İşlem:** Metinler normalize edilir; demo gibi tekrarlı akışlarda aynı içeriğin tekrarları tekilleştirilir; yorumların görüş ve soru özellikleri sonraki motorlara aktarılır.
- **Çıktı:** Tartışma özeti, ana ayrışmalar, ölçülebilir göstergeler, görüş dağılımı, iddia adayları ve açık soruların genel görünümü.
- **Demo kanıtı:** Demo akışında 80 ham yorum 20 benzersiz yoruma indirgenir; bu işlem analiz çıktısını şişirmeden tekrarları kontrol eder.

### Jüriye anlatım
Bu modül karar vermez; tartışmanın genel görünümünü çıkarır. Diğer yedi modülün hangi veriyi kullanacağını belirleyen başlangıç katmanıdır.

## Slayt 9 — Modül 2 · Ortak Zemin
**Alt başlık:** Uzlaşma iddiası değil; ilerleyebilmek için kesişen tema ve gerekçelerin görünürleştirilmesi.

### Slayt içeriği
- **Bulduğu şey:** Farklı görüşlerde tekrar eden tema, gerekçe ve kabul edilebilir başlangıç noktaları.
- **Kanıt bağlantısı:** Ortak zemin maddeleri destekleyen yorum kimlikleriyle ilişkilendirilir; böylece yalnızca genel bir cümle değil, hangi yorumlardan çıktığı da izlenebilir.
- **Yanlış uzlaşmayı önleme:** Bir tema iki tarafın tüm sonuçlarda anlaştığını göstermez. Sistem ortak noktayı, ayrışma ve eksik bilgiyle birlikte sunar.
- **Örnek:** “Kullanım amacı ve sınav bütünlüğü önemli” ortak bir başlangıç olabilir; bundan hangi kullanımın kabul edileceği otomatik olarak çıkarılmaz.

### Jüriye anlatım
Ortak zemin, tartışmayı yumuşatmak için her şeyi uzlaşma gibi göstermek değildir. Gerçek kesişimi, ayrışmanın yanında göstermek için kullanılır.

## Slayt 10 — Modül 3 · Görüş Haritası
**Alt başlık:** Dört sınıf, görüşlerin yönünü ve ara pozisyonları ayrı tutar.

### Slayt içeriği
- **Sınıflar:** Destekleyen · Karşı / Sınırlayıcı · Koşullu / Dengeli · Soru / Tarafsız.
- **Zenginleştirme:** Her küme için temsilci yorumlar, baskın temalar, ortak temalar, karşıt görüş ilişkileri, ilişkili iddia ve soru kimlikleri tutulur.
- **Hibrit karar:** Türkçe yapısal sinyaller yüksek güvenli örnekleri hızlı sınıflandırır; belirsiz örnekler isteğe bağlı Transformer katmanına gidebilir.
- **Dürüstlük:** Etiket görüş yönünü açıklar; haklılık veya doğruluk sonucu değildir. Model güveni de iddianın gerçekliğini göstermez.

### Jüriye anlatım
Özellikle koşullu/dengeli görüşleri ayrı sınıf olarak tutmamız önemli. “Hem destekliyorum hem belirli koşullarda sınırlandırılmalı” cümlesi tek bir kutuya zorlanmıyor.

## Slayt 11 — Modül 4 · İddia Radarı
**Alt başlık:** İddiaları doğrulamaz; hangi cümlelerin doğrulama gerektirdiğini görünür kılar.

### Slayt içeriği
- **İddia adayları:** Nicel/istatistiksel, karşılaştırmalı, etki/nedensellik, yaygınlık/davranış ve genel olgusal iddia türleri.
- **Kaynak farkındalığı:** Kaynak veya kanıt işareti var mı? İddianın doğrulanması için hangi kanıt türü gerekir? Öncelik yüksek, orta veya düşük mü?
- **Örnek:** “Öğrencilerin %70’i kullandı” ifadesi sayısal bir iddia olarak korunur; sistem oranı doğru kabul etmez, kaynağının sorulması gerektiğini işaretler.
- **Güvenlik:** Sistem kendisini bağımsız fact-checking servisi gibi konumlandırmaz; kaynak gösterme ve insan doğrulamasını gerekli sonraki adım olarak bırakır.

### Jüriye anlatım
İddia Radarı’nın değeri, iddiayı susturmak değil, tartışmanın hangi kısmında kanıt gerektiğini göstermektir.

## Slayt 12 — Modül 5 · Cevapsız Sorular
**Alt başlık:** Soruyu yalnızca soru işaretinden değil, anlamından ve tartışmadaki etkisinden izler.

### Slayt içeriği
- **Soru türleri:** Kaynak / Kanıt Talebi · Uygulama / Karar Sorusu · Bilgi / Açıklama Sorusu · Retorik / Meydan Okuma.
- **Gruplama:** Aynı anlamdaki tekrarlar tek soru kimliğinde gruplanır; ilgili yorumlar, etkilenen görüşler ve bağlantılı iddialar tutulur.
- **Durum:** Cevapsız · Kısmen cevaplandı · Cevaplandı. Durum, sonraki yorumlarla ilişkili anlamsal örtüşmeye göre güncellenir.
- **Öncelik:** Kaynak talebi, birden fazla görüşü etkileyen soru veya iddiaya bağlı soru daha görünür hâle gelir.

### Jüriye anlatım
Bu modül tartışmayı “kim daha çok konuştu?” ekseninden çıkarıp “hangi soru hâlâ cevapsız ve karar için neden önemli?” eksenine taşır.

## Slayt 13 — Modül 6 · Yanıt Koçu: yazmadan önce kontrol
**Alt başlık:** Niyeti koru · dili iyileştir · güvenliği denetle

### Slayt içeriği
- **Girdi:** Kullanıcının yazdığı taslak mesaj ve varsa tartışma bağlamı.
- **Analiz:** Hakaret/küfür, kişiye yönelik saldırı, ironi/sarkazm, soru, sayısal iddia, kaynak talebi, görüş yönü, koşullu görüş, konuya katkı eleştirisi ve bağlamı yeniden değerlendirme isteği.
- **Çıktı:** Açıklama, yapıcı öneri, algılanan sinyaller, kullanılan motor ve işlem süresi. Kullanıcının yerine otomatik gönderim yapılmaz.
- **İlke:** Mesaj zaten yapıcıysa gereksiz yere değiştirme; saldırı varsa kişiyi değil görüşü ve gerekçeyi tartışacak biçimde yeniden yaz.

### Jüriye anlatım
Yanıt Koçu’nun hedefi kullanıcıyı tek tip nazik cümleye zorlamak değil. İtirazı, soruyu, sayıyı ve kaynak talebini koruyarak saldırı kabuğunu ayıklamak.

## Slayt 14 — Yanıt Koçu hangi sinyalleri çıkarıyor?
**Alt başlık:** Tek bir kelimeye değil, birleşen sinyallere göre karar veriyor.

### Slayt içeriği
- **Dil ve güvenlik:** Hakaret/küfür · kişiye yönelik saldırı · açık ironi/sarkazm · bağlamı okumama veya yeniden değerlendirme saldırısı.
- **İçerik:** Soru · sayısal/doğrulanabilir iddia · kaynak/kanıt vurgusu · konuya katkı eleştirisi.
- **Görüş:** Görüş ayrılığı/itiraz · destek/olumlu görüş · koşullu/dengeli görüş · nötr/bağlamsal ifade.
- **Yanlış pozitif koruması:** “Tabii ki” veya “aynen katılıyorum” gibi normal olumlu ifadeler tek başına ironi sayılmaz; güçlü ve örtüşen ironi işaretleri aranır.

### Jüriye anlatım
Buradaki ayrım önemli: “tabii ki” kelimesini gördüğü için mesajı ironi sayan basit bir yaklaşım kullanmıyoruz. Bağlam ve birden fazla sinyal birlikte değerlendiriliyor.

## Slayt 15 — Yanıt Koçu’nun karar sırası
**Alt başlık:** Her üretim aynı güvenlik kapısından geçer.

### Slayt içeriği
- **Hızlı yol:** Zaten yapıcı mesajlar korunur; yüksek güvenli saldırı, sayısal iddia, kaynak eleştirisi, koşullu görüş ve ironi için deterministik dönüşüm kullanılır.
- **Üretken yol:** Yalnızca yüksek güvenli kuralların kapsamadığı belirsiz durumlarda Qwen/Qwen2.5-0.5B-Instruct aday üretir. Üretken model zorunlu değildir.
- **Son kapı:** Adayın içinde kişisel saldırı, prompt sızıntısı, anlamsız tekrar, kaybolan sayı/soru/kaynak, tersine dönen görüş veya yeni uydurulmuş sonuç varsa aday reddedilir.

### Akış
1. Normalize et → 2. Sinyalleri çıkar → 3. Yüksek güvenli yapısal yol → 4. Belirsizse isteğe bağlı Qwen adayı → 5. Anlam + güvenlik doğrulaması → 6. Güvenli fallback

### Jüriye anlatım
Bu mimari, küçük üretken modelin her kararı tek başına vermesini engelliyor. Üretken model yalnızca aday üretir; son sözü doğrulama ve güvenli fallback söyler.

## Slayt 16 — Yanıt Koçu’nda anlamı koruma kuralları
**Alt başlık:** Yumuşatmak, içeriği silmek veya görüşü tersine çevirmek değildir.

### Slayt içeriği
- **Korunan öğeler:** Sayılar ve yüzdeler; soru işareti ve soru niyeti; kaynak/kanıt talebi; koşul ve istisnalar; yasaklama/kullanım yönü; sınav bağlamı; ana içerik ankrajları.
- **Eklenemeyenler:** Girişte olmayan istatistik, gerekçe, sonuç, yasaklama veya görüş. Sistem kaynak uydurmaz; kullanıcıyı haklı ilan etmez.
- **Uzunluk kapısı:** Üretken aday en fazla iki kısa doğal cümle hedefler; doğrulama katmanı boş/çok kısa veya gereksiz uzun üretimleri reddeder.
- **Temiz mesaj:** Hakaret, kişiselleştirme, bağlam saldırısı ve ironi yoksa mesaj mümkün olduğunca olduğu gibi bırakılır.

### Jüriye anlatım
Jürinin özellikle bakabileceği nokta şu: sistem kötü mesajı düzeltirken ana niyeti kaybetmiyor. Bunun için sayı, soru, koşul ve görüş yönü ayrı ayrı denetleniyor.

## Slayt 17 — Yanıt Koçu örnekleri: kötü mesajdan yapıcı mesaja
**Alt başlık:** Dönüşümün ölçütü yalnızca nezaket değil; niyet ve somut içeriğin korunmasıdır.

### Slayt içeriği

### Yanıt Koçu örnekleri
- **“Sen bu konudan hiçbir şey anlamıyorsun.”** → “Bu görüşün gerekçesini yeterince ikna edici bulmuyorum. Dayandığın bilgi veya gerekçeleri daha açık paylaşabilir misin?”
- **“Kaynaklarınla gel, uydurup durma.”** → “Paylaşılan bilgilerin yeterince kaynakla desteklenmediğini düşünüyorum. İddiaları dayandıkları kaynaklarla birlikte paylaşabilir misin?”
- **“Tabii canım, yasaklayınca bütün sorunlar çözülecek zaten.”** → “Yapay zekâyı yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.”
- **“Tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.”** → Aynı koşullu görüş korunur; tek taraflı destek veya karşıtlığa çevrilmez.
- **“Geçen dönem öğrencilerin %70’i kullandı.”** → “Geçen dönem öğrencilerin %70’i kullandı. Bu bilginin dayandığı kaynak veya araştırmayı paylaşabilir misin?”

### Jüriye anlatım
Örneklerde saldırı çıkarılıyor ama kaynak talebi, yüzde, sınav koşulu ve görüş yönü korunuyor. Zaten yapıcı cümle ise yeniden yazılmıyor.

## Slayt 18 — Yanıt Koçu test ve performans kanıtı
**Alt başlık:** Test sonucu ile gerçek model çalıştırma durumunu birbirine karıştırmıyoruz.

### Slayt içeriği
- **v0.4.4 raporundaki test:** 29/29 regresyon başarılı; 552 senaryo kontrolü; API sözleşmesi ve FastAPI /health + /api/rewrite TestClient kontrolü başarılı.
- **Kapsam:** 96 saldırı × içerik güvenlik matrisi; 300 sabit tohumlu fuzz; 40 ironi × konu; 12 koşullu/dengeli görüş; 36 normal/olumlu ifade. Normal ifadelerde yanlış ironi pozitifliği: 0.
- **Benchmark:** 1.000 çağrı: ortalama 0,366 ms · medyan 0,340 ms · P95 0,587 ms · maksimum 3,940 ms. Değerler test ortamına aittir.
- **Dürüst not:** Test ortamında gerçek Qwen ağırlıkları yeniden indirilemediği için canlı üretken inference sonucu iddia edilmiyor; deterministik yol, kötü adayın reddi ve güvenli fallback test edildi.
- **Final hazırlığı:** Çalışma notlarında ayrıca 34/34 Yanıt Koçu regresyonu ve 743 senaryo kontrolü tutuldu; bu sayı raporun 29/29 baseline’ı ile tek toplam olarak birleştirilmemelidir.

### Jüriye anlatım
Bu slaytta iki şeyi ayırıyoruz: rapora giren test kanıtı ve final hazırlığında genişletilen yerel kontroller. Ayrıca Qwen canlı inference’ını çalıştırmadığımızı açıkça söylüyoruz.

## Slayt 19 — Modül 7 · Ben Yokken Ne Değişti?
**Alt başlık:** Kullanıcı geri döndüğünde yalnızca “yeni bildirim var” demek yerine ölçülebilir değişikliği gösterir.

### Slayt içeriği
- **Snapshot:** Her analiz sonucu geçmişte ayrı bir anlık görüntü olarak saklanır; önceki sonuçla karşılaştırılabilir.
- **Karşılaştırılanlar:** Görüş dağılımı, yeni veya kaybolan iddia adayları, soru durumu, ortak zemin, temel ayrışma ve köprü sorusu.
- **Bildirim ilkesi:** İçerik tabanlı olay kimliği kullanılır. Ölçülebilir değişiklik yoksa yeni bildirim üretilmez; aynı olay tekrar tekrar bildirilmez.
- **Geri alınabilirlik:** Bildirimler soft-delete mantığıyla silinir; silinen bildirimler yeniden üretim davranışıyla karışmaz ve geri yükleme akışı bulunur.

### Jüriye anlatım
Bu özellik yalnızca geçmiş göstermiyor. Kullanıcı yokken gerçekten ne değişti sorusuna, eski ve yeni analiz çıktısını karşılaştırarak cevap veriyor.

## Slayt 20 — Modül 8 · Köprü Oluştur
**Alt başlık:** Tartışmayı bitiren hüküm değil; bir sonraki yapıcı konuşmayı açan çıktı.

### Slayt içeriği
- **Girdiler:** Ortak zemin, temel ayrışma, kaynak/kanıt ihtiyacı ve cevapsız sorular.
- **Üç parçalı çıktı:** Ortak payda · karşı tarafın kaygısını kişiselleştirmeden tanıma · kanıt + ilerleten soru.
- **Sınır:** Köprü, iki tarafı aynı fikirde göstermez; kullanıcıdan görüşünü değiştirmesini istemez; hangi sorunun yanıtlanmasının ilerleme sağlayacağını önerir.
- **Teknik kural:** Köprü sorusu en fazla 28 kelimeyle sınırlandırılır; ilgili görüş ve iddia kimlikleriyle ilişkilendirilir.

### Jüriye anlatım
Köprü Oluştur’un çıktısı “herkes haklı” gibi boş bir uzlaşma cümlesi değil. Farklı görüşleri koruyup, konuşmanın bir sonraki somut adımını bulmaya çalışıyor.

## Slayt 21 — Ürün yüzeyi: analiz tek ekranda kalmıyor
**Alt başlık:** Analiz sonucu kullanıcı akışına ve tekrar ziyarete bağlanıyor.

### Slayt içeriği
- **Gezinme:** Ana Sayfa · Keşfet · Bildirimler · Mesajlar · Yer İmleri · Listeler · Profil · Teknik Doğrulama.
- **Kaydetme:** Kullanıcı tartışmayı, belirli bir iddia adayını veya Köprü sorusunu yer imlerine alabilir; içerikleri konu listelerine ekleyebilir.
- **Süreklilik:** Analiz geçmişi ve snapshot ayrıntısı yeniden açılır; mesajlar ve köprü paylaşımı tartışma akışına bağlanır.
- **Şeffaflık:** Teknik Doğrulama ekranı veri setini, beklenen/gerçek sınıfları, hataları, zorluk kırılımını ve ölçüm durumunu ayrı gösterir.

### Jüriye anlatım
Proje yalnızca tek seferlik analiz butonundan oluşmuyor. Kullanıcının kaydetmesi, geri dönmesi, değişikliği görmesi ve köprü sorusunu paylaşması için kalıcı ürün yüzeyleri var.

## Slayt 22 — Teknik mimari
**Alt başlık:** Yerel çalışabilen, katmanları ayrılmış ve dış LLM’e zorunlu olmayan yapı.

### Slayt içeriği
- **İstemci:** Next.js 15 · React 19 · TypeScript. Kullanıcı akışı, sekiz analiz adımı, teknik doğrulama ve kalıcı ürün sayfaları.
- **API:** FastAPI · Pydantic · Uvicorn. İstek doğrulama, analiz çağrısı, model durumları, geçmiş, bildirim, mesaj, yer imi ve liste uç noktaları.
- **Analiz:** Türkçe yapısal sinyaller + isteğe bağlı MoritzLaurer/mDeBERTa-v3-base-mnli-xnli. Yanıt Koçu için ayrı ve isteğe bağlı Qwen/Qwen2.5-0.5B-Instruct.
- **Kalıcılık:** SQLite; analiz snapshot’ları, app_meta sonuçları, olay parmak izleri ve iddia önbelleği.
- **Çalışma koşulu:** CPU üzerinde çalışır; uyumlu GPU hızlandırması opsiyoneldir. Dış API veya ücretli token servisi zorunlu değildir.

### Jüriye anlatım
Mimariyi iki nedenle hibrit kurduk: Türkçe yüksek güvenli örneklerde gereksiz model bekleme maliyetini azaltmak ve model hazır değilken güvenli yedek davranışı korumak.

## Slayt 23 — Arka uç analiz hattı
**Alt başlık:** Tek bir sonuç nesnesi, analiz adımlarının birbirine bağlı çıktısını taşır.

### Slayt içeriği
- **Ana analiz:** analyze_post; görüş ayrıntıları, ortak zemin ayrıntıları, görüş kümeleri, iddia adayları, açık/retorik sorular, değişiklikler ve köprü çıktısını birleştirir.
- **İzlenebilirlik:** Yorum kimlikleri; iddia, soru, görüş ve kanıt ilişkilerinde tutulur. Hangi çıktının hangi yorumlara dayandığı kaybolmaz.
- **İzolasyon:** Teknik senaryo değerlendirmesi kayıtlı kullanıcı tartışmalarını, bildirimleri, mesajları, yer imlerini, listeleri ve referans ölçümünü değiştirmez.

### Akış
1. İstek + Pydantic → 2. Tekilleştirme → 3. Görüş sınıflandırma → 4. İddia + önbellek → 5. Soru analizi → 6. Ortak zemin + viewpoint → 7. Köprü + snapshot → 8. Bildirim / geçmiş

### Jüriye anlatım
İşlem hattının amacı yalnızca sonuç üretmek değil, sonucu oluşturan ilişkileri de taşımak. Bu nedenle her modülün çıktısı bir sonraki modül tarafından tekrar kullanılabiliyor.

## Slayt 24 — Model seçimi ve hibrit mimari neden gerekli?
**Alt başlık:** Model kullanımı, ürün davranışının tamamı değildir.

### Slayt içeriği
- **Yapısal hızlı yol:** Türkçe destek/itiraz, koşul, soru, kaynak ve güvenlik sinyalleri açık olduğunda düşük gecikmeli ve açıklanabilir karar.
- **mDeBERTa-XNLI:** Belirsiz görüş veya iddia örneklerinde isteğe bağlı Transformer çıkarımı. Tüm cümleleri zorunlu olarak modele göndermemek için eşik ve hibrit akış kullanılır.
- **Qwen Yanıt Koçu:** Üretken model yalnızca belirsiz yeniden yazım adaylarında devreye girer. Prompt, sayı, soru, görüş yönü ve saldırı doğrulama kapısından geçemeyen aday gösterilmez.
- **Fallback:** Model paketi yoksa veya yükleme/üretim başarısızsa güvenli hibrit/bağlamsal fallback çalışır. Kullanıcıya boş veya saldırgan çıktı dönmemesi hedeflenir.

### Jüriye anlatım
Bu ayrım hem maliyet hem güvenlik açısından önemli. Modelin bulunmaması uygulamanın açılmasını engellemez; modelin ürettiği her şey de otomatik olarak doğru kabul edilmez.

## Slayt 25 — Veri kalıcılığı ve değişikliklerin güvenliği
**Alt başlık:** Kalıcılık, yalnızca veritabanına yazmak değil; tekrarların ve izolasyonun kontrolüdür.

### Slayt içeriği
- **SQLite tabloları:** app_meta · custom_posts · analysis_history · notifications · conversations/messages · bookmarks · topic_lists/topic_list_entries · profiles.
- **Tekilleştirme:** Bildirimlerde benzersiz signature_key; yer imlerinde identity_key; listelerde normalize edilmiş ad; liste öğelerinde liste + içerik kimliği benzersizliği.
- **İşlem güvenliği:** SQLite transaction ve BEGIN IMMEDIATE ile aynı kayda eşzamanlı yazımlarda tekrar üretim riski azaltılır.
- **İzolasyon:** Kullanıcı içeriği ile elle etiketli teknik doğrulama seti ayrı tutulur. Senaryo sonucu app_meta içinde ayrı anahtarla saklanır.
- **Geri alınabilirlik:** Bildirim silme soft-delete mantığındadır; okundu bildirimleri temizleme ve geri yükleme akışları ayrıdır.

### Jüriye anlatım
Jüriye özellikle vurgulanması gereken nokta: teknik değerlendirme çalıştırıldığında kullanıcının kayıtlı tartışması, geçmişi veya bildirimleri bozulmuyor.

## Slayt 26 — API sözleşmesi ve çalışma modları
**Alt başlık:** Kullanıcı arayüzü ile backend arasındaki akışlar açık uç noktalarla ayrılmıştır.

### Slayt içeriği
- **Servis ve modeller:** GET /health · /api/ai/status · /api/coach/status; servis ve model durumunu okumak.
- **Tartışma ve analiz:** GET /api/posts/demo · /api/posts/{id} · POST /api/analyze-discussion · GET /api/analyze/{id}.
- **Yanıt ve değerlendirme:** POST /api/rewrite · GET/POST /api/evaluation*; Yanıt Koçu ve teknik doğrulama.
- **Ürün davranışları:** notifications · messages · bookmarks · lists · history · profile.
- **Çalışma modu:** use_ai=true/false seçilebilir; model hazır değilse durum ve fallback nedeni sonuçta görünür. Varsayılan adresler: frontend 3000, backend 8000.

### Tablo
| Uç nokta grubu | Görev |
| :--: | :--: |
| GET /health · /api/ai/status · /api/coach/status | Servis ve model durumunu okumak |
| GET /api/posts/demo · GET /api/posts/{id} | Demo veya kayıtlı tartışmayı almak |
| POST /api/analyze-discussion · GET /api/analyze/{id} | Yeni veya kayıtlı tartışmayı analiz etmek |
| POST /api/rewrite | Yanıt Koçu’nu çalıştırmak |
| GET/POST /api/evaluation* | Teknik ve çok senaryolu değerlendirme |
| notifications · messages · bookmarks · lists · history · profile | Kalıcı ürün davranışları |

### Jüriye anlatım
API yüzeyini ayrı tutmak, demo sırasında yalnızca arayüzü değil; istek, sonuç ve hata davranışını da denetlenebilir kılıyor.

## Slayt 27 — Teknik doğrulama: veri seti nasıl kuruldu?
**Alt başlık:** Ölçüm, kullanıcı etkisi araştırması değil; kontrollü proje içi sınıflandırma doğrulamasıdır.

### Slayt içeriği
- **Kapsam:** 4 tartışma konusu × 20 örnek = 80 cümle. Dört görüş sınıfının her biri 20 örnekle dengeli temsil edilir.
- **Konular:** Akademik yapay zekâ · okulda telefon kullanımı · kampüste gece ulaşımı · uzaktan çalışma.
- **Zorluk:** 32 temel örnek; 48 zor/örtük örnek. Zor örneklerde örtük tutum, olumsuzlama, koşul ve kaynak eleştirisi bulunur.
- **Yöntem:** Beklenen etiketler elle belirlenir; sistem tahminiyle karşılaştırılır. Konu, sınıf, zorluk, Precision/Recall/F1 ve gerçek karışıklık matrisi ayrı hesaplanır.
- **Sınır:** Veri seti proje içidir; dış benchmark, bilimsel genelleme veya etiketsiz kullanıcı yorumlarında başarı sonucu değildir.

### Jüriye anlatım
Veri setinin küçük ve proje içi olduğunu saklamıyoruz. Buna rağmen yalnızca tek bir toplam başarı değil, sınıf ve zorluk ayrıntısını da gösteriyoruz.

## Slayt 28 — Sonuçlar · konu bazında
**Alt başlık:** 80 örnekte toplam 74 doğru sınıflandırma.

### Slayt içeriği
- **Ana metrik:** Accuracy: %92,5 · Macro-F1: %92,5.
- **Hata politikası:** 6 hata gizlenmedi; beklenen ve gerçekleşen sınıfın ayrıntıları Teknik Doğrulama ekranında gösterilecek şekilde tutuldu.

### Tablo
| Tartışma konusu | Doğru / toplam | Doğruluk |
| :--: | :--: | :--: |
| Akademik yapay zekâ | 19 / 20 | %95 |
| Okulda telefon kullanımı | 18 / 20 | %90 |
| Kampüs gece ulaşımı | 19 / 20 | %95 |
| Uzaktan çalışma | 18 / 20 | %90 |
| TOPLAM | 74 / 80 | %92,5 |

### Jüriye anlatım
Sonuç dört farklı konuda aynı değil; iki konuda %95, iki konuda %90. Bu dağılımı tek bir yüksek yüzdeye indirgemeden veriyoruz.

## Slayt 29 — Sonuçlar · sınıf bazında ve karışıklık matrisi
**Alt başlık:** Koşullu/dengeli görüşler ve karşı/sınırlayıcı görüşler ayrı izleniyor.

### Slayt içeriği
- **Gerçek karışıklık matrisi:** Beklenen ↓ / Tahmin → / Destek: 17, 3, 0, 0 / Karşı: 0, 18, 1, 1 / Koşul: 0, 0, 20, 0 / Soru: 0, 1, 0, 19
- **Yorum:** Hatalar özellikle destekleyen ile karşı/sınırlayıcı sınırında görülüyor; bu nedenle sınıf bazlı sonuçları toplam doğruluğun yanında sunuyoruz.

### Tablo
| Görüş sınıfı | Precision | Recall | F1 | Destek |
| :--: | :--: | :--: | :--: | :--: |
| Destekleyen | %100 | %85 | %91,9 | 20 |
| Karşı / Sınırlayıcı | %81,8 | %90 | %85,7 | 20 |
| Koşullu / Dengeli | %95,2 | %100 | %97,6 | 20 |
| Soru / Tarafsız | %95 | %95 | %95 | 20 |

### Jüriye anlatım
Macro-F1’in %92,5 olması sınıfların dengeli dağılımıyla birlikte yorumlanmalı. Karışıklık matrisinde hangi sınıfların birbirine karıştığını açıkça gösteriyoruz.

## Slayt 30 — Zorluk kırılımı ve motor kullanımı
**Alt başlık:** Kolay örneklerde başarı yüksek; örtük dil hâlâ geliştirme alanı.

### Slayt içeriği
- **Temel ifadeler:** 32 / 32 doğru · %100. Görüş yönü ve soru sinyali açık örneklerde hızlı yapısal yol etkili.
- **Zor / örtük ifadeler:** 42 / 48 doğru · %87,5. Olumsuzlama, koşul, örtük tutum veya kaynak eleştirisi gibi daha fazla bağlam gerektiren örnekler.
- **Motor sayacı:** 71 karar Türkçe yapısal sinyallerle; 9 karar gerçek Transformer çıkarımıyla üretildiği raporlandı.
- **Yorum sınırı:** Bu sayaç test koşusundaki motor kullanımını gösterir; model doğruluğu, kullanıcı memnuniyeti veya iddianın gerçekliği anlamına gelmez.

### Jüriye anlatım
Bu slayt bize nerede zorlandığımızı da gösteriyor. Zor dil için hibrit Transformer yolu var; fakat başarıyı olduğundan yüksek göstermek yerine örtük örneklerdeki düşüşü açıkça veriyoruz.

## Slayt 31 — Gecikme, önbellek ve kaynak davranışı
**Alt başlık:** Yerel CPU kullanımını mümkün kılmak için soğuk/sıcak ayrımı ölçülüyor.

### Slayt içeriği
- **Analiz gecikmesi:** Yerel CPU ölçümünde ilk/soğuk analiz yaklaşık 2,7–3,1 saniye; önbellekli tekrar yaklaşık 10–12 milisaniye. Süre cihaz, model durumu ve içerik uzunluğuna göre değişir.
- **Demo invariant’ları:** 80 ham / 20 benzersiz yorum · kaynak farkındalığı %25 · 2 açık soru · Köprü sorusu ≤28 kelime · 9/9 değişmez korunuyor.
- **Kaynak kullanımı:** Belirli GPU zorunlu değil. Model paketi ilk kez indirilecekse internet gerekebilir; normal ürün akışı dış API veya ücretli token servisine bağlı değildir.
- **Önbellek:** İddia çıkarımlarında içerik kimliği tabanlı önbellek tekrar model çalıştırmayı azaltır; cache sonucu kullanıcı içeriğiyle teknik doğrulama setini karıştırmaz.

### Jüriye anlatım
Gecikme sayısını tek bir ideal değer gibi vermiyoruz. Soğuk ve sıcak çalışmayı ayrı söylüyoruz; kullanıcı bilgisayarında farklı değerler çıkabileceğini not ediyoruz.

## Slayt 32 — Kalite kapısı · rapor ve final hazırlığı
**Alt başlık:** Kodun çalışması, ölçümün saklanması ve demo akışının tekrarlanabilirliği ayrı kontrol ediliyor.

### Slayt içeriği
- **v1.4.0 teknik rapor kanıtı:** 43 test paketi · 808/808 başarılı · önceki regresyonlar 700/700 · yeni testler 108/108.
- **Kod ve derleme:** TypeScript typecheck başarılı · Python compileall başarılı · Next.js optimize production build başarılı.
- **Demo değişmezleri:** 9/9 demo invariant’ı; source awareness, açık soru sayısı, köprü kelime sınırı, tekilleştirme ve model sayaçları ayrı kontrol edilir.
- **Genişletilmiş finalist kontrolü:** Çalışma notlarında backend 1.245/1.245; Yanıt Koçu 34/34 regresyon + 743 senaryo; API smoke 35/35; LAN 4/4; readiness 5/5; npm audit 0.
- **Rapor ayrımı:** 808/808 rapor sürümünün kanıtıdır. 1.245/1.245 ve diğer genişletilmiş değerler final hazırlığı kontrolüdür; iki set tek toplam gibi sunulmamalıdır.

### Jüriye anlatım
Jüriye tek bir test sayısı söyleyip bırakmıyoruz. Rapor sürümünü ve final hazırlığı genişletilmiş kontrollerini ayrı adlandırıyoruz; böylece sayıların hangi kapsama ait olduğu belli.

## Slayt 33 — Güvenlik, gizlilik ve erişilebilirlik
**Alt başlık:** Sorumlu sosyal yapay zekâ, teknik güvenlik ve kullanıcı kontrolünü birlikte gerektirir.

### Slayt içeriği
- **Veri ve gizlilik:** Kullanıcı verisi ile elle etiketli doğrulama verisi ayrı tutulur. .env, veritabanı, sanal ortam, node_modules ve özel anahtarlar depoya eklenmez. Local-first/hybrid çalışma tercih edilir.
- **Yanıt güvenliği:** Kişisel saldırı ve hakaret çıktıya sızmamalı; prompt/ara metin sızıntısı reddedilmeli; sayı, soru, kaynak ve görüş yönü korunmalı; yeni sonuç uydurulmamalı.
- **Arayüz erişilebilirliği:** Klavye ile kullanım, görünür focus, skip link, live region geri bildirimi, mobil drawer ve reduced-motion desteği düşünülür.
- **Kullanıcı kontrolü:** Yanıt otomatik paylaşılmaz. Kullanıcı öneriyi görür, değerlendirir ve göndermeye kendisi karar verir.

### Jüriye anlatım
Güvenli davranış yalnızca hakaret listesinden ibaret değil. Veri izolasyonu, model sınırı, prompt sızıntısı, kullanıcı onayı ve erişilebilir geri bildirim birlikte ele alınıyor.

## Slayt 34 — Sınırlılıklar ve dürüstlük beyanı
**Alt başlık:** Birinci olmak iddiası, eksikleri saklamakla değil, ölçülebilir sınırları doğru anlatmakla güçlenir.

### Slayt içeriği
- **Veri sınırı:** 80 örneklik proje içi doğrulama seti genel nüfusa veya tüm sosyal medya diline genellenemez. 6 hata açıkça gösterilir.
- **Kullanıcı etkisi:** Gerçek kullanıcı pilotu henüz yapılmadı. Bu nedenle yapıcı dilin kullanıcı davranışını kesin olarak iyileştirdiği iddia edilmiyor.
- **Model sınırı:** Canlı Qwen ağırlıkları mevcut test ortamında yeniden çalıştırılmadı. Güvenli yapısal yol, aday doğrulama ve fallback test edildi.
- **Dil sınırı:** Karmaşık, örtük, alaycı veya bağlama çok bağımlı cümlelerde hata olabilir; yeni veri ve kullanıcı pilotu gerekir.
- **Ürün sınırı:** N-KÖPRÜ hakem veya fact-checker değildir; insanın karar verme ve doğrulama sorumluluğunu ortadan kaldırmaz.

### Jüriye anlatım
Bu sınırlılıkları sunuma koymamızın nedeni projeyi zayıflatmak değil; ölçülmeyen şeyi ölçülmüş gibi anlatmamak.

## Slayt 35 — Etkiyi nasıl ölçeceğiz?
**Alt başlık:** Pilot yapılmadan kullanıcı etkisi sonucu söylemiyoruz; ölçüm tasarımını hazır tutuyoruz.

### Slayt içeriği
- **Tasarım:** Anonim, karşıt dengeli AB/BA faz sırası; katılımcı onamı; iki kullanım sırasının etkisini dengeleme.
- **Ölçümler:** Görevi tamamlama süresi · yanıt açıklığı · katılımcının güven değerlendirmesi.
- **Örneklem ve çıktı:** Minimum n=8 planı; verilerin CSV olarak dışa aktarılması; ham ve özet sonuçların ayrılması.
- **Mevcut durum:** Gerçek oturumlar henüz yapılmadı. Bu nedenle herhangi bir etki büyüklüğü, kullanıcı memnuniyeti veya davranış değişimi sonucu sunulmuyor.
- **Sonraki adım:** Pilot verisiyle hangi modülün hangi ölçümde değişim sağladığı ayrı incelenecek; teknik doğruluk ile kullanıcı etkisi aynı metrikte birleştirilmeyecek.

### Jüriye anlatım
Jürinin doğal sorusu “Kullanıcı gerçekten daha iyi konuştu mu?” olacaktır. Cevabımız: bunu henüz ölçmedik; ama onam, karşıt sıra, ölçüm ve dışa aktarma tasarımını hazırladık.

## Slayt 36 — Final demo akışı · 4 dakika 30 saniye
**Alt başlık:** Tek bir örnek tartışma üzerinden baştan sona ürün davranışı.

### Slayt içeriği
- **Demo öncesi:** Readiness 5/5; veri, şema, demo, 8 çıktı ve köprü soru kelime sınırı kontrol edilir.
- **Sunum disiplini:** Her sekmeye ayrı ayrı dağılmak yerine tek hikâye izlenir: problem → analiz → yanıt → köprü → kanıt.

### Tablo
| Süre | Gösterilecek bölüm | Jüriye verilecek mesaj |
| :--: | :--: | :--: |
| 0:00–0:30 | Problem + demo konusu | Uzun tartışmada yapı ve kanıt ihtiyacı kayboluyor. |
| 0:30–1:00 | Tartışmayı Anla | Yorumlar tekilleştiriliyor; genel yapı görünür oluyor. |
| 1:00–1:45 | Ortak Zemin + Görüş Haritası | Kabul, ayrışma ve koşullu görüşler ayrılıyor. |
| 1:45–2:25 | İddia Radarı + Cevapsız Sorular | %70 gibi iddialar doğrulanmış sayılmıyor; kaynak sorusu açılıyor. |
| 2:25–3:25 | Yanıt Koçu | Kötü mesajın saldırı kabuğu çıkıyor; sayı/soru/görüş korunuyor. |
| 3:25–4:05 | Köprü Oluştur | Ortak payda + kaygı + ilerleten soru üretiliyor. |
| 4:05–4:30 | Teknik doğrulama + sınır | %92,5 proje içi ölçüm; 808/808 test; kullanıcı etkisi henüz ölçülmedi. |

### Jüriye anlatım
4 dakika 30 saniyede bütün modüllerin düğmesine basmak yerine aynı tartışma üzerinden dönüşümü göstereceğiz. Jüri, giriş ile sonuç arasındaki farkı tek akışta görecek.

## Slayt 37 — Jürinin sorabileceği sorular · hazır yanıtlar
**Alt başlık:** Teknik ve etik sorulara kısa ama kanıta dayalı cevaplar.

### Slayt içeriği

### Tablo
| Soru | Yanıt |
| :--: | :--: |
| Bu bir fact-checker mı? | Hayır. İddia adayını ve kanıt ihtiyacını gösterir; doğruluk kararını otomatik vermez. |
| LLM olmadan çalışır mı? | Evet. Yapısal/yedek analiz çalışır; mDeBERTa ve Qwen isteğe bağlı katmanlardır. |
| %92,5 dış başarı mı? | Hayır. Dört konuda 80 proje içi elle etiketli örneğin doğrulamasıdır. |
| Yanıt Koçu anlamı değiştirir mi? | Sayı, soru, kaynak, koşul ve görüş yönü doğrulama kapılarıyla korunur; kötü aday reddedilir. |
| Model yoksa ne olur? | Güvenli hibrit veya bağlamsal fallback devreye girer; boş/saldırgan çıktı gösterilmez. |
| Kullanıcı etkisi kanıtlandı mı? | Henüz hayır. Anonim AB/BA pilot tasarımı hazır; gerçek oturum yapılmadı. |

### Jüriye anlatım
Sorulara sloganla değil, sistemin sınırı ve test kanıtıyla cevap vereceğiz.

## Slayt 38 — Ekip ve sorumluluk
**Alt başlık:** Mavi Fab.Lab. · TEKNOFEST 2026 Finalisti

### Slayt içeriği
- **Utku Kara:** Kaptan
- **Ozan Umut Kara:** PDR
- **Yusuf Furkan Çilingir:** Çocuk Gelişimi
- **Hurşit Kandemir:** Çocuk Gelişimi
- **Nimet Sude Çilingir:** Lise 2
- **Ekip çalışması:** Alan bilgisi, ürün tasarımı, yazılım, test, ölçüm, sunum ve demo hazırlığı birlikte yürütüldü.

### Jüriye anlatım
N-KÖPRÜ disiplinler arası bir ekip çalışması olarak geliştirildi. Teknik çözüm ile sosyal/insani kullanım sınırlarını birlikte düşünmeye çalıştık.

## Slayt 39 — Değerlendirmemizi istediğimiz çerçeve
**Alt başlık:** N-KÖPRÜ’yü üç ayrı kanıt katmanıyla değerlendirmenizi istiyoruz.

### Slayt içeriği
- **1 · Problem uyumu:** Tartışma akışında gerçekten kaybolan görüş, iddia, soru ve ortak zemin görünür hâle geliyor mu?
- **2 · Teknik güvenilirlik:** Hibrit mimari, kalıcı veri, Yanıt Koçu doğrulama kapıları, test seti ve sınırlılıklar denetlenebilir mi?
- **3 · Sorumlu etki:** Sistem kullanıcı adına karar vermeden, doğrulanmamış sonucu gerçek gibi sunmadan ve yapıcı bir sonraki adıma alan açıyor mu?
- **Son cümle:** Tartışmayı kazanmak değil; konuşmayı daha anlaşılır, daha kanıtlı ve daha yapıcı hâle getirmek.

### Jüriye anlatım
Kapanışta söylemek istediğimiz şey bu: N-KÖPRÜ, farklı düşünceleri ortadan kaldırmıyor. Farklı düşünceler arasında daha iyi bir konuşma zemini kuruyor.

## Slayt 40 — Ek · veri sözlüğü
**Alt başlık:** Analiz sonucunda hangi bilgiler taşınıyor?

### Slayt içeriği

### Tablo
| Nesne | Tutulan temel alanlar |
| :--: | :--: |
| Viewpoint | Sınıf, görünür ad, oran, özet, kanıt yorumları, temsilci yorum, temalar, karşıt görüş, ilişkili iddia/soru |
| StanceDetail | Yorum kimliği, sınıf, güven, kullanılan motor ve açıklama |
| ClaimItem | İddia metni, tür, öncelik, kaynak durumu, doğrulama ihtiyacı, güven, yorum kimliği |
| CommonGroundItem | Ortak tema, gerekçe, güven, destekleyen yorum kimlikleri |
| QuestionItem | Soru metni, tür, durum, öncelik, etkilenen görüşler, bağlı iddia ve cevap yorumları |
| Analysis snapshot | Tartışma kimliği, analiz JSON’u, değişiklikler ve zaman bilgisi |

### Jüriye anlatım
Bu ek, jüri teknik inceleme istediğinde “sistem neyi veri olarak taşıyor?” sorusuna cevap verir.

## Slayt 41 — Ek · kurulabilirlik ve tekrarlanabilirlik
**Alt başlık:** Çalışan prototipin temel kurulum akışı.

### Slayt içeriği
- **Gereksinim:** Python 3.11 veya 3.12 · Node.js 20+ · Git. Belirli GPU zorunlu değil.
- **Kaynak:** git clone https://github.com/yfurkan/N-KOPRU.git / cd N-KOPRU
- **Backend:** cd backend / py -3.12 -m venv .venv / .\\.venv\\Scripts\\Activate.ps1 / pip install -r requirements.txt / uvicorn app.main:app --reload --port 8000
- **Frontend:** İkinci terminalde: / cd frontend / npm install / npm run dev
- **Adresler:** Uygulama: http://localhost:3000 / Sağlık: http://127.0.0.1:8000/health / API dokümantasyonu: http://127.0.0.1:8000/docs

### Jüriye anlatım
Kurulum akışı rapor ve depo içinde tekrar edilebilir şekilde tutuluyor. AI paketleri isteğe bağlı; temel yedek analiz için zorunlu değiller.

## Slayt 42 — Ek · kanıt haritası ve teslim kaynakları
**Alt başlık:** Sunumdaki her teknik iddianın karşılığı proje dosyalarında bulunuyor.

### Slayt içeriği
- **Kaynak kod:** backend/app: analiz, görüş, iddia, soru, Yanıt Koçu, geçmiş, bildirim ve API katmanları. / frontend/app: kullanıcı akışı, sekiz analiz sekmesi ve teknik doğrulama ekranı.
- **Teknik kanıt:** docs/test-reports/V1_4_0_TEST_RAPORU.txt /  docs/test-reports/V1_4_0_TEST_SONUCLARI.json /  docs/test-reports/YANIT_KOCU_TEST_RAPORU.txt /  docs/test-reports/YANIT_KOCU_BENCHMARK.json
- **Teslim sürümü:** v1.4.0 · v1.4.0-teknofest-final sabit teslim dalı.
- **Sunum kaynağı:** Bu sunumun tam anlatım metni aynı dalda .md olarak tutulur; slayt metni bu metinden türetilmiştir.

### Jüriye anlatım
Sunumu teknik rapordan kopuk bir pazarlama metni olarak değil, kod ve test kanıtlarıyla eşleşen bir jüri dosyası olarak teslim ediyoruz.

## Slayt 43 — Teşekkürler
**Alt başlık:** Sorularınızı yanıtlamaya ve çalışan prototipi göstermeye hazırız.

### Slayt içeriği
- **N-KÖPRÜ:** Yapay Zekâ Destekli Sosyal Tartışma Zekâsı Sistemi
- **Mavi Fab.Lab.:** TEKNOFEST 2026 · N’Sosyal İnovasyon Yarışması Finalisti
- **Not:** Teknik rapor: 98/100 · v1.4.0 çalışan prototip · proje içi teknik doğrulama %92,5

### Jüriye anlatım
Teşekkür ederiz. Sorularınızı önce ürün davranışı, sonra teknik mimari, ölçüm ve sınırlar üzerinden yanıtlayabiliriz.

## Teknik doğruluk notu

- Rapor sürümü v1.4.0: 80 proje içi elle etiketli örnek, 74/80 doğru, %92,5 doğruluk ve Macro-F1, 808/808 otomatik test.
- Yanıt Koçu v0.4.4 test raporu: 29/29 regresyon, 552 senaryo kontrolü; benchmark 1.000 çağrıda ortalama 0,366 ms.
- Final hazırlığındaki genişletilmiş kontroller rapor sürümünden ayrı adlandırılır: 1.245/1.245 backend, 34/34 + 743 Yanıt Koçu kontrolü, API smoke 35/35, LAN 4/4, readiness 5/5, npm audit 0.
- Gerçek kullanıcı etki pilotu ve canlı Qwen ağırlıklarıyla yeniden inference bu metinde sonuç olarak iddia edilmez.