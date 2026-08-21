"""Ortak yardımcılar: kitap tanımları, yol sabitleri, metin temizleme.

Tarih I ve Tarih II (1931, Türk Tarihi Tetkik Cemiyeti) taranmış PDF'lerinden
AI-ready korpus üretmek için kullanılan altyapı.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "PDF"
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
META_DIR = ROOT / "metadata"


@dataclass
class Book:
    """Bir kitabın kimlik ve kaynak bilgileri."""

    slug: str
    pdf: str
    title: str
    volume: str
    subtitle: str
    year: int
    ttk_url: str
    ttk_item: str

    @property
    def pdf_path(self) -> Path:
        return PDF_DIR / self.pdf

    @property
    def out_dir(self) -> Path:
        return DATA_DIR / self.slug

    @property
    def full_title(self) -> str:
        return f"{self.title} {self.volume}: {self.subtitle}"


BOOKS = [
    Book(
        slug="tarih-1-1931",
        pdf="Tarih I.pdf",
        title="Tarih",
        volume="I",
        subtitle="Tarihtenevelki Zamanlar ve Eski Zamanlar",
        year=1931,
        ttk_url="https://kutuphane.ttk.gov.tr/resource?itemId=267298&dkymId=6415",
        ttk_item="267298",
    ),
    Book(
        slug="tarih-2-1931",
        pdf="Tarih II.pdf",
        title="Tarih",
        volume="II",
        subtitle="Ortazamanlar",
        year=1931,
        ttk_url="https://kutuphane.ttk.gov.tr/resource?itemId=267295&dkymId=6416",
        ttk_item="267295",
    ),
]

BOOKS_BY_SLUG = {b.slug: b for b in BOOKS}

# --------------------------------------------------------------------------
# Tarama gürültüsü / filigran
# --------------------------------------------------------------------------

# Her sayfaya basılmış kütüphane filigranı ve damgaları.
WATERMARK_PATTERNS = [
    r"t[uü]rk\s*tar[iı]h\s*kurumu",
    r"k[uü]t[uü]pa?n?e?s[il]?",
    r"^ka\.?\s*no",
    r"^kay[iı]t\s*no",
    r"^esas\s*no",
    r"^tasnif\s*no",
]
WATERMARK_RE = re.compile("|".join(WATERMARK_PATTERNS), re.IGNORECASE)


def norm_for_match(s: str) -> str:
    """Filigran eşleşmesi için kaba normalizasyon."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def is_watermark(text: str) -> bool:
    t = norm_for_match(text)
    if not t:
        return True
    return bool(WATERMARK_RE.search(t))


# Anlamsız tarama artığı satırları (kenar lekeleri, cetvel izleri).
NOISE_RE = re.compile(r"^[\s\W_]{0,3}[a-zA-Z]{0,4}[\s\W_]{0,3}$")


def is_noise_line(text: str) -> bool:
    """Çok kısa, harf oranı düşük satırlar tarama artığıdır."""
    t = text.strip()
    if not t:
        return True
    if len(t) > 12:
        return False
    # Salt rakam: sayfa numarası, tarih, madde numarası olabilir -> daima koru
    if re.fullmatch(r"[0-9]{1,8}", t):
        return False
    # Roma rakamı -> koru
    if re.fullmatch(r"[IVXLCDM]{1,7}", t.upper()):
        return False
    letters = sum(c.isalpha() for c in t)
    if letters == 0:
        return True
    # 'iiUi', 's', '^^^^^' gibi tarama artıkları
    if len(t) <= 4 and letters <= 3:
        return True
    return False


# --------------------------------------------------------------------------
# Metin birleştirme
# --------------------------------------------------------------------------

# Satır sonu tirelemesi: "gayri-\nmeşru" -> "gayrimeşru"
HYPHEN_END_RE = re.compile(r"(\w)[-‐‑­]\s*$")


def dehyphenate(lines: list[str]) -> str:
    """Satır sonu tirelerini birleştirerek akıcı metin üretir."""
    out: list[str] = []
    buf = ""
    for raw in lines:
        line = raw.rstrip()
        if not line:
            if buf:
                out.append(buf)
                buf = ""
            out.append("")
            continue
        if buf:
            buf = buf + line.lstrip() if buf.endswith("\x00") else buf + " " + line.lstrip()
        else:
            buf = line
        m = HYPHEN_END_RE.search(buf)
        if m:
            # tireyi at, sonraki satırı boşluksuz ekle
            buf = HYPHEN_END_RE.sub(r"\1", buf) + "\x00"
        else:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf.replace("\x00", ""))
    return "\n".join(x.replace("\x00", "") for x in out)


def collapse_ws(s: str) -> str:
    s = s.replace(" ", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def page_label(row: dict) -> str:
    """Sayfanın insan tarafından okunan etiketi."""
    if row.get("printed_page") is not None:
        return str(row["printed_page"])
    if row.get("printed_roman"):
        return row["printed_roman"]
    return f"tarama {row['pdf_page'] + 1}{row['side'][0]}"


def page_slug(row: dict) -> str:
    """Sayfanın kalıcı dosya/URL adı. Sitede ve bulgu kayıtlarında aynı olmalı."""
    if row.get("printed_page") is not None:
        return f"s{row['printed_page']:04d}"
    if row.get("printed_roman"):
        return f"r{row['printed_roman'].lower()}"
    return f"u{row['pdf_page']:03d}{row['side'][0]}"


# ---------------------------------------------------------------------------
# Markdown -> HTML (docs/ altındaki belgelerin kullandığı dar altküme).
# Hem site üreticisi hem yayın PDF'i aynı dönüştürücüyü kullanır.
# ---------------------------------------------------------------------------

LIST_RE = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.*)$")


# İncelemenin indeks işaretleri renkle de ayrılır: alıntı mavi, ayet yeşil,
# bulgu kırmızı. Markdown renk taşımaz — kanonik biçimde ayrımı işaretin
# kendisi yapar — bu yüzden renk türev biçimlerde, sınıf adı üzerinden verilir.
# Rengin kendisi burada değil, çıktıyı kuran betiğin stilindedir (web: 06_web,
# PDF: 16_inceleme_yayin).
#
# Dört biçim de tek geçişte karşılanır — aksi hâlde önce sarılan bir işaret
# sonraki geçişte ikinci kez sarılır:
#   [[Alıntı-01](url)]  sayfasına bağlı alıntı işareti
#   [Alıntı-01](url)    aynısının dış parantezsiz hâli
#   [Ayet-01]           çıplak işaret
#   Alıntı-01           dayanak künyesi, aralık, metin içi atıf
#
# İngilizce sürüm aynı işaretleri kendi diliyle yazar (Quote/Verse/Finding) ve
# aynı renkleri alır. Öz ve Claim serileri listede yoktur: onların işareti
# metinde görünmez, göründüğü tek yer olan §2 aralığında da gövde rengindedir.
# Bulgu, alıntı ve ayet aynı başlığın altındadır; ilk ikisi alıntı bloğu
# olduğu için içeri girer, bulgu düz paragraf olduğu için kenara yapışırdı.
# Bu sınıf onu aynı hizaya getirir — alıntıya benzetmeden: rengi ve punto
# gövde metninin, çünkü bulgu aktarma değil hükümdür.
BULGU_P_RE = re.compile(r"^\*\*\[(?:Bulgu|Finding)-\d+\]\*\*")

REF_SINIF = {
    "Alıntı": "r-alinti", "Quote": "r-alinti",
    "Ayet": "r-ayet", "Verse": "r-ayet",
    "Bulgu": "r-bulgu", "Finding": "r-bulgu",
}
_AD = "Alıntı|Ayet|Bulgu|Quote|Verse|Finding"
REF_RE = re.compile(
    rf"\[\[({_AD})-(\d+)\]\(([^)\s]+)\)\]"
    rf"|\[({_AD})-(\d+)\]\(([^)\s]+)\)"
    rf"|\[({_AD})-(\d+)\]"
    rf"|({_AD})-(\d+)"
)


def _ref(m: re.Match) -> str:
    """Bir işareti, köşeli parantezleriyle birlikte tek renkli öğeye çevirir."""
    g = m.groups()
    if g[0]:  # [[Ad-NN](url)]
        ad, no, adres, kose = g[0], g[1], g[2], True
    elif g[3]:  # [Ad-NN](url)
        ad, no, adres, kose = g[3], g[4], g[5], False
    elif g[6]:  # [Ad-NN]
        ad, no, adres, kose = g[6], g[7], None, True
    else:  # Ad-NN
        ad, no, adres, kose = g[8], g[9], None, False
    metin = f"[{ad}-{no}]" if kose else f"{ad}-{no}"
    sinif = REF_SINIF[ad]
    if adres:
        return f'<a href="{adres}" class="{sinif}">{metin}</a>'
    return f'<span class="{sinif}">{metin}</span>'


def md_inline(s: str) -> str:
    # Gövde metnidir, öznitelik değil: tırnaklar kaçırılmaz. Aksi hâlde 1931
    # alıntılarındaki tırnak ve kesme işaretleri &quot;/&#x27; olarak birikir.
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    # İndeks işaretleri genel bağlantı kuralından önce: "[[Alıntı-01](url)]"
    # o kurala göre bağlantı metnini "[Alıntı-01" diye kesiyor, kapanış köşeli
    # parantezi bağlantının dışında kalıyordu.
    s = REF_RE.sub(_ref, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", s)
    return s


def md_table(block: list[str]) -> str:
    grid = [[c.strip() for c in r.strip().strip("|").split("|")] for r in block]
    head = None
    if len(grid) >= 2 and all(c and set(c) <= set("-: ") for c in grid[1]):
        head, grid = grid[0], grid[2:]
    out = ['<div class="tablewrap"><table>']
    if head:
        out.append("<thead><tr>" + "".join(f"<th>{md_inline(c)}</th>" for c in head) + "</tr></thead>")
    out.append("<tbody>")
    for row in grid:
        out.append("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def md_to_html(md: str, toc: list[tuple[int, str, str]] | None = None) -> str:
    """toc verilirse (seviye, çapa, başlık) üçlüleri oraya biriktirilir."""
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("#"):
            lvl = min(len(ln) - len(ln.lstrip("#")), 4)
            raw = ln.lstrip("#").strip()
            # Her başlık adreslenebilir: bir iddia bölümüne doğrudan bağlanabilsin.
            hid = heading_id(raw)
            if toc is not None and lvl in (2, 3):
                toc.append((lvl, hid, re.sub(r"[*`]", "", raw)))
            out.append(f'<h{lvl} id="{hid}">{md_inline(raw)}</h{lvl}>')
            i += 1
        elif ln.strip() in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
        elif ln.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(md_table(block))
        elif ln.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i].lstrip(">").strip())
                i += 1
            ham = " ".join(block).strip()
            # Bulgu da alıntı bloğu içinde yazılır: ham Markdown'da alıntı
            # ve ayetle aynı görünsün, soldaki çizgi orada da olsun diye.
            # Ama bulgu bir aktarma değil hükümdür; <blockquote> onu makineye
            # alıntı diye gösterirdi. Etiketi ayrı, stili aynı.
            if BULGU_P_RE.match(ham):
                out.append(f'<p class="bulgu">{md_inline(ham)}</p>')
            else:
                out.append(f"<blockquote>{md_inline(ham)}</blockquote>")
        elif LIST_RE.match(ln):
            tag = "ol" if re.match(r"^\s*\d+\.\s", ln) else "ul"
            items: list[str] = []
            while i < len(lines):
                m = LIST_RE.match(lines[i])
                if m:
                    items.append(m.group(1))
                elif lines[i].startswith((" ", "\t")) and lines[i].strip() and items:
                    items[-1] += " " + lines[i].strip()  # sarkan satır
                else:
                    break
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{md_inline(x)}</li>" for x in items) + f"</{tag}>")
        else:
            block = []
            while i < len(lines):
                l2 = lines[i]
                if not l2.strip() or l2.startswith(("#", ">")) or l2.lstrip().startswith("|"):
                    break
                if l2.strip() in ("---", "***", "___") or LIST_RE.match(l2):
                    break
                block.append(l2.strip())
                i += 1
            if not block:  # hiçbir dala girmediyse sonsuz döngüyü önle
                block = [lines[i].strip()]
                i += 1
            ham = " ".join(block)
            sinif = ' class="bulgu"' if BULGU_P_RE.match(ham) else ""
            out.append(f"<p{sinif}>{md_inline(ham)}</p>")
    return "".join(out)


TR_FOLD = str.maketrans("çğıİöşüÇĞÖŞÜâîûÂÎÛ", "cgiiosucgosuaiuaiu")


def heading_id(text: str) -> str:
    """Başlıktan kalıcı çapa üretir: "3.3 Vahiy, nübüvvet…" -> "s-3-3-vahiy-nubuvvet".

    Bir iddianın bölümüne derin bağlantı verilebilmesi için gereklidir; başlık
    metni değişmediği sürece çapa da değişmez. ASCII'ye indirilir, çünkü Türkçe
    harf taşıyan çapalar bazı istemcilerde yüzde kodlamasıyla bozulur."""
    t = re.sub(r"[*`_]", "", text)
    t = t.translate(TR_FOLD).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return "s-" + re.sub(r"-{2,}", "-", t)


# --------------------------------------------------------------------------
# Roma rakamı
# --------------------------------------------------------------------------

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s: str) -> int | None:
    s = s.strip().upper()
    if not s or not all(c in ROMAN_VALUES for c in s):
        return None
    total, prev = 0, 0
    for c in reversed(s):
        v = ROMAN_VALUES[c]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total or None


def int_to_roman(n: int) -> str:
    table = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
        (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
        (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = ""
    for v, sym in table:
        while n >= v:
            out += sym
            n -= v
    return out


def write_jsonl(path: Path, rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
