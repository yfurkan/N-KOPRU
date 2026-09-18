# N-KÖPRÜ dokümantasyonu

Bu klasör, GitHub main dalına gönderilecek N-KÖPRÜ v1.5.0 finalist
kaynağının çalıştırma, inceleme ve doğrulama belgelerini içerir.

## Güncel belgeler

- FINALIST_RUNBOOK.md: uygulamayı çalıştırma ve jüri demosu akışı.
- CONTROLLED_DEMO_PROTOCOL.md: gerçek kullanıcı verisi toplamayan sabit demo
  sınırı.
- GITHUB_MAIN_TESLIM_REHBERI.md: boş GitHub deposu oluşturma, main commit’i,
  push ve temiz kopya kontrolü.
- CONFIGURATION.md: yerel ortam değişkenleri ve isteğe bağlı modeller.
- PRIVACY_AND_AI_TRANSPARENCY.md: veri saklama ve yapay zekâ sınırları.
- architecture/technical-architecture-v1.5.0.svg: güncel teknik mimari.
- test-reports/V1_5_0_TEST_RAPORU.txt: bu kaynak paketinin push öncesi yerel
  doğrulama özeti.

## Klasörler

- architecture/: güncel mimari çizim ve arşivlenmiş eski çizimler.
- archive/: v1.0–v1.4 sürümlerine ait tarihsel rapor ve sürüm notları.
- release-notes/: sürüm bazlı değişiklik notları.
- archive/screenshots-v1.4.0/: önceki sürümün tarihsel ekran görüntüleri.
- test-reports/: otomatik test sonuçları ve tarihsel raporlar.

## Tarihsel kayıtların okunması

docs/archive altındaki V1_4_0, V1_4_1, V1_4_2 ve önceki sürüm dosyaları
önceki teknik rapor ve geliştirme kanıtlarıdır. Güncel çalışan kaynak
v1.5.0’dır; arşiv dosyalarındaki sürüm, dal veya test akışı bu teslimin
çalıştırma talimatı olarak kullanılmamalıdır.

## Doğrulama özeti

- Backend: 54 test paketi, 1.246 / 1.246 başarılı.
- Frontend: production build ve TypeScript kontrolü başarılı.
- Production bağımlılık denetimi: 0 açık.
- API kabul kontrolü: scripts/api_smoke.py ile 35 / 35.
- Sistem readiness: 5 zorunlu kontrolün 5’i hazır.

Bu sonuçlar proje içi yazılım doğrulamasıdır. Gerçek kullanıcı araştırması,
canlı sosyal platform bağlantısı, saha etkisi veya bağımsız akademik benchmark
sonucu değildir.
