# N-KÖPRÜ kullanıcı etki pilotu protokolü

## Amaç

Pilot, N-KÖPRÜ analiz katmanının iki kontrollü görevde ham yorum okuma
akışına göre gözlenen süre, doğru karar, anlaşılırlık ve güven farklarını
betimlemek için tasarlanmıştır. Nedensel etki, akademik genelleme veya dış
benchmark iddiası üretmez.

## Tasarım

- Protokol: `1.0-2026-09-05`.
- Önerilen örneklem: **8–12 gerçek katılımcı**.
- Atama: oturum sırasına göre dönüşümlü **AB/BA**.
- Görevler: kampüste gece ulaşımı ve mahalle parkı saatleri.
- Her katılımcı bir görevde ham yorumları, diğer görevde N-KÖPRÜ analiz
  özetini ve görüş haritasını görür.
- Katılımcı görevi bitirmeden diğer fazın doğru cevabı gösterilmez.
- Sunucu süreyi, cevabı ve puanları doğrular; fazlar sıralı ve tekilleştirilmiş
  biçimde kaydedilir.

## Toplanan alanlar

Her tamamlanan faz için yalnız şu alanlar saklanır: anonim oturum kodu, AB/BA
ataması, senaryo, varyant, cevap doğruluğu, süre, anlaşılırlık (1–5), güven
(1–5) ve zaman damgası. İsim, e-posta, telefon, demografi ve serbest metin
toplanmaz.

## Dahil etme ve raporlama

- Deneme oturumları protokolü sınamak içindir ve sonuçlara katılmaz.
- Yarım kalan gerçek oturumlar sonuçlara katılmaz.
- Minimum 8 tamamlanmış gerçek çift görev olmadan ekranda sonuç çıkarılmaz.
- Minimum tamamlandığında medyan süre, doğruluk, anlaşılırlık ve güven
  farkları gösterilir; sonuç “betimsel proje içi gözlem” olarak etiketlenir.
- CSV dışa aktarımı yalnız tamamlanmış gerçek çift görevleri içerir.

## Katılımcı bilgilendirmesi

Katılımcıya görevin amacı, yaklaşık süre, toplanan sınırlı alanlar, anonim
oturum kodu ve istediği anda devam etmeme hakkı açıklanır. Onay verilmezse
oturum başlatılmaz.
