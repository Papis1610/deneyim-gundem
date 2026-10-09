# Deneyim Gündem V5 — yayın için hazırlanmış sürüm

Deneyim Muhasebe markası için, resmî duyuru başlıklarını kaynak bağlantıları ve yayın tarihleriyle gösteren statik web uygulaması. V4 üzerinden geliştirilmiştir.

## Gerçek durum (9 Ekim 2026)
- Canlı TCMB Basın Duyuruları, TCMB Yayınlar ve SGK duyuru listesi alındı. Son 180 gün sınırıyla 36 duyuru mevcut.
- Kodlar Papis1610/deneyim-gundem deposuna yüklenmek üzere hazırlandı. Pages yayını ve günlük görev henüz doğrulanmadı.
- Günlük toplama ve dağıtım iş akışı dosyası hazır. GitHub üzerinde çalıştırılmadı; otomasyonun etkin olduğu iddia edilmez.
- İki canlı toplama başarılı oldu. Uygulamadaki 36 bağlantının tamamı HTTP 200 ile erişildi (HEAD desteklemeyen SGK bağlantıları GET ile kontrol edildi).
- 16 Python testi geçti. JavaScript sözdizimi kontrolü geçti. Gerçek tarayıcıdaki mobil görünüm, filtreler ve detay etkileşimleri henüz test edilmedi: tarayıcı kurulumu başarısız oldu; uzak tarayıcı localhost erişimini engelledi.
- GİB ve Resmî Gazete otomatik veri kaynakları bağlı değil; erişim durumları arayüzde açıkça belirtilir.

## Yerel kullanım
Python 3.12+ ile proje klasöründe:

```bash
python -m unittest discover -s tools -p 'test*.py'
python tools/pipeline.py collect
python -m http.server 8000
```

Ardından http://localhost:8000 adresini açın. Dosyayı doğrudan çift tıklayarak açmak fetch ve service worker için uygun değildir.

## GitHub / Pages yayını
1. Bağlı hesapta `deneyim-gundem` deposunu arayın. Varsa mevcut depoyu kullanın; ikinci bir depo oluşturmayın. Mevcut içerikte çakışma varsa inceleyip birleştirin.
2. Dosyaları deponun `main` dalında kök dizine yükleyin; ZIP içindeki üst klasörü bir katman fazla yüklemeyin.
3. Repository Settings → Pages → Source: GitHub Actions seçin. Actions izinleri ve korumalı dal kuralları iş akışının haber anlık görüntüsünü kaydetmesine izin vermelidir.
4. Actions → Haberleri topla ve GitHub Pages yayinla → Run workflow çalıştırın. build ve deploy sonuçlarının başarılı olduğunu kontrol edin.
5. Environment / deploy çıktısındaki gerçek Pages URL'sini açın. `news.json`, kaynak durumları, tarihlerin görünümü ve kaynak bağlantılarını kontrol edin. 390 px mobil ve masaüstü görünümünde filtre, arama, detay, kaydet ve yeniden yükleme testlerini yapın.
6. Canlı URL kesinleşince QR oluşturun. Yayın doğrulanmadan QR dağıtmayın.

## Günlük güncelleme
Her gün 05:15 UTC (Türkiye saati 08:15) GitHub Actions toplama yapar, `news.json` anlık görüntüsünü depoya kaydeder ve Pages artefaktını dağıtır. Bu saat kesin teslim garantisi değildir; GitHub zamanlanmış işleri geciktirebilir ve etkinlik olmayan açık depolarda zamanlayıcıyı devre dışı bırakabilir. Actions çalışması ve sitedeki son başarılı toplama tarihi izlenmelidir.

Tüm kaynaklar başarısız olursa görev hata verir ve yeni Pages dağıtımı yapılmaz; son canlı sürüm korunur. Bir kaynak başarısızsa son anlık görüntüdeki haberleri korunur, erişim hatası açıkça gösterilir. 36 saatten eski toplama kaydı için arayüz uyarı gösterir. Yenile düğmesi yayımlanmış veri dosyasını yeniden okur; sunucuda yeni toplama başlatmaz.

## Kaynak ve yayın politikası
- İçerik bir resmî başlık dizinidir. Tam metin, yapay zekâ özeti, mevzuat yorumu veya işletmeye etkisi otomatik yayımlanmaz.
- `source_verified: true`, resmî alan adı ve beklenen dizin yapısının kontrolünü belirtir; hukuki inceleme onayı değildir. `verified: false`, `review_status: source_only` korunur.
- Yayın tarihi kaynakta açıkça verilen tarihtir. Atom `updated` alanı yayın tarihi yerine kullanılmaz. TCMB Türkçe ay adları ISO tarihe çevrilir; ham tarih de tutulur.
- Yürürlük tarihi başlıktan veya yayın tarihinden çıkarılmaz. Bu sürümde doğrulanmış yürürlük verisi yoktur ve `effective_at: null` gösterilir.
- TCMB Atom bağlantılarındaki HTTP URL'ler yalnızca aynı resmî alan adında HTTPS'e çevrilir. Harici alan adına yönlendirme, kullanıcı bilgisi içeren URL, standart dışı port ve XML entity reddedilir.
- Kaynak metni arayüze HTML olarak eklenmez. Resmî alan adı dışında bağlantı gösterilmez.
- TCMB kullanım şartlarında kaynak göstererek yayın ile ticari kullanım arasında ayrım bulunur; ticari yeniden kullanım için yazılı izin şartı belirtilmiştir. Bu uygulama başlık ve kaynak bağlantısı dizini tutar, tam metin yayımlamaz. Markalı ürünün kullanım modeline göre gerekli izin kapsamı ayrıca netleştirilmelidir.

## Araştırılan erişim yolları
- TCMB: resmî RSS sayfasındaki Basın Duyuruları ve Yayınlar Atom beslemeleri canlı testte çalıştı.
- SGK: resmî RSS sayfasındaki duyuru bağlantısı XML yerine `/duyuru` HTML listesine gidiyor. Canlı HTML yapısına göre ayrı adaptör geliştirildi; liste yapısı değişirse hata verir. Yayın tarihi görünür tarih kutularından alınır.
- GİB: ana sayfa canlı erişilebilir, ancak içerik dinamik JavaScript uygulamasıyla yükleniyor. Kararlı ve doğrulanmış RSS/API veri yolu bulunmadığından otomatik entegrasyon etkinleştirilmedi.
- Resmî Gazete: `/rss` canlı isteği zaman aşımına uğradı. Veri alınmadı; mevzuat başlıkları uydurulmadı. Mevcut bağlantı yalnızca resmî siteyi açar.

## Depo yapısı
`index.html`, `styles.css`, `app.js`: arayüz. `news.json`: son toplama. `sources.json`: kaynaklar. `tools/pipeline.py`: toplama. `.github/workflows/collect.yml`: günlük toplama ve Pages dağıtımı. `sw.js`: statik dosyalar için ağ öncelikli önbellek; haber JSON'u önbelleğe alınmaz. `data/pending.json`: V4'ten kalan boş editoryal kuyruk; bu sürüm otomatik yorum üretmez.

Kategori ve kaydetme tercihleri yalnızca cihazdaki localStorage'da tutulur. Hesap, çoklu cihaz eşitleme veya push bildirim sistemi yoktur.
