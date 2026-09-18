# N-KÖPRÜ v1.1.0 Release Notes

## Analiz çekirdeği

- Yeni `backend/app/argument_engine.py` eklendi.
- İddia Radarı: hibrit doğrulanabilirlik profili, iddia tipi, öncelik, güven ve kanıt ihtiyacı.
- Ortak Zemin: görüş kümeleri arası çapraz-tema analizi ve yorum-dayanak izi.
- Köprü Oluştur: ortak zemin + ayrışma + eksik kanıt + kaynak sorusu birleşiminden yeni Köprü sentezi.
- Mevcut mDeBERTa-XNLI pipeline'ı, yalnızca zaten yüklüyse belirsiz iddia adaylarında tekrar kullanılır; başarısız model yüklemesi ikinci kez tetiklenmez.

## Veri modeli

`ClaimItem` genişletildi:

- `claim_type`
- `verification_need`
- `priority`
- `confidence`
- `engine`
- `detection_reason`

Yeni `CommonGroundItem`:

- `theme`
- `text`
- `support_count`
- `stance_count`
- `evidence_comment_ids`
- `confidence`
- `engine`

`AnalysisResult` içine `common_ground_details` eklendi. Eski JSON kayıtları varsayılan alanlar sayesinde geriye uyumludur.

Köprü sözlüğüne eklenen alanlar:

- `evidence_comment_ids`
- `confidence`
- `engine`

## Arayüz

- İddia Radarı kartları artık tür, öncelik, kanıt ihtiyacı ve güven gösterir.
- Ortak Zemin kartları dayanak görüş/yorum sayılarını ve yorum numaralarını gösterir.
- Köprü Oluştur panelinde kanıta dayalı sentez üst bilgisi, güven ve dayanak yorumlar gösterilir.
- Eski “İddia Radarı heuristik” geliştirici uyarısı kaldırıldı ve güncel analiz mimarisi açıklaması eklendi.

## Sürüm / kalıcılık

- API sürümü: `1.1.0`
- Frontend package sürümü: `1.1.0`
- SQLite şeması için migration gerekmiyor; analiz geçmişi JSON olarak saklandığı ve yeni alanların varsayılanları olduğu için mevcut v1.0 DB kullanılabilir.

## Test

- 192/192 unittest metodu başarılı.
- Yanıt Koçu: 552 ek senaryo kontrolü başarılı.
- Python compileall başarılı.
- TS/TSX syntax-transpile başarılı.
