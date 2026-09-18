# GitHub main teslim rehberi

Bu belge, N-KÖPRÜ v1.5.0 kaynak paketinin GitHub’da main dalına ilk kez
yüklenmesi içindir. Bu çalışma alanından herhangi bir GitHub deposuna push
yapılmadı; takımın kendi depo adresi ve hesabı kullanılmalıdır.

## 1. GitHub’da boş depo oluşturun

GitHub’da takım adına yeni bir repository açın. İlk yükleme için:

- Depo adını takımın yarışma için belirlediği ad yapın.
- README, .gitignore ve License kutularını işaretlemeyin; hepsi paketin içinde
  zaten vardır.
- Depo görünürlüğünü yarışma kuralına göre seçin.
- Oluşturma sonrası görünen HTTPS veya SSH adresini kopyalayın.

Örnek adres yalnızca biçimi gösterir:
https://github.com/KULLANICI_ADI/DEPO_ADI.git

## 2. ZIP’i açın

ZIP’i örneğin D:\N-KOPRU klasörüne çıkarın. Git komutlarını, içinde README.md,
backend ve frontend klasörlerinin bulunduğu klasörde çalıştırın.

PowerShell:

~~~powershell
cd D:\N-KOPRU
Get-ChildItem
~~~

Listede README.md, backend, frontend, docs, VERSION.txt ve .github klasörleri
görülmelidir. Eğer bir üst klasör görünüyorsa:

~~~powershell
cd .\N-KOPRU
~~~

## 3. İlk main commit’i oluşturun

Aşağıdaki komutlar Windows PowerShell içindir:

~~~powershell
git init
git branch -M main
git add .
git diff --cached --check
git status --short
git diff --cached --name-only
git commit -m "Finalize N-KOPRU v1.5.0"
~~~

Push etmeden önce şu dosyaların staged listede olmadığını kontrol edin:

- .env veya .env.local
- backend/.venv
- frontend/node_modules
- frontend/.next
- *.db, *.sqlite ve model önbellekleri
- kişisel ekran görüntüsü, parola veya token içeren dosyalar

.gitignore bu dosyaları normal durumda zaten dışarıda tutar; yine de git
status çıktısını insan gözüyle kontrol edin. git diff --cached --check boş
dönerse satır sonu ve boşluk hatası yoktur.

## 4. origin ekleyip main’e gönderin

Kopyaladığınız gerçek depo adresini kendi değerinizle değiştirin:

~~~powershell
git remote add origin "https://github.com/KULLANICI_ADI/DEPO_ADI.git"
git remote -v
git push -u origin main
~~~

GitHub kullanıcı adı veya token sorarsa GitHub hesabınızın önerdiği kimlik
doğrulama yöntemini kullanın. Token’ı hiçbir dosyaya yazmayın, README’ye
eklemeyin ve terminal geçmişini başkalarıyla paylaşmayın.

Depo zaten dosya içeriyorsa ilk push’tan önce mevcut main’i inceleyin. Bu
paketin commit’ini zorla yazmak için git push --force kullanmayın. Önce
mevcut dosyaları yedekleyip takımın depo sorumlusuyla birleştirme planı
belirleyin.

## 5. GitHub üzerinde doğrulayın

Push tamamlandıktan sonra GitHub’da:

1. Dal seçicinin main olduğunu kontrol edin.
2. Ana sayfada v1.5.0 README’sinin açıldığını kontrol edin.
3. VERSION.txt içinde 1.5.0 olduğunu kontrol edin.
4. .github/workflows/quality.yml iş akışının çalıştığını açın.
5. Backend testleri ve frontend kalite adımlarının yeşil olduğunu bekleyin.
6. Actions sonucu oluşmadan README’ye "Actions başarılı" yazmayın.

Kalite iş akışı main push’unda şunları çalıştırır:

- Python compileall
- backend unittest discover ile 1.240’lık regresyon paketi
- npm ci
- Next.js production build
- TypeScript kontrolü
- production npm audit

## 6. Temiz kopya ile son kontrol

GitHub’dan main dalını yeni bir klasöre klonlayıp README’deki kurulum
adımlarını izleyin. Bu kontrol, yerel klasörde tesadüfen kalan sanal ortamın
veya cache dosyasının uygulamayı çalıştırıyor olmasını engeller:

~~~powershell
cd D:\Kontrol
git clone --branch main "https://github.com/KULLANICI_ADI/DEPO_ADI.git" N-KOPRU-clean
cd .\N-KOPRU-clean
git log -1 --oneline
Get-Content .\VERSION.txt
~~~

Sonra README’deki backend ve frontend başlatma adımlarını iki ayrı terminalde
uygulayın. Tarayıcıda /health ve /api/system/readiness adreslerini açın.
Sürüm 1.5.0 ve zorunlu hazırlık 5/5 görünmelidir.

## 7. Değerlendiriciye verilecek bilgiler

Teslim formuna yalnızca:

- GitHub repository adresi,
- main dalı,
- gerekiyorsa doğrudan main bağlantısı

ekleyin. Değerlendirici için ilk bakılacak belgeler:

1. README.md
2. docs/FINALIST_RUNBOOK.md
3. docs/CONTROLLED_DEMO_PROTOCOL.md
4. docs/CONFIGURATION.md
5. docs/test-reports/V1_5_0_TEST_RAPORU.txt

Kodun kapsamı özellikle yerel ve tekrarlanabilir tutulmuştur. Gerçek kullanıcı
etkisi, canlı platform bağlantısı veya saha sonucu varmış gibi bir açıklama
yapmayın; bu pakette böyle bir iddia bulunmamaktadır.

## Sık karşılaşılan durumlar

### "remote origin already exists"

Adresin doğru olup olmadığını kontrol edin:

~~~powershell
git remote -v
~~~

Yanlışsa mevcut origin’i silmeden önce adresi ekip içinde doğrulayın. Doğru
adres için:

~~~powershell
git remote set-url origin "https://github.com/KULLANICI_ADI/DEPO_ADI.git"
~~~

### "src refspec main does not match any"

Commit oluşmamıştır. Önce git status ve git log komutlarını çalıştırın,
ardından git add, git diff --cached --check ve git commit adımlarını
tamamlayın.

### GitHub Actions frontend’de takılıyor

Node.js 20 veya üzeri kullanın ve package-lock.json ile npm ci çalıştırın.
Yerel node_modules klasörünü Git’e eklemeyin.

### Backend açılamıyor

backend klasöründe .venv oluşturulduğunu, requirements.txt kurulduğunu ve
8000 portunun boş olduğunu kontrol edin. Ayrıntılı komutlar README.md’dedir.
