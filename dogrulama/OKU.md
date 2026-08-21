# Arama motoru doğrulama dosyaları

Buradaki dosyalar site üretilirken `web/` köküne **olduğu gibi** kopyalanır
(`build/06_web.py`). Sebebi basit: `web/` her üretimde sıfırdan kurulur, oraya
elle konan bir dosya ilk `run_all`'da kaybolur.

| Dosya | Ne için |
|---|---|
| `google*.html` | Google Search Console sahiplik doğrulaması |
| `BingSiteAuth.xml` | Bing Webmaster Tools sahiplik doğrulaması |
| `<32 hex>.txt` | IndexNow anahtarı (Bing/Yandex bildirimi) |

Doğrulama dosyası kaybolursa Search Console mülkü bir süre sonra doğrulamayı
yitirir ve sitemap gönderimi durur; dosyalar bu yüzden depoda tutulur.

Buradaki dosyalar sitemap'e girmez ve hiçbir sayfadan bağlantı almaz.
