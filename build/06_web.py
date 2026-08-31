"""06 — AI tarayıcılarının okuyabileceği statik siteyi üretir.

Yapay zekâ modelleri bu metinlere üç yoldan ulaşır ve her biri farklı bir dosya
biçimi ister:

  1. Eğitim verisi taraması  -> açık lisanslı, temiz, taranabilir düz metin
  2. Arama/RAG (inference)   -> sayfa başına ayrı, kararlı URL'li HTML + JSON-LD
  3. Doğrudan alıntı         -> her sayfanın kendi künyesi ve kalıcı kimliği

Bu yüzden her basılı sayfa için ayrı bir HTML sayfası üretilir: bir model
"Tarih II, s. 156'da ne yazıyor?" sorusunu ancak o sayfa bağımsız olarak
indekslenebiliyorsa yanıtlayabilir.

Üretilenler: web/ altında tam site, sitemap.xml, robots.txt, llms.txt,
llms-full.txt, arama indeksi.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BOOKS,
    META_DIR,
    ROOT,
    WEB_DIR,
    Book,
    heading_id,
    md_to_html,
    page_label,
    page_slug,
    read_jsonl,
    write_json,
    write_text,
)

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
RIGHTS = META["rights"]
# 05_metadata ile aynı kaynaktan okunur; tescil edilmemişse boştur.
DOI = COLL.get("doi") or None
if DOI and "X" in DOI:
    DOI = None
BOOKMETA = {b["slug"]: b for b in META["books"]}
# Yayın kanalları künyeyle aynı yerden okunur (metadata/books.json -> channels).
CHANNELS = META.get("channels", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"
# Okuma sayacının adres kalıbı; boş bırakılırsa sayfalara sayaç konmaz.
SAYAC = (CHANNELS.get("counter") or "").strip()
# Veri kümesinin Hugging Face adresi; inceleme sayfalarının altbilgisinde
# DOI ile sayacın arasında durur.
HF_URL = (CHANNELS.get("huggingface") or "").strip()
# İncelemenin Internet Archive öğesi. Kanal listesinde değil, review künyesinde
# durur: arşiv nüshası korpusun değil, incelemenin kendi kaydıdır.
IA_URL = ((META.get("review") or {}).get("internet_archive") or "").strip()
TODAY = date.today().isoformat()

# Elle düzeltilmiş bölümler ve onlar üzerine yapılan inceleme. Korpusun geri
# kalanı ham OCR olduğu için bu ikisi sitenin en değerli parçasıdır; ayrı
# adresleri ve llms.txt'te ayrı bölümleri vardır.
# İnceleme iki sayfadır: inceleme.md incelemenin ÖZÜDÜR ve okuyucunun giriş
# sayfası inceleme.html'i besler; bütün delil aygıtını (46 alıntı, 38 ayet,
# 19 bulgu, itiraz cevapları, tam kaynakça) taşıyan kapsamlı metin ayrı
# dosyadadır ve inceleme-kapsamli.html'i besler. Akademik kimlik — DOI,
# Scholar etiketleri, arşiv künyeleri — kapsamlı sayfanındır: Zenodo
# kaydıyla birebir örtüşen metin odur.
REVIEW_MD = ROOT / "docs" / "inceleme.md"
REVIEW_FULL_MD = ROOT / "docs" / "inceleme-kapsamli.md"
# Kaynak dosyanın adı depoda REVIEW-EN.md kalır; sitede sunulan ad
# review.md'dir — sayfa review.html, PDF review.pdf, ham metin review.md.
REVIEW_EN_MD = ROOT / "docs" / "REVIEW-EN.md"
# İncelemenin ekleri (Ek A/B/C) ayrı bir belgedir: ana metni okunur tutar,
# dayanakları isteyen okuyucu bağlantıdan ulaşır.
REVIEW_ANNEX_MD = ROOT / "docs" / "inceleme-ekler.md"
# Eklerin İngilizce sürümü. Alıntılar, lügat maddeleri ve 1931 ön sözü orada da
# Türkçe durur; İngilizcesi her birinin altında köşeli parantezle verilir.
REVIEW_ANNEX_EN_MD = ROOT / "docs" / "REVIEW-APPENDICES-EN.md"
# İncelemenin KENDİ DOI'si — korpusunkinden ayrı. Ayrı bir çalışma olarak
# yayımlandığı için kendi başlığı, özeti ve atıf künyesi vardır.
REVIEW_DOI = (META.get("review") or {}).get("doi") or None
REVIEW_EN_TITLE = (META.get("review") or {}).get("title_en") or "1931 review"
# Sayfa özeti arama sonucunda görünen metindir; incelemenin özetiyle aynı
# çerçeveyi söylemesi gerekir.
REVIEW_EN_DESC = (
    "What Turkey's official 1931 history textbooks say about religion and Islam, compared "
    "with the Qur'an: 34 direct quotations, 22 verses, 19 findings. The divergence is shown "
    "to lie at the level of the articles of belief, not in detail; every claim is documented "
    "with a verbatim, page-cited quotation."
)
REVIEW_TITLE = (META.get("review") or {}).get("title") or "1931 incelemesi"
# Özet sayfasının başlığı; kapsamlı metnin başlığından "özeti" ekiyle ayrılır.
REVIEW_OZ_TITLE = (META.get("review") or {}).get("title_oz") or f"{REVIEW_TITLE} — özet"
REVIEW_AUTHORS = (META.get("review") or {}).get("authors") or ["Anonim"]
# Atıf satırı ve PDF kapağı tek bir ad dizesi ister; Scholar ise her yazar için
# ayrı bir citation_author etiketi bekler. İkisi de aynı listeden türer.
REVIEW_AUTHOR_LINE = " · ".join(REVIEW_AUTHORS)
REVIEW_EMAIL = (META.get("review") or {}).get("email") or ""


REVIEW_DESC = (
    "1931 basımı resmî tarih ders kitaplarının din, vahiy ve nübüvvet hakkındaki "
    "ifadelerinin Kur'an ile karşılaştırması: 46 doğrudan alıntı, 38 ayet, 19 bulgu. "
    "Ayrılığın ayrıntıda değil itikadî temelde olduğu gösterilir; her iddia sayfa künyeli "
    "birebir alıntıyla belgelenmiş ve kaynak sayfaya karşı makine ile doğrulanmıştır."
)


def selections() -> list[dict]:
    """Elle düzeltilmiş bölümlerin künyesi (secim/index.json)."""
    path = ROOT / "secim" / "index.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("selections", [])


def inferred_labels() -> dict[str, int]:
    """page_id -> basılı sayfa, yalnız numarası taramada basılı olmayan sayfalar için.

    Bölüm açılış sayfalarına numara basılmaz; korpus onları "numarasız" bırakır.
    secim/ bu sayfaların yerini komşularından çıkarmıştır (inferred_page). Dizinde
    "tarama 23r" yerine "1 (çıkarım)" gösterebilmek için o bilgi buradan okunur."""
    out: dict[str, int] = {}
    for sel in selections():
        path = ROOT / "secim" / sel["slug"] / "sayfalar.jsonl"
        if not path.exists():
            continue
        for row in read_jsonl(path):
            if row.get("printed_page") is None and row.get("inferred_page"):
                out[row["page_id"]] = row["inferred_page"]
    return out

# Metin ve veri toplayan botlar. Bu proje bilinçli olarak hepsine izin verir:
# amaç, kaynakların yapay zekâ modellerince okunup referans alınmasıdır.
AI_CRAWLERS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User",
    "ClaudeBot", "Claude-Web", "anthropic-ai", "Claude-SearchBot",
    "Google-Extended", "GoogleOther",
    "PerplexityBot", "Perplexity-User",
    "CCBot", "Applebot-Extended", "Bytespider",
    "meta-externalagent", "FacebookBot",
    "Amazonbot", "cohere-ai", "Diffbot", "Timpibot", "YouBot",
]

CSS = """\
:root{--bg:#fbfaf7;--fg:#1c1a17;--mut:#6b645c;--acc:#7a4a2b;--bd:#e3ded4;--card:#fff;
 --r-alinti:#1550c8;--r-ayet:#177a3f;--r-bulgu:#b3231e}
@media(prefers-color-scheme:dark){:root{--bg:#16150f;--fg:#ece7dd;--mut:#a49c90;--acc:#d6a77a;--bd:#332f26;--card:#1e1c15;
 --r-alinti:#8ab4ff;--r-ayet:#7ed295;--r-bulgu:#ff8f88}}
*{box-sizing:border-box}
html{font-size:16px}
body{margin:0;background:var(--bg);color:var(--fg);
 font:1.0625rem/1.72 Georgia,'Iowan Old Style','Times New Roman',serif;}
.wrap{max-width:44rem;margin:0 auto;padding:1.5rem 1.15rem 4rem}
/* Geniş monitörde sayfa, ortada ince bir şerit halinde kalmasın. Sayfadaki
   bütün ölçüler rem'e bağlı olduğu için kök puntoyu büyütmek sütunu, başlıkları
   ve boşlukları birlikte büyütür; satırdaki harf sayısı (~80) değişmediği için
   sütun genişlerken metin okunaksız hâle gelmez. 992px altında (telefon,
   tablet) ölçü olduğu gibi kalır. */
@media(min-width:992px){html{font-size:17px}.wrap{padding:2rem 1.5rem 5rem}}
@media(min-width:1344px){html{font-size:18px}.wrap{max-width:45rem}}
@media(min-width:1760px){html{font-size:19px}.wrap{max-width:46rem}}
header.site{border-bottom:1px solid var(--bd);margin-bottom:1.5rem;padding-bottom:.9rem}
a{color:var(--acc)}
h1{font-size:1.6rem;line-height:1.3;margin:.2rem 0 .5rem}
h2{font-size:1.15rem;margin:2rem 0 .6rem;color:var(--acc)}
.meta{color:var(--mut);font-size:.86rem;line-height:1.55}
.cite{background:var(--card);border:1px solid var(--bd);border-left:3px solid var(--acc);
 padding:.65rem .85rem;margin:1.1rem 0;font-size:.85rem;color:var(--mut);border-radius:3px}
.cite b{color:var(--fg)}
.pagetext{white-space:pre-wrap;margin:1.2rem 0;font-size:1.02rem}
nav.pager{display:flex;justify-content:space-between;gap:1rem;margin:2rem 0 0;
 padding-top:1rem;border-top:1px solid var(--bd);font-size:.9rem}
ul.toc{list-style:none;padding:0}
ul.toc li{padding:.28rem 0;border-bottom:1px solid var(--bd)}
.grid{display:grid;gap:.9rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
.card{background:var(--card);border:1px solid var(--bd);border-radius:5px;padding:1rem}
.pill{display:inline-block;background:var(--card);border:1px solid var(--bd);border-radius:999px;
 padding:.12rem .6rem;font-size:.76rem;color:var(--mut);margin:.15rem .2rem .15rem 0}
code{background:var(--card);border:1px solid var(--bd);border-radius:3px;padding:.1rem .3rem;font-size:.85em}
.warn{background:var(--card);border:1px solid var(--bd);border-left:3px solid #b5852f;
 padding:.7rem .9rem;font-size:.85rem;border-radius:3px;margin:1rem 0}
.ok{background:var(--card);border:1px solid var(--bd);border-left:3px solid #4a7c3f;
 padding:.7rem .9rem;font-size:.85rem;border-radius:3px;margin:1rem 0}
h3{font-size:1.02rem;margin:1.7rem 0 .4rem}
h4{font-size:.94rem;margin:1.3rem 0 .3rem;color:var(--mut)}
/* Bulgu, alıntı ve ayet aynı başlığın altındadır ve aynı görünür: ölçü,
   punto, gövde rengi ve sol çizgi tek kuraldan gelir. Ayrımı yalnız
   işaretin rengi taşır (.r-alinti / .r-ayet / .r-bulgu). */
blockquote,p.bulgu{border-left:3px solid var(--bd);margin:1rem 0;padding:.15rem 0 .15rem .95rem;
 color:var(--mut);font-size:.95rem}
/* İncelemenin indeks işaretleri: alıntı mavi, ayet yeşil, bulgu kırmızı.
   Sınıf seçicisi 'a' seçicisini yener; bağlı işaret de kendi rengini alır. */
.r-alinti{color:var(--r-alinti)}
.r-ayet{color:var(--r-ayet)}
.r-bulgu{color:var(--r-bulgu)}
.tablewrap{overflow-x:auto;margin:1.1rem 0}
table{border-collapse:collapse;width:100%;font-size:.87rem}
th,td{border:1px solid var(--bd);padding:.4rem .55rem;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:bold}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--bd);
 color:var(--mut);font-size:.82rem}
img.sayac{height:1.15em;width:auto;opacity:.8;vertical-align:-.22em}
details.k2,details.k3,details.k4{margin:0}
details.k2>summary,details.k3>summary,details.k4>summary{cursor:pointer;list-style:none;display:flex;
 align-items:baseline;gap:.5rem}
details.k2>summary::-webkit-details-marker,
details.k3>summary::-webkit-details-marker,
details.k4>summary::-webkit-details-marker{display:none}
details.k2>summary::before,details.k3>summary::before,
details.k4>summary::before{content:"+";flex:0 0 auto;
 font-weight:bold;color:var(--mut);width:1em;text-align:center}
details.k2[open]>summary::before,details.k3[open]>summary::before,
details.k4[open]>summary::before{content:"−"}
details.k2>summary h2,details.k3>summary h3,details.k4>summary h4{margin:0}
details.k2>summary:hover h2,details.k3>summary:hover h3,
details.k4>summary:hover h4{text-decoration:underline}
details.k3{margin-left:1.15rem}
details.k4{margin-left:1.15rem}
p.sayac{margin:1.2rem 0 0;text-align:center}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# Okuma sayacı. GitHub Pages ziyaretçi saymaz; sayfanın kendi altına konan bu
# rozet dış bir hizmetten (books.json -> channels.counter) gelir ve sayım sayfa
# başınadır. Alan boşsa hiç basılmaz. Rozet <img> olduğu için hizmet çökse
# sayfa etkilenmez; genişlik/yükseklik CSS'te sabit, yerleşme kaymaz.
def hf_ogesi() -> str:
    """Altbilgideki Hugging Face bağı. Kanal tanımsızsa boş döner."""
    if not HF_URL:
        return ""
    return f'<a href="{esc(HF_URL)}">Hugging Face</a>'


def ia_ogesi() -> str:
    """Altbilgideki Internet Archive bağı. Künyede adres yoksa boş döner."""
    if not IA_URL:
        return ""
    return f'<a href="{esc(IA_URL)}">Internet Archive</a>'


def sayac_ogesi(canonical: str) -> str:
    """Rozetin kendisi. Altbilgi satırının son öğesi olarak kullanılır.

    loading="lazy" konmaz: rozet sayfanın en altındadır, tembel yüklemede yalnız
    sonuna kadar kaydıran okuyucu sayılırdı — üstelik tarayıcı çoğu zaman hiç
    yüklemiyordu. referrerpolicy sayımı etkilemez (anahtar adresin içinde)."""
    if not SAYAC or not canonical:
        return ""
    yol = re.sub(r"^https?://", "", canonical).rstrip("/")
    if not yol:
        return ""
    return (f'<img class="sayac" src="{esc(SAYAC.replace("{yol}", yol))}" '
            f'alt="Bu sayfanın ziyaret sayısı" referrerpolicy="no-referrer">')


def sayac_yerlestir(body: str, canonical: str) -> str:
    """Rozeti altbilginin sonuna, " · " ile ayrılmış son öğe olarak koyar.

    İnceleme sayfalarında altbilgi zaten " · " ile dizilmiş bir satır; rozet
    oraya DOI'den sonra kendisi ekleniyor. Bu işlev kalan sayfaları karşılar:
    altbilgi varsa kapanıştan hemen önce, yoksa gövdenin sonuna."""
    rozet = sayac_ogesi(canonical)
    if not rozet or 'class="sayac"' in body:
        return body
    kapanis = body.rfind("</footer>")
    if kapanis == -1:
        return body + f'<p class="sayac">{rozet}</p>'
    return body[:kapanis] + " · " + rozet + body[kapanis:]


def shell(
    title: str,
    body: str,
    desc: str,
    jsonld: dict | None = None,
    canonical: str = "",
    lang: str = "tr",
    alternate: tuple[str, str] | None = None,
    head_extra: str = "",
) -> str:
    ld = (
        f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
        if jsonld
        else ""
    )
    can = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    if alternate:
        alt_lang, alt_url = alternate
        can += (
            f'<link rel="alternate" hreflang="{alt_lang}" href="{esc(alt_url)}">'
            f'<link rel="alternate" hreflang="{lang}" href="{esc(canonical)}">'
        )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
{can}
{head_extra}
{ld}
<style>{CSS}</style>
</head>
<body><div class="wrap">{sayac_yerlestir(body, canonical)}</div></body>
</html>
"""


def site_header(depth: int) -> str:
    up = "../" * depth
    return (
        f'<header class="site"><div class="meta">'
        f'<a href="{up}index.html">Tarih Ders Kitapları 1931</a> · '
        f'<a href="{up}ara.html">Arama</a> · '
        f'<a href="{up}duzeltilmis.html">Düzeltilmiş sayfalar</a> · '
        f'<a href="{up}inceleme.html">İnceleme</a> · '
        f'<a href="{up}hakkinda.html">Hakkında</a> · '
        f'<a href="{up}veri.html">Veri &amp; API</a>'
        f"</div></header>"
    )


# ---------------------------------------------------------------------------
# Markdown → HTML.
#
# Bağımlılık eklememek için, docs/ altındaki belgelerin fiilen kullandığı dar
# altkümeyi çevirir: başlık, tablo, alıntı, sıralı/sırasız liste, yatay çizgi,
# kalın/eğik/kod/bağlantı. Kod bloğu ve iç içe liste yoktur, desteklenmez.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


def build_page_html(book: Book, row: dict, prev_row, next_row) -> str:
    bm = BOOKMETA[book.slug]
    lbl = page_label(row)
    title = f"{bm['title']} {bm['volume']} ({bm['year']}), s. {lbl}"
    head = row.get("running_head")
    url = f"{BASE_URL}/{book.slug}/{page_slug(row)}.html"

    snippet = " ".join(row["text"].split())[:250]
    corrected = row.get("text_source") == "corrected"
    conf = row.get("page_confidence")
    conf_note = ""
    if corrected:
        conf_note = (
            '<div class="ok">Bu sayfanın metni <b>taranmış aslıyla karşılaştırılarak elle '
            "düzeltilmiştir</b>; sitedeki diğer sayfalar gibi ham OCR değildir. Ham OCR metni "
            "aynı kayıtta <code>text_ocr</code> alanında saklanır. "
            '<a href="../duzeltilmis.html">Düzeltilmiş sayfaların tamamı →</a></div>'
        )
    # Metnin doğruluğu ile sayfa numarasının doğruluğu ayrı meselelerdir: elle
    # düzeltilmiş bir sayfanın numarası yine de çıkarım olabilir. İkisi de gösterilir.
    if conf == "inferred":
        conf_note += (
            '<div class="warn">Bu sayfanın numarası taramada okunamadığı için sayfa dizisinden '
            "çıkarılmıştır. Kritik alıntılarda tarama görüntüsünden teyit ediniz.</div>"
        )
    elif conf == "uncertain":
        conf_note += (
            '<div class="warn">Bu sayfanın numarası <b>şüphelidir</b> (tek/çift beklentisine '
            "uymuyor). Alıntı öncesi tarama görüntüsünden mutlaka teyit ediniz.</div>"
        )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": url,
        "url": url,
        "name": title,
        "inLanguage": "tr",
        "isPartOf": {
            "@type": "Book",
            "name": bm["title_full"],
            "datePublished": str(bm["year"]),
            "author": {"@type": "Organization", "name": COLL["corporate_author"]["name_1931"]},
            "publisher": {"@type": "Organization", "name": bm["publisher"]},
        },
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "text": row["text"][:5000],
        "citation": row["citation"],
        "pagination": str(lbl),
    }

    body = [site_header(1)]
    body.append(f"<h1>{esc(bm['title'])} {esc(bm['volume'])} — sayfa {esc(lbl)}</h1>")
    body.append(
        f'<p class="meta">{esc(bm["title_full"])} · '
        f'{esc(COLL["corporate_author"]["name_1931"])} · {esc(bm["place"])}, {bm["year"]}'
        + (f" · <b>{esc(head)}</b>" if head else "")
        + "</p>"
    )
    body.append(conf_note)
    body.append(f'<div class="pagetext">{esc(row["text"])}</div>')
    body.append(
        f'<div class="cite"><b>Alıntı:</b> {esc(row["citation"])}<br>'
        f'<b>Sayfa kimliği:</b> <code>{esc(row["page_id"])}</code><br>'
        f'<b>Kaynak tarama:</b> <a href="{esc(bm["ttk_url"])}">TTK Kütüphanesi</a>, '
        f'tarama sayfası {row["scan_ref"]["pdf_page_1based"]} '
        f'({"sol" if row["side"] == "verso" else "sağ"})</div>'
    )
    nav = ['<nav class="pager">']
    nav.append(
        f'<a href="{page_slug(prev_row)}.html">← s. {esc(page_label(prev_row))}</a>' if prev_row else "<span></span>"
    )
    nav.append(f'<a href="index.html">içindekiler</a>')
    nav.append(
        f'<a href="{page_slug(next_row)}.html">s. {esc(page_label(next_row))} →</a>' if next_row else "<span></span>"
    )
    nav.append("</nav>")
    body.append("".join(nav))
    body.append(
        f"<footer>"
        + (
            "Bu sayfanın metni taramayla karşılaştırılarak elle düzeltilmiştir. "
            if corrected
            else "Metin OCR çıktısıdır, elle düzeltilmemiştir. "
        )
        + f'Türetilmiş veri {esc(RIGHTS["derived_dataset_license"])}.</footer>'
    )
    return shell(title, "".join(body), snippet, jsonld, url)


def build_book_index(book: Book, rows: list[dict], sections: list[dict]) -> str:
    bm = BOOKMETA[book.slug]
    body = [site_header(1)]
    body.append(f"<h1>{esc(bm['title_full'])}</h1>")
    body.append(
        f'<p class="meta">{esc(COLL["corporate_author"]["name_1931"])} · '
        f'{esc(bm["publisher"])} · {esc(bm["place"])}, {bm["year"]}<br>'
        f'{esc(bm["approval"])}<br>{esc(bm["illustrations_statement"])}</p>'
    )
    body.append(
        f'<div class="cite"><b>Tam metin dosyaları:</b> '
        f'<a href="full.txt">düz metin</a> · '
        f'<a href="{book.slug}.md">markdown</a> · '
        f'<a href="{book.slug}.tei.xml">TEI-XML</a> · '
        f'<a href="pages.jsonl">pages.jsonl</a> · '
        f'<a href="chunks.jsonl">chunks.jsonl</a></div>'
    )
    if sections:
        body.append("<h2>Bölümler</h2><ul class='toc'>")
        for s in sections:
            tgt = f"s{s['start_page']:04d}.html" if s.get("start_page") else "#"
            rng = f"s. {s['start_page']}–{s['end_page']}" if s.get("start_page") else ""
            body.append(f'<li><a href="{tgt}">{esc(s["heading"])}</a> <span class="meta">{rng}</span></li>')
        body.append("</ul>")

    body.append("<h2>Sayfalar</h2><p>")
    for row in rows:
        if row["is_empty"]:
            continue
        body.append(f'<a class="pill" href="{page_slug(row)}.html">{esc(page_label(row))}</a>')
    body.append("</p>")
    body.append("<footer>Türk Tarih Kurumu Kütüphanesi taramasından üretilmiştir.</footer>")
    return shell(
        bm["title_full"],
        "".join(body),
        f'{bm["title_full"]} — tam metin, sayfa sayfa.',
        json.loads((META_DIR / "schema-org" / f"{book.slug}.jsonld").read_text(encoding="utf-8")),
        f"{BASE_URL}/{book.slug}/",
    )


def build_home(all_rows: dict[str, list[dict]]) -> str:
    body = [site_header(0)]
    body.append(f"<h1>{esc(COLL['name'])}</h1>")
    body.append(f"<p>{esc(COLL['description'])}</p>")
    body.append('<div class="grid">')
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        rows = all_rows[b.slug]
        n = len([r for r in rows if not r["is_empty"]])
        body.append(
            f'<div class="card"><h2 style="margin-top:0">'
            f'<a href="{b.slug}/index.html">{esc(bm["title_full"])}</a></h2>'
            f'<p class="meta">{esc(bm["place"])}, {bm["year"]} · {n} sayfa<br>'
            f'{esc(bm["illustrations_statement"])}</p></div>'
        )
    body.append("</div>")
    body.append("<h2>Bu proje ne yapar?</h2>")
    body.append(
        "<p>1931–1941 arasında Türkiye'de liselerde <b>resmî tarih ders kitabı</b> olarak "
        "okutulan Tarih serisinin taranmış nüshaları, makine-okunabilir ve "
        "<b>sayfa sayfa alıntılanabilir</b> hale getirilmiştir. Her basılı sayfanın kendi kalıcı "
        "adresi, künyesi ve tarama referansı vardır; böylece bir iddia doğrudan basılı sayfaya "
        "kadar izlenebilir.</p>"
    )
    body.append(
        '<div class="warn">Metinlerin <b>tamamı düzeltilmemiş OCR</b> çıktısıdır. Bilimsel alıntı '
        "yapmadan önce ilgili sayfayı kaynak taramadan teyit ediniz; her sayfada tarama referansı "
        "verilmiştir. Aşağıdaki iki bölüm bunun istisnasıdır.</div>"
    )
    n_corr = sum(len([r for r in rows if r.get("text_source") == "corrected"]) for rows in all_rows.values())
    body.append("<h2>Doğrulanmış çekirdek</h2>")
    body.append(
        f"<p>İki bölüm — toplam <b>{n_corr} sayfa</b> — taranmış aslıyla sayfa sayfa "
        "karşılaştırılarak elle düzeltilmiştir. Alıntı yapacaksanız bu sayfaları tercih ediniz.</p>"
    )
    body.append('<ul class="toc">')
    for sel in selections():
        lo, hi = sel["printed_range"]
        body.append(
            f'<li><a href="duzeltilmis.html">{esc(sel["heading"])}</a> — '
            f'{esc(sel["book_title"].split(":")[0])}, basılı s. {lo}-{hi} '
            f'<span class="pill">{sel.get("pages_body", 0)} sayfa</span></li>'
        )
    # İngilizce sürüm ana sayfadan bağlanmazsa üç tık derinde kalıyor: index →
    # inceleme.html → review.html. Erişimin büyük kısmı İngilizce üzerinden
    # işlediği için bir adım öne alınır.
    body.append(
        f'<li><a href="inceleme.html">{esc(REVIEW_TITLE)}</a> — bu sayfalar üzerine, her iddiası '
        'sayfa künyeli alıntıyla belgelenmiş inceleme <span class="pill">CC0</span>'
        + (' · <a href="review.html">English version</a>' if REVIEW_EN_MD.exists() else "")
        # Giriş sayfası (inceleme.html) özettir; delillerin tamamına ana
        # sayfadan tek adımda ulaşılabilsin.
        + ('. Bütün delil aygıtını — 46 alıntının, 38 ayetin ve 19 bulgunun '
           'tamamını — veren <a href="inceleme-kapsamli.html">kapsamlı metin</a> '
           'ayrı sayfadadır.' if REVIEW_FULL_MD.exists() else "")
        + '</li>'
    )
    body.append("</ul>")
    body.append("<h2>Kaynak</h2>")
    body.append(
        f'<p class="meta">Taramalar: '
        f'<a href="{esc(META["source_repository"]["url"])}">'
        f'{esc(META["source_repository"]["name"])}</a> · yer numarası '
        f'<code>{esc(META["source_repository"]["call_number"])}</code></p>'
    )
    body.append(channels_block())
    body.append(citation_block())
    body.append('<p><a href="veri.html">Veri kümesi, API ve indirme biçimleri →</a></p>')
    body.append("<footer>Türetilmiş veri CC0 1.0. Kaynak eser kamu malıdır (bkz. Hakkında).</footer>")
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Collection",
        "@id": BASE_URL + "/",
        "name": COLL["name"],
        "description": COLL["description"],
        "inLanguage": "tr",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "hasPart": [
            {"@type": "Book", "name": BOOKMETA[b.slug]["title_full"], "url": f"{BASE_URL}/{b.slug}/"}
            for b in BOOKS
        ],
        # Arama motoru ve dil modeli, aynı korpusun Zenodo/HuggingFace/Internet
        # Archive/Vikikaynak/Wikidata nüshalarını ancak buradan birbirine bağlar.
        "sameAs": [url for _etiket, url, _ne in channel_rows()],
    }
    return shell(COLL["name"], "".join(body), COLL["description"], jsonld, BASE_URL + "/")


def build_about() -> str:
    body = [site_header(0), "<h1>Hakkında</h1>"]
    body.append("<h2>Kaynak eser</h2>")
    body.append(
        f'<p>{esc(COLL["description"])} Kitapların kurumsal yazarı '
        f'<b>{esc(COLL["corporate_author"]["name_1931"])}</b>dir. '
        f'{esc(COLL["corporate_author"]["note"])}</p>'
    )
    body.append("<h2>Kitabın hazırlanmasında çalışanlar</h2><ul class='toc'>")
    for c in COLL["contributors"]:
        body.append(
            f'<li><b>{esc(c["name_1931"])}</b>'
            + (f' <span class="meta">({esc(c["name_modern"])})</span>' if c["name_modern"] != c["name_1931"] else "")
            + f'<br><span class="meta">{esc(c["role_1931"])}</span></li>'
        )
    body.append("</ul>")
    body.append(f'<p class="meta">{esc(COLL["contributor_note"])}</p>')
    body.append("<h2>Nasıl üretildi?</h2>")
    body.append(
        "<p>Kaynak PDF'lerde her tarama sayfası bir <i>açık kitap</i> (çift sayfa) görüntüsüdür. "
        "İşleme hattı cilt payını tespit edip sol ve sağ sayfayı ayırır, kütüphane filigranını "
        "temizler, satırları koordinatlarına göre gerçek okuma sırasına dizer.</p>"
        "<p>Taramaların gömülü OCR katmanında <b>sayfa numaraları ve bölüm başlıkları yoktur</b> — "
        "tarayıcı yazılım bunları atmıştır. Alıntılanabilirliğin tek dayanağı basılı sayfa numarası "
        "olduğu için bu şerit tarama görüntüsünden yeniden OCR edilmiş; ardından sayfa numaralarının "
        "birer birer artması ve sol sayfanın çift / sağ sayfanın tek olması kısıtlarıyla "
        "doğrulanmıştır.</p>"
    )
    body.append("<h2>Haklar</h2>")
    body.append(f'<p>{esc(RIGHTS["reasoning"])}</p>')
    body.append(f'<p class="meta">{esc(RIGHTS["derived_dataset_note"])}</p>')
    body.append("<h2>Sınırlar</h2>")
    body.append(
        "<ul><li>Metin <b>elle düzeltilmemiş OCR</b> çıktısıdır; 1931 imlası ve Osmanlı Türkçesi "
        "kelime dağarcığı OCR hata oranını yükseltir.</li>"
        "<li>Kenar boşluğundaki omuz başlıkları gövde metnine karışabilir.</li>"
        "<li>Resim altı yazıları ve harita etiketleri eksik veya bozuk olabilir.</li>"
        "<li>Numarasız levha sayfaları dizide boşluk olarak görünür.</li></ul>"
    )
    return shell("Hakkında — " + COLL["name"], "".join(body), "Kaynak, yöntem, haklar ve sınırlar.", None, f"{BASE_URL}/hakkinda.html")


def channel_rows() -> list[tuple[str, str, str]]:
    """Aynı korpusun yayımlandığı diğer yerler: (etiket, adres, ne olduğu).

    Kanal listesi tek yerde (metadata/books.json -> channels ve kitap
    kayıtlarındaki alanlar) durur. Site, llms.txt ve veri kümesi kartı bu
    listeden üretilir; bir kanal eklenince üçü birden öğrenir.
    """
    rows: list[tuple[str, str, str]] = []
    if DOI:
        rows.append((
            "Zenodo", f"https://doi.org/{DOI}",
            "arşiv nüshası ve DOI — atıf buraya yapılır, adres bütün sürümleri temsil eder",
        ))
    if CHANNELS.get("huggingface"):
        rows.append((
            "Hugging Face", CHANNELS["huggingface"],
            "veri kümesi olarak: ham korpus, elle doğrulanmış alt küme, RAG parçaları, inceleme",
        ))
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("internet_archive"):
            rows.append((
                f'Internet Archive — {bm["title"]} {bm["volume"]}', bm["internet_archive"],
                "kaynak taramanın tam nüshası (PDF)",
            ))
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("wikisource_work"):
            rows.append((
                f'Vikikaynak — {bm["title"]} {bm["volume"]}', bm["wikisource_work"],
                "elle düzeltilmiş bölümlerin istinsahı, taramayla yan yana",
            ))
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("wikidata"):
            rows.append((
                f'Wikidata — {bm["title"]} {bm["volume"]}',
                f'https://www.wikidata.org/wiki/{bm["wikidata"]}',
                "kitabın künye kaydı (bilgi grafiği)",
            ))
    if CHANNELS.get("repository"):
        rows.append((
            "GitHub", CHANNELS["repository"],
            "işleme hattının kaynak kodu, düzeltmeler ve sürüm geçmişi",
        ))
    # İnceleme ayrı bir çalışmadır ve kendi kanalları vardır; korpusunkilerle
    # karışmasın diye ayrı ad taşırlar.
    inc = META.get("review") or {}
    if inc.get("doi"):
        rows.append((
            "Zenodo — inceleme", f"https://doi.org/{inc['doi']}",
            "incelemenin kendi arşiv kaydı ve DOI'si",
        ))
    if inc.get("internet_archive"):
        rows.append((
            "Internet Archive — inceleme", inc["internet_archive"],
            "incelemenin PDF, Markdown ve JSONL nüshaları",
        ))
    if inc.get("wikidata"):
        rows.append((
            "Wikidata — inceleme", f"https://www.wikidata.org/wiki/{inc['wikidata']}",
            "incelemenin künye kaydı (bilgi grafiği)",
        ))
    return rows


def channels_block() -> str:
    rows = channel_rows()
    if not rows:
        return ""
    out = ["<h2>Yayın kanalları</h2>",
           '<p class="meta">Aynı korpus aşağıdaki yerlerde de durur; hepsi aynı metinden üretilir.</p>',
           '<ul class="toc">']
    for etiket, url, ne in rows:
        out.append(f'<li><a href="{esc(url)}">{esc(etiket)}</a> — {esc(ne)}</li>')
    out.append("</ul>")
    return "".join(out)


def citation_block() -> str:
    """Görünür atıf künyesi. DOI tescil edilmemişse hiç basılmaz."""
    if not DOI:
        return ""
    return (
        '<div class="cite"><b>Atıf / Cite as:</b><br>'
        f'{esc(COLL["corporate_author"]["name_1931"])} ({TODAY[:4]}). '
        f'<i>{esc(COLL["name"])} — makine-okunabilir tam metin</i>. '
        f'Zenodo. <a href="https://doi.org/{esc(DOI)}">https://doi.org/{esc(DOI)}</a>'
        "</div>"
    )


def build_data_page() -> str:
    body = [site_header(0), "<h1>Veri kümesi, API ve biçimler</h1>"]
    body.append(citation_block())
    body.append("<h2>Dosya biçimleri</h2><ul class='toc'>")
    for name, desc in [
        ("full.txt", "Sayfa işaretli düz metin ([[s. N]]). Dil modeline doğrudan yapıştırmak için."),
        ("&lt;kitap&gt;.md", "Sayfa çıpalı Markdown."),
        ("&lt;kitap&gt;.tei.xml", "TEI P5 — bilimsel arşiv standardı, &lt;pb/&gt; sayfa sınırlarıyla."),
        ("pages.jsonl", "Sayfa başına bir JSON kaydı: metin + künye + tarama referansı."),
        ("chunks.jsonl", "RAG için hazır parçalar; her parça sayfa aralığı künyesi taşır."),
        ("structure.json", "Bölüm haritası."),
    ]:
        body.append(f"<li><code>{name}</code> — <span class='meta'>{desc}</span></li>")
    body.append("</ul>")
    body.append("<h2>Kitaplar</h2><ul class='toc'>")
    for b in BOOKS:
        body.append(
            f'<li><a href="{b.slug}/index.html">{esc(BOOKMETA[b.slug]["title_full"])}</a> — '
            f'<a href="{b.slug}/pages.jsonl">pages.jsonl</a>, '
            f'<a href="{b.slug}/full.txt">full.txt</a>, '
            f'<a href="{b.slug}/{b.slug}.tei.xml">TEI</a></li>'
        )
    body.append("</ul>")
    body.append("<h2>Metadata</h2><ul class='toc'>")
    for name, desc in [
        ("metadata/croissant.json", "MLCommons Croissant — HuggingFace veri kümesi tanımı"),
        ("metadata/datacite.xml", "DataCite — DOI tescili"),
        ("metadata/dublin-core/", "Dublin Core / OAI-DC — kütüphane toplayıcıları"),
        ("metadata/marc21/", "MARC21-XML — kütüphane katalogları"),
        ("metadata/schema-org/", "schema.org JSON-LD — arama motorları"),
    ]:
        body.append(f'<li><a href="{name}">{name}</a> — <span class="meta">{desc}</span></li>')
    body.append("</ul>")
    body.append("<h2>Yapay zekâ tarayıcıları</h2>")
    body.append(
        "<p>Bu site <code>robots.txt</code> içinde tüm büyük yapay zekâ tarayıcılarına açıkça izin "
        "verir ve <a href='llms.txt'>llms.txt</a> ile makine-okunabilir bir içerik haritası sunar. "
        "Amaç, bu resmî kaynakların modellerce okunup doğru sayfa numarasıyla referans "
        "alınabilmesidir.</p>"
    )
    return shell("Veri ve API — " + COLL["name"], "".join(body), "İndirme biçimleri, metadata şemaları ve API.", None, f"{BASE_URL}/veri.html")


# ---------------------------------------------------------------------------


SEARCH_JS = """
const F={'â':'a','Â':'a','î':'i','Î':'i','û':'u','Û':'u','İ':'i','I':'i','ı':'i',
'Ü':'u','ü':'u','Ö':'o','ö':'o','Ç':'c','ç':'c','Ş':'s','ş':'s','Ğ':'g','ğ':'g'};
const fold=s=>s.replace(/[âÂîÎûÛİIıÜüÖöÇçŞşĞğ]/g,c=>F[c]).toLowerCase();
let IDX=null;
const el=id=>document.getElementById(id);
async function load(){if(IDX)return IDX;
  el('status').textContent='indeks yükleniyor…';
  IDX=await (await fetch('search-index.json')).json();
  IDX.forEach(r=>r._f=fold(r.t)); return IDX;}
async function run(){
  const q=el('q').value.trim(); if(!q){el('out').innerHTML='';el('status').textContent='';return;}
  const idx=await load(); const fq=fold(q);
  const book=el('book').value;
  const hits=idx.filter(r=>(!book||r.b===book)&&r._f.includes(fq)).slice(0,120);
  el('status').textContent=hits.length+' sonuç'+(hits.length>=120?' (ilk 120)':'');
  el('out').innerHTML=hits.map(r=>{
    const i=r._f.indexOf(fq); const s=Math.max(0,i-90);
    const raw=r.t.slice(s,i+160);
    const safe=raw.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
    const lbl=r.p!=null?('s. '+r.p):'numarasız';
    const bk=r.b==='tarih-1-1931'?'Tarih I':'Tarih II';
    return `<div class="card" style="margin:.6rem 0"><a href="${r.u}"><b>${bk}, ${lbl}</b></a>`+
      (r.h?` <span class="meta">— ${r.h}</span>`:'')+
      `<div class="meta" style="margin-top:.35rem">…${safe}…</div></div>`;}).join('');
}
el('q').addEventListener('input',()=>{clearTimeout(window._t);window._t=setTimeout(run,220);});
el('book').addEventListener('change',run);
const p=new URLSearchParams(location.search).get('q');
if(p){el('q').value=p;run();}
"""


# İncelemenin yayın paketi; PDF'i site üzerinden de sunulur.
REVIEW_PDF = ROOT / "inceleme" / "yayin" / "inceleme-tr.pdf"
REVIEW_OZ_PDF = ROOT / "inceleme" / "yayin" / "inceleme-oz-tr.pdf"
REVIEW_EN_PDF = ROOT / "inceleme" / "yayin" / "inceleme-en.pdf"


def scholar_meta(baslik: str, dil: str, pdf_adi: str, sayfa_url: str) -> str:
    """Google Scholar'ın aradığı Highwire Press etiketleri.

    Scholar bir sayfayı ancak bu etiketlerle "makale" sayar: başlık, yazar,
    tarih ve **aynı sunucudan erişilebilir bir PDF**. Bunlar olmadan metin,
    ne kadar iyi künyelenmiş olursa olsun, akademik dizinlerde görünmez —
    Zenodo kaydı ayrı bir kanaldır ve Scholar'ın oraya uğraması garanti değildir.
    """
    etiket = [
        ("citation_title", baslik),
        *[("citation_author", a) for a in REVIEW_AUTHORS],
        ("citation_publication_date", TODAY.replace("-", "/")),
        ("citation_online_date", TODAY.replace("-", "/")),
        ("citation_language", dil),
        ("citation_abstract_html_url", sayfa_url),
        ("citation_public_url", sayfa_url),
        ("citation_technical_report_institution", "Zenodo"),
    ]
    if REVIEW_DOI:
        etiket.append(("citation_doi", REVIEW_DOI))
    if pdf_adi:
        etiket.append(("citation_pdf_url", f"{BASE_URL}/{pdf_adi}"))
    return "".join(f'<meta name="{k}" content="{esc(v)}">' for k, v in etiket)


# Katlanabilir bölümler. İnceleme uzun bir belge; ekranda tamamı açık geldiğinde
# okuyucu nereden başlayacağını göremiyordu. h2 tıklanınca alt başlıklar, h3
# tıklanınca alıntı-ayet-bulgu blokları açılır. İçerik DOM'da durmaya devam eder:
# <details> gizler ama silmez, dolayısıyla arama motorları ve dil modelleri
# metnin tamamını görür, sayfa içi arama da çalışır.
def katlanabilir(govde: str) -> str:
    """h2 ve h3 başlıklarını <details>/<summary> içine alır."""

    def sar(parca: str, seviye: int) -> str:
        kalip = re.compile(rf'(<h{seviye} id="[^"]*">.*?</h{seviye}>)', re.S)
        parcalar = kalip.split(parca)
        if len(parcalar) < 3:
            return parca
        out = [parcalar[0]]
        for i in range(1, len(parcalar), 2):
            baslik, govde_ic = parcalar[i], parcalar[i + 1]
            if seviye < 4:
                govde_ic = sar(govde_ic, seviye + 1)
            # Bölüm sonundaki ayraç dışarıda kalsın, kutunun içinde çirkin duruyor
            son = ""
            if govde_ic.rstrip().endswith("<hr>"):
                govde_ic = govde_ic.rstrip()[: -len("<hr>")]
                son = "<hr>"
            out.append(f'<details class="k{seviye}"><summary>{baslik}</summary>'
                       f"{govde_ic}</details>{son}")
        return "".join(out)

    ic = sar(govde, 2)
    # Derin bağlantı: kapalı bir bölümün içindeki bir başlığa bağlantıyla
    # gelindiğinde tarayıcı oraya kaydıramaz; üst <details> öğeleri elle açılır.
    betik = (
        "<script>"
        "function acHedef(){var h=location.hash;if(!h||h.length<2)return;"
        "var t=document.getElementById(decodeURIComponent(h.slice(1)));if(!t)return;"
        "var p=t.closest('details');while(p){p.open=true;p=p.parentElement&&"
        "p.parentElement.closest('details')}t.scrollIntoView()}"
        "addEventListener('hashchange',acHedef);acHedef();</script>"
    )
    return ic + betik


def build_review_page(oz: bool) -> str:
    """İnceleme sayfaları: inceleme.html (özet) ve inceleme-kapsamli.html.

    inceleme.html incelemenin öz hâlidir ve okuyucunun giriş sayfasıdır;
    kapsamlı sayfa bütün delil aygıtını taşır. Akademik kimlik — Scholar
    etiketleri, DOI'nin JSON-LD kimliği, İngilizce hreflang eşi — kapsamlı
    sayfadadır: Zenodo kaydıyla ve İngilizce çeviriyle birebir örtüşen metin
    odur. Sayfa doğrudan incelemenin kendisiyle açılır: site menüsü, kapsam
    kutusu, atıf künyesi ve içindekiler bilerek yoktur — okuma sayfası metinle
    başlar. Makineye giden bilgi bundan etkilenmez: künye, DOI, PDF adresi ve
    İngilizce sürüm bağı sayfa başlığındaki (head) etiketlerde durur."""
    ad = "inceleme" if oz else "inceleme-kapsamli"
    url = f"{BASE_URL}/{ad}.html"
    md = REVIEW_MD if oz else REVIEW_FULL_MD
    baslik = REVIEW_OZ_TITLE if oz else REVIEW_TITLE
    pdf = REVIEW_OZ_PDF if oz else REVIEW_PDF
    body: list[str] = []
    toc: list[tuple[int, str, str]] = []
    body.append(katlanabilir(md_to_html(md.read_text(encoding="utf-8"), toc)))
    # Sayfanın başındaki kutu kaldırıldığı için PDF, İngilizce sürüm ve bulgular
    # gövdede hiçbir yerden bağlantı almıyordu: dosyalar sitemap ve
    # citation_pdf_url dışında görünmez kalıyor, bağlantı izleyerek gezen
    # tarayıcılar (GPTBot, CCBot…) onlara hiç uğramıyordu. Metnin bittiği yerde
    # tek satır, sayfanın başını kalabalıklaştırmadan bunu karşılar.
    alt = []
    if pdf.exists():
        alt.append(f'<a href="{ad}.pdf">PDF</a>')
    alt.append('<a href="inceleme-kapsamli.html">Kapsamlı metin</a>' if oz
               else '<a href="inceleme.html">İncelemenin özeti</a>')
    if REVIEW_EN_MD.exists():
        alt.append('<a href="review.html">English version</a>')
    if REVIEW_EMAIL:
        alt.append(f'Yazışma: <a href="mailto:{esc(REVIEW_EMAIL)}">{esc(REVIEW_EMAIL)}</a>')
    alt.append(f'<a href="{ad}.md">ham Markdown</a>')
    if REVIEW_DOI:
        alt.append(f'DOI: <a href="https://doi.org/{esc(REVIEW_DOI)}">{esc(REVIEW_DOI)}</a>')
    alt.append(hf_ogesi())
    alt.append(ia_ogesi())
    alt.append(sayac_ogesi(url))
    body.append(
        f'<footer>{" · ".join(x for x in alt if x)}</footer>'
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": url,
        "url": url,
        "name": baslik,
        "headline": baslik,
        "description": REVIEW_DESC,
        "inLanguage": "tr",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "about": [
            {"@type": "Book", "name": BOOKMETA[b.slug]["title_full"], "url": f"{BASE_URL}/{b.slug}/"}
            for b in BOOKS
        ],
        "encodingFormat": "text/html",
    }
    if oz:
        # Özet ayrı bir çalışma değildir: kimliği kapsamlı metne bağlanır ve
        # DOI özet sayfasının JSON-LD'sine yazılmaz — aynı DOI iki farklı
        # başlıkla dolaşmasın.
        jsonld["isBasedOn"] = {"@type": "ScholarlyArticle",
                               "url": f"{BASE_URL}/inceleme-kapsamli.html",
                               "name": REVIEW_TITLE}
    elif REVIEW_DOI:
        jsonld["identifier"] = f"https://doi.org/{REVIEW_DOI}"
        jsonld["sameAs"] = f"https://doi.org/{REVIEW_DOI}"
    return shell(
        baslik,
        "".join(body),
        REVIEW_DESC,
        jsonld,
        url,
        alternate=None if oz else (
            ("en", f"{BASE_URL}/review.html") if REVIEW_EN_MD.exists() else None),
        head_extra="" if oz else scholar_meta(
            REVIEW_TITLE, "tr", f"{ad}.pdf" if pdf.exists() else "", url),
    )


def build_review_annex_page() -> str:
    """docs/inceleme-ekler.md — incelemenin ekleri (Ek A/B/C/D).

    Ana metinden ayrı bir sayfadır: inceleme okunur kalsın, dayanakları
    (ayet dosyaları, terim dosyaları, ön söz) isteyen okuyucu buraya geçsin."""
    url = f"{BASE_URL}/inceleme-ekler.html"
    toc: list[tuple[int, str, str]] = []
    body = [katlanabilir(md_to_html(REVIEW_ANNEX_MD.read_text(encoding="utf-8"), toc))]
    # Ekler kapsamlı metnin aygıtıdır; "ana metin" bağı da oraya gider.
    alt = ['<a href="inceleme-kapsamli.html">İncelemenin ana metni</a>']
    if REVIEW_ANNEX_EN_MD.exists():
        alt.append('<a href="review-appendices.html">English version</a>')
    alt.append('<a href="inceleme-ekler.md">ham Markdown</a>')
    if REVIEW_EMAIL:
        alt.append(f'Yazışma: <a href="mailto:{esc(REVIEW_EMAIL)}">{esc(REVIEW_EMAIL)}</a>')
    if REVIEW_DOI:
        alt.append(f'DOI: <a href="https://doi.org/{esc(REVIEW_DOI)}">{esc(REVIEW_DOI)}</a>')
    alt.append(hf_ogesi())
    alt.append(ia_ogesi())
    alt.append(sayac_ogesi(url))
    body.append(
        f'<footer>{" · ".join(x for x in alt if x)}</footer>'
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": url,
        "url": url,
        "name": f"{REVIEW_TITLE} — Ekler",
        "inLanguage": "tr",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "isPartOf": {"@type": "ScholarlyArticle", "url": f"{BASE_URL}/inceleme-kapsamli.html",
                     "name": REVIEW_TITLE},
        "encodingFormat": "text/html",
    }
    return shell(
        f"{REVIEW_TITLE} — Ekler",
        "".join(body),
        "İncelemenin ekleri: ayet dosyaları, terim dosyaları, ön söz ve heyet "
        "sayfaları, hükümlerin dayanak tipi.",
        jsonld,
        url,
    )


def build_review_annex_en_page() -> str:
    """docs/REVIEW-APPENDICES-EN.md — eklerin İngilizce sürümü.

    Türkçe eklerin karşılığıdır: alıntılar, lügat maddeleri ve 1931 ön sözü
    alıntılanabilir kalsın diye Türkçe durur, İngilizcesi altlarında verilir."""
    url = f"{BASE_URL}/review-appendices.html"
    toc: list[tuple[int, str, str]] = []
    body = [katlanabilir(md_to_html(REVIEW_ANNEX_EN_MD.read_text(encoding="utf-8"), toc))]
    alt = ['<a href="review.html">Main text of the review</a>',
           '<a href="inceleme-ekler.html">Türkçe aslı</a>',
           '<a href="review-appendices.md">raw Markdown</a>']
    if REVIEW_EMAIL:
        alt.append(f'Correspondence: <a href="mailto:{esc(REVIEW_EMAIL)}">{esc(REVIEW_EMAIL)}</a>')
    if REVIEW_DOI:
        alt.append(f'DOI: <a href="https://doi.org/{esc(REVIEW_DOI)}">{esc(REVIEW_DOI)}</a>')
    alt.append(hf_ogesi())
    alt.append(ia_ogesi())
    alt.append(sayac_ogesi(url))
    body.append(
        f'<footer>{" · ".join(x for x in alt if x)}</footer>'
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": url,
        "url": url,
        "name": f"{REVIEW_EN_TITLE} — Appendices",
        "inLanguage": "en",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "isPartOf": {"@type": "ScholarlyArticle", "url": f"{BASE_URL}/review.html",
                     "name": REVIEW_EN_TITLE},
        "workTranslation": {"@type": "ScholarlyArticle",
                            "url": f"{BASE_URL}/inceleme-ekler.html", "inLanguage": "tr"},
        "encodingFormat": "text/html",
    }
    return shell(
        f"{REVIEW_EN_TITLE} — Appendices",
        "".join(body),
        "Appendices to the review: verse files, term files, the 1931 preface and the "
        "drafting-committee pages, and the grounds of each judgement.",
        jsonld,
        url,
    )


def build_review_en_page() -> str:
    """docs/REVIEW-EN.md — İngilizce sürüm.

    Erişimin büyük kısmı İngilizce üzerinden işler; alıntılar 1931 Türkçesiyle
    kalır, çevirisi yanına konur ve alıntılanabilir metin Türkçe olandır."""
    url = f"{BASE_URL}/review.html"
    # Sayfa doğrudan başlıkla açılır: üst gezinti çubuğu, kapsam notu, atıf
    # kutusu ve içindekiler kaldırıldı. Aynı bağların hepsi altbilgide durur.
    toc: list[tuple[int, str, str]] = []
    body = [katlanabilir(md_to_html(REVIEW_EN_MD.read_text(encoding="utf-8"), toc))]
    alt = []
    if REVIEW_EN_PDF.exists():
        alt.append('<a href="review.pdf">PDF</a>')
    # Çeviri kapsamlı metnin çevirisidir; "Türkçe aslı" da odur.
    alt.append('<a href="inceleme-kapsamli.html">Türkçe aslı</a>')
    if REVIEW_EMAIL:
        alt.append(f'Correspondence: <a href="mailto:{esc(REVIEW_EMAIL)}">{esc(REVIEW_EMAIL)}</a>')
    alt.append('<a href="review.md">raw Markdown</a>')
    if REVIEW_DOI:
        alt.append(f'DOI: <a href="https://doi.org/{esc(REVIEW_DOI)}">{esc(REVIEW_DOI)}</a>')
    alt.append(hf_ogesi())
    alt.append(ia_ogesi())
    alt.append(sayac_ogesi(url))
    body.append(
        f'<footer>{" · ".join(x for x in alt if x)}</footer>'
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": url,
        "url": url,
        "name": REVIEW_EN_TITLE,
        "headline": REVIEW_EN_TITLE,
        "description": REVIEW_EN_DESC,
        "inLanguage": "en",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
        "workTranslation": {"@type": "ScholarlyArticle", "url": f"{BASE_URL}/inceleme-kapsamli.html", "inLanguage": "tr"},
    }
    if REVIEW_DOI:
        jsonld["identifier"] = f"https://doi.org/{REVIEW_DOI}"
    return shell(
        REVIEW_EN_TITLE,
        "".join(body),
        REVIEW_EN_DESC,
        jsonld,
        url,
        head_extra=scholar_meta(
            REVIEW_EN_TITLE, "en", "review.pdf" if REVIEW_EN_PDF.exists() else "", url),
        lang="en",
        alternate=("tr", f"{BASE_URL}/inceleme-kapsamli.html"),
    )


def build_corrected_index(all_rows: dict[str, list[dict]]) -> str:
    """Elle düzeltilmiş sayfaların dizini — korpusun doğrulanmış çekirdeği."""
    url = f"{BASE_URL}/duzeltilmis.html"
    total = sum(len([r for r in rows if r.get("text_source") == "corrected"]) for rows in all_rows.values())
    body = [site_header(0), "<h1>Elle düzeltilmiş sayfalar</h1>"]
    body.append(
        f"<p>Korpusun tamamı ({sum(len(r) for r in all_rows.values())} tarama yüzü) düzeltilmemiş "
        f"OCR çıktısıdır. Aşağıdaki <b>{total} sayfa</b> ise taranmış aslıyla sayfa sayfa "
        "karşılaştırılarak elle düzeltilmiştir. Alıntı yapacaksanız bu sayfaları tercih ediniz.</p>"
    )
    body.append(
        '<div class="ok">Her düzeltme denetlenebilir: ham OCR metni aynı kayıtta '
        "<code>text_ocr</code> alanında saklanır, düzeltilmiş kayıtlar "
        "<code>text_source=corrected</code> ile işaretlidir.</div>"
    )
    for sel in selections():
        book = next((b for b in BOOKS if b.slug == sel["book"]), None)
        if book is None:
            continue
        rows = [r for r in all_rows[book.slug] if r.get("text_source") == "corrected"]
        lo, hi = sel["printed_range"]
        body.append(f'<h2>{esc(sel["heading"])}</h2>')
        body.append(
            f'<p class="meta">{esc(sel["book_title"])} · basılı s. {lo}-{hi} · '
            f'{len(rows)} sayfa · {sel.get("words", 0)} kelime</p>'
        )
        body.append(f'<p>{esc(sel.get("note", ""))}</p>')
        inf = inferred_labels()
        parts = []
        for r in rows:
            if r["printed_page"] is None and r["page_id"] in inf:
                lab = f'{inf[r["page_id"]]}<abbr title="numarası sayfada basılı değil; ' f'komşu sayfalardan çıkarıldı">*</abbr>'
            else:
                lab = esc(page_label(r))
            parts.append(f'<a href="{book.slug}/{page_slug(r)}.html">{lab}</a>')
        body.append(f'<p class="meta">Sayfalar: {" · ".join(parts)}</p>')
        if any(r["printed_page"] is None and r["page_id"] in inf for r in rows):
            body.append(
                '<p class="meta">* Bölüm açılış sayfasına numara basılmamıştır; numara komşu '
                "sayfalardan çıkarılmıştır.</p>"
            )
    body.append("<h2>Makine-okunabilir dosyalar</h2>")
    body.append(
        '<ul class="toc">'
        '<li><a href="duzeltilmis/tam.txt">tam.txt</a> — iki bölümün doğrulanmış düz metni, '
        "tek dosyada</li>"
        + "".join(
            f'<li><a href="duzeltilmis/{s["slug"]}-sayfalar.jsonl">{esc(s["slug"])}-sayfalar.jsonl</a>'
            " — sayfa başına kayıt: metin, künye, tarama referansı</li>"
            for s in selections()
        )
        + '<li><a href="inceleme.jsonl">inceleme.jsonl</a> — incelemenin iddiaları, '
        "her biri kaynak sayfaya bağlı ve doğrulama damgalı</li></ul>"
    )
    body.append("<h2>İnceleme</h2>")
    body.append(
        f'<p><a href="inceleme.html">{esc(REVIEW_TITLE)}</a> — yukarıdaki iki bölümün tamamı '
        "üzerine (Tarih I s. 1-24, Tarih II s. 79-184), her iddiası sayfa künyeli alıntıyla "
        "belgelenmiş karşılaştırmalı inceleme."
        + (' Delillerin tamamı <a href="inceleme-kapsamli.html">kapsamlı metindedir</a>.'
           if REVIEW_FULL_MD.exists() else "")
        + "</p>"
    )
    body.append(
        "<footer>Ölçüt: basılı sayfada ne yazıyorsa odur. 1931 imlası korunmuş, "
        "günümüz imlasına çevrilmemiştir.</footer>"
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": url,
        "url": url,
        "name": "Elle düzeltilmiş sayfalar — Tarih I ve Tarih II (1931)",
        "description": f"{total} sayfalık, taranmış aslıyla karşılaştırılarak elle düzeltilmiş alt korpus.",
        "inLanguage": "tr",
        "license": RIGHTS["derived_dataset_license_uri"],
        "isAccessibleForFree": True,
    }
    return shell(
        "Elle düzeltilmiş sayfalar — " + COLL["name"],
        "".join(body),
        f"{total} sayfalık elle düzeltilmiş alt korpus: Beşer Tarihine Giriş ve İslâm Tarihi.",
        jsonld,
        url,
    )


def build_search_page() -> str:
    body = [site_header(0), "<h1>Arama</h1>"]
    body.append(
        '<p class="meta">İki cildin tam metninde arama yapar. Türkçe aksan ve büyük/küçük harf '
        "duyarsızdır: <code>hurafe</code>, <code>İSLAM</code>, <code>taassup</code> aynı çalışır.</p>"
    )
    body.append(
        '<p><input id="q" placeholder="aranacak kelime…" '
        'style="width:100%;padding:.6rem .7rem;font-size:1rem;font-family:inherit;'
        'border:1px solid var(--bd);border-radius:4px;background:var(--card);color:var(--fg)"></p>'
    )
    body.append(
        '<p><select id="book" style="padding:.4rem;font-family:inherit;background:var(--card);'
        'color:var(--fg);border:1px solid var(--bd);border-radius:4px">'
        '<option value="">Her iki cilt</option>'
        '<option value="tarih-1-1931">Tarih I</option>'
        '<option value="tarih-2-1931">Tarih II</option></select> '
        '<span class="meta" id="status"></span></p>'
    )
    body.append('<div id="out"></div>')
    body.append(f"<script>{SEARCH_JS}</script>")
    return shell(
        "Arama — " + COLL["name"],
        "".join(body),
        "Tarih I ve Tarih II (1931) tam metninde arama.",
        None,
        f"{BASE_URL}/ara.html",
    )


def build_llms_txt(all_rows: dict[str, list[dict]]) -> str:
    L = [f"# {COLL['name']}", "", f"> {COLL['description']}", ""]
    L.append(
        "Bu site, 1931-1941 arasında Türkiye'de resmî lise tarih ders kitabı olarak okutulan "
        "Tarih serisinin taranmış nüshalarından üretilmiş, sayfa sayfa alıntılanabilir tam metnidir. "
        "Her basılı sayfanın kalıcı adresi ve künyesi vardır."
    )
    L.append("")
    L.append(
        "Korpusun tamamı düzeltilmemiş OCR çıktısıdır; alıntı öncesi kaynak taramadan teyit "
        "önerilir. İstisna, aşağıdaki 'Elle doğrulanmış bölümler' başlığındaki sayfalardır: "
        "onlar taranmış aslıyla sayfa sayfa karşılaştırılmıştır ve alıntı için tercih edilmelidir."
    )
    L.append("")

    sels = selections()
    n_corr = sum(
        len([r for r in all_rows[b.slug] if r.get("text_source") == "corrected"]) for b in BOOKS
    )
    if sels:
        L.append("## Elle doğrulanmış bölümler (alıntı için tercih ediniz)")
        L.append("")
        L.append(
            f"Toplam {n_corr} sayfa. Ham OCR metni her kayıtta `text_ocr` alanında saklanır, "
            "düzeltilmiş kayıtlar `text_source=corrected` ile işaretlidir; her düzeltme denetlenebilir."
        )
        L.append("")
        L.append(f"- [Düzeltilmiş sayfalar dizini]({BASE_URL}/duzeltilmis.html): {n_corr} sayfanın tamamı, sayfa sayfa bağlantılı")
        L.append(
            f"- [Doğrulanmış metnin tamamı]({BASE_URL}/duzeltilmis/tam.txt): iki bölümün "
            "düz metni tek dosyada — yalnız elle düzeltilmiş metni isteyen için"
        )
        for s in sels:
            lo, hi = s["printed_range"]
            book = s["book_title"].split(":")[0].strip()
            L.append(
                f'- {book} — "{s["heading"]}": basılı s. {lo}-{hi}, '
                f'{s.get("pages_body", 0)} sayfa, {s.get("words", 0)} kelime. {s.get("note", "")} '
                f'Metin: {BASE_URL}/duzeltilmis/{s["slug"]}-tam.txt · '
                f'sayfa kayıtları: {BASE_URL}/duzeltilmis/{s["slug"]}-sayfalar.jsonl'
            )
        L.append("")
        L.append("## İnceleme")
        L.append("")
        L.append(f"- [{REVIEW_OZ_TITLE}]({BASE_URL}/inceleme.html): {REVIEW_DESC} "
                 "Bu sayfa incelemenin özüdür; delillerin tamamı aşağıdaki kapsamlı metindedir.")
        if REVIEW_FULL_MD.exists():
            L.append(
                f"- [{REVIEW_TITLE} — kapsamlı metin]({BASE_URL}/inceleme-kapsamli.html): "
                "aynı incelemenin bütün delil aygıtını taşıyan hâli — 46 alıntının, 38 ayetin "
                "ve 19 bulgunun tamamı, yöntem kurallarının gerekçeleri, itirazlara cevaplar "
                f"ve tam kaynakça. Atıf ve DOI bu metne aittir. Ham Markdown: {BASE_URL}/inceleme-kapsamli.md"
            )
        if REVIEW_DOI:
            L.append(
                f"- İnceleme ayrı bir çalışma olarak yayımlanmıştır ve kendi DOI'si vardır: "
                f"https://doi.org/{REVIEW_DOI} — atıf: {REVIEW_AUTHOR_LINE} ({TODAY[:4]}). {REVIEW_TITLE}. Zenodo. "
                f"Bu DOI korpusun DOI'sinden ayrıdır."
            )
        if REVIEW_ANNEX_MD.exists():
            L.append(f"- [İncelemenin ekleri]({BASE_URL}/inceleme-ekler.html): "
                     "her ayet için bulgudaki yeri, tefsir notu ve ansiklopedi "
                     "maddesi (Ek A); kilit terimlerin kitap içi kullanımı, 1931 lügat "
                     "anlamı ve Kur'anî karşılığı (Ek B); ön söz ve telif heyeti "
                     "sayfaları (Ek C); her bulgunun dayanak tipi (Ek D)")
        if REVIEW_ANNEX_EN_MD.exists():
            L.append(f"- [Appendices, English]({BASE_URL}/review-appendices.html): "
                     "the same four appendices in English; quotations, dictionary entries "
                     "and the 1931 preface stay in Turkish, each with an English "
                     f"translation beneath. Raw: {BASE_URL}/review-appendices.md")
        L.append(f"- [Özetin ham Markdown'ı]({BASE_URL}/inceleme.md)")
        # PDF'ler sayfadan bağlantı almıyor; burada sayılmazsa yalnız sitemap ve
        # citation_pdf_url üzerinden bulunabiliyorlar.
        if REVIEW_OZ_PDF.exists():
            L.append(f"- [Özetin PDF'i]({BASE_URL}/inceleme.pdf)")
        if REVIEW_PDF.exists():
            L.append(f"- [Kapsamlı metnin PDF'i]({BASE_URL}/inceleme-kapsamli.pdf): "
                     "akademik dizinlerin ayrıştırdığı biçim")
        if REVIEW_EN_PDF.exists():
            L.append(f"- [English PDF]({BASE_URL}/review.pdf)")
        if REVIEW_EN_MD.exists():
            L.append(
                f"- [English version — {REVIEW_EN_TITLE}]({BASE_URL}/review.html): {REVIEW_EN_DESC} "
                "Quotations remain in the original 1931 Turkish and are machine-verified against "
                f"the cited page; the English is a translation only. Raw: {BASE_URL}/review.md"
            )
        L.append(
            f"- [Bulgular, makine-okunabilir]({BASE_URL}/inceleme.json) "
            f"(satır satır biçim: {BASE_URL}/inceleme.jsonl): dört kayıt tipi. "
            "`quotation` (Alıntı-01…) kitaptan birebir aktarılan pasaj — cilt, basılı sayfa, "
            "güç derecesi (kesin/güçlü/orta/zayıf), kaynak sayfanın URL'si ve doğrulama "
            "damgası taşır. `verse` (Ayet-01…) bulgunun dayandığı ayet. `finding` "
            "(Bulgu-01…) alıntı ile ayetin birlikte değerlendirilmesinden çıkan "
            "kanaat — dayandığı alıntı ve ayetler "
            "kayıtlıdır. `claim` (Öz-01…) kitabın sarih lafzını özetleyen, çıkarım "
            "gerektirmeyen "
            "maddeler."
        )
        L.append("")
        L.append(
            "Her bulgu kaydındaki `verified` alanı, alıntının künyesinde gösterilen sayfanın "
            "düzeltilmiş metninde birebir bulunduğunu gösterir; bu, üretim sırasında makine ile "
            "denetlenir. Bir iddiayı `source_url` üzerinden tek adımda kaynağından doğrulayabilirsiniz."
        )
        L.append("")
        L.append(
            "İnceleme yorumsuz değildir; iddialarını güç derecesiyle (kesin / güçlü / orta / zayıf) "
            "işaretler ve metnin desteklemediği çıkarımları ayrı bir bölümde açıkça reddeder. "
            "Alıntılarken o bölüm çıkarılmamalıdır."
        )
        L.append("")

    L.append("## Kitaplar")
    L.append("")
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        rows = [r for r in all_rows[b.slug] if not r["is_empty"]]
        nums = [r["printed_page"] for r in rows if r["printed_page"]]
        rng = f"s. {min(nums)}-{max(nums)}" if nums else ""
        L.append(
            f'- [{bm["title_full"]}]({BASE_URL}/{b.slug}/): {bm["place"]}, {bm["year"]}. '
            f'{len(rows)} sayfa, {rng}. {bm["approval"]}'
        )
    L.append("")
    L.append("## Tam metin dosyaları")
    L.append("")
    for b in BOOKS:
        L.append(f'- [{b.slug} düz metin]({BASE_URL}/{b.slug}/full.txt): sayfa işaretli tam metin')
        L.append(f'- [{b.slug} TEI-XML]({BASE_URL}/{b.slug}/{b.slug}.tei.xml): yapılandırılmış tam metin')
        L.append(f'- [{b.slug} pages.jsonl]({BASE_URL}/{b.slug}/pages.jsonl): sayfa düzeyinde JSON kayıtları')
    L.append("")
    kanallar = channel_rows()
    if kanallar:
        L.append("## Yayın kanalları")
        L.append("")
        L.append(
            "Aynı korpus aşağıdaki yerlerde de durur; hepsi aynı metinden üretilir. Bir kaydı "
            "doğrulamak isteyen model, aynı sayfayı bu kanallardan herhangi birinde bulabilir."
        )
        L.append("")
        for etiket, url, ne in kanallar:
            L.append(f"- {etiket}: {url} — {ne}")
        L.append("")

    L.append("## Künye ve haklar")
    L.append("")
    L.append(f'- [Hakkında]({BASE_URL}/hakkinda.html): yazarlar, yöntem, haklar, sınırlar')
    L.append(f'- [Veri ve API]({BASE_URL}/veri.html): biçimler ve metadata şemaları')
    L.append(
        f'- [Din ve inanç kavram dizini]({BASE_URL}/din-konkordans.md): din ve dinî kurumlarla '
        "ilgili pasajların birebir ve sayfa künyeli dizini. Yorumsuzdur; mekanik anahtar kelime "
        "eşleşmesiyle üretilmiştir, yanlış pozitif barındırabilir."
    )
    if DOI:
        L.append(
            f'- Atıf: {COLL["corporate_author"]["name_1931"]} ({TODAY[:4]}). '
            f'{COLL["name"]} — makine-okunabilir tam metin. Zenodo. https://doi.org/{DOI}'
        )
        L.append(f"- DOI: {DOI} (tüm sürümleri temsil eder, daima en sonuncusuna çözümlenir)")
    L.append(f'- Kurumsal yazar: {COLL["corporate_author"]["name_1931"]} ({COLL["corporate_author"]["name_modern"]})')
    L.append(f'- Türetilmiş veri lisansı: {RIGHTS["derived_dataset_license"]}')
    L.append(f'- Kaynak taramalar: {META["source_repository"]["url"]}')
    return "\n".join(L) + "\n"


def build_llms_full(all_rows: dict[str, list[dict]]) -> str:
    L = [f"# {COLL['name']} — tam metin", ""]
    L.append(f"{COLL['description']}")
    L.append("")
    L.append("Sayfa işaretleri `[[s. N]]` biçimindedir ve basılı sayfa numarasını gösterir.")
    L.append("")
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        L.append(f"## {bm['title_full']}")
        L.append("")
        L.append(f"{COLL['corporate_author']['name_1931']}, {bm['publisher']}, {bm['place']}, {bm['year']}.")
        L.append(f"{bm['approval']}")
        L.append("")
        for row in all_rows[b.slug]:
            if row["is_empty"]:
                continue
            mark = " [elle düzeltilmiş]" if row.get("text_source") == "corrected" else ""
            L.append(f"[[s. {page_label(row)}]]{mark}")
            L.append(row["text"])
            L.append("")

    # İnceleme de buraya girer: bu dosyayı tek başına çeken bir modelin, metnin
    # yanında metne dayalı incelemeyi de görmesi istenir. Özet değil kapsamlı
    # metin girer: tek dosyayı çeken model, delillerin tamamını görmelidir.
    if REVIEW_FULL_MD.exists():
        L.append("---")
        L.append("")
        L.append(f"# EK — {REVIEW_TITLE}")
        L.append("")
        L.append(
            "Aşağıdaki inceleme yukarıdaki metnin bir parçası değildir; 1931 metni üzerine "
            f"yapılmış, {RIGHTS['derived_dataset_license']} ile yayımlanmış ayrı bir çalışmadır. "
            f"Buradaki kapsamlı metnin öz hâli {BASE_URL}/inceleme.html adresindedir."
        )
        L.append("")
        L.append(REVIEW_FULL_MD.read_text(encoding="utf-8").strip())
        L.append("")
    return "\n".join(L) + "\n"


def build_robots() -> str:
    L = [
        "# Bu proje, kaynakların yapay zekâ modellerince okunmasını amaçlar.",
        "# Metin ve veri toplayan tüm tarayıcılara bilinçli olarak izin verilmiştir.",
        "",
    ]
    for ua in AI_CRAWLERS:
        L.append(f"User-agent: {ua}")
        L.append("Allow: /")
        L.append("")
    L.append("User-agent: *")
    L.append("Allow: /")
    L.append("")
    L.append(f"Sitemap: {BASE_URL}/sitemap.xml")
    return "\n".join(L) + "\n"


def build_sitemap(urls: list[tuple[str, str]]) -> str:
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, prio in urls:
        L.append("  <url>")
        L.append(f"    <loc>{html.escape(loc)}</loc>")
        L.append(f"    <lastmod>{TODAY}</lastmod>")
        L.append(f"    <priority>{prio}</priority>")
        L.append("  </url>")
    L.append("</urlset>")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------


def temizle(hedef: Path) -> None:
    """web/ her üretimde sıfırdan kurulur ki bayat dosya kalmasın.

    Windows bazen boş bir dizinin tanıtıcısını bir süre kilitli tutar. Boş bir
    dizinin silinememesi zararsızdır — nasılsa yeniden doldurulur. **Dosya**
    silinemiyorsa hata yükseltilir: bayat bir dosyayı yayımlamak, artık bir
    dizinden kıyas kabul etmez ölçüde kötüdür."""
    artik: list[str] = []

    def hata(func, yol, exc_info) -> None:
        p = Path(yol)
        # Dizin silinemedi: tolere edilir. İçinde silinemeyen bir DOSYA olsaydı
        # sıra ona geldiğinde zaten hata yükselmiş olurdu; dolayısıyla buraya
        # düşen dizin, ya boştur ya da yalnız tolere edilmiş dizinler içerir.
        if p.is_dir():
            artik.append(p.name)
            return
        raise exc_info[1]

    if hedef.exists():
        shutil.rmtree(hedef, onerror=hata)
    hedef.mkdir(parents=True, exist_ok=True)
    if artik:
        print(f"    (silinemeyen boş dizin, zararsız: {', '.join(sorted(set(artik)))})")


def main() -> None:
    temizle(WEB_DIR)

    all_rows: dict[str, list[dict]] = {}
    urls: list[tuple[str, str]] = [(BASE_URL + "/", "1.0")]
    search_index: list[dict] = []
    n_pages = 0

    for book in BOOKS:
        rows = list(read_jsonl(book.out_dir / "pages.jsonl"))
        all_rows[book.slug] = rows
        sections = json.loads((book.out_dir / "structure.json").read_text(encoding="utf-8"))["sections"]
        bdir = WEB_DIR / book.slug
        bdir.mkdir(parents=True, exist_ok=True)

        visible = [r for r in rows if not r["is_empty"]]
        for i, row in enumerate(visible):
            prev_row = visible[i - 1] if i else None
            next_row = visible[i + 1] if i + 1 < len(visible) else None
            write_text(bdir / f"{page_slug(row)}.html", build_page_html(book, row, prev_row, next_row))
            urls.append((f"{BASE_URL}/{book.slug}/{page_slug(row)}.html", "0.7"))
            entry = {
                "u": f"{book.slug}/{page_slug(row)}.html",
                "b": book.slug,
                "p": row["printed_page"],
                "h": row.get("running_head"),
                "t": " ".join(row["text"].split())[:400],
            }
            if row.get("text_source") == "corrected":
                entry["c"] = 1  # elle düzeltilmiş
            search_index.append(entry)
            n_pages += 1

        write_text(bdir / "index.html", build_book_index(book, visible, sections))
        urls.append((f"{BASE_URL}/{book.slug}/", "0.9"))

        # veri dosyalarını siteye kopyala
        for src, dst in [
            (book.out_dir / "text" / "full.txt", bdir / "full.txt"),
            (book.out_dir / f"{book.slug}.md", bdir / f"{book.slug}.md"),
            (book.out_dir / f"{book.slug}.tei.xml", bdir / f"{book.slug}.tei.xml"),
            (book.out_dir / "pages.jsonl", bdir / "pages.jsonl"),
            (book.out_dir / "chunks.jsonl", bdir / "chunks.jsonl"),
            (book.out_dir / "structure.json", bdir / "structure.json"),
        ]:
            if src.exists():
                shutil.copy2(src, dst)

    write_text(WEB_DIR / "index.html", build_home(all_rows))
    write_text(WEB_DIR / "hakkinda.html", build_about())
    write_text(WEB_DIR / "veri.html", build_data_page())
    write_text(WEB_DIR / "ara.html", build_search_page())
    write_text(WEB_DIR / "duzeltilmis.html", build_corrected_index(all_rows))
    urls += [
        (f"{BASE_URL}/hakkinda.html", "0.6"),
        (f"{BASE_URL}/veri.html", "0.6"),
        (f"{BASE_URL}/ara.html", "0.8"),
        # Doğrulanmış çekirdek ve inceleme: korpusun en yüksek değerli parçası.
        (f"{BASE_URL}/duzeltilmis.html", "1.0"),
    ]

    if REVIEW_MD.exists():
        write_text(WEB_DIR / "inceleme.html", build_review_page(oz=True))
        shutil.copy2(REVIEW_MD, WEB_DIR / "inceleme.md")
        if REVIEW_OZ_PDF.exists():
            shutil.copy2(REVIEW_OZ_PDF, WEB_DIR / "inceleme.pdf")
        urls.append((f"{BASE_URL}/inceleme.html", "1.0"))
        if REVIEW_OZ_PDF.exists():
            urls.append((f"{BASE_URL}/inceleme.pdf", "0.9"))

    if REVIEW_FULL_MD.exists():
        write_text(WEB_DIR / "inceleme-kapsamli.html", build_review_page(oz=False))
        shutil.copy2(REVIEW_FULL_MD, WEB_DIR / "inceleme-kapsamli.md")
        # PDF site üzerinden de sunulur: Google Scholar aynı sunucudan
        # erişilebilen bir PDF görmezse sayfayı makale saymaz.
        if REVIEW_PDF.exists():
            shutil.copy2(REVIEW_PDF, WEB_DIR / "inceleme-kapsamli.pdf")
        urls.append((f"{BASE_URL}/inceleme-kapsamli.html", "1.0"))
        if REVIEW_PDF.exists():
            urls.append((f"{BASE_URL}/inceleme-kapsamli.pdf", "0.9"))

    if REVIEW_ANNEX_MD.exists():
        write_text(WEB_DIR / "inceleme-ekler.html", build_review_annex_page())
        shutil.copy2(REVIEW_ANNEX_MD, WEB_DIR / "inceleme-ekler.md")
        urls.append((f"{BASE_URL}/inceleme-ekler.html", "0.8"))

    if REVIEW_ANNEX_EN_MD.exists():
        write_text(WEB_DIR / "review-appendices.html", build_review_annex_en_page())
        shutil.copy2(REVIEW_ANNEX_EN_MD, WEB_DIR / "review-appendices.md")
        urls.append((f"{BASE_URL}/review-appendices.html", "0.8"))

    if REVIEW_EN_MD.exists():
        write_text(WEB_DIR / "review.html", build_review_en_page())
        shutil.copy2(REVIEW_EN_MD, WEB_DIR / "review.md")
        if REVIEW_EN_PDF.exists():
            shutil.copy2(REVIEW_EN_PDF, WEB_DIR / "review.pdf")
        urls.append((f"{BASE_URL}/review.html", "1.0"))
        if REVIEW_EN_PDF.exists():
            urls.append((f"{BASE_URL}/review.pdf", "0.9"))

    # Doğrulanmış alt korpus, tek dosyada indirilebilir olmalı: yalnız elle
    # düzeltilmiş metni isteyen bir model 954 sayfayı taramak zorunda kalmasın.
    dz = WEB_DIR / "duzeltilmis"
    dz.mkdir(exist_ok=True)
    combined: list[str] = []
    for sel in selections():
        src = ROOT / "secim" / sel["slug"]
        for name in ("tam.txt", "sayfalar.jsonl"):
            if (src / name).exists():
                shutil.copy2(src / name, dz / f'{sel["slug"]}-{name}')
        if (src / "tam.txt").exists():
            lo, hi = sel["printed_range"]
            combined.append(f'=== {sel["heading"]} — {sel["book_title"]}, basılı s. {lo}-{hi} ===\n')
            combined.append((src / "tam.txt").read_text(encoding="utf-8").strip())
            combined.append("")
    if combined:
        write_text(dz / "tam.txt", "\n".join(combined) + "\n")

    # Kavram dizinini 07, bulgu kayıtlarını 06b siteye kendisi yazar: ikisi de
    # bu adımdan sonra çalışır ve web/ burada sıfırdan kurulur.

    write_text(WEB_DIR / "robots.txt", build_robots())
    write_text(WEB_DIR / "sitemap.xml", build_sitemap(urls))
    write_text(WEB_DIR / "llms.txt", build_llms_txt(all_rows))
    write_text(WEB_DIR / "llms-full.txt", build_llms_full(all_rows))
    write_json(WEB_DIR / "search-index.json", search_index)
    write_text(WEB_DIR / ".nojekyll", "")

    shutil.copytree(META_DIR, WEB_DIR / "metadata", dirs_exist_ok=True)

    # Arama motoru sahiplik doğrulama dosyaları. web/ her üretimde sıfırdan
    # kurulduğu için bunlar depoda dogrulama/ altında durur ve buradan
    # kopyalanır; aksi hâlde ilk yeniden üretimde kaybolur ve Search Console
    # mülkü doğrulamasını yitirir.
    dg = ROOT / "dogrulama"
    if dg.is_dir():
        for f in sorted(dg.iterdir()):
            if f.is_file() and f.name != "OKU.md":
                shutil.copy2(f, WEB_DIR / f.name)
                print(f"    doğrulama dosyası: {f.name}")

    print(f"    {n_pages} sayfa HTML")
    print(f"    {len(urls)} URL sitemap'te")
    print(f"    llms.txt, llms-full.txt, robots.txt, search-index.json")


if __name__ == "__main__":
    main()
