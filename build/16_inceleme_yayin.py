"""16 — İncelemeyi kendi başına duran bir yayın olarak paketler.

    python build/16_inceleme_yayin.py

Çıktı: inceleme/yayin/

Sorun şuydu: inceleme, korpusun Zenodo kaydındaki 13 MB'lık depo zip'inin
içine gömülüydü. Ne DataCite, ne OpenAlex, ne Google Scholar, ne de bir dil
modeli onu ayrı bir çalışma olarak görebiliyordu — kaydın başlığı korpusun
adıydı, türü "Dataset"ti. Bu adım incelemeye kendi kimliğini verir: kendi
başlığı, kendi özeti (TR + EN), kendi yazarı ve kendi DOI'siyle.

Pakette ne var:

  inceleme-tr.md    asıl belge (kanonik biçim)
  inceleme-en.md    İngilizce sürüm
  bulgular.jsonl    alıntılar (doğrulama damgalı) ve bulgular (dayanakları kayıtlı)
  inceleme-tr.pdf   Google Scholar PDF ayrıştırır; .md'yi ayrıştırmaz
  inceleme-en.pdf
  zenodo.json       kaydın künyesi — Zenodo formuna girilecek değerler

PDF, .md'nin yerine geçmez; aynı belgenin ikinci biçimidir ve yalnız
PDF ayrıştıran dizinler için vardır.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import META_DIR, ROOT, md_to_html, write_json, write_text  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
RIGHTS = META["rights"]
# Adres künyeyle aynı yerden gelir (books.json -> channels.site).
CHANNELS = META.get("channels", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"
OUT = ROOT / "inceleme" / "yayin"
TODAY = date.today().isoformat()

YAZAR = (META.get("review") or {}).get("author") or "Anonim"
KORPUS_DOI = COLL.get("doi")

REVIEW = META.get("review") or {}
BASLIK_TR = REVIEW.get("title") or "1931 incelemesi"
BASLIK_EN = REVIEW.get("title_en") or "1931 review"

TR_MD = ROOT / "docs" / "inceleme.md"
EN_MD = ROOT / "docs" / "REVIEW-EN.md"


def ozet_ham(yol: Path, etiket: str) -> str:
    """Belgenin kendi özet paragrafı, markdown'ı olduğu gibi.

    Künye ve PDF kapağı buradan beslenir. Özet betikte sabit yazılırsa belge
    değiştikçe sessizce eskiyor; Zenodo kaydının üst kısmında bir sürüm önceki
    metin görünmesinin sebebi buydu."""
    md = yol.read_text(encoding="utf-8")
    m = re.search(rf"^\*\*{etiket}:\*\*\s*(.+?)(?=\n\n)", md, re.M | re.S)
    if not m:
        raise SystemExit(f"    {yol.name}: '{etiket}:' paragrafı bulunamadı")
    return re.sub(r"\s+", " ", m.group(1)).strip()


def ozet_duz(ham: str) -> str:
    """Düz metin: künye alanları için. Bağlantılar ve vurgular düşer."""
    return re.sub(r"[*`]", "", re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", ham)).strip()


def ozet_html(ham: str) -> str:
    """PDF kapağı için: bağlantılar <a> olarak korunur.

    Özet gövdeden çıkarıldığı için PDF'te başka yerde geçmiyor; burada da
    düzleştirilirse belgede tek bir bağlantı kalmıyor."""
    t = re.sub(r"\[([^\]]+)\]\(([^)]*)\)", r'<a href="\2">\1</a>', ham)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)


HAM_TR = ozet_ham(TR_MD, "Özet")
HAM_EN = ozet_ham(EN_MD, "Abstract")
# Düz metin sürüm: HTML kabul etmeyen alanlar için (şimdilik kullanılmıyor,
# künye ve PDF ikisi de HTML alıyor).
OZET_TR = ozet_duz(HAM_TR)
OZET_EN = ozet_duz(HAM_EN)

PDF_CSS = """
@font-face {font-family: govde; src: url(times.ttf);}
@font-face {font-family: govde; src: url(timesbd.ttf); font-weight: bold;}
@font-face {font-family: govde; src: url(timesi.ttf); font-style: italic;}
body {font-family: govde; font-size: 10.5pt; line-height: 1.4;}
h1 {font-size: 16pt; margin: 0 0 6pt 0;}
h2 {font-size: 12.5pt; margin: 14pt 0 4pt 0;}
h3 {font-size: 11pt; margin: 11pt 0 3pt 0;}
h4 {font-size: 10.5pt; margin: 9pt 0 3pt 0;}
p {margin: 0 0 6pt 0; text-align: justify;}
blockquote, p.bulgu {margin: 6pt 0 6pt 14pt; font-size: 10pt; text-align: left;}
li {margin: 0 0 3pt 0;}
table {width: 100%; font-size: 9pt;}
th, td {border: 0.5px solid #999; padding: 2pt 3pt; text-align: left; vertical-align: top;}
th {font-weight: bold;}
code {font-size: 9.5pt;}
.r-alinti {color: #1550c8;}
.r-ayet {color: #177a3f;}
.r-bulgu {color: #b3231e;}
.kapak {font-size: 10pt; margin-top: 10pt;}
hr {margin: 8pt 0;}
"""


def kapak(baslik: str, ozet: str, en: bool) -> str:
    e = lambda tr, ing: ing if en else tr  # noqa: E731
    return (
        f"<h1>{baslik}</h1>"
        f'<p class="kapak"><b>{YAZAR}</b><br>{TODAY}</p>'
        f'<p class="kapak"><b>{e("Özet", "Abstract")}.</b> {ozet}</p>'
        f'<p class="kapak">'
        f'{e("Kaynak metin ve veri kümesi", "Source text and dataset")}: '
        f"https://doi.org/{KORPUS_DOI}<br>"
        f'{e("Çevrimiçi sürüm", "Online version")}: {BASE_URL}/'
        f'{e("inceleme.html", "review.html")}<br>'
        f'{e("Makine-okunabilir iddialar", "Machine-readable claims")}: {BASE_URL}/inceleme.jsonl<br>'
        f'{e("Lisans", "License")}: {RIGHTS["derived_dataset_license"]}'
        f"</p><hr>"
    )


def pdf_govdesi(md: str, etiket: str) -> str:
    """Belgenin başlığını ve özetini gövdeden düşürür.

    PDF'in kapak bloğu ikisini de zaten basıyor; markdown olduğu gibi
    eklenince ilk sayfada başlık ve özet alt alta iki kez çıkıyordu.
    Kaynak .md dosyası kanonik biçim olduğu için orada duruyorlar,
    yalnız bu türev çıktıda ayıklanıyorlar.
    """
    yeni = re.sub(r"\A\s*#\s+.+?\n", "", md, count=1)
    if yeni == md:
        raise SystemExit(f"    PDF: beklenen '# ' başlığı bulunamadı")
    md, yeni = yeni, re.sub(rf"\A\s*\*\*{etiket}:\*\*.*?(?=\n\n)", "", yeni, count=1, flags=re.S)
    if yeni == md:
        raise SystemExit(f"    PDF: beklenen '**{etiket}:**' paragrafı bulunamadı")
    return yeni.lstrip("\n")


def pdf_yaz(md_yolu: Path, hedef: Path, baslik: str, ozet: str, en: bool) -> None:
    import pymupdf

    ham = pdf_govdesi(md_yolu.read_text(encoding="utf-8"),
                      "Abstract" if en else "Özet")
    govde = kapak(baslik, ozet, en) + md_to_html(ham)
    story = pymupdf.Story(
        html=f"<body>{govde}</body>",
        archive=pymupdf.Archive(r"C:\Windows\Fonts"),
        user_css=PDF_CSS,
    )
    # Önce ham PDF geçici dosyaya yazılır; nihai dosya ondan üretilir. Ters sıra
    # Windows'ta çalışmıyor: açık/yeni kapanmış PDF'in üzerine yazılamıyor.
    gecici = Path(tempfile.gettempdir()) / f"{hedef.stem}.ham.pdf"
    writer = pymupdf.DocumentWriter(str(gecici))
    alan = pymupdf.Rect(56, 56, 539, 786)  # A4, ~2 cm kenar boşluğu

    # Story <a href> etiketini metin olarak basar ama PDF bağlantısı üretmez;
    # belge bu yüzden tek bir tıklanabilir bağlantı içermiyordu. Konumları
    # dizilim sırasında toplayıp bağlantıları sonradan ekliyoruz.
    baglar: list[tuple[int, pymupdf.Rect, str]] = []
    capalar: dict[str, tuple[int, float]] = {}
    sayfa_no = {"n": 0}

    def konum(pos) -> None:
        if getattr(pos, "href", None):
            baglar.append((sayfa_no["n"], pymupdf.Rect(pos.rect), pos.href))
        kimlik = getattr(pos, "id", None)
        if kimlik and kimlik not in capalar:
            capalar[kimlik] = (sayfa_no["n"], pymupdf.Rect(pos.rect).y0)

    devam = 1
    while devam:
        sayfa_no["n"] += 1
        dev = writer.begin_page(pymupdf.paper_rect("a4"))
        devam, _ = story.place(alan)
        story.element_positions(konum)
        story.draw(dev)
        writer.end_page()
    writer.close()

    # Sayfa numaraları + font alt kümeleme. Alt kümeleme olmadan tam Times
    # ailesi gömülür ve 22 KB'lık belge 3,4 MB'lık PDF üretir.
    doc = pymupdf.open(str(gecici))
    for i, sayfa in enumerate(doc, 1):
        sayfa.insert_text((295, 812), str(i), fontsize=9, fontname="helv")
    for no, dortgen, adres in baglar:
        if adres.startswith("#"):
            # Bölümler arası atıf: URI değil, belge içi atlama olmalı.
            varis = capalar.get(adres[1:])
            if not varis:
                raise SystemExit(f"    {hedef.name}: '{adres}' çapası belgede yok")
            doc[no - 1].insert_link({"kind": pymupdf.LINK_GOTO, "from": dortgen,
                                     "page": varis[0] - 1,
                                     "to": pymupdf.Point(56, varis[1])})
        else:
            doc[no - 1].insert_link({"kind": pymupdf.LINK_URI, "from": dortgen, "uri": adres})
    if not baglar:
        raise SystemExit(f"    {hedef.name}: hiç bağlantı toplanamadı — <a> işleme bozulmuş olabilir")
    doc.subset_fonts()
    doc.save(str(hedef), garbage=4, deflate=True)
    doc.close()
    try:  # Windows dosyayı bir süre kilitli tutabilir; kalırsa zararsız
        gecici.unlink(missing_ok=True)
    except OSError:
        pass


def zenodo_kunyesi() -> dict:
    return {
        "title": BASLIK_TR,
        "upload_type": "publication",
        "publication_type": "report",
        "publication_date": TODAY,
        "creators": [{"name": YAZAR}],
        "description": (
            # Zenodo açıklaması HTML kabul eder. Düz metin verilirse belgedeki
            # bağlantılar ve vurgular kaybolur; kayıt sayfasında özet, kaynak
            # kitaplara bağlanmayan ve hiçbir yeri vurgulanmayan bir blok olarak
            # görünür. Bu yüzden künyede de ozet_html kullanılır.
            f"<p><strong>Özet:</strong> {ozet_html(HAM_TR)}</p>"
            f"<p><strong>Abstract (English):</strong> {ozet_html(HAM_EN)}</p>"
            f'<p>Çevrimiçi sürüm: <a href="{BASE_URL}/inceleme.html">{BASE_URL}/inceleme.html</a> '
            f'(İngilizcesi: <a href="{BASE_URL}/review.html">/review.html</a>)</p>'
        ),
        "language": "tur",
        "access_right": "open",
        "license": "cc-zero",
        "keywords": [
            "Türk Tarih Tezi",
            "Tarih — Ders kitapları — Türkiye",
            "İslam itikadı",
            "Din ve devlet — Türkiye",
            "Erken Cumhuriyet dönemi ideolojisi",
            "Vahiy ve nübüvvet",
            "Islam--Doctrines",
            "History--Textbooks",
            "Turkey--History--Study and teaching",
        ],
        "related_identifiers": [
            {"identifier": KORPUS_DOI, "relation": "isSupplementTo", "scheme": "doi"},
            {"identifier": f"{BASE_URL}/inceleme.html", "relation": "isIdenticalTo", "scheme": "url"},
            *([{"identifier": REVIEW["internet_archive"], "relation": "isIdenticalTo",
                "scheme": "url"}] if REVIEW.get("internet_archive") else []),
        ],
    }


def main() -> None:
    tr_md, en_md = TR_MD, EN_MD
    bulgular = ROOT / "inceleme" / "bulgular.jsonl"
    if not tr_md.exists():
        raise SystemExit("    inceleme belgesi yok")

    if OUT.exists():
        # Windows dizin tanıtıcısını kilitli tutabilir; dosyalar silindiği
        # sürece zararsızdır, dizin yeniden doldurulur.
        shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)

    shutil.copy2(tr_md, OUT / "inceleme-tr.md")
    if en_md.exists():
        shutil.copy2(en_md, OUT / "inceleme-en.md")
    if bulgular.exists():
        shutil.copy2(bulgular, OUT / "bulgular.jsonl")

    pdf_yaz(tr_md, OUT / "inceleme-tr.pdf", BASLIK_TR, ozet_html(HAM_TR), en=False)
    if en_md.exists():
        pdf_yaz(en_md, OUT / "inceleme-en.pdf", BASLIK_EN, ozet_html(HAM_EN), en=True)

    write_json(OUT / "zenodo.json", zenodo_kunyesi())
    write_text(
        OUT / "OKU.txt",
        "İncelemenin kendi Zenodo kaydı için hazırlanmış pakettir.\n\n"
        "zenodo.json içindeki değerler Zenodo formuna girilecek künyedir.\n"
        "Diğer dosyalar kayda yüklenecek dosyalardır.\n\n"
        f"Korpus DOI'si (isSupplementTo ile bağlanır): {KORPUS_DOI}\n",
    )

    for f in sorted(OUT.iterdir()):
        print(f"    {f.name:22} {f.stat().st_size / 1024:8.1f} KB")


if __name__ == "__main__":
    main()
