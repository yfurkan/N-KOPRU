# N-KÖPRÜ

### Yapay Zekâ Destekli Sosyal Tartışma Zekâsı Sistemi

**TEKNOFEST 2026 · N’Sosyal İnovasyon Yarışması · Sosyal Yapay Zekâ**

N-KÖPRÜ, yüksek hacimli sosyal medya tartışmalarındaki görüşleri, ortak
zemini, temel ayrışmaları, doğrulanabilir iddiaları ve cevapsız soruları
görünür hâle getiren çalışan bir tartışma analiz platformudur. Amaç,
konuşmaları susturmak değil; anlayışı ve nitelikli etkileşimi büyütmektir.

| Çok senaryolu Macro-F1 | Gerçek sınıflandırma | Otomatik testler | Çalışan analiz adımı |
|:---:|:---:|:---:|:---:|
| **%92,5** | **74 / 80 doğru** | **808 / 808 başarılı** | **8 modül** |

> Bu sonuçlar dört konuda hazırlanmış, 80 elle etiketlenmiş **proje içi**
> doğrulama örneğine aittir. Bağımsız akademik benchmark, dış veri seti
> başarısı veya gerçek kullanıcı performansı olarak yorumlanmamalıdır.

**Teslim sürümü:** `v1.4.0` ·
**Sabit TEKNOFEST teslimi:** [`v1.4.0-teknofest-final`](https://github.com/yfurkan/N-KOPRU/tree/v1.4.0-teknofest-final)

![N-KÖPRÜ v1.4.0 çalışan uygulama: tartışma akışı ve sekiz adımlı analiz paneli](docs/screenshots/analysis-panel.webp)

## Hangi problemi çözüyor?

Uzun sosyal medya tartışmalarında tekrar eden yorumlar, karşıt görüşler,
kanıtsız iddialar ve yanıtlanmamış sorular birbirine karışır. N-KÖPRÜ,
tartışmayı okunabilir bir bilgi haritasına dönüştürür; farklı tarafların
gerçekte nerede ayrıştığını ve hangi ortak ölçütlerle konuşabileceklerini
açıkça gösterir.

## Sekiz çalışan analiz modülü

| Adım | Modül | Üretilen çıktı |
|:---:|---|---|
| 1 | **Tartışmayı Anla** | Tartışma özeti, temel ayrışmalar ve ölçülebilir göstergeler |
| 2 | **Ortak Zemin** | Karşıt görüşler arasında kesişen tema ve gerekçeler |
| 3 | **Görüş Haritası** | Görüş kümeleri, temsilci yorumlar ve kümeler arası ilişkiler |
| 4 | **İddia Radarı** | Doğrulanabilir iddia adayları, öncelik ve gerekli kanıt türü |
| 5 | **Cevapsız Sorular** | Kaynak/bilgi soruları, yanıt bağlantıları ve öncelik |
| 6 | **Yanıt Koçu** | Yapıcı ve güvenli yanıt önerileri |
| 7 | **Ben Yokken Ne Değişti?** | Anlık görüntüler arasındaki gerçek içerik değişiklikleri |
| 8 | **Köprü Oluştur** | Ortak kabul, temel ayrışma ve kısa köprü sorusu |

**Kalıcı ürün modülleri:** Profil, analiz geçmişi, anlık görüntü
karşılaştırması, anlamlı değişiklik odaklı bildirimler, mesajlar, yer imleri,
listeler ve teknik doğrulama. Kullanıcı verileri SQLite üzerinde kalır;
silinen bildirimler yeniden üretilmez.

## Teknik mimari

![N-KÖPRÜ v1.4.0 teknik mimarisi: Next.js, FastAPI, hibrit analiz, isteğe bağlı Yanıt Koçu ve SQLite](docs/architecture/technical-architecture.webp)

| Katman | Kullanılan teknoloji |
|---|---|
| Web arayüzü | Next.js 15, React 19 ve TypeScript |
| HTTP API | FastAPI, Pydantic ve Uvicorn |
| Görüş ve iddia analizi | Türkçe yapısal sinyaller + `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` |
| İsteğe bağlı Yanıt Koçu | Ayrı ve yerel `Qwen/Qwen2.5-0.5B-Instruct` katmanı |
| Kalıcılık | SQLite, anlık görüntüler, olay parmak izleri ve içerik önbelleği |

Hibrit motor, yüksek güvenli Türkçe yapısal sinyallerle çözülebilen
ifadelerde gereksiz model çıkarımı yapmaz. Belirsiz yorumlarda mDeBERTa-XNLI
devreye girer. Üretken Qwen modeli yalnızca isteğe bağlı Yanıt Koçu
akışının parçasıdır; bütün analizler için zorunlu bir dış LLM API çağrısı
veya ücretli token servisi kullanılmaz.

Uygulama **CPU üzerinde çalışabilir**. Uyumlu GPU hızlandırması isteğe
bağlıdır; belirli bir bilgisayar veya ekran kartı modeli zorunlu değildir.

## Ölçülmüş teknik doğrulama

![N-KÖPRÜ Teknik Doğrulama ekranı: 80 örnek, 74 doğru sınıflandırma ve çok senaryolu sonuçlar](docs/screenshots/technical-validation.webp)

### Dört konuda 80 elle etiketlenmiş örnek

| Tartışma konusu | Doğru / toplam | Doğruluk |
|---|:---:|:---:|
| Akademik yapay zekâ | 19 / 20 | %95 |
| Okulda telefon kullanımı | 18 / 20 | %90 |
| Kampüste gece ulaşımı | 19 / 20 | %95 |
| Uzaktan çalışma | 18 / 20 | %90 |
| **Toplam** | **74 / 80** | **%92,5** |

- Dört görüş sınıfının her biri **20 örnekle** dengeli temsil edilir.
- Temel ifadeler: **32 / 32 doğru**; zor ve örtük ifadeler: **42 / 48 doğru**.
- **71** karar Türkçe yapısal sinyallerle, **9** karar gerçek Transformer
  çıkarımıyla üretilmiştir.
- **6 sınıflandırma hatası** gizlenmez; beklenen ve gerçekleşen görüşler
  Teknik Doğrulama ekranında ayrı ayrı gösterilir.
- Bir yerel CPU ölçümünde ilk/soğuk analiz yaklaşık **2,7–3,1 saniye**,
  önbellekli tekrar yaklaşık **10–12 milisaniye** sürmüştür. Süreler cihaza,
  model durumuna ve tartışma içeriğine göre değişir.

### Sınıf bazlı sonuçlar

| Görüş sınıfı | Precision | Recall | F1 | Destek |
|---|:---:|:---:|:---:|:---:|
| Destekleyen | %100 | %85 | %91,9 | 20 |
| Karşı / Sınırlayıcı | %81,8 | %90 | %85,7 | 20 |
| Koşullu / Dengeli | %95,2 | %100 | %97,6 | 20 |
| Soru / Tarafsız | %95 | %95 | %95 | 20 |

### Karışıklık matrisi

Satırlar elle belirlenen etiketi, sütunlar sistemin gerçek tahminini gösterir.

| Beklenen ↓ / Tahmin → | Destek | Karşı | Koşul | Soru |
|---|:---:|:---:|:---:|:---:|
| **Destek** | 17 | 3 | 0 | 0 |
| **Karşı** | 0 | 18 | 1 | 1 |
| **Koşul** | 0 | 0 | 20 | 0 |
| **Soru** | 0 | 1 | 0 | 19 |

## Sıfırdan kurulum

Önerilen gereksinimler: **Python 3.11 veya 3.12**, **Node.js 20+** ve Git.
Backend ve frontend iki ayrı terminalde çalıştırılır.

### 1. Kaynak kodu indir

```bash
git clone https://github.com/yfurkan/N-KOPRU.git
cd N-KOPRU
```

### 2. Backend — Windows / PowerShell

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Python 3.12 yerine kurulu başka bir desteklenen sürüm kullanılıyorsa sanal
ortam `python -m venv .venv` komutuyla da oluşturulabilir.

### Backend — macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend — ikinci terminal

Proje kök dizininden:

```bash
cd frontend
npm install
npm run dev
```

| Servis | Adres |
|---|---|
| Uygulama | http://localhost:3000 |
| Backend sağlık kontrolü | http://127.0.0.1:8000/health |
| Etkileşimli API dokümantasyonu | http://127.0.0.1:8000/docs |

### 4. Gerçek AI modelleri — isteğe bağlı

Backend sanal ortamı etkin durumdayken:

```bash
pip install -r requirements-ai.txt
```

Uygulamada AI modelini hazırla; ilk kullanımda ilgili model dosyaları
indirilebilir. AI paketleri olmadan uygulama, desteklenen yapısal/yedek
analiz davranışıyla açılır. GPU zorunlu değildir.

## Testleri çalıştırma

Backend dizininde ve sanal ortam etkinken:

```bash
pip install -r requirements-test.txt
python -m unittest discover -s tests -p "run_*.py" -v
```

Teslim sürümünde **43 test paketi ve 808 başarılı otomatik test** bulunur.
Bildirim tekilleştirme, SQLite kalıcılığı, canlı tartışma, görüş tutarlılığı,
iddia önbelleği, sekiz analiz adımı ve arayüz sözleşmeleri test kapsamındadır.

Frontend kontrolleri:

```bash
npx tsc --noEmit
npm run build
```

## Depo düzeni

- [`backend/`](backend/): FastAPI API, analiz motorları ve 43 test paketi.
- [`frontend/`](frontend/): Next.js uygulaması ve kullanıcı arayüzü.
- [`docs/test-reports/`](docs/test-reports/): Bütün sürümlerin gerçek test,
  denetim, geçiş ve benchmark çıktıları.
- [`docs/release-notes/`](docs/release-notes/): Sürüm bazlı teslim notları.
- [`docs/screenshots/`](docs/screenshots/): Çalışan uygulama ekran görüntüleri.
- [`docs/architecture/`](docs/architecture/): Gerçek teknik mimari görseli.
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md): İsteğe bağlı ortam
  değişkenleri ve çalışma yapılandırması.
- [`CHANGELOG.md`](CHANGELOG.md): Önceki bütün sürümlerin eksiksiz geçmişi.
- [`VERSION.txt`](VERSION.txt): Kaynak paketin uygulama sürümü.

Doğrudan teslim kanıtları:

- [v1.4.0 test raporu](docs/test-reports/V1_4_0_TEST_RAPORU.txt)
- [v1.4.0 makine okunabilir test sonuçları](docs/test-reports/V1_4_0_TEST_SONUCLARI.json)
- [v1.4.0 sürüm notları](docs/release-notes/V1_4_0_RELEASE_NOTES.md)
- [Sabit TEKNOFEST teslim dalı](https://github.com/yfurkan/N-KOPRU/tree/v1.4.0-teknofest-final)

## Veri güvenliği ve ölçüm sınırları

- `.env`, veritabanları, sanal ortamlar, `node_modules`, derleme çıktıları
  ve özel anahtarlar kaynak depoya eklenmez.
- Kullanıcı içeriği ile elle etiketlenmiş doğrulama verisi birbirinden ayrı
  değerlendirilir; etiketsiz kullanıcı yorumlarına sahte doğruluk/F1 skoru
  atanmaz.
- Model güveni, yorumun doğruluğu veya kullanıcının haklılığı anlamına
  gelmez; yalnızca ilgili sınıflandırma kararına ilişkindir.
- Teknik sonuçlar proje içi doğrulamadır. Bağımsız veri seti, akademik
  genelleme veya tamamlanmış kullanıcı pilotu iddiasında bulunulmaz.

---

**N-KÖPRÜ:** Farklı düşün. Daha iyi konuş.
