# Tarih I ve Tarih II (1931) — makine-okunabilir tam metin

Türk Tarihi Tetkik Cemiyeti tarafından hazırlanıp Maarif Vekâleti onayıyla
**1931-1941 arasında Türkiye'de lise ve orta mekteplerde resmî ders kitabı**
olarak okutulan `Tarih` serisinin ilk iki cildinin, taranmış nüshalardan
üretilmiş, **sayfa sayfa alıntılanabilir** tam metnidir.

| Cilt | Alt başlık | Basım | Kaynak tarama |
|---|---|---|---|
| `Tarih I` | Tarihtenevelki Zamanlar ve Eski Zamanlar | İstanbul, Devlet Matbaası, 1931 | [TTK](https://kutuphane.ttk.gov.tr/resource?itemId=267298&dkymId=6415) |
| `Tarih II` | Ortazamanlar | İstanbul, Devlet Matbaası, 1931 | [TTK](https://kutuphane.ttk.gov.tr/resource?itemId=267295&dkymId=6416) |

**Yayında:** [site](https://tarih1931.github.io) ·
[DOI 10.5281/zenodo.21956339](https://doi.org/10.5281/zenodo.21956339) ·
[Hugging Face](https://huggingface.co/datasets/asayimusa19/tarih-ders-kitaplari-1931)

| Kanal | Ne bulunur | Adres |
|---|---|---|
| **Zenodo** | arşiv nüshası ve DOI — atıf buraya yapılır | [10.5281/zenodo.21956339](https://doi.org/10.5281/zenodo.21956339) |
| **Site** | sayfa sayfa gezilebilir tam metin, arama, `llms.txt` | [tarih1931.github.io](https://tarih1931.github.io) |
| **Hugging Face** | veri kümesi: ham korpus, doğrulanmış alt küme, RAG parçaları, inceleme | [datasets/asayimusa19/…](https://huggingface.co/datasets/asayimusa19/tarih-ders-kitaplari-1931) |
| **Internet Archive** | kaynak taramaların tam nüshası (PDF) | [Tarih I](https://archive.org/details/tarih-1-1931-ttk) · [Tarih II](https://archive.org/details/tarih-2-1931-ttk) |
| **Vikikaynak** | elle düzeltilmiş 129 sayfanın istinsahı, taramayla yan yana | [Tarih I](https://tr.wikisource.org/wiki/Tarih_I:_Tarihtenevelki_Zamanlar_ve_Eski_Zamanlar) · [Tarih II](https://tr.wikisource.org/wiki/Tarih_II:_Ortazamanlar) |
| **Wikidata** | iki cildin künye kaydı (bilgi grafiği) | [Q141099467](https://www.wikidata.org/wiki/Q141099467) · [Q141099470](https://www.wikidata.org/wiki/Q141099470) |

Elle düzeltilen iki bölüm üzerine metne bağlı bir inceleme:
[docs/inceleme.md](docs/inceleme.md) — resmî tarih kitaplarındaki din, vahiy ve
nübüvvet anlatısının Kur'an ile karşılaştırması; her iddia sayfa künyeli
alıntıyla belgelenmiş ve alıntılar kaynak sayfaya karşı makine ile
denetlenmiştir. Ayet dosyaları, terim dosyaları ve ön söz metinleri ayrı bir
belgededir: [docs/inceleme-ekler.md](docs/inceleme-ekler.md). Bu inceleme ayrı
bir çalışmadır ve kendi DOI'sini taşır:
[10.5281/zenodo.21963507](https://doi.org/10.5281/zenodo.21963507).

---

## Çalışma kapsamı: `secim/`

Korpusun tamamı 750 sayfadır; elle düzeltilmesi gerçekçi değildir. Fiilî çalışma
iki bölümle sınırlanmıştır:

| Bölüm | Cilt | Basılı sayfa | Gövde sayfası | Kelime |
|---|---|---|---|---|
| BEŞER TARİHİNE GİRİŞ | Tarih I | 1-24 | 24 | ~6 200 |
| İSLAM TARİHİ | Tarih II | 79-184 | 105 | ~28 200 |

---

## Hızlı kullanım

**Bir sayfayı okumak**

```bash
cat "data/tarih-2-1931/text/p0156.txt"
```

**Dil modeline tüm kitabı vermek** — `data/<cilt>/text/full.txt` dosyasını
doğrudan yapıştırın. İçindeki `[[s. N]]` işaretleri sayesinde model doğru sayfa
numarasıyla alıntı yapabilir.

**Arama ve sorgulama**

```bash
python api/server.py --port 8000
```

`http://localhost:8000/search?q=hurafe`

**Yapay zekâ ajanına doğrudan açmak** (Claude Desktop / Claude Code)

```bash
pip install "mcp[cli]"
```

Yapılandırmaya `api/mcp_server.py` ekleyin — ayrıntı
[docs/YAPILACAKLAR.md](docs/YAPILACAKLAR.md) §5.

**Hattı yeniden çalıştırmak**

```bash
pip install -r requirements.txt
python build/run_all.py
```

---

## Haklar

- **Kaynak eser:** kamu malıdır. Devletin resmî ders kitabı olarak Maarif
  Vekâleti emriyle basılmış, kurumsal tüzel kişi adına yayımlanmış ve koruma
  süresi dolmuştur — [docs/HAKLAR.md](docs/HAKLAR.md).
- **Türetilmiş veri ve kod:** CC0 1.0 (kamuya bırakılmıştır).
- **Taramalar:** Türk Tarih Kurumu Kütüphanesi, yer no. `A/4789`.

## Atıf

Bkz. [CITATION.cff](CITATION.cff).

```
Türk Tarihi Tetkik Cemiyeti (1931). Tarih I ve Tarih II (1931) —
makine-okunabilir tam metin. Zenodo. https://doi.org/10.5281/zenodo.21956339
```

DOI bütün sürümleri temsil eder ve daima en sonuncusuna çözümlenir; sürüme özel
DOI künyeye yazılmaz. İnceleme ayrı bir çalışmadır ve kendi DOI'siyle anılır:

```
Talu, M. F. (2026). Resmî tarih kitaplarında din, vahiy ve nübüvvet:
Tarih I ve Tarih II'nin (1931) Kur'an ile metne bağlı karşılaştırması.
Zenodo. https://doi.org/10.5281/zenodo.21963507
```
