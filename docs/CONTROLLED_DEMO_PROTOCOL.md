# Kontrollü Senaryo Protokolü

## Amaç

Bu ekran bir kullanıcı araştırması veya etki ölçümü değildir. N-KÖPRÜ v1.5.0
finalist yazılımının jüri önünde aynı akışı tekrar tekrar gösterebilmesi için
hazırlanmış yerel bir ürün demosudur.

Jüri, iki sabit tartışma konusu üzerinde şu farkı görür:

1. Ham yorumlar doğrudan okunur.
2. Aynı tartışma, N-KÖPRÜ’nün özet, görüş kümeleri ve Köprü çıktısıyla
   incelenir.
3. Her iki görünümün sonunda konuya bağlı karar sorusu yanıtlanır.

Senaryolar:

- Kampüste gece ulaşımı: hizmetin sürmesi, kaldırılması veya güvenlik ve
  talep koşullarıyla sınırlı yürütülmesi.
- Mahalle parklarının 22.00’den sonra kullanımı: erişim, sessizlik ve güvenlik
  arasında koşullu bir düzenleme.

## Bilinçli sınırlar

- Gerçek katılımcı, gerçek oturum veya kullanıcı hesabı yoktur.
- İsim, e-posta, telefon, demografi, iletişim bilgisi ve canlı platform verisi
  toplanmaz.
- Harici sosyal ağ, webhook, canlı yorum akışı veya ücretli dış LLM servisi
  kullanılmaz.
- Ekranda görülen süre, yanıt ve puanlar yalnızca sabit demo akışının
  çalıştığını göstermek için yerel SQLite’a yazılır.
- Bu kayıtlar gerçek kullanıcı metriği, başarı oranı veya etki sonucu değildir.
- Dışa aktarılabilir kullanıcı araştırması sonucu üretilmez.

Eski istemcilerle uyumluluk nedeniyle backend uçlarının URL yolu
"/api/pilot" olarak kalmıştır. Bu ad ürünün kapsamını değiştirmez:
practice=false isteği reddedilir, yalnızca sabit demo akışı çalışır.

## Jüri sırasında kullanım

1. Uygulamada "Kontrollü Senaryo" ekranını açın.
2. "Deneme Akışını Başlat" düğmesine basın.
3. İlk görevde ham yorumları ve karar sorusunu gösterin.
4. İkinci görevde N-KÖPRÜ özetini, görüş haritasını ve Köprü sorusunu
   gösterin.
5. "Gerçek sonuç üretilmiyor" açıklamasını özellikle görünür bırakın.
6. Aynı akışı yeniden çalıştırmak için "Denemeyi Yeniden Başlat" düğmesini
   kullanın.

## Kod kanıtı

- backend/app/pilot.py: demo oturumu ve veri sınırı.
- backend/app/database.py: yerel SQLite şeması.
- backend/tests/run_finalist_pilot_regression.py: sabit senaryo, iki faz,
  sıra, idempotency ve gerçek metrik yolunun kapalı olduğunu denetler.
- frontend/app/page.tsx: jüriye görünen "Kontrollü Senaryo" ekranı.
