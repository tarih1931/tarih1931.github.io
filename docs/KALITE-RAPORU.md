# Korpus Kalite Raporu

Bu rapor otomatik üretilmiştir (`build/08_verify.py`). Hiçbir düzeltme yapılmaz; 
yalnız ölçüm ve kusur bildirimi içerir.

## Genel

| Cilt | Fiziksel sayfa | Numaralı | Numarasız | Boş | Sayfa aralığı | Karakter |
|---|---:|---:|---:|---:|---|---:|
| Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar | 583 | 378 | 205 | 96 | 2–384 | 770,660 |
| Tarih II: Ortazamanlar | 593 | 366 | 227 | 126 | 2–389 | 797,344 |

## Sayfa numarası güven dağılımı

`ocr` = taramadan doğrudan okundu · `inferred` = sayfa dizisinden çıkarıldı · 
`uncertain` = tek/çift beklentisine uymuyor, teyit gerekir

| Cilt | ocr | inferred | uncertain | yok |
|---|---:|---:|---:|---:|
| Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar | 362 | 16 | 0 | 205 |
| Tarih II: Ortazamanlar | 340 | 26 | 0 | 227 |

## Tutarlılık

### Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar

- Eksik sayfa numarası: **5**
  - 57, 58, 64, 73, 265
  - Bu numaralar genellikle metin dışı **levha sayfalarına** (renkli tablo, harita, resim) denk gelir; kitapta o numara basılı olmayabilir.
- Tekrarlanan sayfa numarası: **0** 
- Parite ihlali (sol sayfa tek / sağ sayfa çift): **0**

### Tarih II: Ortazamanlar

- Eksik sayfa numarası: **22**
  - 9, 17, 25, 33, 40, 57, 73, 185, 201, 202, 203, 204, 205, 206, 207, 208, 217, 225, 230, 231, 232, 248
  - Bu numaralar genellikle metin dışı **levha sayfalarına** (renkli tablo, harita, resim) denk gelir; kitapta o numara basılı olmayabilir.
- Tekrarlanan sayfa numarası: **0** 
- Parite ihlali (sol sayfa tek / sağ sayfa çift): **0**

## OCR sağlık göstergeleri

`junk_ratio` = tanınmayan karakter oranı · `short_word_ratio` = 1-2 harflik 
kelime oranı (yüksekse metin parçalanmış demektir)

| Cilt | Kelime | junk_ratio | short_word_ratio | ort. kelime uzunluğu |
|---|---:|---:|---:|---:|
| Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar | 100,180 | 0.0021 | 0.1471 | 6.03 |
| Tarih II: Ortazamanlar | 100,544 | 0.0009 | 0.1336 | 6.28 |

### En bozuk 10 sayfa (cilt başına)

**Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar**

| Sayfa | junk_ratio | kelime |
|---|---:|---:|
| tarih-1-1931-u031r | 0.1625 | 29 |
| 42 | 0.0522 | 54 |
| 43 | 0.0472 | 35 |
| tarih-1-1931-u265v | 0.0448 | 45 |
| 44 | 0.0438 | 46 |
| 192 | 0.0389 | 216 |
| 239 | 0.0324 | 179 |
| 237 | 0.032 | 159 |
| tarih-1-1931-u184r | 0.0282 | 281 |
| 45 | 0.0266 | 62 |

**Tarih II: Ortazamanlar**

| Sayfa | junk_ratio | kelime |
|---|---:|---:|
| tarih-2-1931-u296s | 0.1352 | 27 |
| tarih-2-1931-u155r | 0.0529 | 71 |
| tarih-2-1931-u164v | 0.0526 | 187 |
| tarih-2-1931-u089r | 0.0359 | 89 |
| tarih-2-1931-u038v | 0.0326 | 122 |
| tarih-2-1931-u089v | 0.0322 | 85 |
| tarih-2-1931-u268v | 0.024 | 154 |
| tarih-2-1931-u226v | 0.0226 | 54 |
| tarih-2-1931-u196r | 0.019 | 43 |
| tarih-2-1931-u165r | 0.0168 | 49 |

## Bilinen sınırlar

- Metin **elle düzeltilmemiş OCR** çıktısıdır. 1931 imlası ve Osmanlı Türkçesi kelime dağarcığı hata oranını yükseltir.
- Kenar boşluğundaki **omuz başlıkları** gövde metnine karışabilir.
- **Resim altı yazıları** ve harita etiketleri eksik veya bozuk olabilir.
- Kaynak tarama 150 DPI'dır; daha yüksek çözünürlüklü bir tarama, yeniden OCR ile kaliteyi belirgin biçimde artırır.
- Numarasız **levha sayfaları** sayfa dizisinde boşluk olarak görünür.
