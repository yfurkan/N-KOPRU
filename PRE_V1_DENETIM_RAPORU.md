# N-KÖPRÜ — v1.0 Öncesi Kaynak Kod Denetimi

Denetlenen taban: `NKOPRU_v1_PRECHECK_SOURCE.zip`  
Stabilizasyon sürümü: **v0.9.2**

## Sonuç

Mevcut kaynak kod; Ana Sayfa/analiz akışı, Keşfet, Bildirimler, Mesajlar, Yer İmleri, Listeler ve Yanıt Koçu açısından birbirine bağlı çalışan bir yerel prototip tabanıdır. v0.9.2 ile bildirim yönetimi tamamlandı ve kaynak kodda birkaç durum/senkronizasyon problemi giderildi.

Bu sürüm **v1.0 için temiz tabandır**, ancak aşağıdaki maddeler v1.0'da tamamlanmadan “ürün tamamlandı” denmemelidir.

## v0.9.2'de düzeltilenler

### Bildirimler
- `Tümü / Okunmamış / Okunanlar` filtreleri.
- Tek bildirim için `Okundu yap / Okunmadı yap / Bildirimi sil` menüsü.
- Sağ ayrıntı panelinden okundu durumu değiştirme ve silme.
- `Okunanları temizle` toplu işlemi.
- Tekil ve toplu silme sonrasında 5 saniyelik **Geri Al** akışı.
- Sol menü rozeti yalnızca okunmamış bildirim sayısını kullanır.
- Toplam / okunmamış / okunan sayaçları backend'den birlikte okunur.
- Bildirim hedefi zaten açık tartışmaya aitse tekrar AI analizi çalıştırılmaz.
- Farklı tartışmaya geçişte gönderi ve analiz paralel yüklenir.
- Tüm bildirimler silindiğinde başlangıç bildirimlerinin kendiliğinden yeniden oluşması engellendi.
- Kullanıcının sildiği aynı analiz olayı, aynı analiz tekrar çalıştırıldığında anında yeniden üretilmez.

### Genel stabilizasyon
- Listelerde bütün listeler kullanıcı tarafından silinirse varsayılan listelerin istemeden yeniden oluşması engellendi.
- Yer İmleri kimlik sayacı test sıfırlamasında doğru şekilde sıfırlanır.
- Yer İmleri ve Listeler oturum depolarına eşzamanlı erişim için kilit eklendi.
- Özel tartışma kimliği üretimi eşzamanlı isteklere karşı kilitlendi.
- Keşfet `Hızlı Analiz` akışında gönderi ve analiz paralel yüklenir.
- Eski sürüm numarası taşıyan bazı kullanıcı metinleri güncellendi ve teknik açıklamalar daha doğru hâle getirildi.
- Bildirim/Yer İmleri/Listeler zaman etiketleri gerçek `created_at` değerinden dinamik hesaplanır.
- Kullanıcı arayüzündeki geliştirici/sürüm rozetleri (ör. “GERÇEK MODÜL”, v0.x etiketleri) temizlenerek ürün dili sadeleştirildi; sürüm bilgisi kaynak ve sağlık uçlarında tutuldu.
- Profil placeholder kartlarındaki sahte sayısal metrikler kaldırıldı; gerçek profil istatistikleri v1.0 iş listesinde bırakıldı.

## Modül denetimi

### 1. Ana Sayfa / Tartışma Analizi — Çalışıyor
- Gönderi ve yorum akışı.
- Yeni tartışma girişi.
- 8 adımlı analiz paneli.
- Aynı tartışmanın ilgili analiz adımına geri dönüş bağlantıları.

### 2. Görüş Haritası — Çalışıyor, AI destekli
- mDeBERTa-XNLI + yüksek kesinlikli yapısal Türkçe sinyaller.
- Transformer'a gitmeyen yorumlar ayrı gösterilebiliyor.
- Model güveni sadece gerçek model çıkarımı varsa gösteriliyor.

### 3. Yanıt Koçu — Çalışıyor ve kapsamlı regresyon testi var
- Hakaret/kişiselleştirme temizleme.
- Anlam, sayı, soru, kaynak talebi ve dengeli görüş koruma.
- İroni/sarkazm kontrolü.
- Güvensiz üretken AI çıktısını reddeden koruma katmanı.

### 4. Keşfet — Çalışıyor, veri kaynağı yerel katalog
- Arama, kategori filtresi, önizleme, tartışmayı açma ve hızlı analiz.
- **Eksik:** gerçek N'Sosyal/canlı ağ veri bağlantısı yok; katalog kontrollü demo verisidir.

### 5. Bildirimler — v0.9.2 ile tamamlandı
- Analiz olaylarından bildirim üretme, filtreleme, okuma, silme, toplu temizleme, geri alma ve doğru analiz adımına dönüş.
- **Eksik:** kalıcı kullanıcı veritabanı olmadığı için backend kapanınca bildirim geçmişi sıfırlanır.

### 6. Mesajlar — Çalışıyor, yerel oturum sistemi
- Mesaj gönderme.
- Köprü kartını konuşmaya aktarma.
- Köprü kartından ilgili analize dönme.
- **Eksik:** gerçek kullanıcı/kişi dizini, kimlik doğrulama ve kalıcı mesaj veritabanı yok.

### 7. Yer İmleri — Çalışıyor, yerel oturum sistemi
- Tartışma, iddia ve Köprü kaydı.
- Filtreleme, kaldırma, ilgili analize dönüş.
- **Eksik:** kalıcı kullanıcı veritabanı yok.

### 8. Listeler — Çalışıyor, yerel oturum sistemi
- Liste oluşturma/silme.
- Tartışma, birden fazla iddia ve Köprü ekleme.
- Tekrarlı öğe koruması, sayaçlar, filtreler ve ilgili analize dönüş.
- **Eksik:** kalıcı kullanıcı veritabanı yok.

### 9. Profil — Henüz gerçek modül değil
- Sol menüde görünür fakat mevcut kaynakta statik/gösterim amaçlı kartlar kullanır.
- **v1.0'ın ana işi:** profil API'si, gerçek aktivite geçmişi ve diğer modüllerden türetilen sayaçlar.

## v1.0'a kalması gereken kritik işler

1. **Kalıcı veri katmanı**: SQLite başlangıç için yeterli; bildirim, mesaj, yer imi, liste, analiz geçmişi ve profil restart sonrasında korunmalı.
2. **Profil**: gerçek kullanıcı özeti, analiz geçmişi, Köprü sayısı, kayıtlar ve listeler backend verisinden gelmeli.
3. **Ben Yokken Ne Değişti?**: mevcut kod gerçek geçmiş anlık görüntü karşılaştırması yapmıyor; yalnızca ilk analiz bilgisi sunuyor. Snapshot/diff altyapısı kurulmalı.
4. **İddia Radarı**: şu anda yapısal/heuristik iddia tespiti kullanıyor. v1.0'da AI/NER veya Türkçe claim modeli ve güven puanı eklenmeli.
5. **Ortak Zemin + Köprü Oluştur**: çalışıyor ancak önemli bölümü kurallı/şablonlu çıkarım. v1.0'da kontrollü üretken AI + anlam doğrulama katmanına geçirilmesi projeyi rapordaki hedefe daha çok yaklaştırır.
6. **Canlı veri entegrasyonu**: Keşfet kontrollü yerel veri kullanıyor. Yarışma demosunda bu açıkça “demo veri” olarak kalmalı; gerçek platform entegrasyonu varsa ayrı adaptör katmanı eklenmeli.
7. **Kimlik doğrulama / çok kullanıcılı yapı**: mevcut çalışma tek yerel kullanıcı varsayar.

## Test sonucu

- Python/FastAPI regresyon + UI sözleşme testleri: **147/147 başarılı**.
- Yanıt Koçu test setinin içinde ayrıca **552 senaryo kontrolü** bulunuyor.
- `page.tsx`, `layout.tsx`, `api.ts`, `types.ts` TypeScript transpile/sözdizimi kontrolü: **0 hata**.
- Python kaynakları `py_compile` kontrolünden geçti.

> Not: Bu denetim ortamında gerçek Hugging Face model ağırlıklarıyla uzun CPU inference tekrar çalıştırılmadı. Gerçek model davranışı kullanıcının kurulu bilgisayarında ayrıca smoke-test edilmelidir; mevcut regresyonlar model etrafındaki iş mantığı ve güvenlik katmanlarını doğrular.
