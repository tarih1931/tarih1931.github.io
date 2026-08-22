# Yapmanız gerekenler

Teknik üretimin tamamı bu klasörde hazır. Aşağıdakiler **sizin hesaplarınızla**
ve **sizin kararınızla** yapılması gereken, benim sizin adınıza yapmadığım
adımlardır. Sıra, etki/emek oranına göre dizilmiştir.

---

## 1. Yayına alın — sıralı ve somut

### 1.1 GitHub deposu — ✅ tamamlandı (15.08.2026)

| | |
|---|---|
| Depo | https://github.com/tarih1931/tarih1931.github.io — herkese açık |
| `main` | push edildi; yerel HEAD = `origin/main` |
| Pages | Source: **GitHub Actions**; site yayında |
| Site | https://tarih1931.github.io |

Bundan sonra `main` dalına yapılan her push, `.github/workflows/pages.yml`
üzerinden `web/` klasörünü yeniden yayımlar; ayrıca bir şey yapmanız gerekmez.

> Dal tabanlı yayın (“Deploy from a branch”) bu depoda kullanılamaz: klasör
> olarak yalnız `/ (kök)` ve `/docs` sunulur, site ise `web/` altındadır ve
> `docs/` başka iş görür. İş akışı bu yüzden vardır.

**Sürümler:** `v1.0.0` (15.08.2026), `v1.1.0` ve `v1.1.1` (19.08.2026),
`v1.2.0` (20.08.2026), `v1.3.0` ve `v1.3.1` (21.08.2026) yayımlanmıştır; Zenodo
altısını da arşivlemiştir (§1.2). İlk dördünde sıra önemliydi — sürüm, Zenodo bağlantısı
kurulduktan *sonra* oluşturulmalıydı. `v1.3.0`'den itibaren bu bağlantı
kullanılmıyor; arşiv nüshası jetonla basılıyor, release'in sırası artık
hiçbir şeyi etkilemiyor.

> **Kaynak taramalar depoda değil.** `PDF/Tarih I.pdf` ve `PDF/Tarih II.pdf`
> dosyalarının her biri ~106 MB; GitHub'ın 100 MB dosya sınırını aşar ve push'u
> reddettirir. Taramaların yeri Internet Archive ve Zenodo'dur (§1.2, §1.3);
> yükledikten sonra depodan oraya bağlantı verilir. Git LFS de mümkündür ama
> GitHub Pages LFS dosyalarını sunmaz ve aylık 1 GB bant genişliği sınırı vardır.

### 1.2 Zenodo → DOI — ✅ tamamlandı (15.08.2026)

| | |
|---|---|
| **Concept DOI** (künyelerde kullanılan) | `10.5281/zenodo.21956339` |
| Sürüm DOI'si (`v1.0.0`) | `10.5281/zenodo.21956340` |
| Kayıt | https://doi.org/10.5281/zenodo.21956339 |

Concept DOI bütün sürümleri temsil eder ve daima en sonuncusuna çözümlenir;
künyelere o yazılır. Sürüme özel DOI yeni sürümde eskiyeceği için atıf
zincirini kırar.

DOI artık kodda değil, **`metadata/books.json` → `collection.doi`** alanında
durur; hem künye adımı hem site adımı oradan okur. Alan boşsa DOI hiçbir
künyeye yazılmaz. Sürüm numarası da aynı yerdedir: **`collection.version`**.

> ### ✅ `v1.1.0` yayımlandı (19.08.2026)
>
> | | |
> |---|---|
> | Sürüm DOI'si (`v1.1.0`) | `10.5281/zenodo.22011166` |
> | Release | https://github.com/tarih1931/tarih1931.github.io/releases/tag/v1.1.0 |
>
> `v1.0.0` arşivinde düzeltilmiş metin 38 sayfaydı, `v1.1.0`'de **129**. Concept
> DOI artık bu sürüme çözümlenir; künye dosyalarına dokunmak gerekmedi.
>
> **O günün yordamı:** Zenodo GitHub'ın `release` olayını dinliyordu;
> `git push --tags` o olayı doğurmaz, bu yüzden release açmak gerekiyordu.
> Bu yol 21.08.2026'da bırakıldı — bugünkü sıra için §1.2'nin devamına bakın.

> ### ✅ `v1.1.1` yayımlandı (19.08.2026) — künye kanalları gösteriyor
>
> | | |
> |---|---|
> | Sürüm DOI'si (`v1.1.1`) | `10.5281/zenodo.22014675` |
> | Release | https://github.com/tarih1931/tarih1931.github.io/releases/tag/v1.1.1 |
>
> `.zenodo.json` bu sürümde 2 bağdan **9 bağa** çıktı: Internet Archive
> taramaları (`isDerivedFrom`), incelemenin DOI'si (`isSupplementedBy`),
> HuggingFace (`isIdenticalTo`), site (`isVariantFormOf`), Vikikaynak istinsahı
> (`isSourceOf`). İnceleme ile korpus arasındaki bağ artık çift yönlü. Zenodo
> künyeyi yalnız release anında okur; `v1.0.0` ve `v1.1.0` arşivlerinde bu
> bağlar yoktur ve orada kalır — concept DOI en sonuncuya çözümlendiği için
> künyeye bakan bir toplayıcı doğru kaydı görür.
>
> Etiket bu kez sürüm notlarını içeren commit'i gösterir; `v1.1.0`'de notlar
> etiketten sonra eklenmiş ve arşivlenen zip'e girmemişti.

> ### ✅ `v1.2.0` yayımlandı (20.08.2026) — inceleme referansları adlandırıldı
>
> | | |
> |---|---|
> | Sürüm DOI'si (`v1.2.0`) | `10.5281/zenodo.22035196` |
> | Release | https://github.com/tarih1931/tarih1931.github.io/releases/tag/v1.2.0 |
> | Etiket | `6cbd314` — sürüm notlarını içeren commit |
>
> İncelemenin indeks işaretleri kısaltma olmaktan çıkıp ne olduklarını söyleyen
> adlara döndü: `A1`/`K1`/`B1`/`C1` yerine `Alıntı-01`, `Ayet-01`, `Bulgu-01`,
> `Öz-01`. Bulgu işareti de diğerleriyle aynı köşeli parantezli biçime geldi
> (`**Bulgu B7.**` → `**[Bulgu-07]**`). İngilizce sürüm aynı şemayı kendi
> diliyle kullanır: `Quote-01`, `Verse-01`, `Finding-01`, `Claim-01`.
>
> HTML ve PDF'te işaretler renkle de ayrılır — alıntı mavi, ayet yeşil, bulgu
> kırmızı. Renk `.md`'de tutulamadığı için `common.md_inline` işareti köşeli
> parantezleriyle birlikte sınıflı tek bir ögeye çevirir; rengi site (06) ve
> PDF (16) stili tanımlar. Kanonik biçimde ayrımı işaretin kendisi yapar.
>
> §2'nin indeks künyesi paragrafı kalktığı için `06b`'deki "§2 toplam aralığı
> ilan etmeli" denetimi de düştü — ilan edecek cümle kalmadı. İndeksin
> eksiksizliği, işaret sayısının kayıtla tutması, §2 tablosundaki eksen
> aralıkları ve alıntıların künyesindeki sayfada birebir bulunması denetimleri
> yerinde.
>
> Arşivlenen nüsha `…-v1.2.0.zip` (14,6 MB); concept DOI artık bu sürüme
> çözümlenir. Etiket, sürüm notlarını içeren commit'e taşındıktan sonra
> release açıldı; böylece notlar arşivlenen zip'in içindedir.
>
> İncelemenin kendi kaydı aynı gün ayrıca tazelendi: `10.5281/zenodo.22033498`
> (§1.2b).

> ### ✅ `v1.3.0` yayımlandı (21.08.2026) — adres taşındı, kanallar izledi
>
> | | |
> |---|---|
> | Sürüm DOI'si (`v1.3.0`) | `10.5281/zenodo.22047658` |
> | Etiket | sürüm notlarını içeren commit |
>
> Site, önceki GitHub Pages adresinden **`https://tarih1931.github.io`**
> adresine taşındı; eski depo silindi. Yaşayan
> bütün kayıtlar aynı gün yeni adrese çevrildi: Zenodo künyeleri (korpus ve
> inceleme), Wikidata'daki dört P953 ifadesi, üç Internet Archive öğesi ve
> HuggingFace veri kümesi. Silmenin bedeli kayıtlıdır — 21.08 öncesi
> arşivlenmiş nüshalardaki eski adres bağları ölüdür
> ([TASINMA.md](TASINMA.md) §8).
>
> İncelemenin İngilizce sayfası doğrudan başlıkla açılıyor: üst gezinti çubuğu,
> kapsam notu, atıf kutusu, içindekiler, dil notu ve dosya satırı kalktı.
> Başlık da Türkçe aslının birebir karşılığına geldi — *The Approach of Official
> History Textbooks Taught in High Schools Between 1931 and 1941 to Islamic
> Belief*. Kaldırılan bağların hepsi altbilgide duruyor.
>
> **Bu sürüm Zenodo'ya GitHub tümleşiğiyle değil jetonla basıldı.** Sebebi ve
> yordamı bu bölümün devamındadır; anahtar bir daha açılmayacak.

> ### ✅ `v1.3.1` yayımlandı (21.08.2026) — arşiv nüshası düzeltildi
>
> | | |
> |---|---|
> | Sürüm DOI'si (`v1.3.1`) | `10.5281/zenodo.22047838` |
>
> `v1.3.0` kaydına, yayımlama komutu yanlış çalıştırıldığı için incelemenin beş
> dosyası da yüklendi ve künyesi bir an incelemeninkiyle değişti. Künye aynı
> gün geri alındı; dosyalar geri alınamadı, çünkü Zenodo yayımlanmış kaydın
> kovasını kilitler (*"Bucket is locked for modifications"*). Bu sürüm yalnız
> korpus zip'ini taşır; concept DOI artık temiz kayda çözümlenir, `v1.3.0`
> geride kalmış bir sürüm olarak erişilebilir kalır.
>
> Betik de düzeltildi: `--taslak … --yayimla` artık yalnız yayımlıyor, paket
> yüklemiyor. Tuzağı betiğin kendi yönergesi kuruyordu.

Yeni bir sürüm gerektiğinde izlenecek yol **21.08.2026'da değişti**:
Zenodo'nun GitHub anahtarı artık kullanılmıyor. Sebep taşınmayla ortaya çıktı —
o anahtar kayıtları **depo başına** tutar ve bir depo için ilk release'te yeni
bir concept DOI üretir; var olan bir kayda bağlanamaz. Depo
`tarih1931/tarih1931.github.io` adına taşınınca (üstelik silinip yeniden
açılınca) Zenodo burayı yeni bir depo sayacak ve korpusun kimliğini
`10.5281/zenodo.21956339`'dan koparacaktı. Onun yerine arşiv nüshası yerelde
üretilip jetonla yükleniyor.

**Neden en yüksek getirili:** DOI, kaynağı akademik atıf zincirine sokar.
Atıf alan bir kaynak, atıf yapan yayınlar üzerinden defalarca taranır.

Künye dosyaları hazır: `.zenodo.json` (depo kökü), `metadata/datacite.xml`,
`CITATION.cff` — hepsi `build/05_metadata.py` tarafından üretilir.

**Adım 1 — Sürüm numarasını künyeye yazın**

`metadata/books.json` → `collection.version` alanını yeni numaraya çekin, sonra:

```bash
python build/run_all.py --from 05
```

Bu, künyeleri + siteyi + kavram dizinini + kalite raporunu yeniden üretir; OCR
adımlarına dokunmaz, `corrections/` altındaki düzeltmeler etkilenmez. Sonuçları
commit'leyip push edin — Pages iş akışı siteyi günceller.

**Adım 2 — Etiketi sürüm notlarını içeren commit'e koyun**

```bash
git tag v1.3.0 && git push origin v1.3.0
```

**Adım 3 — Zenodo'ya yeni sürüm olarak yükleyin**

```bash
python build/17_zenodo_yukle.py --korpus --yeni-surum 22035196 --etiket v1.3.0
```

`--yeni-surum` değeri **en son yayımlanmış sürümün** kayıt numarasıdır (`v1.2.0`
için 22035196); concept DOI korunur. Betik etiketin kaynak zip'ini `git archive`
ile üretir, künyeyi `metadata/zenodo.json`'dan yazar ve **taslak bırakır**.
`collection.version` ile etiket ayrışırsa durur. Gözden geçirdikten sonra:

```bash
python build/17_zenodo_yukle.py --taslak <taslak-id> --yayimla
```

Yayımlamak geri alınamaz: sürüm DOI'si kesinleşir, dosyalar bir daha değişmez.

**Adım 4 — GitHub release'i (isteğe bağlı)**

Release artık yalnız GitHub tarafında bir kayıttır: Zenodo'yu tetiklemez, sırası
önemli değildir. Sürüm notlarını görünür kılmak için açılabilir.

> **Concept DOI değişmez.** Künyelerde `metadata/books.json` →
> `collection.doi` yazılıdır ve daima en son sürüme çözümlenir; yeni sürümde
> künye dosyalarına dokunmak gerekmez.

> **Taramalar bu yolla Zenodo'ya gitmez.** `PDF/` `.gitignore` içindedir ve
> Zenodo yalnız git arşivini alır. Taramaları Zenodo'da da istiyorsanız elle
> ayrı bir kayıt açıp yükleyin ve iki kaydı `isSupplementTo` ile ilişkilendirin;
> aksi hâlde taramaların yeri Internet Archive'dır (§1.3).

> **Künyede yalnız Türk Tarihi Tetkik Cemiyeti yazılıdır.** `.zenodo.json`
> içindeki `creators` alanı 1931 eserinin sahibini gösterir; dijitalleştirmeyi
> yapan kişi hiçbir alanda görünmez. Atıf zincirinin sizi de göstermesini
> istiyorsanız `build/05_metadata.py` içindeki `zenodo_json()` fonksiyonuna
> kendinizi `contributors` olarak ekleyin — karar sizindir.

### 1.2b İncelemenin kendi Zenodo kaydı — ✅ yayında

İnceleme korpustan ayrı bir çalışmadır ve ayrı bir concept DOI taşır; ikisi
Zenodo'da `isSupplementTo` ile bağlıdır.

| | |
|---|---|
| **Concept DOI** (künyelerde kullanılan) | `10.5281/zenodo.21963507` |
| Kayıt | https://doi.org/10.5281/zenodo.21963507 |
| Son yayımlanan sürüm | `22059860` (22.08.2026) — DOI `10.5281/zenodo.22059860` |

DOI `metadata/books.json` → `review.doi` alanında durur; site, `llms.txt` ve
Vikikaynak düzenleme özetleri oradan okur.

21.08.2026'da iki sürüm açıldı: `22046650` metnin son hâlini getirdi (adres
taşınması sonrası bağlar, sadeleşen İngilizce sayfa), `22047835` ise yazar adını
**Anonim**'e çevirdi. İkincisi gerekliydi çünkü `22046650`'nin PDF kapağında
takma ad basılıydı ve yayımlanmış dosya değiştirilemiyor; künye alanı yerinde
düzeltilebildi, kapak düzeltilemedi.

22.08.2026'da `22059572` açıldı: Türkçe metin elden geçti (bulgular ve §4.2
yeniden yazıldı, §4 ile §5 başlıkları değişti, §7 sadeleşti), İngilizce sürüm
buna göre güncellendi ve künyedeki yazar **Prof. Dr. Muhammed Fatih Talu**
oldu. Ad artık belgenin başlığı altında da durur; PDF kapağı, Zenodo
`creators`, archive.org `creator`, site atıf kutusu, Scholar etiketleri ve
Wikidata P2093 tek alandan (`books.json` -> `review.author`) beslenir.

Aynı gün `22059727` (§4.2 üç paragraftan bire indi) ve `22059860` (§7'deki
imlâ notu tek paragrafa toplandı) açıldı; ikisinde de İngilizce sürüm
eşitlendi. Concept DOI artık `22059860`'a çözümlenir.

Metin değiştiğinde **daima yeni sürüm** açılır — yeni kayıt açmak ayrı bir
concept DOI üretir ve çalışmanın kimliğini ikiye böler:

```bash
python build/16_inceleme_yayin.py
python build/17_zenodo_yukle.py --yeni-surum <son sürümün kimliği>
```

Betik taslağı **yayımlamaz**; gözden geçirdikten sonra arayüzdeki Publish
düğmesiyle ya da `--taslak <kimlik> --yayimla` ile yayımlarsınız. Yayımlamak
geri alınamaz.

> **Açık taslak varsa `--yeni-surum` çalışmaz.** Zenodo bir concept altında
> aynı anda tek taslak tutar; yarım kalmış bir taslak varken yeni sürüm isteği
> `400 … files.enabled: Please remove all files first` ile döner. Açık taslağı
> `GET /api/deposit/depositions?status=draft` ile bulup `--taslak <kimlik>` ile
> sürdürün; yeni bir taslak açmayın.

> **Yayımlamadan önce siteyi push edin.** Künyedeki `isIdenticalTo`, sitedeki
> `inceleme.html` sayfasına işaret eder; site eskiyken yayımlarsanız DOI, kendi
> metniyle örtüşmeyen bir sayfayı gösterir.

### 1.3 Internet Archive — ✅ tamamlandı (16.08.2026)

- https://archive.org/details/tarih-1-1931-ttk — Tarih I.pdf
- https://archive.org/details/tarih-2-1931-ttk — Tarih II.pdf

Künyeler API ile doğrulandı; her iki öğe herkese açık. Ayrıntı:
[KANALLAR.md §2](KANALLAR.md).

Künye 19.08.2026'da tazelendi: açıklamada HuggingFace, Vikikaynak ve Wikidata
adresleri de var, ayrıca makine-okunabilir `external-identifier` alanına
`urn:doi:…` ve `urn:wikidata:…` yazıldı. Künye değişirse 106 MB'lık PDF'i
yeniden göndermeye gerek yoktur:

```bash
python build/15_archive.py --kunye
```

### 1.3b İncelemenin kendi arşiv öğesi — ✅ (19.08.2026)

https://archive.org/details/tarih-1931-islam-incelemesi — PDF (TR+EN), Markdown
ve bulgular. Korpus öğelerinden ayrıdır; künyesinde DOI ve CC0 vardır.

```bash
python build/15_archive.py --inceleme
```

### 1.4 Hugging Face Datasets — ✅ tamamlandı (19.08.2026)

https://huggingface.co/datasets/asayimusa19/tarih-ders-kitaplari-1931

Beş config: `sayfalar`, `dogrulanmis` (129 sayfa), `parcalar`, `inceleme`
(iddialar) ve `inceleme-metin` (incelemenin tam metni, TR + EN, bölüm bölüm).
Veri kümesi kartı klasörle birlikte üretilir ve 19.08.2026'dan beri DOI'li atıf
künyesini, incelemenin ayrı DOI'sini ve bütün yayın kanallarını sayar. Ayrıntı:
[KANALLAR.md §3](KANALLAR.md).

Korpus değiştikçe tazelemek tek komuttur — klasör depo ağacının dışına üretilir
ve yüklemeden önce içeriği denetlenir:

```bash
python build/13_huggingface.py --upload
```

> İstinsah 129 sayfaya çıktığında bu adım bir süre atlandı ve `dogrulanmis`
> config'i 79-93 aralığında kaldı; 19.08.2026'da tazelenip 79-184'e tamamlandı.
> Bölüm kapsamı her genişlediğinde bu komut yeniden çalıştırılmalıdır.

### 1.5 Wikidata — ✅ tamamlandı

| Cilt | Öğe | İfade | Kaynaklı |
|---|---|---:|---:|
| Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar | [Q141099467](https://www.wikidata.org/wiki/Q141099467) | 10 | 5 |
| Tarih II: Ortazamanlar | [Q141099470](https://www.wikidata.org/wiki/Q141099470) | 10 | 5 |

İki öğe P155/P156 ile birbirine bağlıdır. Girilen bütün ifadelerin gerekçesi ve
P356'nın neden bilerek boş bırakıldığı [KANALLAR.md §1](KANALLAR.md)'dedir.

**Kaynaklar eklendi (19.08.2026).** Künye taşıyan beş ifadeye (yazar, yayımcı,
yayım yeri, yayım tarihi, başlık) TTK tarama adresi `P854` ile kaynak olarak
yazıldı. QuickStatements beklenmedi — o araç otomatik onaylı hesap ister (4 gün
+ 50 düzenleme); kaynaklar doğrudan API ile eklendi:

```bash
python build/14_wikidata.py --yaz
```

Betik var olan kaynağı çoğaltmaz; yeniden çalıştırmak zararsızdır. Aynı adım
`Q374071` (Türk Tarih Kurumu) öğesine tr.wikisource eser sahibi sayfasını da
bağlar. `P31`, `P407`, `P6216` ve `P953` bilerek kaynaksızdır: ilk üçü tanım
gereği, sonuncusu kendi adresiyle sabittir.

**İncelemenin kendi öğesi de açıldı (19.08.2026):**
[Q141130317](https://www.wikidata.org/wiki/Q141130317) — DOI'si, yazarı, tarihi,
lisansı ve konusu (iki cilt + İslam) girili; iki cilt öğesi `P1343` ile buna
geri bağlı. Ayrıntı: [KANALLAR.md §1](KANALLAR.md).

**Neden:** Modeller künye bilgisini bilgi grafiğinden doğrular. Wikidata öğesi
olmayan bir kitabın künyesi model tarafından uydurulur.

### 1.6 Vikikaynak — ✅ tamamlandı (19.08.2026)

https://tr.wikisource.org

Bu adım diğerlerinin toplamından fazla iş görebilir (bkz. [STRATEJI.md](STRATEJI.md) §4),
çünkü Wikimedia metinleri neredeyse bütün büyük dil modellerinin eğitim verisinde
ağırlıklı olarak bulunur.

İstinsah edilen 129 sayfanın tamamı Sayfa: ad alanına girildi:

| | Sayfa | Durum |
|---|---:|---|
| Tarih I, basılı 1-11 | 11 | Başkasının işi — dokunulmadı |
| Tarih I, basılı 12-24 | 13 | Yüklendi, seviye 3 |
| Tarih II, basılı 79-93 | 14 | Yüklendi, seviye 3 |
| Tarih II, basılı 94-184 | 91 | Yüklendi, seviye 3 |

Son 91 sayfa 19.08.2026'da yazıldı; hata ve atlanan yok. Köy Çeşmesi'ne haber
verildi ve teamül teyit edildi
([VIKIKAYNAK-YOL-HARITASI.md](VIKIKAYNAK-YOL-HARITASI.md) §3, Adım 2).

Ana ad alanındaki dört sayfa da kuruldu:

- [Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar](https://tr.wikisource.org/wiki/Tarih_I:_Tarihtenevelki_Zamanlar_ve_Eski_Zamanlar) → `/Beşer Tarihine Giriş`
- [Tarih II: Ortazamanlar](https://tr.wikisource.org/wiki/Tarih_II:_Ortazamanlar) → `/İslâm Tarihi`

Bölüm sayfaları `<pages>` aralığını `secim/index.json` + Commons ofsetinden
türetir; bölüm genişlerse betik doğru aralığı kendiliğinden verir.

```bash
python build/12_vikikaynak.py        # taslakları üret
python build/18_vikikaynak_yukle.py  # Sayfa: ad alanı — ne yazılacağını göster
python build/18_vikikaynak_yukle.py --yaz
python build/19_vikikaynak_bolum.py --yaz   # cilt + bölüm sayfaları (18'den SONRA)
```

Elle yapıştırmak isterseniz liste hazır:
[`vikikaynak/YUKLEME.md`](../vikikaynak/YUKLEME.md).

> **Eser sahibi sayfası da açıldı (19.08.2026).**
> [`Kişi:Türk Tarihi Tetkik Cemiyeti`](https://tr.wikisource.org/wiki/Kişi:Türk_Tarihi_Tetkik_Cemiyeti)
> `{{Kişi}}` şablonuyla kuruldu, `vikipedi_bağlantısı=Türk Tarih Kurumu` verildi
> ve `Q374071` öğesine tr.wikisource bağlantısı eklendi; dört sayfadaki kırmızı
> bağlantı kapandı. Sayfayı `19_vikikaynak_bolum.py` üretir, ayrı bir adım
> değildir.

---

## 2. OCR düzeltmesi — kapandı

Fiilî çalışma kapsamı `secim/` altındaki iki bölümdü ve **ikisi de tamamlandı**:

| Bölüm | Cilt | Basılı sayfa | Gövde sayfası |
|---|---|---|---|
| Beşer Tarihine Giriş | Tarih I | 1-24 | 24 |
| İslâm Tarihi | Tarih II | 79-184 | 105 |

Toplam 129 sayfa, taranmış aslıyla sayfa sayfa karşılaştırılmıştır; bu kapsamda
düzeltilmemiş sayfa kalmamıştır. **Kapsamın genişletilmesi planlanmamaktadır.**
Korpusun geri kalan ~825 sayfası ham OCR olarak kalacaktır.

Yeni bir bölüm düzeltilmek istenirse yol açıktır: `10_secim.py` içindeki aralık
genişletilir, `11_birlesik.py` tablosuna yeni sayfa sınırı kararları yazılır ve
hat `03b → 04 → 10 → 11 → 05 → 06 → 06b → 07 → 08` sırasıyla çalıştırılır.
`docs/KALITE-RAPORU.md` her cildin **en bozuk 10 sayfasını** listeler; oradan
başlamak en çok kazancı verir.

Düzeltme için taramayı metnin yanında gösteren yerel arayüz:

```bash
python build/duzelt.py
```

Tarayıcıda `http://localhost:8800` açılır: solda taranmış sayfa, sağda
düzeltilebilir metin. <kbd>Ctrl+S</kbd> kaydeder, <kbd>Alt</kbd>+<kbd>←</kbd>/<kbd>→</kbd>
sayfa değiştirir. Kaydedilen metin `corrections/<kitap>/<page_id>.txt` dosyasına
yazılır ve **yeniden üretimde kaybolmaz**.

Düzeltmeleri korpusa işlemek için:

```bash
python build/run_all.py --from 03b --skip-ocr
```

`secim/` aralığı da değiştiyse `run_all` tek başına yetmez: `10_secim.py` ile
`11_birlesik.py` 04 ile 05 arasına elle sokulmalıdır, çünkü `05_metadata` ve
`06_web` `secim/` çıktılarını okur.

Ayrıntı: [corrections/README.md](../corrections/README.md). Düzeltmenin altındaki
OCR metni değişirse hat uyarı basar; sessizce yanlış metin üretmez.

**Ölçüt:** basılı sayfada ne yazıyorsa odur. 1931 imlası korunur, günümüz
imlasına çevrilmez.

---

## 3. Görünürlük

- **Google Search Console**'a siteyi ekleyip `sitemap.xml`'i gönderin.
- Sitedeki `robots.txt` tüm büyük yapay zekâ tarayıcılarına (GPTBot, ClaudeBot,
  Google-Extended, PerplexityBot, CCBot …) açıkça izin verir — bilinçli tercihtir.
- `llms.txt` ve `llms-full.txt` hazır; dil modellerine yönelik içerik haritasıdır.
- İlgili **Vikipedi maddelerine** (Türk Tarih Tezi, Tarih ders kitapları, Türk
  Tarih Kurumu) kaynak olarak ekleyin. Vikipedi'den gelen bağlantılar, taranma
  sıklığını belirgin biçimde artırır.

---

## 4. Yapay zekâ ajanlarına doğrudan açmak (isteğe bağlı)

`api/mcp_server.py` hazır. Claude Desktop veya Claude Code'a eklemek için:

```bash
pip install "mcp[cli]"
```

Sonra yapılandırmaya şunu ekleyin:

```json
{
  "mcpServers": {
    "tarih-1931": {
      "command": "python",
      "args": ["D:/Talu/1931/api/mcp_server.py"]
    }
  }
}
```

Yol, deponun o bilgisayardaki **mutlak** konumudur; projeyi taşıdığınızda
güncelleyin ([TASINMA.md](TASINMA.md)).

Bundan sonra modele doğrudan "Tarih II, s. 156'da ne yazıyor?" diye
sorabilirsiniz; metni tahmin etmez, gerçekten okur.

REST API için: `python api/server.py --port 8000`

---

## 5. Kararlar

1. **Lisans — karar verildi: CC0 1.0.** Türetilmiş veri kamuya bırakılmıştır.
   Tam metin `LICENSE` dosyasındadır; künye alanları `metadata/books.json`
   içindeki `derived_dataset_license` alanından üretilir.
2. **İsim — karar verildi:** depo `tarih1931/tarih1931.github.io`,
   site https://tarih1931.github.io. Eski ad `tarih-ders-kitaplari-1931`
   21.08.2026'da bırakıldı; yalnız HuggingFace veri kümesi onu sürdürüyor.
3. **Sunum dili — açık.** Site şu an tamamen Türkçe. İngilizce bir sürüm,
   uluslararası akademik görünürlüğü ve taranma ihtimalini belirgin biçimde
   artırır. Karar verilmedi.
