# N-KÖPRÜ v1.5.0 — Finalist Sunum ve Etki Hazırlığı

v1.5.0, v1.4.2 analiz çekirdeğini koruyarak final jüri sunumunu, ürün
hazırlığını ve kullanıcı etkisi kanıtını tek bir çalıştırılabilir akışta
toplar. Sabit `v1.4.0-teknofest-final` etiketi ve `main` teslim geçmişi
korunur; bu sürüm `finalist-v1.5.0` geliştirme dalındadır.

## Ürün tarafı

- **Sunum Modu:** 4:30 kontrollü sayaç, beş adımlı jüri hikâyesi, canlı
  özet/görüş/köprü/teknik doğrulama bağlantıları ve sunum öncesi sistem
  hazırlık kartı.
- **Etki Pilotu:** en az 8 tamamlanmış gerçek katılımcı hedefleyen, anonim ve
  karşı dengelenmiş AB/BA protokolü. Ham yorum okuma ile N-KÖPRÜ analizini
  gece ulaşımı ve park saatleri görevlerinde karşılaştırır.
- Pilot; süre, doğruluk, anlaşılırlık ve güven ölçümlerini toplar. Deneme
  oturumları ve yarım kalan gerçek oturumlar sonuçlara katılmaz. Sonuçlar
  minimum örneklem tamamlanana kadar otomatik olarak “sonuç çıkarılmadı”
  olarak gösterilir.
- **Konu bağlamı:** ortak zemin, Görüş Haritası ve Köprü aynı tartışma
  ölçütlerini kullanır; uzaktan çalışma için verimlilik, ekip koordinasyonu
  ve çalışan esnekliği gibi ölçütler görünürdür.
- **Mobil ve erişilebilir arayüz:** mobil menü/analiz çekmecesi, atlama
  bağlantısı, canlı bölge, görünür klavye odağı, sekme semantiği, ok tuşları,
  Home/End gezinmesi, azaltılmış hareket desteği ve varsayılan gizlilik modu.
- Başlangıç demo yükleme hatası, analiz bağlantısı ve pilot hata durumları
  kullanıcıya sessizce kaybolmak yerine açıklanır.

## Teknik kalite ve güvenlik

- `backend/app/readiness.py` ile SQLite bütünlüğü, ürün şeması, 20 benzersiz
  demo yorumu, sekiz analiz çıktısı ve 28 kelimelik Köprü sınırı tek istekte
  denetlenir. Transformer ve Yanıt Koçu modelleri isteğe bağlıdır.
- Frontend Next.js `15.5.25` sürümüne yükseltilmiş, `postcss` ve `sharp`
  güvenlik düzeltmeleri lockfile override ile sabitlenmiştir.
- `npm audit --omit=dev`: **0 güvenlik açığı**.
- CORS varsayılan olarak yalnızca yerel frontend adreslerini kabul eder;
  sunucu kurulumu için `N_KOPRU_CORS_ORIGINS` ile açıkça ayarlanabilir.
- `.env`, SQLite veritabanı, model önbelleği, `.venv`, `node_modules` ve
  `.next` kaynak teslimine dahil edilmez.

## Doğrulama

- Backend: **54 test paketi, 1.232 / 1.232 başarılı**.
- Frontend: TypeScript kontrolü başarılı; Next.js üretim derlemesi başarılı.
- Python: `compileall` başarılı.
- API kabul dumanı: **12/12** akış başarılı (health, readiness, demo,
  analiz, özel tartışma, canlı yorum, pilot, CSV ve CORS dahil).
- Pilot gerçek kullanıcı verisi henüz yoktur; bu nedenle v1.5.0 ölçülmüş
  kullanıcı etkisi iddiasında bulunmaz. Arayüz ve saklama protokolü gerçek
  katılımcı oturumlarına hazırdır.

## Kurulum

```powershell
cd D:\NKOPRU\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

İkinci terminal:

```powershell
cd D:\NKOPRU\frontend
npm run dev
```

Jüri provasında önce `http://localhost:3000` → **Sunum Modu** açılır.
Gerçek pilot yapılacaksa **Etki Pilotu** ekranında bilgilendirilmiş onay
alınır; deneme oturumu sonuç metriklerine eklenmez.
