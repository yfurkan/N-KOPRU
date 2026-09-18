# N-KÖPRÜ v1.2.0 — Sürüm Notları

## Özet

v1.2.0, Cevapsız Sorular modülünü soru işareti tabanlı listeden yapısal-semantik bir soru ve yanıt durumu analizine dönüştürür. v1.1.2 bildirim dedup davranışı, v1.1.1 semantik İddia Radarı/Ortak Zemin/Köprü katmanı ve v1.0 SQLite kalıcılığı korunur.

## Yeni soru analizi

- Bilgi/açıklama, uygulama/karar ve kaynak/kanıt talebi sınıfları
- Soru işareti bulunmayan açık kaynak talepleri
- Retorik soruları bilgi talebinden ayırma
- Aynı anlamdaki soruları tek kartta gruplama
- `Cevapsız`, `Kısmen cevaplandı`, `Cevaplandı` durumları
- Sonraki yorumlara dayalı, muhafazakâr yanıt bağlantısı
- Yüksek/Orta/Düşük öncelik
- Etkilenen görüş kümeleri
- Dayanak, tekrar ve yanıt yorum numaraları
- Sorunun cevaplanmasının tartışmaya olası etkisini açıklayan alan
- Tespit güveninin anlamını açıkça belirten kullanıcı arayüzü

## Veri modeli ve geriye uyumluluk

`QuestionItem` modeli yeni alanlarla genişletildi. Alanların tamamı geriye uyumlu varsayılanlara sahiptir. Eski snapshot JSON'ları yeni kodda doğrulanıp açılabilir. Yeni alanlar mevcut `analysis_history.analysis_json` içinde saklandığından SQLite tablo şemasında yıkıcı değişiklik veya veri sıfırlama yapılmaz.

## Snapshot ve bildirim davranışı

- Soru durumunun cevapsızdan kısmi/yanıtlıya geçmesi snapshot değişim notuna eklenir.
- Yanıtlanmış veya retorik soru kaynak talebi bildirimi oluşturmaz.
- Semantik tekrar yeni soru bildirimi oluşturmaz.
- Soru bildirimi kimliği yorum numarasından bağımsız görünür soru metnine dayanır.
- v1.1.2'nin silinen bildirimi yeniden üretmeme ve aynı olay/içerik dedup davranışı korunur.

## Demo sonucu

Demo tartışmasında gerçek kaynak talepleri yorum #6 ve #13 olarak ayrılır. Öneri cümleleri #3, #9 ve #20 artık yanlışlıkla soru kartına dönüşmez. Mevcut %25 Kaynak farkındalığı ve en fazla 28 kelimelik Köprü sorusu korunur.

## Doğrulama

- 236/236 unittest metodu başarılı
- 33 yeni v1.2.0 soru testi
- 552 Yanıt Koçu senaryo kontrolü başarılı
- Gerçek iki Python süreciyle SQLite restart testi başarılı
- Eski snapshot model uyumluluğu başarılı
- Python compileall başarılı
- Bu çalışma ortamındaki ağ yetki sınırı nedeniyle tam npm kurulumu, `tsc --noEmit` ve Next.js production build tamamlanamadı; başarılı olduğu iddia edilmez.
