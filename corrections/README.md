# Elle yapılmış OCR düzeltmeleri

Hat, metni her çalıştırmada PDF'ten yeniden çıkarır. Bu klasör, elle düzeltilen
sayfaların yeniden üretimde kaybolmasını önler.

```
corrections/<kitap-slug>/<page_id>.txt    düzeltilmiş tam sayfa metni
corrections/<kitap-slug>/manifest.json    hangi düzeltme hangi OCR üstüne yazıldı
```

`page_id` sayfanın kalıcı kimliğidir: basılı numaralı sayfalarda `p0042`,
numarası basılmamış sayfalarda tarama birimi (`u022r`). `data/<slug>/pages.jsonl`
içindeki `page_id` alanının son parçasıdır.

## Nasıl çalışır

```bash
python build/duzelt.py              # tarama solda, metin sağda; Ctrl+S kaydeder
python build/03b_corrections.py     # düzeltmeleri pages.jsonl'e işler
python build/run_all.py --from 04   # metin, TEI, site ve dizini yeniden üret
```

Tam hat çalıştırıldığında (`run_all.py`) 03b adımı sırası gelince kendiliğinden
devreye girer; ayrıca çağırmak gerekmez.

`secim/` aralığı da değiştiyse bu kadarı yetmez: `run_all.py` 10 ve 11. adımları
içermez, oysa `05_metadata.py` ile `06_web.py` `secim/index.json` ve
`secim/<bölüm>/sayfalar.jsonl` dosyalarını okur. Sıra şudur:

```bash
python build/03b_corrections.py
python build/04_emit.py
python build/10_secim.py      # alt korpusu yeniden çıkar
python build/11_birlesik.py   # sayfa sınırlarını birleştir
python build/05_metadata.py && python build/06_web.py && python build/06b_inceleme.py
python build/07_thematic.py && python build/08_verify.py
```

Düzeltilmiş sayfa `pages.jsonl` içinde işaretlenir: `text_source: "corrected"`,
`corrected_at`, ve ham OCR metni `text_ocr` alanında saklanır. Düzeltme dosyası
silinirse sayfa ham OCR metnine geri döner.

## Bayatlama

`manifest.json`, düzeltmenin **hangi OCR metni üzerine** yapıldığını sha1 ile
saklar. Hattın ilk adımları değişir de aynı sayfanın OCR çıktısı başkalaşırsa,
düzeltme artık başka bir metnin üstüne yazılıyor demektir. Bu durumda düzeltme
yine uygulanır, ama `correction_stale` işaretlenir ve uyarı basılır:

```
UYARI — altındaki OCR metni değişmiş: p0084
```

Böyle bir uyarı görürseniz o sayfayı taramayla yeniden karşılaştırın.

## Ölçüt

Düzeltme, **basılı sayfada ne yazıyorsa odur**. 1931 imlası korunur
(*tarihtenevelki*, *ortazaman*, *evel*, *mekteb*), günümüz imlasına çevrilmez.
Kaynak metni düzeltmek değil, taramayı doğru okumak amaçlanır.
