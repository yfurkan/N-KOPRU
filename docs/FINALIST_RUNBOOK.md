# N-KÖPRÜ v1.5.0 finalist çalışma kılavuzu

Bu kılavuz, GitHub main dalından alınan kaynakla uygulamayı açıp jüriye
tekrarlanabilir bir demo göstermek içindir.

## Sunumdan önce

1. Kaynağı temiz bir klasöre çıkarın.
2. Python 3.11 veya 3.12, Node.js 20 veya üzeri ve Git kurulu olsun.
3. README’deki backend ve frontend kurulumunu tamamlayın.
4. Backend’i bir terminalde, frontend’i ikinci terminalde çalıştırın.
5. Tarayıcıda http://localhost:3000 adresini açın.
6. Sunum Modu’na girip readiness kartlarında 5/5 ve HAZIR durumunu bekleyin.

Windows’ta sanal ortam oluşturulduktan sonra kökteki iki yardımcı dosya
kullanılabilir:

- N_KOPRU_BACKEND_BASLAT.bat
- N_KOPRU_FRONTEND_BASLAT.bat

## Jüri için önerilen akış

### 1. Ürünü ve sınırı söyleyin

N-KÖPRÜ uzun ve dağınık bir sosyal tartışmayı tek bir görüşe indirgemeden
özetler. Hangi görüşlerin bulunduğunu, hangi iddiaların kanıt istediğini,
hangi soruların cevapsız kaldığını ve tarafların ortak zemininin nerede
olduğunu aynı konu bağlamında gösterir.

Uygulama bu teslimde yerel çalışır. Dış sosyal medya hesabına bağlanmaz,
canlı yorum akışı çekmez ve gerçek kullanıcı etkisi sonucu üretmez.

### 2. Sunum Modu’nu gösterin

- 4:30 sayacı başlatıp durdurulabilir ve sıfırlanabilir.
- Beş adımlı anlatı akışı, konuşma sırasını takip etmek için vardır.
- Hazırlık kartları SQLite, sabit demo, analiz sözleşmesi ve Köprü sınırını
  kontrol eder.
- Demo verisini hazırla düğmesi aynı tartışma sonucunu özet, Görüş Haritası
  ve Köprü ekranlarına taşır.

### 3. Aynı analiz kaydını takip edin

Sabit demo açıldıktan sonra şu sırayı izleyin:

1. Tartışmayı Anla: yorumların kısa ve açıklanabilir özetini gösterin.
2. Görüş Haritası: destekleyen, karşı/sınırlayıcı, koşullu/dengeli ve soru
   kümelerinin nasıl ayrıldığını gösterin.
3. İddia Radarı: sayı veya neden-sonuç iddiasının neden kanıt istediğini
   gösterin.
4. Cevapsız Sorular: bilgi boşluğunun hangi görüşleri etkileyebileceğini
   açıklayın.
5. Yanıt Koçu: hakaret kabuğunu temizleyip kaynak, soru, sayı ve ana görüşü
   koruyan yapıcı öneriyi gösterin.
6. Ben Yokken Ne Değişti?: önceki anlık görüntü ile yeni yorum arasındaki
   anlamlı farkı gösterin.
7. Köprü Oluştur: ortak kabul, ana ayrışma ve eksik bilgiyi konuya bağlı
   sonraki soruya bağlayın.

### 4. Kontrollü Senaryo ekranını gösterin

Bu ekran bir kullanıcı testi değildir. İki sabit konuda ham yorum akışı ile
N-KÖPRÜ görünümünü karşılaştırır. Görevlerin ve puanların amacı yalnızca
akışın çalıştığını göstermektir. Ekrandaki "Gerçek sonuç üretilmiyor"
ifadesini kapatmayın veya başka bir başarı iddiasıyla değiştirmeyin.

Ayrıntılı sınır ve kod karşılıkları CONTROLLED_DEMO_PROTOCOL.md dosyasındadır.

## Teknik inceleme sırası

Değerlendirici veya ekip üyesi kodu şu sırayla okuyabilir:

1. VERSION.txt ve backend/app/version.py: v1.5.0.
2. backend/app/main.py: API sözleşmesi, health ve CORS.
3. backend/app/analyzer.py: analiz orkestrasyonu.
4. backend/app/viewpoint_engine.py, argument_engine.py ve question_engine.py:
   görüş, iddia ve soru üretimi.
5. backend/app/coach_engine.py: Yanıt Koçu sinyalleri, güvenlik ve aday
   doğrulama kapısı.
6. backend/app/readiness.py: sunum öncesi zorunlu kontroller.
7. frontend/app/page.tsx: sekmeler, Sunum Modu ve Kontrollü Senaryo.
8. backend/tests ve scripts/api_smoke.py: yeniden üretilebilir kontroller.

## Sorun giderme

- Backend bağlantısı yoksa backend terminalinde hata olup olmadığını ve
  http://127.0.0.1:8000/health adresini kontrol edin.
- Readiness başarısızsa API yanıtındaki failed kontrolün açıklamasını okuyun;
  demo verisini yeniden hazırlayın.
- AI modeli kurulu değilse bu beklenen bir durumdur. Yapısal yedek motor
  sunumu engellemez ve arayüz modelin isteğe bağlı olduğunu gösterir.
- Port 8000 veya 3000 doluysa çalışan süreci kapatın ya da ilgili ayarı
  README’deki yerel yapılandırma dosyasıyla değiştirin.
- Frontend bağımlılıklarında sorun olursa package-lock.json ile npm ci
  çalıştırın; node_modules klasörünü Git’e eklemeyin.
