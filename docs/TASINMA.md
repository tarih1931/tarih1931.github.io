# Projeyi başka bir bilgisayara taşımak

Depo GitHub'da olduğu için taşıma büyük ölçüde `git clone`'dan ibarettir.
Elle taşınması gereken tek şey kaynak taramalardır.

## 1. Depoyu klonlayın

```bash
git clone https://github.com/tarih1931/tarih1931.github.io.git 1931
```

Bu, 1916 dosyayı getirir: düzeltmeler (`corrections/`), üretilmiş korpus
(`data/`), site (`web/`), metadata, hat betikleri, belgeler ve Vikikaynak
çıktıları. **Elle yapılan 129 sayfalık düzeltme depoda olduğu için kaybolmaz.**

## 2. Taramaları elle kopyalayın

`PDF/` klasörü depoda **değildir** — dosyalar GitHub'ın 100 MB sınırının
üstünde, ayrıca klasörde telifli modern eserler de var.

USB bellek veya bulut ile şu iki dosyayı taşıyın:

```
PDF/Tarih I.pdf      106 MB
PDF/Tarih II.pdf     107 MB
```

Yeni bilgisayarda depo kökünde `PDF/` klasörü açıp içine koyun. Dosya adlarını
değiştirmeyin; `build/common.py` bu adlara göre arar.

> Taramaları taşımazsanız korpus, site ve Vikikaynak çıktıları yine çalışır —
> hepsi üretilmiş hâlde depoda. Taramalar yalnız şunlar için gerekir:
> `build/duzelt.py` (düzeltme arayüzü sayfa görüntüsünü PDF'ten üretir),
> `build/09_images.py`, ve hattın 01-03 adımlarını baştan çalıştırmak.

## 3. Python ortamı

```bash
pip install -r requirements.txt
```

Python 3.11 veya üstü. Paketler: `pymupdf`, `rapidocr-onnxruntime`, `numpy`.

## 4. Git kimliği

Kimlik bu depoya özel ayarlanmıştı, klonda gelmez:

```bash
git config user.name "tarih1931"
```

```bash
git config user.email "319375533+tarih1931@users.noreply.github.com"
```

## 5. Doğrulama

Her şeyin yerinde olduğunu tek komutla görün:

```bash
python build/03b_corrections.py --rapor
```

Beklenen çıktı:

```
tarih-1-1931: 24 düzeltilmiş sayfa uygulandı (583 sayfa içinde)
tarih-2-1931: 105 düzeltilmiş sayfa uygulandı (593 sayfa içinde)
```

Bayat düzeltme uyarısı **çıkmamalıdır**. Çıkarsa `PDF/` dosyaları farklı bir
nüsha demektir; aynı taramaları kopyaladığınızdan emin olun.

## 6. Claude Code ile devam

Projeyi açarken **klasör olarak deponun kökünü seçin** (`.../1931`). Eski
bilgisayarda oturum boş bir `Ataturk` klasöründe açıldığı için her seferinde
klasör izni istemek ve dosya bağlantılarını göreli yazmak gerekiyordu; kökü
doğru seçerseniz bu sorun olmaz.

Bağlam için okunacak dosyalar: [README.md](../README.md),
[YAPILACAKLAR.md](YAPILACAKLAR.md), [VIKIKAYNAK-YOL-HARITASI.md](VIKIKAYNAK-YOL-HARITASI.md).

## 7. Eski bilgisayarda kalanlar

Taşımadan önce şunların depoda olduğundan emin olun — `git status` temiz
olmalı. Depoya girmeyen ve **yeniden üretilebilen** dosyalar:

| Dosya | Durum |
|---|---|
| `data/*/raw_pages.jsonl` | 01. adım yeniden üretir |
| `build/__pycache__/`, `build/headers.log` | işleme artığı |
| `.claude/settings.local.json` | yerel araç ayarı |

Bunları taşımaya gerek yoktur.

## 8. Adres taşınması — 2026-08-21

Site, önceki GitHub Pages adresinden **`https://tarih1931.github.io`**
adresine taşındı. Depo artık
`tarih1931/tarih1931.github.io` (kullanıcı sayfası: `web/` klasörü kökte yayınlanır).

Eski depo aynı gün **silindi**; klonda tek uzak adres kaldı:

```
origin  https://tarih1931@github.com/tarih1931/tarih1931.github.io.git
```

Silmenin bedeli ölçüldü ve göze alındı: Zenodo yayımlanmış dosyayı bir daha
değiştirmediği için, 21.08.2026'dan önce arşivlenmiş nüshalardaki eski adres
bağları artık ölüdür — incelemenin o günden önceki sürümlerinin PDF'lerinde 19
ayrı sayfaya giden 64 bağ işareti ve korpusun `v1.0.0`–`v1.2.0` zip'leri.

**Yaşayan bütün kayıtlar yeni adrese bakar.** Zenodo künyeleri (korpus ve
inceleme), Wikidata P953 ifadeleri, Internet Archive öğeleri, HuggingFace veri
kümesi ve sitenin kendisi aynı gün tek tek güncellendi; ayrıntısı
[KANALLAR.md](KANALLAR.md) içindedir.

> **İncelemenin yazarı Anonim'dir.** Değer tek yerde durur:
> `metadata/books.json` -> `review.author`. Künyeler, site, Zenodo, Internet
> Archive ve Wikidata oradan okur. 21.08.2026'dan önce Zenodo'da yayımlanmış
> sürümlerin PDF kapaklarında eski değer basılıdır ve orada kalır — Zenodo
> yayımlanmış kaydın dosyalarını kilitler; concept DOI temiz sürüme
> çözümlendiği için künyeye bakan onu görmez.

## 9. Depo silinirse geri getirme

21.08.2026'da depo yanlışlıkla silindi ve yerel klondan geri kuruldu. Yordam
denenmiştir; GitHub'ın "deleted repositories" listesi boş çıkarsa da işler:

1. Aynı adla **boş** bir depo açın (README/`.gitignore`/lisans işaretlemeden).
   Kullanıcı sayfasında ad `<kullanıcı>.github.io` olmak zorundadır.
2. Geçmişi basın:

```bash
git push -u origin main
```

```bash
git push origin --tags
```

3. Settings -> Pages -> Source: **GitHub Actions**. `pages.yml` ilk push'ta
   zaten kuyruğa girer; kaynak seçilince site bir dakikada döner.
4. Release'leri isterseniz elle yeniden açın (etiketler 2. adımda geri
   gitti). Sıra derdi yoktur: Zenodo'nun GitHub anahtarı bu projede
   **kapalıdır**, release Zenodo'yu tetiklemez. Korpusun yeni sürümü
   `build/17_zenodo_yukle.py --korpus` ile jetonla basılır
   (bkz. [YAPILACAKLAR.md](YAPILACAKLAR.md) §1.2).

Yerel klon tam bir yedektir; istenirse tek dosyaya da alınır:

```bash
git bundle create ../1931-yedek.bundle --all
```
