# Gizlilik ve yapay zekâ şeffaflığı

## Yerel veri sınırı

N-KÖPRÜ varsayılan kurulumda yerel FastAPI + SQLite ile çalışır. Kullanıcı
verileri ve analiz geçmişi yerel veritabanında tutulur. Kaynak depoya `.env`,
model önbelleği, SQLite dosyası veya erişim belirteci eklenmez.

## Pilot gizliliği

Etki Pilotu rastgele bir `NK-XXXXXX` oturum kodu kullanır. İsim, e-posta,
telefon, demografi veya serbest metin toplanmaz. Deneme oturumları ayrı
işaretlenir ve gerçek sonuçlardan dışlanır. CSV dışa aktarımı yalnız
tamamlanmış gerçek çift görevleri içerir.

## Model katmanları

- Türkçe yapısal sinyaller yüksek güvenli kararları açıklanabilir biçimde
  çözer.
- Belirsiz görüş ve iddia adaylarında mDeBERTa-XNLI isteğe bağlı ikinci
  karar katmanıdır.
- Qwen yalnızca Yanıt Koçu üretimi içindir; görüş doğruluğu veya akademik
  başarı ölçümü değildir.
- Model güveni, yorumun “doğru” veya kullanıcının “haklı” olduğu anlamına
  gelmez.
- Model yüklenmezse yedek motor çalışır ve arayüz bunu açıkça etiketler.

## Ölçüm sınırları

80 örneklik teknik kontroller proje içi etiketli kontrollerdir; bağımsız
akademik benchmark değildir. Etiketsiz kullanıcı yorumlarına doğruluk veya
Macro-F1 atanmaz. Pilot minimum örneklemden önce sonuç üretmez; sonrasında da
çıktı nedensel veya toplum geneline yayılan bir iddia olarak sunulmaz.
