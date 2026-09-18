# Yerel yapılandırma

N-KÖPRÜ v1.5.0 varsayılan ayarlarıyla internet gerektirmeyen yapısal yedek
motor üzerinden çalışır. Aşağıdaki seçenekler yalnızca yerel çalışma
adresini, SQLite konumunu veya isteğe bağlı model katmanını değiştirmek için
kullanılır.

## Backend değişkenleri

| Değişken | Varsayılan | Kullanım |
|---|---|---|
| N_KOPRU_DB_PATH | backend/data/nkopru.db | Yerel SQLite dosyasının açık yolu |
| N_KOPRU_CORS_ORIGINS | localhost ve 127.0.0.1 için 3000 | İzin verilen frontend adresleri |
| N_KOPRU_CORS_ORIGIN_REGEX | localhost ve private LAN için 3000 | LAN sunumunda tarayıcı origin deseni |
| N_KOPRU_AI_BATCH_SIZE | 4 | İsteğe bağlı model çıkarım grup boyutu |
| N_KOPRU_STANCE_MODEL | mDeBERTa-XNLI model adı | Görüş ve iddia için isteğe bağlı model |
| N_KOPRU_COACH_MODEL | Qwen 0.5B model adı | Yanıt Koçu için isteğe bağlı yerel aday |
| N_KOPRU_COACH_FAST_PATH | 1 | Güvenli yapısal yolu öncele |
| N_KOPRU_COACH_MAX_NEW_TOKENS | 48 | Yerel Yanıt Koçu aday uzunluğu |

Kopyalanabilir örnekler backend/.env.example ve frontend/.env.example
dosyalarındadır. .env veya .env.local dosyaları kişisel yerel ayardır ve
Git’e eklenmemelidir.

## Backend’i LAN sunumuna açma

Tek bilgisayarda README’deki 127.0.0.1 komutu yeterlidir. Aynı özel ağdaki
başka bir cihazdan tarayıcı açılacaksa backend şu şekilde başlatılabilir:

~~~powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
~~~

Varsayılan CORS yalnızca localhost, 127.0.0.1 ve özel ağdaki frontend’in
3000 portuna izin verir. Uygulama dış sosyal platforma istek göndermez;
CORS ayarı yalnız tarayıcının yerel API’ye erişim sınırıdır.

## İsteğe bağlı yapay zekâ modelleri

- mDeBERTa-XNLI, belirsiz görüş ve iddia adaylarında ikinci katmandır.
- Qwen, yalnızca Yanıt Koçu için aday metin üretir.
- İki model de v1.5.0 yerel demosu için zorunlu değildir.
- Model yüklenmezse yapısal yedek motor çalışır; arayüz bu durumu gizlemez.
- Model paketleri kurulsa bile ürün harici bir LLM API anahtarına bağlanmaz.
- Model indirme seçilirse ilk kurulum internet ve disk alanı gerektirebilir.

## Veri konumu

SQLite dosyası backend/data altında oluşabilir. .gitignore; SQLite, WAL/SHM,
model önbelleği, sanal ortam, node_modules ve Next.js çıktısını kaynak
tesliminden dışarıda bırakır. Temiz GitHub tesliminde bu dosyalar bulunmamalıdır.
