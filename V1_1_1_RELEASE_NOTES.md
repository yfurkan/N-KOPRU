# N-KÖPRÜ v1.1.1 — Release Notes

## Amaç

v1.1.1, v1.1.0 semantik analiz sürümünde gerçek kullanım ekranında görülen iki kalite sorununu kapatır: **Kaynak farkındalığı metriğinin kaynak taleplerini yok sayması** ve **Köprü sorusunun gereğinden uzun olması**.

## Düzeltme 1 — Kaynak farkındalığı

- Eski hesap: yalnızca İddia Radarı adaylarında doğrudan kaynak işareti bulunan iddiaların oranı.
- Yeni hesap: benzersiz yorumların içinde kaynak/araştırma/veri/kanıt/istatistik/ölçüm ihtiyacını açıkça gündeme getiren yorumların oranı.
- Kaynak sunan yorumlar ve açık kaynak/veri talepleri birlikte farkındalık sinyali kabul edilir.
- Motor meta verisine `source_awareness_engine`, `source_awareness_comment_count`, `source_provided_count` ve `evidence_request_count` eklendi.
- Demo veri setinde beklenen değer: **%25 (5/20 yorum)** ve **2 açık kaynak/veri talebi**.
- Arayüze metriğin tanımı eklendi; yüzde artık “kaynağın doğruluğu” gibi yanlış yorumlanmıyor.

## Düzeltme 2 — Kısa Köprü sorusu

- Köprü sorusu tartışma başlığını tekrar etmiyor.
- Ortak zemin + ana ayrışma + kanıt ihtiyacı korunuyor.
- Kontrollü üst sınır: **28 kelime**.
- Dinamik soru bu sınırı aşarsa yarım cümle kesmek yerine kısa ve tam bir yedek soru kullanılıyor.
- Motor meta verisine `bridge_question_word_count` ve `bridge_question_max_words` eklendi.
- Demo sorusu 21 kelime.

## Geriye uyumluluk

- SQLite şeması değiştirilmedi.
- Mevcut `backend/data/nkopru.db` kaynak pakete dahil edilmez.
- Profil, bildirim, mesaj, yer imi, liste ve analiz geçmişi korunur.
- v1.0/v1.1.0 snapshot'ları model varsayılanlarıyla açılmaya devam eder.

## Test

- 15 regresyon/UI test betiği
- **198/198 unittest metodu başarılı**
- Yanıt Koçu: **552 senaryo kontrolü başarılı**
- Python `compileall`: başarılı
- `page.tsx`, `layout.tsx`, `api.ts`, `types.ts`: TypeScript syntax-transpile başarılı
- Tam `tsc --noEmit` bu kaynak pakette `node_modules` bulunmadığı için çalıştırılmadı; tam tip kontrolü geçtiği iddia edilmez.
