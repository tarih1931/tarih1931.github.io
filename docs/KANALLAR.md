# Yayın kanalları — girilecek değerler

> **Adres taşındı — 2026-08-21.** Site artık `https://tarih1931.github.io`
> adresinde yayınlanıyor. Aşağıdaki değerler **yeni** adresle yazılmıştır.
> Önceki adres aynı gün kapandı: eski depo silindi. Yaşayan bütün kayıtlar — Zenodo künyeleri, Wikidata
> P953 ifadeleri, Internet Archive öğeleri ve HuggingFace veri kümesi — yeni
> adrese çevrildi; elle güncellenecek bir değer kalmadı.


Hesap gerektiren adımların hazır künyeleri. Her alanın değeri
`metadata/books.json` ile aynıdır; uydurma değer yoktur.

Sıra ve genel durum: [YAPILACAKLAR.md](YAPILACAKLAR.md).

---

## 1. Wikidata (§1.5)

**Neden:** Modeller künye bilgisini bilgi grafiğinden doğrular. Wikidata öğesi
olmayan bir kitabın künyesi model tarafından uydurulur.

**Öğeler oluşturuldu:** [Q141099467](https://www.wikidata.org/wiki/Q141099467)
(Tarih I) ve [Q141099470](https://www.wikidata.org/wiki/Q141099470) (Tarih II) —
etiket ve açıklamalar tr/en olarak girilmiş durumda.

**✅ İfadeler girildi (16.08.2026).** Her iki öğede de 10 ifade var ve API ile
tek tek doğrulandı: örneği, yazar, yayımcı, yayın yeri, yayın tarihi, dil,
telif durumu, başlık, tam metin URL'si ve ciltler arası sıra.

**✅ Kaynaklar da eklendi (19.08.2026).** Künye taşıyan beş ifadeye (P50 yazar,
P123 yayımcı, P291 yayım yeri, P577 yayım tarihi, P1476 başlık) TTK tarama
adresi `P854` ile kaynak yazıldı; iki öğede toplam 10 kaynak. API ile
doğrulandı.

Yol QuickStatements değildi: o araç **otomatik onaylı** hesap ister (Wikidata'da
50 düzenleme + 4 gün) ve hesapta 29 düzenleme vardı. MediaWiki API'si bu şartı
aramaz, dolayısıyla kaynaklar doğrudan yazıldı:

```bash
python build/14_wikidata.py --yaz
```

Betik var olan kaynağı **çoğaltmaz** — ikinci çalıştırma "kaynak zaten var" der
ve hiçbir düzenleme yapmaz. Aynı adım `Q374071` (Türk Tarih Kurumu) öğesine
tr.wikisource'taki [eser sahibi
sayfasını](https://tr.wikisource.org/wiki/Kişi:Türk_Tarihi_Tetkik_Cemiyeti)
`trwikisource` bağlantısı olarak ekler.

Kimlik, Vikikaynak yüklemesiyle aynı dosyadan okunur (`~/.wikisource-bot`): bot
parolası tek bir vikiye değil hesaba bağlıdır, Wikidata'da da geçerlidir.

**İncelemenin kendi öğesi (19.08.2026):**
[Q141130317](https://www.wikidata.org/wiki/Q141130317) — rapor (`Q10870555`),
DOI `10.5281/ZENODO.21963507`, yazar adı, yayın tarihi, iki dil, yayımcı
Zenodo, lisans CC0, konu olarak iki cilt ve İslam, tam metin adresleri (TR+EN).
Künye taşıyan beş ifade Zenodo kaydına kaynaklıdır. İki cilt öğesi de
`P1343` (kaynakta anlatılan) ile incelemeye geri bağlıdır.

```bash
python build/14_wikidata.py --inceleme
```

Betik önce DOI ile arar; öğe varsa dokunmaz. **DOI'nin burada yazılması
çelişki değildir:** DOI türetilmiş çalışmaya aittir, incelemenin kendisi de
türetilmiş bir çalışmadır — yazılmadığı yer 1931 basımı kitapların öğeleridir.

`P31`, `P407`, `P6216` ve `P953` bilerek kaynaksız bırakıldı: ilki tür, ikincisi
dil, üçüncüsü telif durumu — tanım gereğidir; sonuncusu zaten kendi adresini
gösterir.

Elle yapmak isterseniz `python build/14_wikidata.py` yalnız
`wikidata/quickstatements.txt` dosyasını yazar (20 ifade);
https://quickstatements.toolforge.org → **Import V1 commands** → yapıştır →
**Run**. Aynı sonucu verir, hesap otomatik onaylı olduğunda kullanılabilir.

> **P356 (DOI) bilerek yazılmaz.** DOI, iki cildin *türetilmiş veri kümesine*
> aittir, tek bir cildin kendisine değil. Kitap öğesine DOI yazmak yanlış bir
> kimlik iddiası olurdu. Bu belgenin önceki sürümü "DOI'yi ekleyin" diyordu,
> yanlıştı.

Aşağıdaki Q ve P numaralarının tamamı Wikidata'da tek tek doğrulanmıştır.

### Ortak ifadeler (her iki öğe)

| Özellik | Değer | Q no |
|---|---|---|
| örneği (P31) | textbook | `Q83790` |
| yazar (P50) | Turkish Historical Society | `Q374071` |
| yayımcı (P123) | Ministry of National Education | `Q1359675` |
| yayım yeri (P291) | Istanbul | `Q406` |
| yayım tarihi (P577) | 1931 | — |
| eser dili (P407) | Turkish | `Q256` |
| telif durumu (P6216) | public domain | `Q19652` |

> **P50 hakkında.** 1931'deki ad *Türk Tarihi Tetkik Cemiyeti*'dir; Wikidata'da
> ayrı öğesi yoktur. `Q374071` aynı kurumun bugünkü hâlidir (Türk Tarih Kurumu)
> ve doğru bağlantıdır.
>
> **P6216 hakkında.** Kamu malı olan *kaynak eserdir*. CC0 (`Q6938433`) türetilmiş
> veriye aittir; onu bu öğelere değil, veri kümesi kaydına yazınız.

### Öğe 1 — Tarih I

```
Etiket (tr)    Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar
Açıklama (tr)  Türkiye'de 1931-1941 arasında okutulan resmî lise tarih ders kitabı
Açıklama (en)  official history textbook used in Turkish secondary schools, 1931-1941
P1476 (başlık) Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar   (tr)
P953  (tam eser burada) https://tarih1931.github.io/tarih-1-1931/
```

### Öğe 2 — Tarih II

```
Etiket (tr)    Tarih II: Ortazamanlar
Açıklama (tr)  Türkiye'de 1931-1941 arasında okutulan resmî lise tarih ders kitabı
Açıklama (en)  official history textbook used in Turkish secondary schools, 1931-1941
P1476 (başlık) Tarih II: Ortazamanlar   (tr)
P953  (tam eser burada) https://tarih1931.github.io/tarih-2-1931/
```

Her iki öğede kaynak (referans) olarak TTK Kütüphanesi kaydını verin:
`https://kutuphane.ttk.gov.tr/` — yer no. `A/4789`.

---

## 2. Internet Archive (§1.3)

**✅ Yayında (16.08.2026):**

- https://archive.org/details/tarih-1-1931-ttk — Tarih I.pdf, 105,9 MB
- https://archive.org/details/tarih-2-1931-ttk — Tarih II.pdf, 106,5 MB

Künyeler API ile doğrulandı; her iki öğe herkese açık. Arşiv, yükleme sonrası
kendi türevlerini (tam metin OCR, çevrimiçi okuyucu, küçük resimler) saatler
içinde üretir — tam metin araması o türevden gelir.

**Künye tazelendi (19.08.2026).** Açıklamada artık site ve DOI'nin yanında
HuggingFace, Vikikaynak ve Wikidata adresleri de var; ayrıca makine-okunabilir
`external-identifier` alanına `urn:doi:10.5281/zenodo.21956339` ve öğenin
`urn:wikidata:Q…` numarası yazıldı. Künye değişirse 106 MB'lık PDF'i yeniden
göndermek gerekmez:

```bash
python build/15_archive.py --kunye
```

**İncelemenin kendi arşiv öğesi (19.08.2026):**
https://archive.org/details/tarih-1931-islam-incelemesi — Türkçe ve İngilizce
PDF, aynı ikisinin Markdown'ı ve `bulgular.jsonl`. Korpustan ayrı bir öğedir:
aynı öğeye konsaydı arşivin tam metin araması onu 106 MB'lık taramanın eki
sayardı. Künyede `urn:doi:10.5281/zenodo.21963507` ve CC0 vardır.

```bash
python build/15_archive.py --inceleme
```

Yeniden yüklemek ya da güncellemek gerekirse aşağıdaki yol geçerlidir.

Bir kez, **kendi terminalinizde** (parola sorar):

```bash
ia configure
```

Sonra yükleme tek komuttur:

```bash
python build/15_archive.py --upload
```

Betik iki ayrı öğe oluşturur — `tarih-1-1931-ttk` ve `tarih-2-1931-ttk`.
Her cilt için ayrı öğe, tek öğeye iki PDF koymaktan iyidir: arşivin tam metin
araması öğe düzeyinde çalışır. Künye alanları `metadata/books.json`'dan üretilir.

> **Beyaz liste koruması.** Betik `PDF/` klasörünü hiç taramaz; yalnız
> `books.json` içindeki `source_pdf` alanlarında adı geçen iki 1931 taramasını
> yükler. Klasördeki telifli modern kitaplara erişmesi yapısal olarak mümkün
> değildir — HuggingFace'te bütün klasörün yüklendiği kaza bunu gerektirdi.

> **Lisans işareti CC0 değil, Public Domain Mark.** CC0 bir hak devri
> beyanıdır; 1931 eseri ise koruma süresi dolduğu için zaten kamu malıdır.
> Doğru işaret `publicdomain/mark/1.0`. Türetilmiş veri kümesinin CC0 olduğu
> açıklamada ayrıca belirtilir. (Bu belgenin önceki sürümü CC0 diyordu.)

Elle yüklemek isterseniz: https://archive.org/upload — künye değerleri aşağıda.

### Tarih I

```
title        Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar
creator      Türk Tarihi Tetkik Cemiyeti
publisher    Maarif Vekâleti — Devlet Matbaası
date         1931
language     Turkish
subject      Tarih — Ders kitapları — Türkiye; Türk Tarih Tezi; Eğitim — Türkiye — 1931-1941
licenseurl   https://creativecommons.org/publicdomain/zero/1.0/
source       https://kutuphane.ttk.gov.tr/resource?itemId=267298&dkymId=6415
```

`description` alanına:

> Türk Tarihi Tetkik Cemiyeti tarafından hazırlanıp Maarif Vekâleti emriyle
> basılan ve 1931-1941 arasında Türkiye'de lise ve orta mekteplerde resmî ders
> kitabı olarak okutulan Tarih serisinin birinci cildi. Maarif Vekâleti Millî
> Talim ve Terbiye Dairesinin 2/8/1931 tarih ve 1869 numaralı emrile 30 000
> nüsha tab'edilmiştir. 7 renkli tablo — 22 harita — 136 resim.
> Makine-okunabilir tam metin ve sayfa künyeleri:
> https://tarih1931.github.io

### Tarih II

```
title        Tarih II: Ortazamanlar
creator      Türk Tarihi Tetkik Cemiyeti
publisher    Maarif Vekâleti — Devlet Matbaası
date         1931
language     Turkish
subject      Tarih — Ders kitapları — Türkiye; Türk Tarih Tezi; Eğitim — Türkiye — 1931-1941
licenseurl   https://creativecommons.org/publicdomain/zero/1.0/
source       https://kutuphane.ttk.gov.tr/resource?itemId=267295&dkymId=6416
```

`description` alanına:

> …Tarih serisinin ikinci cildi. Maarif Vekâleti Millî Talim ve Terbiye
> Dairesinin 28/11/1931 tarih ve 2847 numaralı emrile 25 000 nüsha
> tab'edilmiştir. 8 renkli tablo — 46 harita — 113 resim.
> Makine-okunabilir tam metin ve sayfa künyeleri:
> https://tarih1931.github.io

> **licenseurl hakkında.** CC0 burada *taramaya eklenen* katkı içindir; kaynak
> eser zaten kamu malıdır. Arşivin formunda "public domain" seçeneği varsa onu
> işaretlemek daha doğrudur.

---

## 3. HuggingFace (§1.4)

**✅ Yayında:** https://huggingface.co/datasets/asayimusa19/tarih-ders-kitaplari-1931

Güncellemek için tek komut yeter:

```bash
python build/13_huggingface.py --upload
```

Klasör **depo ağacının dışına** (`<depo>/../<depo adı>-hf`) üretilir ve
yüklemeden önce içeriği denetlenir; beklenenden başka dosya varsa betik durur.

**İncelemenin tam metni de veri kümesinde (19.08.2026).** `inceleme` config'i
yalnız iddiaları taşıyordu; gerekçe, yöntem ve tartışma yoktu. `inceleme-metin`
config'i tam metni bölüm bölüm verir (TR + EN, 9'ar bölüm): bölüm başlığı, gövde,
dil, DOI ve kaynak sayfanın adresi.

Veri kümesi kartı 19.08.2026'da genişletildi: DOI'li atıf künyesi, incelemenin
ayrı DOI'si ve bütün yayın kanalları (site, depo, Zenodo, Internet Archive,
Vikikaynak, Wikidata) kartta sayılır. Adresler `metadata/books.json` →
`channels` alanından gelir; kartta elle yazılmış adres yoktur.

> **Bu neden böyle.** Klasör bir kez depo kökünde üretilmişti ve yükleme
> sırasında bütün çalışma dizini gönderildi — `PDF/` altındaki **telifli modern
> kitaplar** dahil. Depo silinip yeniden kuruldu. Ayrı dizin, o kazanın
> tekrarını fizikî olarak imkânsız kılar.

Elle yüklemek isterseniz: https://huggingface.co/new-dataset → klasörün
**içeriğini** yükleyin (klasörün kendisini değil).

Düzen bilinçlidir — dört ayrı config:

| Config | Ne | Metin |
|---|---|---|
| `sayfalar` | İki cildin tamamı | Düzeltilmemiş OCR |
| `dogrulanmis` | İki bölüm, 129 sayfa | **Elle düzeltilmiş** |
| `parcalar` | RAG parçaları | Düzeltilmemiş OCR |
| `inceleme` | İncelemenin iddiaları | — |

Doğrulanmış alt korpus ham OCR ile aynı havuza konmaz: aksi hâlde 954 sayfalık
düzeltilmemiş metin, 129 sayfalık doğrulanmış metni görünmez kılar.

Veri kümesi kartı (`README.md`) klasörle birlikte üretilir; ayrıca yazmanız
gereken bir şey yoktur.

---

## 4. Görünürlük (§3)

- **Google Search Console** → siteyi ekleyin, `sitemap.xml` gönderin.
- **Vikipedi**: ilgili maddelere (Türk Tarih Tezi, Türk Tarih Kurumu, Tarih ders
  kitapları) kaynak olarak **yalnız birincil metni ve taramaları** ekleyin.

> İncelemeyi Vikipedi'ye eklemeyin: özgün araştırma sayılır, geri alınır ve geri
> alma geçmişi kalıcı olumsuz sinyaldir. İnceleme kendi adresinde ve DOI'siyle
> durmalıdır.
