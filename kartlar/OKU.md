# Kart serisi

`kartlar.html`, incelemenin §3 "Eksen eksen karşılaştırma" bölümünden hazırlanmış
16 görsel kartı kitap gibi sayfa çevrilerek okunacak biçimde sunar
(https://tarih1931.github.io/kartlar.html).

- `kartlar.html` → yayında `web/kartlar.html`
- `dosyalar/` → yayında `web/kartlar/`
  - `01-kapak.png` … `16-kapanis.png`: kartlar, 1080×1350 px
  - `tarih1931-kartlar.pdf`: aynı kartlar tek PDF'te; "Tarih I" ve "Tarih II" bağlantıları tıklanabilir
  - `page-flip.browser.js`: sayfa çevirme kütüphanesi (StPageFlip 2.0.7, MIT; lisans: `page-flip-LICENSE.txt`)

`build/06_web.py` bu klasörü her üretimde `web/` altına kopyalar ve
`kartlar.html` adresini sitemap'e ekler.

## Üretim

Bu klasördeki dosyalar elle yazılmaz. Kart metinleri `gorsel-metinleri.md`
dosyasındadır; `uret.mjs` bu dosyadan PNG kartları, PDF'i ve `kartlar.html`
sayfasını üretir (`node uret.mjs`, çıktı `site/` klasörüne yazılır). Çıktı
buraya kopyalanır:

- `site/kartlar.html` → `kartlar/kartlar.html`
- `site/kartlar/*` → `kartlar/dosyalar/`

Kartlardaki her alıntı ve meal parçası, üretimden sonra 1931 metniyle ve
kapsamlı metindeki Diyanet mealiyle birebir karşılaştırılmıştır.
