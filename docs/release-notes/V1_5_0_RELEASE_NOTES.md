# N-KÖPRÜ v1.5.0 — finalist kaynak teslim notları

v1.5.0, yarışma finalinde açılıp incelenmek üzere hazırlanmış yerel kaynak
teslimidir. Hedef Git dalı main’dir. Uygulama v1.4.0 teknik raporundan
ayrı olarak sürümünü VERSION.txt ve backend/app/version.py üzerinden 1.5.0
olarak bildirir.

## Ürün akışı

- Sunum Modu’nda 4:30 kullanıcı kontrollü sayaç, beş anlatı adımı, readiness
  kartları ve aynı demo analizine bağlanan kanıt düğmeleri bulunur.
- Sekiz analiz modülü aynı tartışma konusu üzerinden tutarlı çıktı verir:
  Tartışmayı Anla, Ortak Zemin, Görüş Haritası, İddia Radarı, Cevapsız
  Sorular, Yanıt Koçu, Ben Yokken Ne Değişti? ve Köprü Oluştur.
- Kontrollü Senaryo ekranı iki sabit yerel örnekte ham yorumlar ile N-KÖPRÜ
  çıktısını karşılaştırır. Gerçek kullanıcı ve etki metriği yolu kapalıdır.
- Yanıt Koçu; saldırı kabuğunu temizlerken sayı, soru, kaynak talebi, ironi,
  koşullu görüş ve ana anlamı korumaya odaklanır. Kişisel küçümseme, gizlenmiş
  küfür, birleşik cinsel/ailevi argo, dehümanize edici hitaplar, kovma,
  tehdit ve kırıcı suçlama kalıpları; noktalı, boşluklu, leet, ASCII, harf
  uzatmalı ve bitişik yazım varyantlarıyla birlikte güvenli yoldan ayrılır.
  Saldırı sinyalinde Qwen/Hugging Face yolu çağrılmaz; deterministik güvenli
  katman kullanılır. Cevap şablonları aynı saldırı ailesinde tek metne
  kilitlenmez ve nesnel bağlamlar yanlışlıkla saldırı sayılmaz.
- Mobil menü, analiz çekmecesi, skip-link, canlı durum alanı, klavye ile sekme
  gezinmesi ve reduced-motion desteği korunur.

## Teknik çalışma

- FastAPI + Pydantic + Uvicorn backend.
- Next.js 15.5.25 + React 19 + TypeScript frontend.
- SQLite kalıcılığı; kullanıcıya ait dosyalar ve cache kaynak teslimine girmez.
- Modelsiz çalışma zorunlu demo yoludur; mDeBERTa-XNLI ve Qwen isteğe bağlı
  yerel katmanlardır.
- CORS varsayılan olarak localhost ve private LAN frontend origin’leriyle
  sınırlıdır.

## Push öncesi yerel doğrulama

- Backend: 54 test paketi, 1.252 / 1.252.
- Python compileall: başarılı.
- Frontend production build: başarılı.
- TypeScript: başarılı.
- Production npm audit: 0 açık.
- scripts/api_smoke.py: 35 / 35.
- /api/system/readiness: 5 zorunlu kontrolün 5’i hazır.

Bu belge GitHub Actions’ın sonucunu temsil etmez. Actions, kaynak main dalına
push edildikten sonra .github/workflows/quality.yml tarafından yeniden
çalıştırılır.

## Bilinçli kapsam

Bu sürüm canlı sosyal ağ entegrasyonu, gerçek kullanıcı araştırması, saha
ölçümü veya bağımsız akademik benchmark sunmaz. Jüri demosu sabit verilerle
yerel ve tekrarlanabilir çalışır. Kurulum ve GitHub yükleme adımları README.md
ile docs/GITHUB_MAIN_TESLIM_REHBERI.md içindedir.
