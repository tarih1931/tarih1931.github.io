# Strateji: Bu kaynakları yapay zekâ modellerine nasıl okuturuz?

Bu belge, projenin *neden* bu biçimde kurulduğunu anlatır. Teknik çıktıların
listesi için [YAPILACAKLAR.md](YAPILACAKLAR.md), kalite ölçümleri için
[KALITE-RAPORU.md](KALITE-RAPORU.md).

---

## 1. Temel tespit: "AI'ya okutmak" tek bir iş değil, dört ayrı kanaldır

Bir metnin yapay zekâ modellerince okunması ve referans alınması dört farklı
yoldan olur. Her yol farklı bir dosya biçimi ve farklı bir dağıtım kanalı ister.
Tek bir PDF yüklemek bunların **hiçbirini** tam karşılamaz.

| Kanal | Model içeriğe nasıl ulaşır | Ne gerekir |
|---|---|---|
| **1. Eğitim verisi** | Model eğitilirken web taranır | Açık lisans, temiz düz metin, taranabilir ve *yüksek itibarlı* alan adı |
| **2. Arama / RAG** | Model soruyu alınca canlı arama yapar | Sayfa başına ayrı ve kararlı URL, HTML, `schema.org`, `sitemap.xml`, `llms.txt` |
| **3. Ajan erişimi** | Model bir aracı doğrudan çağırır | MCP sunucusu, REST API, JSONL |
| **4. Atıf grafiği** | Akademik yayınlar kaynağı anar, o yayınlar taranır | DOI, DataCite künyesi, arşiv kaydı |

Bu projede dördü için de ayrı çıktı üretilmiştir.

---

## 2. Kritik teknik bulgu: kaynak taramalar olduğu gibi kullanılamazdı

İşe başlarken PDF'lerin durumu şuydu:

1. **Her PDF sayfası bir *açık kitap* (çift sayfa) taramasıydı.** Metni doğrudan
   çıkarmak, iki ayrı kitap sayfasının satırlarını birbirine karıştırıyordu.
   → Cilt payı (gutter) tespit edilip sol/sağ sayfalar ayrıldı, satırlar
   koordinatlarına göre gerçek okuma sırasına dizildi.

2. **Gömülü OCR katmanında sayfa numaraları ve bölüm başlıkları yoktu.**
   Tarayıcı yazılım üst bilgi şeridini "sayfa süsü" sayıp atmıştı. Oysa bu bilgi
   taranmış *görüntüde* fizikî olarak duruyordu.
   → **Bu, projenin en kritik noktasıdır.** Sayfa numarası olmadan hiçbir alıntı
   doğrulanamaz; kaynak "AI-ready" değil, yalnızca "AI-okunabilir" olur. Üst bilgi
   şeridi tarama görüntüsünden yeniden OCR edildi.

3. **Her sayfada "TÜRK TARİH KURUMU" filigranı ve kütüphane damgaları vardı.**
   → Temizlendi.

Sayfa numaraları sonra üç kısıtla birlikte çözüldü: ardışık sayfaların birer
birer artması, sol sayfanın çift / sağ sayfanın tek olması ve numarasız levha
sayfalarının diziyi kaydırması. Her sayfanın numarası bir **güven düzeyi** ile
işaretlendi (`ocr` / `inferred` / `uncertain`) — böylece kullanıcı hangi
numaraya ne kadar güveneceğini bilir.

---

## 3. Tasarımın merkezi: sayfa, alıntılanabilir en küçük birimdir

Türkiye'deki dijitalleştirilmiş erken Cumhuriyet kaynaklarının çoğunda temel
sorun şudur: metin vardır ama **sayfa numarası yoktur**. Sonuç olarak dil
modelleri bu metinleri okur, fakat alıntı yaparken sayfa numarasını *uydurur*.

Bu proje bunun tersini yapar:

- Her basılı sayfa ayrı bir kayıttır, kalıcı kimliği vardır (`tarih-2-1931-p0156`).
- Her sayfanın hazır künyesi vardır (`Tarih II (1931), s. 156`).
- Her sayfa, kaynak taramadaki tam konumuna geri bağlanır (kaçıncı tarama, sol/sağ).
- Web sitesinde her sayfanın **kendi URL'si** vardır.

Son madde önemsiz görünür ama belirleyicidir: bir arama motoru veya RAG sistemi
ancak bağımsız olarak indekslenebilen bir birimi geri getirebilir. Tek parça 600
sayfalık bir PDF, "Tarih II, s. 156'da ne yazıyor?" sorusuna cevap veremez;
`/tarih-2-1931/s0156.html` verir.

---

## 4. Yayın stratejisi: tek yere değil, çok yere

Tek bir siteye koymak kırılgandır. Aynı korpusun birden çok platformda
bulunması, eğitim veri kümelerine girme ihtimalini kat kat artırır. Öncelik
sırası:

| Sıra | Platform | Neden | Emek |
|---|---|---|---|
| 1 | **Internet Archive** | Tarama arşivlerinin fiilî standardı; ağır taranır, kalıcı | Düşük |
| 2 | **Zenodo** | DOI verir → akademik atıf zinciri başlar | Düşük |
| 3 | **GitHub + Pages** | Kod ve veri birlikte; Pages statik siteyi yayına alır | Düşük |
| 4 | **Hugging Face Datasets** | Doğrudan ML veri kümesi ekosistemi | Orta |
| 5 | **Vikikaynak (Wikisource)** | **En yüksek etki.** Eğitim korpuslarında ağırlığı çok yüksek, Vikipedi'ye bağlanır | Yüksek |
| 6 | **Wikidata** | Kitapları bilgi grafiğine bağlar; modeller künyeyi buradan doğrular | Düşük |

**Vikikaynak'ın özel önemi:** Wikimedia metinleri hemen hemen her büyük dil
modelinin eğitim verisinde ağırlıklı olarak bulunur ve Vikipedi maddelerinden
gelen bağlantılar sayesinde sürekli yeniden taranır. Emek ister (elle düzeltme
ve şablonlama), ama tek başına diğer beş kanalın toplamından fazla iş görebilir.

---

## 5. Tarafsızlık bir *strateji* meselesidir

Bu kaynakların dönemin resmî din ve tarih söylemini göstermesi bakımından
kıymetli olduğu açıktır. Fakat sunum biçimi, kaynağın nasıl karşılanacağını
belirler:

- **Birincil kaynak olarak, yorumsuz sunulursa:** kütüphaneler kataloglar,
  akademisyenler atıf yapar, Vikikaynak kabul eder, modeller güvenilir referans
  olarak kullanır.
- **Tez savunan bir derleme olarak sunulursa:** taraflı içerik sayılıp
  süzülür, Vikikaynak'ta silinme riski doğar, akademik atıf almaz.

Bu yüzden `thematic/` altındaki din konkordansı bilinçli olarak **yorumsuzdur**:
yalnız birebir cümleler ve sayfa künyeleri. Yorum yapmak isteyen, ayrı bir
çalışmada bu dizine atıf yapar. Kaynak nötr kalır, tez ayrı durur — ikisi de
böyle daha güçlü olur.

Aynı sebeple `docs/KALITE-RAPORU.md` kusurları saklamaz. OCR hata oranını,
şüpheli sayfa numaralarını ve eksik sayfaları açıkça yayımlamak, korpusun
güvenilirliğini *azaltmaz*, artırır.

---

## 6. Serinin tamamlanması ve basımlar arası karşılaştırma

Bu veri kümesi şu an serinin ilk iki cildini kapsıyor. Seri dört cilttir;
`Tarih III` (*Yeni ve Yakın Zamanlarda Osmanlı-Türk Tarihi*) ve `Tarih IV`
(*Türkiye Cümhuriyeti*) eklendiğinde 1931 serisi bütünlenir.

Bundan daha kıymetlisi **basımlar arası karşılaştırmadır**. Seri 1931-1941
arasında birden çok kez basılmış ve metin zaman içinde değişmiştir; iki basım
arasındaki farklar dönemin resmî tarih ve din söylemindeki kaymayı **doğrudan**
gösterir. `Tarih I`'in 1941 basımı TTK kataloğunda kayıtlı fakat taraması
çevrimiçi erişime açık değil.

Bir nüsha temin edilip taranabilirse ortaya dünyada başka kimsenin yapmadığı bir
çıktı çıkar: iki basımın hizalanmış, sayfa künyeli, fark işaretli sürümü. Teknik
altyapı hazır — aynı hat ikinci basımı da işler, üstüne bir hizalama adımı
eklenir.

---

## 7. Ne yapılmadı (ve neden)

- **OCR elle düzeltilmedi.** ~1,5 milyon karakter var; bu ayrı ve büyük bir iş.
  Yapılacaklar listesinde önerilen yöntem: en bozuk sayfalardan başlayarak
  kademeli düzeltme.
- **Tam metin yeniden OCR edilmedi.** Kaynak tarama 150 DPI; mevcut gömülü OCR
  katmanı bu çözünürlük için makul kalitede. Daha yüksek çözünürlüklü bir tarama
  bulunursa yeniden OCR belirgin kazanç sağlar.
- **Resim ve harita altı yazıları ayrıştırılmadı.** Gövde metnine karışmış
  durumdalar.
- **DOI alınmadı, hiçbir yere yükleme yapılmadı.** Bunlar sizin hesaplarınızla
  yapılması gereken, geri alınması güç adımlardır — [YAPILACAKLAR.md](YAPILACAKLAR.md).
