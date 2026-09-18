# N-KÖPRÜ v1.1.2 — Anlamlı Bildirim / Dedup Düzeltmesi

## Amaç

v1.1.2, SQLite kalıcılığı sonrasında aynı tartışmanın yeniden analiz edilmesiyle Bildirimler merkezinin gereksiz biçimde büyümesini engeller. Snapshot geçmişi her analiz çalıştırmasında kaydedilmeye devam eder; **bildirim ise yalnızca kullanıcı açısından yeni ve anlamlı bir olay varsa üretilir.**

## Yeni bildirim mantığı

- Aynı tartışma yeniden analiz edilir ve snapshot karşılaştırması **“ölçülebilir değişiklik yok”** sonucunu verirse **0 yeni bildirim** oluşur.
- İlk analiz, mevcut davranışı koruyarak analiz/görüş/iddia/kaynak/Köprü için başlangıç bildirimlerini oluşturabilir.
- Sonraki analizlerde yalnızca gerçekten yeni olay türü bildirim üretir:
  - yeni görüş kümesi veya en az 5 puanlık anlamlı görüş oranı değişimi,
  - yeni doğrulanabilir iddia,
  - yeni cevapsız soru / kaynak talebi,
  - ortak zeminin değişmesi,
  - Köprü sorusunun değişmesi.
- Genel “analiz hazır” bildirimi sonraki aynı tartışma analizlerinde tekrar üretilmez.

## İçerik tabanlı olay kimliği

Önceki sürümlerde bildirim tekilleştirme görünür başlığa dayanıyordu. v1.1.2 ile yeni olaylar için imza, UI başlığından bağımsız **semantik olay içeriğinden SHA-256 tabanlı sabit bir kimlikle** üretilir.

Böylece:

- metin başlığı sürüm içinde değişse bile aynı olay tekrar doğmaz,
- aynı iddia/soru/Köprü içeriği ikinci kez bildirim oluşturmaz,
- kullanıcı bir bildirimi silmişse aynı olay yeniden analiz edildiğinde geri gelmez,
- gerçekten farklı yeni içerik ayrı bir bildirim olabilir.

## Eski mükerrer bildirimler için tek seferlik temizlik

v1.1.2 ilk açılışında yalnızca otomatik analiz bildirimleri için bir kez çalışan geriye uyumluluk temizliği uygulanır. Aynı `kind + post + analiz adımı` ailesinde önceki sürümlerden kalmış birden çok aktif kopya varsa **en yeni kayıt tutulur, eski aktif kopyalar soft-delete edilir.**

- Kullanıcının önceden sildiği kayıtlar yeniden açılmaz.
- Eşdeğer kopyalardan herhangi biri daha önce okunmuşsa tutulan kayıt da **okunmuş** kalır; temizlik eski bir olayı tekrar “yeni” yapmaz.
- Bu migration yalnızca bir kez çalışır. v1.1.2 sonrasında farklı ve gerçek yeni olaylar aynı ailede ayrı bildirim olarak saklanabilir.

Bu nedenle eski veritabanında örneğin `13` okunmamış/aktif otomatik bildirim görünüyorsa ilk backend açılışından sonra sayı düşebilir. Bu, kayıt kaybı değil; önceki sürümlerden kalmış eşdeğer otomatik bildirimlerin birleştirilmesidir.

## Arayüz

Bildirim merkezi açıklaması yeni davranışla uyumlu hâle getirildi:

- değişiklik olmadan tekrar analiz etmenin yeni bildirim üretmediği açıkça belirtilir,
- yalnızca yeni görüş, iddia, soru, ortak zemin veya Köprü değişikliklerinin bildirim oluşturacağı anlatılır.

Okundu/okunmadı, tek silme, Okunanları temizle ve Geri Al davranışları aynen korunur.

## Geriye uyumluluk

- SQLite şeması değiştirilmedi.
- `backend/data/nkopru.db` kaynak ZIP'e dahil edilmez.
- Profil, analiz geçmişi, snapshot'lar, mesajlar, Yer İmleri ve Listeler korunur.
- v1.0 / v1.1.x geçmiş snapshot'ları açılmaya devam eder.

## Test

- 15 test betiği
- **203/203 unittest metodu başarılı**
- Bildirim regresyonu: **22/22**
- Bildirim UI sözleşmesi: **11/11**
- Yanıt Koçu: **29/29 + 552 senaryo kontrolü**
- Semantik analiz: **20/20 regresyon + 10/10 UI sözleşmesi**
- Python `compileall`: başarılı
- `page.tsx`, `layout.tsx`, `api.ts`, `types.ts`: TypeScript syntax-transpile başarılı
- Tam `tsc --noEmit`, kaynak pakette `node_modules` bulunmadığı için çalıştırılmadı; tam tip kontrolünün geçtiği iddia edilmez.
