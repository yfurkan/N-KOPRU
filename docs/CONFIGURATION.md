# İsteğe bağlı yapılandırma

N-KÖPRÜ varsayılan ayarlarıyla yerel CPU üzerinde çalışır. Aşağıdaki ortam
değişkenleri yalnızca model, veritabanı veya API adresini değiştirmek
gerektiğinde kullanılmalıdır.

## Backend

| Ortam değişkeni | Varsayılan | Açıklama |
|---|---|---|
| `N_KOPRU_AI_MODEL` | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | Hibrit görüş ve belirsiz iddia analizinde kullanılan Transformer modeli |
| `N_KOPRU_AI_BATCH_SIZE` | `4` | Uygun olduğunda işlenecek model çıkarımı grup boyutu |
| `N_KOPRU_COACH_MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` | İsteğe bağlı Yanıt Koçu üretken modeli |
| `N_KOPRU_COACH_MAX_NEW_TOKENS` | `48` | Yanıt Koçu için azami yeni token sayısı |
| `N_KOPRU_COACH_FAST_PATH` | `1` | Yüksek güvenli durumlarda hızlı yapısal yanıt yolunu kullanır |
| `N_KOPRU_DB_PATH` | Uygulamanın yerel SQLite yolu | Kalıcı veritabanı dosyasının açık konumu |

PowerShell örneği:

```powershell
$env:N_KOPRU_DB_PATH = "D:\NKOPRU\veri\nkopru.db"
uvicorn app.main:app --reload --port 8000
```

macOS / Linux örneği:

```bash
export N_KOPRU_AI_BATCH_SIZE=4
uvicorn app.main:app --reload --port 8000
```

Backend bu değerleri çalışan sürecin ortamından okur. Yerel bir `.env`
dosyası oluşturulursa içeriğin ilgili terminal ortamına ayrıca aktarılması
gerekebilir; gizli bilgiler hiçbir zaman depoya eklenmemelidir.

## Frontend

| Ortam değişkeni | Varsayılan | Açıklama |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Next.js arayüzünün erişeceği FastAPI adresi |

Backend farklı bir adreste çalışıyorsa `frontend/.env.local` içine
`NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` biçiminde tanımlanabilir.
`.env.local` özel yerel dosyadır ve Git deposuna eklenmemelidir.

## Donanım ve model kullanımı

- Belirli GPU, ekran kartı veya bilgisayar modeli gerekmez.
- Uyumlu hızlandırma varsa kullanılabilir; CPU çalışması desteklenir.
- mDeBERTa-XNLI görüş/iddia katmanıdır; Qwen isteğe bağlı Yanıt Koçu
  katmanıdır. İki model birbirinin yerine geçmiş gibi raporlanmamalıdır.
- İlk model indirme internet bağlantısı gerektirebilir. Hugging Face erişim
  belirteci yalnızca kullanıcının kendi erişim ihtiyacı için isteğe bağlıdır;
  kaynak depoya hiçbir belirteç eklenmez.
