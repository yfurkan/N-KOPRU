# N-KÖPRÜ v1.0.0 Release Notes

## Tamamlanan ürünleştirme katmanı

1. Bellek tabanlı Bildirimler, Mesajlar, Yer İmleri ve Listeler SQLite'a taşındı.
2. Özel tartışmaların ID ve içerikleri kalıcı hâle getirildi.
3. Analiz snapshot geçmişi ve geçmiş detay API'si eklendi.
4. Ardışık analizler için gerçek snapshot fark hesabı eklendi.
5. Profil backend'i ve düzenlenebilir yerel kullanıcı profili eklendi.
6. Profil sayaçları sahte/sabit değerler yerine doğrudan SQLite verisinden hesaplanıyor.
7. Profilde geçmiş analiz seçme, detay inceleme ve AI çalıştırmadan eski snapshot'a dönme eklendi.
8. UI'daki eski “bu oturumda tutulur / v1.0'da veritabanı bağlanacak” metinleri kaldırıldı; kalıcı SQLite durumu görünür yapıldı.
9. Silinen varsayılan listelerin ve bildirimlerin yeniden seed edilmemesi kalıcı metadata ile güvence altına alındı.
10. SQLite bağlantıları işlem bazlı açılıp kapanacak şekilde düzenlendi; thread-safe FastAPI/TestClient kullanımına uygunlaştırıldı.

## Veri dosyası

Varsayılan konum: `backend/data/nkopru.db`

Geliştirici/test ortamında `N_KOPRU_DB_PATH` çevre değişkeni ile farklı bir SQLite yolu seçilebilir.

## Bilinen ürün sınırları

- Kimlik doğrulama ve çok kullanıcı izolasyonu yok; yerel tek kullanıcı profili kullanılıyor.
- Keşfet gerçek zamanlı dış ağ akışı değil, kontrollü yerel katalog.
- İddia Radarı ve kaynak durumu çıkarımında heuristik parçalar bulunuyor.
- Snapshot fark sistemi gerçek ve kalıcıdır; ancak yerel katalog tartışmaları kendiliğinden değişmediği için fark oluşması, aynı `post_id` altındaki verinin sonraki entegrasyonlarda güncellenmesine bağlıdır.
