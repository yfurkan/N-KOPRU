# Finalist çalışma ve sunum kılavuzu

Bu kılavuz `finalist-v1.5.0` dalındaki uygulama içindir. Sabit yarışma
teslimi `v1.4.0-teknofest-final` değişmez.

## Sunumdan önce

1. Backend ve frontend'i başlatın.
2. `http://localhost:8000/health` adresinde sürümün `1.5.0` olduğunu kontrol
   edin.
3. Uygulamada **Sunum Modu → Hazırlığı Yenile** düğmesine basın.
4. Zorunlu hazırlık kartlarında `Hazır` durumunu ve 5/5 zorunlu kontrolü
   görün.
5. **Canlı Özeti Aç** ile sabit demo tartışmasını açın; gerekiyorsa AI
   modelini ayrıca hazırlayın. Model yüklenmezse yapısal yedek motor sunumu
   engellemez.

## Önerilen 4:30 akış

| Süre | Ekran | Vurgu |
|---:|---|---|
| 0:00–0:35 | Problem ve amaç | Uzun tartışmayı karar haritasına dönüştürme |
| 0:35–1:35 | Tartışmayı Anla | 20 benzersiz yorum, ayrışma ve kaynak farkındalığı |
| 1:35–2:35 | Görüş Haritası | Görüş kümeleri ve temsilci yorumlar |
| 2:35–3:25 | İddia/Soru | Hangi kanıtın eksik olduğu |
| 3:25–4:30 | Köprü ve etki | Ortak ölçüt, kısa köprü sorusu ve pilot tasarımı |

Sayaç yalnızca prova yardımcısıdır; sunum metnini otomatik ilerletmez.

## Ana kabul testi

Kullanıcının yapacağı tek test bu akıştır:

- **Sunum Modu:** hazırlık `Hazır`, sayaç başlat/durdur/sıfırla çalışıyor.
- **Canlı demo:** Tartışmayı Anla, Görüş Haritası ve Köprü bağlantıları aynı
  tartışmayı açıyor.
- **Teknik Doğrulama:** mevcut referans ve ayrılmış yeni kontrol düğmeleri
  sonuçları birbirine karıştırmıyor.
- **Etki Pilotu:** deneme oturumu başlıyor, iki görev tamamlanıyor ve sonuç
  ekranında deneme verisinin gerçek metriklere katılmadığı görülüyor.
- **Mobil görünüm:** menü ve analiz paneli açılıp kapanıyor; Escape ve klavye
  oklarıyla sekmeler arasında geçiş yapılabiliyor.

## Pilot veri toplama

Gerçek oturum için `Etki Pilotu` ekranında “Gerçek Pilot Oturumu” seçilir.
Katılımcıdan yalnız bilgilendirilmiş onay ve iki görev için cevap, süre,
anlaşılırlık ve güven puanı alınır. İsim, e-posta, demografi veya serbest metin
istenmez. En az 8 tamamlanmış gerçek çift görev olmadan sonuç cümlesi
üretilmez; 8 sonrasında çıktı yalnız betimsel proje içi gözlemdir.

## Sorun giderme

- Backend bağlantısı yoksa frontend hata mesajını gösterir; backend terminali
  ve `/health` kontrol edilir.
- Model indirme jüri öncesi tamamlanamazsa AI düğmesi zorunlu değildir; Sunum
  Modu yapısal yedek ile devam eder.
- Veritabanı taşınacaksa `N_KOPRU_DB_PATH` açık bir dosya yoluna ayarlanır;
  mevcut SQLite dosyası silinmez.
