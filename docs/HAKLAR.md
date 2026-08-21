# Haklar ve lisans

## 1. Kaynak eserin durumu: kamu malı

**Eser:** `Tarih I` ve `Tarih II`, Türk Tarihi Tetkik Cemiyeti, Maarif Vekâleti,
İstanbul, Devlet Matbaası, 1931.

Eser kamu malıdır. Dayanaklar:

**Resmî yayın niteliği.** Her iki cilt, Maarif Vekâleti Millî Talim ve Terbiye
Dairesi'nin emriyle, devletin resmî lise ders kitabı olarak bastırılmıştır.
Künye sayfalarında bu açıkça yazılıdır:

> *Maarif Vekâleti Millî Talim ve Terbiye Dairesinin 2/8/1931 tarih ve 1869
> numaralı emrile **30 000 nüsha** tab'edilmiştir.* (Tarih I, s. 6)

> *Maarif Vekâleti Millî Talim ve Terbiye Dairesinin 28/11/1931 tarih ve 2847
> numaralı emrile **25 000 nüsha** tab'edilmiştir.* (Tarih II, s. 6)

**Koruma süresi dolmuştur.** İç kapakta yazar olarak kurumsal bir tüzel kişi —
Türk Tarihi Tetkik Cemiyeti — görünür. 5846 sayılı FSEK m.27 uyarınca tüzel kişi
adına yayımlanan eserlerde koruma süresi yayımdan itibaren **70 yıldır**:
1931 + 70 = **2001**.

**Hak sahibi kurum eseri zaten kamuya açmıştır.** Cemiyetin ardılı olan Türk
Tarih Kurumu, taranmış nüshaları kendi resmî sitesinde
([kutuphane.ttk.gov.tr](https://kutuphane.ttk.gov.tr/)) herkese açık olarak
sunmaktadır.

**Haklar beyanı:** https://rightsstatements.org/vocab/NoC-OKLR/1.0/
(*No Copyright — Other Known Legal Restrictions*)

### Eseri hazırlayanlar

İç kapak kurumsal yazarı gösterir; eseri hazırlayan on üç kişi ise **9. sayfada**
*"Kitabın hazırlanmasında çalışanlar"* başlığı altında ad, soyad, mebusu
oldukları şehir ve cemiyetteki görevleriyle birlikte tek tek sayılmıştır. Tam
liste `metadata/books.json` içindedir ve web sitesinin *Hakkında* sayfasında
yayımlanır.

Bu isimler, telif değil **atıf** meselesidir: eseri kimin hazırladığı
künyeden bilinmektedir ve bu bilgi künye kayıtlarında (Dublin Core, MARC21,
schema.org, TEI) katkı sağlayan olarak korunmuştur.

---

## 2. Bu projede üretilen türetilmiş verinin durumu

Aşağıdakiler bu projede üretilmiştir ve **CC0 1.0** ile kamuya bırakılmıştır:

- Çift sayfa taramalarının ayrıştırılması ve okuma sırasının kurulması
- Sayfa numaralarının yeniden OCR'ı ve dizi çözümlemesi
- Sayfa düzeyinde JSONL kayıtları, TEI-XML, Markdown, RAG parçaları
- Bütün metadata dosyaları (Dublin Core, MARC21, schema.org, DataCite, Croissant)
- Din/inanç kavram dizini
- İşleme hattı kodu (`build/`), API ve MCP sunucusu

CC0 metni: https://creativecommons.org/publicdomain/zero/1.0/

Atıf istiyorsanız CC BY 4.0'a geçebilirsiniz; `metadata/books.json` içindeki
`derived_dataset_license` alanını değiştirip `python build/run_all.py --from 05`
çalıştırmanız yeterlidir.

---

## 3. Taramaların kaynağı

Taranmış görüntüler **Türk Tarih Kurumu Kütüphanesi**ne aittir:

- Katalog kaydı: https://kutuphane.ttk.gov.tr/details?id=508611&materialType=KT
- Yer numarası: `A/4789`
- `Tarih I` (1931): https://kutuphane.ttk.gov.tr/resource?itemId=267298&dkymId=6415
- `Tarih II` (1931): https://kutuphane.ttk.gov.tr/resource?itemId=267295&dkymId=6416

Kaynak, üretilen her sayfada, her metadata dosyasında ve web sitesinin her
sayfasında açıkça gösterilmektedir.

Kamu malı bir eserin sadık (yaratıcı katkı içermeyen) taramasının yeni bir telif
doğurmadığı, dijitalleştirme alanında yaygın kabul gören bir yorumdur.

---

## 4. Önemli uyarı: `PDF/` klasöründeki diğer eserler

`PDF/` klasöründe bu projeye **dahil edilmeyen** başka kitaplar da var. Bunların
büyük kısmı **telif hakkı devam eden modern eserlerdir** ve hiçbiri işleme
hattına alınmamıştır:

- Ali Güler — *İttihatçılar ve Mustafa Kemal*
- Atilla Oral — *Atatürk'ün Sansürlenen Mektubu*
- Bülent Demirbaş — *İbrahim Temo'nun İttihad ve Terakki Anıları*
- Doğu Perinçek — *Atatürk, Din ve Laiklik Üzerine*
- Falih Rıfkı Atay — *Atatürk'ün Bana Anlattıkları*
- Rıza Nur — *Hayat ve Hatıralarım*
- Uğur Mumcu — *Kâzım Karabekir Anlatıyor*
- İsmet Bozdağ — *Abdülhamid'in Hatıra Defteri*
- Afet İnan — *Medenî Bilgiler* (modern derleme baskısı)
- *Atatürk'ün Bütün Eserleri*, c. 24

Bunlar kişisel araştırma için okunabilir; fakat **yayımlanamaz, veri kümesine
konulamaz, açık lisansla dağıtılamaz.** Yazarları veya hak sahipleri yakın
tarihlidir. Zenodo, Internet Archive, Hugging Face veya GitHub'a yüklerken
`PDF/` klasörünün tamamını değil, yalnız `Tarih I.pdf` ve `Tarih II.pdf`
dosyalarını dahil edin.

> Pratik öneri: depoya bir `.gitignore` ekleyip `PDF/` içindeki bu dosyaları
> hariç tutun; yanlışlıkla yayımlanmalarının önüne geçer.

---

## 5. Kullanıcılara uyarı

Bu korpustaki metinler, `secim/` altındaki iki bölüm dışında **elle düzeltilmemiş
OCR** çıktısıdır. Bilimsel alıntı yapmadan önce ilgili sayfayı kaynak taramadan
teyit ediniz; her sayfa kaydında taramadaki tam konum (`scan_ref`) verilmiştir.

İki bölüm — Tarih I "Beşer Tarihine Giriş" (basılı s. 1-24) ve Tarih II "İslâm
Tarihi" (basılı s. 79-184), toplam 129 sayfa — taranmış aslıyla sayfa sayfa
karşılaştırılarak elle düzeltilmiştir; bu kayıtlar `text_source: corrected` ile
işaretlidir ve ham OCR metni `text_ocr` alanında saklanır. Alıntı yapılacaksa
bu sayfalar tercih edilmelidir.

---

## 6. ABD'deki durum — Wikimedia için belirleyici

Yukarıdaki §1 yalnız **Türkiye** hukukunu değerlendirir. Wikimedia Commons ve
Vikikaynak, bir eserin hem kaynak ülkede **hem de ABD'de** kamu malı olmasını
şart koşar. Bu iki tarih burada aynı değildir.

**URAA meselesi.** ABD'nin *Uruguay Round Agreements Act* düzenlemesi, kaynak
ülkesinde **1 Ocak 1996** tarihinde hâlâ korunan yabancı eserlerin ABD telifini
geri getirmiştir. Commons'ın Türkiye sayfası, URAA tarihini Türkiye için
1 Ocak 1996 olarak listeler ve 31 Aralık 1930'dan sonra yayımlanmış eserler için
bu ölçütü uygular.

Bu projenin §1'deki kendi tespiti — koruma süresinin 1931 + 70 = **2001**'de
dolduğu — eseri 1996'da *hâlâ korunuyor* konumuna koyar. Bu okumaya göre:

| | Tarih |
|---|---|
| Türkiye'de kamu malı | 2001 |
| ABD'de kamu malı (1931 + 95 yıl) | **1 Ocak 2027** |

**Sonuç:** Wikimedia'ya (Commons'a tarama, Vikikaynak'a metin) yükleme için
güvenli tarih 1 Ocak 2027'dir. Daha erken yüklenen içerik silinmeye açıktır.

**Karşı argüman.** FSEK'in tüzel kişi eserleri için 70 yıllık süresi 1995-2001
arasındaki değişikliklerle bugünkü hâlini almıştır; 1996'da yürürlükte olan
sürenin daha kısa olduğu ve eserin o tarihte zaten kamu malı olduğu — dolayısıyla
URAA ile geri getirilecek bir telif bulunmadığı — savunulabilir. Bu, Türk telif
hukuku uzmanlığı gerektiren bir sorudur; bu belge onu cevaplamaz. Erken yükleme
düşünülüyorsa Vikikaynak topluluğuna danışmak doğru yoldur.

**Diğer platformlar.** Internet Archive, Hugging Face ve GitHub Pages ABD
merkezlidir; aynı soru teorik olarak onlar için de geçerlidir. Pratikte risk
düşüktür: hak sahibi konumundaki Türk Tarih Kurumu taramaları kendi resmî
sitesinde herkese açık sunmaktadır ve eser devletin resmî ders kitabıdır.
Wikimedia'yı ayıran şey, bu kuralı kendiliğinden ve titizlikle uygulamasıdır.
