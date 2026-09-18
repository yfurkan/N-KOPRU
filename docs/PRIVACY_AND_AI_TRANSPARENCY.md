# Gizlilik ve yapay zekâ şeffaflığı

## Çalışma modeli

N-KÖPRÜ v1.5.0 varsayılan olarak yerel FastAPI + SQLite + Next.js
mimarisinde çalışır. Uygulama, teslim paketinde canlı sosyal medya hesabına,
dış yorum akışına, webhook’a veya harici ücretli LLM API’sine bağlanmaz.

Kullanıcının ana ekrana yazdığı yerel tartışma ve analiz geçmişi çalıştırılan
bilgisayarın SQLite dosyasında tutulabilir. Bu dosya Git’e eklenmez. Kullanıcı
verisi veya sır içeren .env dosyaları da depoya eklenmemelidir.

## Kontrollü demo sınırı

Kontrollü Senaryo ekranındaki iki tartışma ve görevler depoya dahil sabit
örneklerdir. Ekran gerçek kişi, gerçek oturum veya kullanıcı araştırması
toplamaz. Deneme sırasında görülen kod, süre, yanıt ve derecelendirmeler
yalnızca arayüzün iki aşamalı akışını yeniden çalıştırmak için yerel olarak
tutulur. Bunlar kullanıcı başarısı, etki ölçümü veya saha kanıtı değildir.

Backend, eski istemcilerle uyumluluk için /api/pilot URL yolunu korur; gerçek
kullanıcı modu practice=false ile reddedilir. Kontrollü akışın ayrıntıları
CONTROLLED_DEMO_PROTOCOL.md dosyasında, regresyonları ise backend/tests içinde
yer alır.

## Analiz katmanları

- Yapısal Türkçe sinyaller; görüş yönü, ironi, hakaret, soru, sayı ve kaynak
  ihtiyacı gibi gözlenebilir metin işaretlerini açık kurallarla işler.
- mDeBERTa-XNLI isteğe bağlı ikinci görüş/iddia katmanıdır.
- Qwen isteğe bağlı Yanıt Koçu adayıdır; model çıktısı otomatik olarak doğru
  kabul edilmez.
- Üretken aday; hakaret, prompt sızıntısı, sayı/link kaybı, ana görüş
  kaybı ve uygunsuz uzunluk kontrollerinden geçmeden gösterilmez.
- Model güveni, bir görüşün doğru olduğu veya kullanıcının haklı olduğu
  anlamına gelmez.
- Model kurulumu yoksa yedek motor çalışır ve arayüzde açıkça etiketlenir.

## İddia ve ölçüm sınırı

1.240 otomatik test, kod ve ürün sözleşmelerinin proje içi doğrulamasıdır.
Etiketsiz kullanıcı metnine doğruluk veya Macro-F1 atanmaz. Teknik raporun
önceki sürüm sonuçları tarihsel kayıt olarak tutulur; v1.5.0 için gerçek
kullanıcı etkisi veya genellenebilir başarı iddiası yapılmaz.
