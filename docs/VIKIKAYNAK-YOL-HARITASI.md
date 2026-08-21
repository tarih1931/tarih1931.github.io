# Vikikaynak yol haritası

Düzeltilmiş 129 sayfanın Türkçe Vikikaynak'a aktarılması.

> **Baştaki varsayım yanlış çıktı.** "Taramaları Commons'a yükleyip Dizin
> kuracağız, ama 1 Ocak 2027'yi beklemek gerekebilir" diye planlamıştık.
> Araştırma bunun gereksiz olduğunu gösterdi: **her iki kitabın taraması zaten
> Commons'ta ve Dizin sayfaları zaten kurulu.** Yükleme yapılmayacak; yapılacak
> iş mevcut dizine bağlı sayfaları doldurmak.

---

## 0. Telif meselesi — kapandı

| | |
|---|---|
| `Tarih I Tarihtenevelki Zamanlar ve Eski Zamanlar.pdf` | Commons'ta, 513 sayfa, `{{PD-Turkey}}` |
| `Tarih II Ortazamanlar.pdf` | Commons'ta, 539 sayfa, `{{PD-Turkey}}` |
| `Dizin:Tarih I …pdf` | tr.wikisource'ta kurulu |
| `Dizin:Tarih II Ortazamanlar.pdf` | tr.wikisource'ta kurulu |

Commons topluluğu bu dosyaları zaten kabul etmiş durumda. Siz yeni bir dosya
yüklemeyeceğiniz için URAA sorusu sizin kararınız olmaktan çıkıyor.

Araştırmanın bulduğu ek delil, [HAKLAR.md §6](HAKLAR.md)'daki karşı argümanı
güçlendiriyor: **FSEK'in 1951 tarihli özgün metninde tüzel kişi eserleri için
süre 20 yıldı**, 70 yıl 1995 değişikliğiyle geldi. Buna göre eser 1 Ocak
1996'da Türkiye'de çoktan kamu malıydı, dolayısıyla URAA hiç tetiklenmedi.
Kesin değil — ama beklemeye gerek olmadığı yönündeki okuma daha sağlam.

*Kalan risk:* Commons dosyaları teorik olarak silinmeye aday gösterilebilir.
Bu sizin eyleminizden doğmuyor ve olursa Vikikaynak metni de etkilenir. Risk
1 Ocak 2027'de tamamen sıfırlanır.

---

## 1. Sayfa eşlemesi

Commons'taki tarama bizim kaynak PDF'imizden **farklı**: tek sayfa taraması,
farklı ön bölüm. Eşleme ampirik olarak çözüldü ve üç noktada doğrulandı:

```
Commons sayfası = basılı sayfa + ofset

Tarih I  → ofset 33      Tarih II → ofset 22
```

| Doğrulama | Commons | Basılı | İlk satır |
|---|---|---|---|
| Tarih I | 34 | 1 | "HALİN MAZİ İLE ALÂKASI" |
| Tarih I | 44 | 11 | "Bu devirde insanlar, iptidaî ve sefilâne…" |
| Tarih II | 106 | 84 | "İslâmiyetten evel Arabistanda intişar eden…" |
| Tarih II | 115 | 93 | "MUHAMMET MEDİNEDE" |

---

## 2. İşin gerçek büyüklüğü

129 sayfanın hepsi yazılmadı; **19.08.2026 itibarıyla iş bitmiştir**:

| Durum | Sayfa | Sonuç |
|---|---|---|
| **Yüklendi** (Tarih I 12-24, Tarih II 79-93) | 27 | Seviye 3 "İstinsah edildi" |
| **Yüklendi** (Tarih II, basılı 94-184) | 91 | Seviye 3 — 19.08.2026'da yazıldı |
| **Zaten istinsah edilmiş** (Tarih I, basılı 1-11) | 11 | **Dokunulmadı** |
| Levha (metin yok) | 16 | Atlandı |

Son 91 sayfa `18_vikikaynak_yukle.py --yaz` ile yazıldı: hata yok, atlanan yok,
27 sayfa zaten aynı olduğu için dokunulmadı. Liste ve her sayfanın adresi
[vikikaynak/YUKLEME.md](../vikikaynak/YUKLEME.md) dosyasındadır;
`python build/12_vikikaynak.py` ile üretilir.

**Tarih I'in ilk 11 sayfasına neden dokunmuyoruz.** Bu sayfaları *2004onuralp*
adlı bir Vikikaynak kullanıcısı 24.05.2025'te istinsah etmiş. Metnimizle
karşılaştırdım: **%99,3 aynı.** Farklar bizim lehimize bile değil — orada
"iptidaî" yazıyor, bizde "iptidai"; şapkalı biçim asla daha sadık. Başkasının
tamamlanmış işini kendi sürümümüzle değiştirmek hem gereksiz hem topluluk
teamülüne aykırı olur.

> **Durum 19.08.2026'da API ile yeniden ölçüldü** (`list=allpages`, ad alanı 250).
> Tarih I: dizin 34-57'nin tamamı dolu — 34-44 *2004onuralp*'in, 45-57 bu
> depodan yüklenmiş ve seviye 3. Tarih II: dizin 101-115 dolu ve örneklenen
> sayfaların hepsi seviye 3; **116 ve sonrası hiç yok.** Yani 84-93'teki eski
> ham OCR sorunu kapandı, geriye yalnız boş sayfalara yazmak kaldı.

Kapanan sorunun kaydı: Tarih II dizin 106'da anonim bir IP'nin bıraktığı seviye 1
metin şöyleydi —

```
İ slamiyetten evel Arabista ncia intişar eden … muşrı"klı"k,, ta b ı" r e d er.
```

Yerine düzeltilmiş metin yazıldı.

---

## 3. Adım adım

### Adım 1 — Hesap (10 dk)

https://tr.wikisource.org → hesap açın. Sayfa oluşturmak için bekleme süresi
yok; dosya yüklemek için 4 gün gerekiyor ama **dosya yüklemeyeceksiniz**.

### Adım 2 — Topluluğa haber verin — YAPILDI (16.08.2026)

Not, Köy Çeşmesi'ne bırakıldı ve 18.08.2026'da iki düzeltme ekiyle
tamamlandı: https://tr.wikisource.org/wiki/Vikikaynak:Köy_çeşmesi

Gönderilen metin `vikikaynak/KOY-CESMESI-MESAJI.txt` dosyasındadır ve
değiştirilmemelidir. Aşağıdaki alıntı o gün gönderilen hâlidir; **basılı
94-184'ü kapsamaz.** O aralık için bildirim yapılacaksa ayrı bir not yazılmalı.

> **Başlık:** Tarih I ve Tarih II (1931) — iki bölümün istinsahı
>
> Merhaba. Tarih I'in "Beşer Tarihine Giriş" (basılı s. 1-24) ve Tarih II'nin
> "İslâm Tarihi" (basılı s. 79-93) bölümlerini, taramayla karşılaştırarak sayfa
> sayfa düzelttim ve Sayfa: ad alanına girmek istiyorum.
>
> İki hususu sormak isterim:
>
> 1. Tarih I'in basılı 1-11 sayfaları (Dizin sayfa 34-44) Kibele tarafından
>    zaten istinsah edilmiş. Benim metnimle %99 örtüşüyor; **dokunmayı
>    düşünmüyorum**, yalnız 12-24 arasını ekleyeceğim. Doğru yaklaşım bu mudur?
> 2. Tarih II'nin basılı 84-93 sayfalarında (Dizin 106-115) anonim katkıyla
>    girilmiş, kalite seviyesi 1 olan ham OCR var. Bunların üzerine düzeltilmiş
>    metni yazmam uygun mudur, yoksa izlenmesi gereken başka bir usul var mı?
>
> Metin CC0 ile yayımlanmış bir çalışmadan geliyor; 1931 imlası korunmuştur.
>
> Teşekkürler.

Cevap alındı: *Satirdan kahraman* teamülü şöyle özetledi — "Burada yapacağımız
tek şey istinsah… ana metinde ne görünüyorsa yazım yanlışları dâhil olduğu gibi
geçiriyoruz." Bu, bizim ölçütümüzle birebir örtüşür (basımın kendi dizgi
hataları düzeltilmez, `{{sic}}` ile işaretlenir). 27 sayfa bu adımdan sora
yüklendi ve geri alınmadı.

### Adım 3 — Sayfaları girin — ✅ tamamlandı (19.08.2026)

129 sayfanın hepsi Sayfa: ad alanındadır. Betikle:

```bash
python build/18_vikikaynak_yukle.py         # ne yazılacağını göster
python build/18_vikikaynak_yukle.py --yaz   # bot parolasıyla yaz
```

Betik sayfa başına 10 sn bekler (yeni hesapların düzenleme hızı sınırı dakikada
~8'dir); 91 sayfa ~20 dakika sürdü. Daha önce yazılmış sayfaya dokunmaz, başkası
düzenlemişse `--zorla` verilmedikçe atlar.

Aşağıdaki elle tarif, ileride tek tük sayfa girilirse diye bırakılmıştır.
Yapılacak listesi: [`vikikaynak/YUKLEME.md`](../vikikaynak/YUKLEME.md)

Her satırda Vikikaynak sayfa adresi ve yapıştırılacak dosya var. Akış:

1. Listedeki bağlantıyı açın → "Kaynağı değiştir"
2. `vikikaynak/<bölüm>/<numara>.txt` dosyasının **tamamını** yapıştırın
3. Sağdaki kalite kutusunda **İstinsah edildi**'yi işaretleyin
4. Düzenleme özeti yazın:
   - Yeni sayfa için: `Taramayla karşılaştırılarak istinsah edildi`
   - Üzerine yazarken: `Ham OCR düzeltildi; taramayla sayfa sayfa karşılaştırıldı`

Dosyalar üstbilgiyi (`{{rh}}`) ve sayfa sonunda bölünen kelimeler için
`{{ysb}}`/`{{yss}}` çiftlerini içeriyor — elle bir şey eklemenize gerek yok.
Basılı sayfa numarası gövdeye yazılmadı; Vikikaynak kuralı bunu yasaklıyor.

### Adım 4 — Dizin künyesini doldurun — ✅ tamamlandı (16.08.2026)

Her iki dizin de dolduruldu ve API ile alan alan doğrulandı: künye alanlarının
tamamı doğru, Tarih II'deki `Year=1930` hatası 1931 olarak düzeltildi,
`Source=_empty_` → `pdf` yapıldı, `Progress=İE` korundu.

Aşağıdaki tarif, ileride başka bir cilt eklenirse diye bırakılmıştır.

> **Dizin sayfası ham vikimetin olarak düzenlenmez.** "Değiştir"e bastığınızda
> Türkçe etiketli bir **form** açılır (Tür, Eser ismi, Dil, Cilt, Yazar…) ve
> alanlar tek tek doldurulur. Aşağıdaki blok, formu doldurduğunuzda arka planda
> oluşacak sonucu gösterir; kutulara yapıştırılacak metin **alan alan**
> aşağıdaki tablodadır.
>
> **"İstinsah edildi" kutusu bu sayfada yoktur** — o, Sayfa: ad alanındaki tek
> tek sayfalarda bulunur (Adım 3). Dizin sayfasındaki karşılığı **"İlerleme"**
> alanıdır ve bütün cildi anlatır.

| Form alanı | Tarih I | Tarih II |
|---|---|---|
| Tür | `book` | `book` |
| Eser ismi | `Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar` | `Tarih II: Ortazamanlar` |
| Dil | `tr` | `tr` |
| Cilt | `I` | `II` |
| Yazar | `Türk Tarihi Tetkik Cemiyeti` | `Türk Tarihi Tetkik Cemiyeti` |
| Yayıncı | `Maarif Vekâleti — Devlet Matbaası` | `Maarif Vekâleti — Devlet Matbaası` |
| Basım Yeri | `İstanbul` | `İstanbul` |
| Basım yılı | `1931` | `1931` ← **1930 yazıyor, düzeltilecek** |
| Tarama biçimi | `pdf` (zaten doğru) | `pdf` ← `_empty_` yazıyor |
| Kapak resmi | `1` (dokunmayın) | `1` (dokunmayın) |
| İlerleme | `İE` (dokunmayın) | `İE` (dokunmayın) |
| Sayfalar | `<pagelist />` (dokunmayın) | `<pagelist />` (dokunmayın) |
| İçindekiler | boş bırakın | boş bırakın |

Kalan alanlar (Çevirmen, Editör, Resimleyen, Kurum, Sıralama harfi, ISBN, OCLC,
Tarama çözünürlüğü, Css, Başlık, Dipnot) boş kalır.

Formu kaydettiğinizde sayfa şu hâle gelir:

**Dizin:Tarih I Tarihtenevelki Zamanlar ve Eski Zamanlar.pdf**

```
{{:MediaWiki:Proofreadpage_index_template
|Type=book
|Title=Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar
|Language=tr
|Volume=I
|Author=Türk Tarihi Tetkik Cemiyeti
|Translator=
|Editor=
|Illustrator=
|School=
|Publisher=Maarif Vekâleti — Devlet Matbaası
|Address=İstanbul
|Year=1931
|Key=
|ISBN=
|OCLC=
|Source=pdf
|Image=1
|Progress=İE
|Pages=<pagelist />
|Volumes=
|Remarks=Liseler için resmî tarih ders kitabı. Maarif Vekâleti Millî Talim ve Terbiye Dairesinin 2/8/1931 tarih ve 1869 numaralı emrile 30 000 nüsha tab'edilmiştir.
|Width=
|Css=
|Header=
|Footer=
}}
```

**Dizin:Tarih II Ortazamanlar.pdf**

```
{{:MediaWiki:Proofreadpage_index_template
|Type=book
|Title=Tarih II: Ortazamanlar
|Language=tr
|Volume=II
|Author=Türk Tarihi Tetkik Cemiyeti
|Translator=
|Editor=
|Illustrator=
|School=
|Publisher=Maarif Vekâleti — Devlet Matbaası
|Address=İstanbul
|Year=1931
|Key=
|ISBN=
|OCLC=
|Source=pdf
|Image=1
|Progress=İE
|Pages=<pagelist />
|Volumes=
|Remarks=Liseler için resmî tarih ders kitabı. Maarif Vekâleti Millî Talim ve Terbiye Dairesinin 28/11/1931 tarih ve 2847 numaralı emrile 25 000 nüsha tab'edilmiştir.
|Width=
|Css=
|Header=
|Footer=
}}
```

Düzenleme özeti: `künye dolduruldu (kaynak: kitabın künye sayfası)` — Tarih II
için: `künye dolduruldu; basım yılı 1930 -> 1931 (künye sayfasındaki basım emri 28/11/1931 tarihli)`

**Üç dikkat noktası:**

1. **`Year=1930` hatası yalnız Tarih II'dedir** ve canlıda doğrulanmıştır.
   Künye sayfasındaki basım emri 28/11/1931 tarihlidir; 1931 doğrudur.
2. **`Progress=İE` olarak bırakılır.** Bu vikideki kodlar:
   `T`=tamamlandı (bütün sayfalar doğrulandı), `D`=istinsah edildi,
   `İE`=istinsah edilecek, `SE`=eşleştirilecek. Biz 500+ sayfalık cildin
   yalnız 27 sayfasını istinsah ediyoruz; cildin tamamı için `D` yazmak
   gerçeğe aykırı olur. (Bu belgenin önceki sürümü `D` diyordu, yanlıştı.)
3. **`Yazar` alanına düz metin yazılır, köşeli parantez konmaz.** Şablon bu
   alanı olduğu gibi basar; `Yazar:Türk Tarihi Tetkik Cemiyeti` sayfası
   olmadığı için bağlantı vermek kırık bağlantı üretirdi. Aynısı `Eser ismi`
   için de geçerlidir.
4. **`İçindekiler` (Remarks) alanı şimdilik boş kalır.** Şablon onu sağdaki
   "İçindekiler" sütununda gösterir; basım notu oraya uymaz. Adım 5'te bölüm
   sayfaları oluşturulduktan sonra buraya bölüm bağlantısı konabilir.

### Adım 5 — Bölüm sayfalarını oluşturun — ✅ tamamlandı (19.08.2026)

Dört sayfa da kuruldu ve şablon hatası vermeden render oluyor:

- [Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar](https://tr.wikisource.org/wiki/Tarih_I:_Tarihtenevelki_Zamanlar_ve_Eski_Zamanlar) → `/Beşer Tarihine Giriş`
- [Tarih II: Ortazamanlar](https://tr.wikisource.org/wiki/Tarih_II:_Ortazamanlar) → `/İslâm Tarihi`

```bash
python build/19_vikikaynak_bolum.py         # ne yazılacağını göster
python build/19_vikikaynak_bolum.py --yaz
```

Aşağıdaki vikimetin betiğin ürettiğinin aynısıdır; `<pages>` aralığı elle
yazılmaz, `secim/index.json` içindeki basılı aralık ile Commons ofsetinden
türetilir. Var olan sayfanın üzerine `--zorla` verilmedikçe yazılmaz.

> **Bu adım Adım 3'ten sonra yapılır.** `<pages>` etiketi Sayfa: ad alanındaki
> metni çeker; sayfalar henüz girilmemişken bu sayfayı oluşturursanız boş bir
> bölüm yayımlamış olursunuz.

> **`Kişi:Türk Tarihi Tetkik Cemiyeti` kırmızı bağlantısı.** `{{eser başlığı}}`
> şablonu `eser sahibi` alanını `Kişi:` ad alanına bağlar; o sayfa yoktur ve
> dört sayfada da kırmızı görünür. Vikikaynak'ta yaygındır, zararsızdır.
> Açılacaksa `{{Kişi}}` şablonuyla ve `vikipedi_bağlantısı=Türk Tarih Kurumu`
> ile açılır (Wikidata Q374071; cemiyet 1935'te bu adı aldı). Şablon şahıslar
> için tasarlanmıştır — `doğumyılı`/`ölümyılı` ve cinsiyet kategorileri tüzel
> kişiye uymaz, boş bırakılır.

Kullanılan şablonların üçü de bu vikide mevcuttur
(`Eser başlığı`, `Eser son`, `KM-Türkiye-isimsiz`).

Cildin tamamı istinsah edilmediği için, cilt sayfasını bölümü gösteren kısa
bir giriş olarak kurmak en dürüst yoldur.

**Sayfa adı: `Tarih II: Ortazamanlar`**

```
{{eser başlığı
 | önceki      =
 | sonraki     =
 | başlık      =Tarih II: Ortazamanlar
 | bölüm       =
 | eser sahibi =Türk Tarihi Tetkik Cemiyeti
 | notlar      =Maarif Vekâleti, İstanbul, Devlet Matbaası, 1931. Liseler için resmî tarih ders kitabı. Bu ciltten şimdilik yalnız aşağıdaki bölüm istinsah edilmiştir.
}}

* [[Tarih II: Ortazamanlar/İslâm Tarihi|İslâm Tarihi]] (basılı s. 79-184)

{{eser son
 |telif={{KM-Türkiye-isimsiz}}
 |kaynak=[[Dizin:Tarih II Ortazamanlar.pdf]]
}}
```

**Sayfa adı: `Tarih II: Ortazamanlar/İslâm Tarihi`**

```
{{eser başlığı
 | önceki      =
 | sonraki     =
 | başlık      =Tarih II: Ortazamanlar
 | bölüm       =İslâm Tarihi
 | eser sahibi =Türk Tarihi Tetkik Cemiyeti
 | notlar      =Maarif Vekâleti, İstanbul, Devlet Matbaası, 1931. Basılı s. 79-184.
}}

<pages index="Tarih II Ortazamanlar.pdf" from=101 to=206 />

{{eser son
 |telif={{KM-Türkiye-isimsiz}}
 |kaynak=[[Dizin:Tarih II Ortazamanlar.pdf]]
}}
```

**Tarih I için aynısı**, şu değişikliklerle: sayfa adları
`Tarih I: Tarihtenevelki Zamanlar ve Eski Zamanlar` ve
`…/Beşer Tarihine Giriş`; bölüm `Beşer Tarihine Giriş`; basılı s. 1-24;
`<pages index="Tarih I Tarihtenevelki Zamanlar ve Eski Zamanlar.pdf" from=34 to=57 />`.

> `{{eser başlığı}}` şablonunda **boş parametreleri silmeyin** — şablon aksi
> hâlde görünür hata verir.
>
> `{{KM-Türkiye-isimsiz}}` şablonu tüzel kişi eserlerini hedefliyor ve bu
> kitaba birebir oturuyor: *"Yayımlanırken sahibi belirtilmeyen veya sahibi bir
> tüzel kişi olan bu eser, yayımlanma tarihinin üzerinden 70 yıl geçmesinden
> dolayı Türkiye'de kamu malı olmuştur."* Yine de Adım 2'deki mesajda teyit
> ettirin.

---

## 4. Bu ne kazandırır

Vikikaynak metni, Wikimedia'nın veri kümelerine girer ve Vikipedi'den gelen
bağlantılarla düzenli olarak yeniden taranır. 118 sayfalık katkı, bu iki bölümü
dil modelleri için **düzeltilmiş** hâliyle erişilebilir kılar — daha önce
oradaki ham OCR modelleri yanıltıyordu.

## 5. Bu neyi kapsamıyor

- **Orijinal tarama zaten Commons'ta**, ayrı bir iş yok.
- **İngilizce erişim** bu yol haritasının dışında. Vikikaynak dil bazlıdır;
  İngilizce metin en.wikisource'a ait ve orası çeviri kabul etmez (çeviri
  Vikikaynak'ta ayrı bir statüdedir). İngilizce görünürlük için doğru kanallar
  başkadır ve ayrıca planlanmalıdır.
- **İnceleme raporu Vikikaynak'a konulamaz** — orası kaynak metinler içindir.
