"""06b — İncelemenin iddialarını makine-okunabilir delile çevirir.

Yorumlu bir metni bir dil modeli ancak iddialarını kaynağa kadar takip
edebiliyorsa güvenle kullanır. Bu adım, docs/inceleme.md
içindeki düzyazıyı kayıt kayıt ayrıştırır ve her alıntıyı, künyesinde
gösterilen sayfanın **düzeltilmiş** metnine karşı doğrular.

Üretilen kayıt tipleri:

  quotation §3 ve §4 — kitaptan birebir aktarılan pasajlar (Alıntı-01…). Cilt,
            basılı sayfa, güç derecesi (kesin/güçlü/orta/zayıf), kaynak
            sayfanın URL'si ve doğrulama damgası taşır. Doğrulanabilir olan
            tek tip budur: lafız, künyesindeki sayfada aranır.
  finding   §3 ve §4 — alıntının Kur'an nassı karşısında değerlendirilmesinden
            çıkan kanaat (Bulgu-01…). Dayandığı alıntılar ve ayetler kayıtlıdır.
            Bulgu, alıntının kendisi değildir; ikisinin ayrı tutulması bu
            dosyanın esasıdır.
  verse     §3 ve §4 — bulgunun dayandığı ayetler (Ayet-01…). Alıntı gibi
            doğrulanmaz; kaynağı kitap değil Kur'an'dır.
  claim     kitaba dayanarak söylenebilecekler (Öz-01…). Bulgu değildir: itikadî
            hüküm taşımaz, yalnız kitabın sarih lafzını özetler. Bu tip yalnız
            belgede numaralı böyle bir bölüm varsa üretilir; §3 ve §4 her alıntıyı
            zaten bağlamıyla tartıştığı için o bölüm kaldırılmıştır.
  limit     Metne dayanarak SÖYLENEMEYECEK olanlar (S1…Sn). Bu tip yalnız
            belgede böyle bir bölüm varsa üretilir; şu an yoktur.

Çıktı: inceleme/bulgular.jsonl (+ web/inceleme.jsonl, site için).

Bu adım 06_web'den SONRA çalışır: 06 web/ klasörünü sıfırdan kurar.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BOOKS, ROOT, WEB_DIR, heading_id, page_slug, read_jsonl, write_jsonl, write_text,
)

REVIEW_MD = ROOT / "docs" / "inceleme.md"
# Ekler ayrı bir belgededir (Ek A/B/C). Ayrıştırılmaz — alıntı ya da ayet kaydı
# taşımaz — fakat ana metnin indekslerine atıf yapar; o atıflar denetlenir.
ANNEX_MD = ROOT / "docs" / "inceleme-ekler.md"
ANNEX_EN_MD = ROOT / "docs" / "REVIEW-APPENDICES-EN.md"
OUT_DIR = ROOT / "inceleme"
_META = json.loads((ROOT / "metadata" / "books.json").read_text(encoding="utf-8"))
# Adres künyeyle aynı yerden gelir (books.json -> channels.site). Burada ikinci
# bir kopyası tutulmaz: site taşındığında bu betik eski adresi üretmeye devam
# ederse incelemenin 34 alıntısının delil zinciri ölü adrese bakar.
BASE_URL = (_META.get("channels") or {}).get("site") or "https://tarih1931.github.io"
REVIEW_URL = f"{BASE_URL}/inceleme.html"
REVIEW_DOI = (_META.get("review") or {}).get("doi") or None

VOLUME = {"tarih-1-1931": "Tarih I", "tarih-2-1931": "Tarih II"}


# ---------------------------------------------------------------------------
# Kaynak metin: yalnız elle düzeltilmiş sayfalar
# ---------------------------------------------------------------------------


def clean(s: str) -> str:
    """Saklanacak metin: yalnız biçim gürültüsü temizlenir, lafız korunur."""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[*`]", "", s)  # markdown vurgusu
    return re.sub(r"[\s ]+", " ", s).strip()


def match_key(s: str) -> str:
    """Karşılaştırma anahtarı.

    İki kabul edilmiş fark hoş görülür, çünkü ikisi de lafzı değiştirmez:

    * Alıntı içindeki tırnaklar tek tırnağa çevrilir (§9'da kayıtlı): basımda
      "kabile allahı", raporda 'kabile allahı'. Kesme işareti etkilenmez.
    * Büyük/küçük harf. Cümle başındaki alıntı, rapor kendi cümlesinin ortasına
      yerleştirdiğinde küçük harfle başlar ("Birincisi" -> "birincisi").
      Türkçeye özgü İ/I eşlemesi elle yapılır; str.lower() 'İ' için birleşik
      nokta üretir ve eşleşmeyi bozar."""
    s = clean(s).replace('"', "'")
    return s.replace("İ", "i").replace("I", "ı").lower()


def corrected_pages() -> dict[int, dict]:
    """basılı sayfa -> kayıt. Bölümler ayrık sayfa aralıklarında olduğu için
    (Tarih I 1-24, Tarih II 79-184) sayfa numarası cildi tek başına belirler."""
    out: dict[int, dict] = {}
    inferred = {}
    sec = ROOT / "secim" / "index.json"
    if sec.exists():
        for sel in json.loads(sec.read_text(encoding="utf-8")).get("selections", []):
            path = ROOT / "secim" / sel["slug"] / "sayfalar.jsonl"
            if path.exists():
                for row in read_jsonl(path):
                    if row.get("printed_page") is None and row.get("inferred_page"):
                        inferred[row["page_id"]] = row["inferred_page"]

    for book in BOOKS:
        path = book.out_dir / "pages.jsonl"
        if not path.exists():
            continue
        for row in read_jsonl(path):
            if row.get("text_source") != "corrected":
                continue
            pp = row.get("printed_page") or inferred.get(row["page_id"])
            if not pp:
                continue
            out[pp] = {
                "book": book.slug,
                "volume": VOLUME.get(book.slug, book.slug),
                "printed_page": pp,
                "citation": row["citation"],
                "url": f"{BASE_URL}/{book.slug}/{page_slug(row)}.html",
                "_text": match_key(row["text"]),
            }
    return out


def verify(quote: str, pages: list[int], corpus: dict[int, dict]) -> bool:
    """Alıntı, künyesindeki sayfa(lar)ın metninde birebir geçiyor mu?

    "…" ile kısaltılmış alıntılarda her parça ayrı ayrı aranır. Sayfa aralığı
    verilmişse sayfaların metni birleştirilerek bakılır: cümle sayfa sonunda
    bölünmüş olabilir."""
    texts = [corpus[p]["_text"] for p in pages if p in corpus]
    if not texts:
        return False
    # Cümle sayfa sonunda bölünmüş olabilir; kelime de bölünmüş olabilir
    # ("…husule getir" / "mektedir"). Bu yüzden sayfalar hem boşlukla hem
    # boşluksuz birleştirilip ikisine de bakılır.
    hays = (" ".join(texts), "".join(texts))
    # Atlanan yer "(…)" ile gösterilir: yalın üç nokta, metnin kendi noktalamasıymış
    # gibi okunuyordu. Parantez ayraçtan sayılır, aksi hâlde parça eşleşmesi bozulur.
    frags = [f.strip(" ()[],.;:—-") for f in re.split(r"\(…\)|…|\.\.\.", match_key(quote))]
    frags = [f for f in frags if len(f) >= 20] or [match_key(quote)]
    return any(all(f in hay for f in frags) for hay in hays)


# ---------------------------------------------------------------------------
# Ayrıştırma
# ---------------------------------------------------------------------------

#   "— **Tarih I, s. 21**" veya "— **[Tarih I](url), s. 21**"
#   Cilt adı zorunlu değil; verilirse korpusa karşı doğrulanır.
CITE_RE = re.compile(
    r"—\s*(?:\[?(Tarih I{1,2})\]?(?:\([^)]*\))?\s*,\s*)?"
    r"s\.\s*([\d]+)(?:\s*[-–]\s*(\d+))?\s*(?:\((\w+)\))?\s*$"
)

# Alıntının başındaki sıra indeksi: "**[Alıntı-07]** …" veya sayfasına bağlı
# hâli "**[[Alıntı-07](url)]** …". clean() yıldızları atar, bağlantı
# sözdizimini bırakır.
IDX_RE = re.compile(r"^\[\[?(Alıntı-\d+)\](?:\([^)]*\))?\]?\s*")

# Ayet kaydı: "**[Ayet-01]** "…" — **Âl-i İmrân 19**"
AYET_RE = re.compile(r"^\[(Ayet-\d+)\]\s*(.+)$")

# Bulgu bloğu: "> **[Bulgu-07]** …"
# Bulgu da alıntı ve ayet gibi alıntı bloğu içinde yazılır — üçü aynı başlığın
# altında aynı görünsün diye. Aktarma olmadığı için tipi yine finding'dir.
BULGU_BAS_RE = re.compile(r"^\*\*\[(Bulgu-\d+)\]\*\*\s*")
BLOK_RE = re.compile(r"(?:^>[^\n]*\n?)+", re.M)


def bulgular(sub: str):
    """Bir alt bölümdeki bulguları (işaret, gövde) olarak verir."""
    for blok in BLOK_RE.findall(sub):
        metin = "\n".join(l.lstrip(">").strip() for l in blok.splitlines())
        m = BULGU_BAS_RE.match(metin)
        if m:
            yield m.group(1), metin[m.end():]
# Bulgunun dayanağı metne ikinci kez yazılmaz. Bulgu, dayandığı alıntı ve ayetle
# aynı başlığın altında basılır — §3'ün girişi bunu böyle ilan eder — dayanak da
# o bloktan okunur. Künye ayrıca bulgu paragrafının sonunda tekrarlanınca okuyucu
# aynı referansı iki kere okuyordu; kayıt için gereken bilgi zaten sayfadadır.
ALINTI_ISARET_RE = re.compile(r"\*\*\[\[?(Alıntı-\d+)\]")
AYET_ISARET_RE = re.compile(r"\*\*\[(Ayet-\d+)\]\*\*")
ALT_BASLIK_RE = re.compile(r"^####\s+.+$", re.M)

# Tek istisna: dayanağı kendi başlığının altında durmayan bulgu. §4.2 kendi
# alıntısını taşımaz — §3.3 ile §4.1'in alıntılarının itikadî neticesini tartışır
# — bu yüzden dayanağı burada açıkça yazılır. Buraya yazılan her işaretin gerçek
# bir alıntıya karşılık gelmesi check_index'te ayrıca denetlenir.
BLOK_DISI_DAYANAK = {
    "Bulgu-19": ["Alıntı-23", "Alıntı-24", "Alıntı-26", "Alıntı-35", "Alıntı-45", "Alıntı-46"],
}


def alt_bloklar(sub: str) -> list[str]:
    """Alt bölümü #### başlıklarına böler; #### yoksa bütünü tek blok verir.

    Bir bloktaki alıntı, ayet ve bulgu birbirine aittir: bulgu, o alıntıların o
    ayetler karşısında değerlendirilmesidir. Bölme bu yüzden gerekli — yoksa
    §3.1'in beş bulgusu o alt bölümdeki on alıntının hepsine dayanmış görünürdü."""
    return [p for p in ALT_BASLIK_RE.split(sub) if p.strip()]


# Metinde geçen her indeks atfı. Öz ve S serilerinin işareti metinde durmaz —
# yalnız §2'nin ilan ettiği aralıkta ve makine-okunabilir kayıtta görünür.
ATIF_RE = re.compile(r"(?<![\w/-])((?:Alıntı|Ayet|Bulgu|Öz)-\d+|S\d+)\b")


def sections(md: str, level: int) -> list[tuple[str, str]]:
    """(başlık, gövde) listesi."""
    mark = "#" * level + " "
    parts = re.split(rf"^{re.escape(mark)}(.+)$", md, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def parse_verses(md: str) -> list[dict]:
    """Bulguların dayandığı ayetler (Ayet-01…).

    Ayet, alıntı gibi doğrulanmaz: kaynağı kitap değil Kur'an'dır. Ayrı bir tip
    olmasının sebebi, bulgunun iki dayanağının — kitabın lafzı ile nassın lafzı —
    ayrı ayrı görülebilmesidir."""
    rows: list[dict] = []
    for bolum in ("3.", "4."):
        body = next((b for h, b in sections(md, 2) if h.startswith(bolum)), "")
        for heading, sub in sections(body, 3):
            num = heading.split()[0]
            for block in re.findall(r"(?:^>.*\n?)+", sub, re.M):
                text = clean(" ".join(l.lstrip("> ").rstrip() for l in block.splitlines()))
                m = AYET_RE.match(text)
                if not m:
                    continue
                govde = m.group(2)
                if " — " not in govde:
                    raise SystemExit(f"{m.group(1)}: künye yok — '… — **Sûre N**' bekleniyor")
                lafiz, kunye = govde.rsplit(" — ", 1)
                rows.append(
                    {
                        "id": m.group(1),
                        "type": "verse",
                        "section": num,
                        "reference": kunye.strip(),
                        "text": lafiz.strip().strip("\"'").strip(),
                    }
                )
    return rows


def parse_axis(md: str, corpus: dict[int, dict], bolum: str, ayetler: dict[str, str]) -> list[dict]:
    """Bir bölümü iki ayrı kayıt tipine ayırır.

    quotation  kitaptan birebir aktarılan pasaj (Alıntı-01…). Doğrulanabilir
               olan budur: künyesindeki sayfada birebir bulunup bulunmadığı.
    finding    alıntının Kur'an nassı karşısında değerlendirilmesinden çıkan
               kanaat (Bulgu-01…). Dayandığı alıntılar ve ayetler kaydedilir.

    Aynı usul §3'e (eksen eksen karşılaştırma) ve §4'e (övgü cümleleri)
    uygulanır; ikisi de kitabın lafzına dayanır, ikisi de aynı denetimden
    geçer."""
    body = next((b for h, b in sections(md, 2) if h.startswith(bolum)), "")
    rows: list[dict] = []
    for heading, sub in sections(body, 3):
        num = heading.split()[0]
        axis = re.split(r"\s+—\s+", re.sub(r"[*`]", "", heading), 1)[0]
        axis = axis[len(num) :].strip()
        anchor = "s-" + re.sub(r"[^a-z0-9]+", "-", _fold(heading)).strip("-")
        url = f"{REVIEW_URL}#{anchor}"

        for block in re.findall(r"(?:^>.*\n?)+", sub, re.M):
            text = clean(" ".join(l.lstrip("> ").rstrip() for l in block.splitlines()))
            m = CITE_RE.search(text)
            if not m:
                continue  # künyesiz blok: kapsam uyarısı vb.
            quote = text[: m.start()].strip()
            mi = IDX_RE.match(quote)
            if not mi:
                if AYET_RE.match(quote):
                    continue  # ayet kaydı; parse_verses ele alır
                raise SystemExit(f"indekssiz alıntı (§{num}): {quote[:60]}…")
            quote = quote[mi.end() :].strip().strip("\"'").strip()
            if not quote:
                continue
            pages = [int(m.group(2))] + ([int(m.group(3))] if m.group(3) else [])
            src = corpus.get(pages[0], {})
            if m.group(1) and src and m.group(1) != src["volume"]:
                raise SystemExit(
                    f"{mi.group(1)}: künye '{m.group(1)}' diyor, s.{pages[0]} "
                    f"{src['volume']} cildinde"
                )
            rows.append(
                {
                    "id": mi.group(1),
                    "type": "quotation",
                    "axis": axis,
                    "section": num,
                    "section_url": url,
                    "quote": quote,
                    "strength": m.group(4) or None,
                    "book": src.get("book"),
                    "volume": src.get("volume"),
                    "printed_page": pages[0],
                    "printed_page_end": pages[1] if len(pages) > 1 else None,
                    "citation": src.get("citation"),
                    "source_url": src.get("url"),
                    "verified": verify(quote, pages, corpus),
                }
            )

        for blok in alt_bloklar(sub):
            alintilar = ALINTI_ISARET_RE.findall(blok)
            verses = AYET_ISARET_RE.findall(blok)
            for bid, govde in bulgular(blok):
                quotations = BLOK_DISI_DAYANAK.get(bid, alintilar)
                if not quotations:
                    raise SystemExit(
                        f"{bid}: başlığının altında alıntı yok — dayanağı başka "
                        f"bölümdeyse BLOK_DISI_DAYANAK'a yazılmalı"
                    )
                if not verses:
                    raise SystemExit(f"{bid}: başlığının altında ayet yok")
                eksik = [v for v in verses if v not in ayetler]
                if eksik:
                    raise SystemExit(f"{bid} tanımsız ayete atıf yapıyor: {eksik}")
                rows.append(
                    {
                        "id": bid,
                        "type": "finding",
                        "axis": axis,
                        "section": num,
                        "section_url": url,
                        "statement": clean(govde.strip()),
                        "quotations": list(quotations),
                        "verses": list(verses),
                        "quran": [ayetler[v] for v in verses],
                    }
                )
    return rows


def parse_claims(md: str) -> list[dict]:
    """§5 — kitaba dayanarak söylenebilecekler (Öz-01…).

    Bunlar bulgu değildir: itikadî bir hüküm taşımaz, yalnız kitabın sarih
    lafzını özetler. Her maddenin künyesi, o lafzı taşıyan alıntıdır."""
    h5, body = next(((h, b) for h, b in sections(md, 2) if h.startswith("5.")), ("5.", ""))
    rows: list[dict] = []
    for i, item in enumerate(re.findall(r"^\d+\.\s+(.*?)(?=^\d+\.\s|\Z)", body, re.M | re.S), 1):
        text = re.sub(r"\s*-{3,}\s*$", "", clean(item))  # son maddede bölüm ayracı
        m = re.search(r"\((Alıntı-\d+(?:,\s*Alıntı-\d+)*)\)\s*$", text)
        if not m:
            raise SystemExit(f"§5 madde {i}: alıntı künyesi yok — '(Alıntı-…)' bekleniyor")
        rows.append(
            {
                "id": _isaret("Öz-", 2, i),
                "type": "claim",
                "statement": text[: m.start()].strip(),
                "quotations": [q.strip() for q in m.group(1).split(",")],
                "section_url": f"{REVIEW_URL}#{heading_id(h5)}",
            }
        )
    return rows


def parse_limits(md: str) -> list[dict]:
    """§6 — delil sınırları (S1…Sn).

    Bunlar alıntı da bulgu da değildir: kitabın lafzının *ispat etmediği*
    iddiaları sayar. Ayrı bir tip olmalarının sebebi budur — bir sınır, bir
    hüküm değil, hükmün nereye kadar gittiğinin kaydıdır."""
    body = next((b for h, b in sections(md, 2) if h.startswith("6.")), "")
    rows: list[dict] = []
    for item in re.findall(r"^\d+\.\s+(.*?)(?=^\d+\.\s|\Z)", body, re.M | re.S):
        text = clean(item)
        mi = re.match(r"^\[(S\d+)\]\s*", text)
        if not mi:
            raise SystemExit(f"indekssiz sınır: {text[:60]}…")
        text = text[mi.end() :].strip()
        m = re.match(r'^"?(.+?)"?\s*denemez\.\s*(.*)$', text)
        rows.append(
            {
                "id": mi.group(1),
                "type": "limit",
                "claim": (m.group(1).strip().strip('"') if m else text),
                "verdict": "metin bunu desteklemez",
                "reason": (m.group(2).strip() if m else None),
                "refers_to": sorted(set(ATIF_RE.findall(text))),
                "section_url": f"{REVIEW_URL}#s-6-kitaba-dayanarak-soylenemeyecekler",
            }
        )
    return rows


def check_translation(corpus: dict[int, dict]) -> tuple[int, int, list[str]]:
    """İngilizce sürümdeki Türkçe alıntıları da doğrular.

    Çeviri sürümünde alıntının kendisi 1931 Türkçesiyle kalır; İngilizcesi
    köşeli parantez içinde yanına konur. Buradaki risk, çeviri yazılırken
    Türkçe lafzın elle kopyalanması sırasında bozulmasıdır — bu denetim onu
    yakalar. Alıntılanan sayfa künyesi "p. N" biçimindedir."""
    path = ROOT / "docs" / "REVIEW-EN.md"
    if not path.exists():
        return 0, 0, []
    ok, total, bad = 0, 0, []
    for block in re.findall(r"(?:^>.*\n?)+", path.read_text(encoding="utf-8"), re.M):
        text = clean(" ".join(l.lstrip("> ").rstrip() for l in block.splitlines()))
        # Künye "— p. 21" ya da "— [Tarih I](url), p. 21" biçiminde olabilir.
        m = re.search(
            # Sayfa aralığı İngilizce sürümde "pp. 85-86" biçimindedir; yalnız "p."
            # arayan bir kalıp o künyeleri hiç görmez ve alıntı sessizce denetim
            # dışında kalırdı.
            r"—\s*(?:\[?Tarih I{1,2}\]?(?:\([^)]*\))?\s*,\s*)?pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?",
            text,
        )
        if not m:
            continue
        head = text[: m.start()].strip()
        if '"' not in head:
            continue
        quote = head[head.index('"') + 1 : head.rindex('"')] if head.count('"') >= 2 else head
        if len(quote) < 20:
            continue
        total += 1
        pages = [int(m.group(1))] + ([int(m.group(2))] if m.group(2) else [])
        if verify(quote, pages, corpus):
            ok += 1
        else:
            bad.append(f"p.{pages[0]}  {quote[:60]}…")
    return ok, total, bad


def _aralik(ids: list[str]) -> str:
    # Ayraç kısa çizgi (-) değil en tire (–): işaretin kendisi zaten kısa çizgi
    # taşıyor, "Alıntı-01-Alıntı-34" dizisinde ilk işaretin nerede bittiği
    # okunmuyor.
    return ids[0] if len(ids) == 1 else f"{ids[0]}–{ids[-1]}"


def _hucre(satir: str) -> list[str]:
    """Markdown tablo satırının hücreleri, vurgu işaretlerinden arınmış."""
    return [c.strip(" *") for c in satir.strip("|").split("|")]


# (kayıt tipi, işaret ön eki, etiket, sıra numarasının basamak sayısı).
# Seriler iki basamakla yazılır — "Alıntı-07" sıralı okumada "Alıntı-7"den daha
# kolay taranır ve metin içi arama tek biçim bulur. Öz ve S serilerinin metinde
# işareti yoktur; kimlikleri yalnız makine-okunabilir kayıtta durur.
SERI = (
    ("quotation", "Alıntı-", "alıntı", 2),
    ("finding", "Bulgu-", "bulgu", 2),
    ("claim", "Öz-", "söylenebilecek", 2),
    ("verse", "Ayet-", "ayet", 2),
    ("limit", "S", "delil sınırı", 0),
)


def _isaret(on: str, basamak: int, i: int) -> str:
    return f"{on}{i:0{basamak}d}" if basamak else f"{on}{i}"


def check_index(md: str, rows: list[dict]) -> dict[str, int]:
    """Üç indeksin bütünlüğü.

    Sayı ancak şunların hepsi tutarsa gerçektir: her indeks (Alıntı-01…,
    Bulgu-01…, Ayet-01…) eksiksiz ve sıralıdır; metindeki işaret sayısı
    ayrıştırılan kayıt sayısını tutar; §2 tablosundaki her eksen aralığı o
    eksende fiilen bulunanla örtüşür; her bulgu hem mevcut bir alıntıya hem bir
    ayete dayanır; ve hiçbir alıntı bulgusuz kalmaz."""
    # Belgedeki işaret sayısı ile ayrıştırılan kayıt sayısı tutmalı. Aksi hâlde
    # künye biçimi değişip ayrıştırıcı sessizce hiçbir şey bulamayabilir.
    for kalip, tip, etiket in (
        (r"\*\*\[\[?Alıntı-\d+\]", "quotation", "alıntı"),
        (r"\*\*\[Ayet-\d+\]\*\*", "verse", "ayet"),
        (r"^> \*\*\[Bulgu-\d+\]\*\*", "finding", "bulgu"),
    ):
        m_sayi = len(re.findall(kalip, md, re.M))
        r_sayi = sum(1 for r in rows if r["type"] == tip)
        if m_sayi != r_sayi:
            raise SystemExit(
                f"metinde {m_sayi} {etiket} işareti var, ayrıştırılan {r_sayi} — "
                f"künye biçimi ayrıştırıcıyla uyuşmuyor"
            )

    sayilar: dict[str, int] = {}
    for tip, on, etiket, basamak in SERI:
        ids = [r["id"] for r in rows if r["type"] == tip]
        beklenen = [_isaret(on, basamak, i) for i in range(1, len(ids) + 1)]
        if ids != beklenen:
            raise SystemExit(f"{etiket} indeksi bozuk:\n  var:      {ids}\n  beklenen: {beklenen}")
        sayilar[tip] = len(ids)

    # Bulgunun tarifi: alıntı + ayet -> kanaat. İkisinden biri eksikse bulgu değildir.
    var = {r["id"] for r in rows if r["type"] == "quotation"}
    for r in rows:
        if r["type"] != "claim":
            continue
        eksik = [q for q in r["quotations"] if q not in var]
        if eksik:
            raise SystemExit(f"{r['id']} olmayan alıntıya dayanıyor: {eksik}")

    kullanilan: set[str] = set()
    for r in rows:
        if r["type"] != "finding":
            continue
        eksik = [q for q in r["quotations"] if q not in var]
        if eksik:
            raise SystemExit(f"{r['id']} olmayan alıntıya dayanıyor: {eksik}")
        if not r["quotations"]:
            raise SystemExit(f"{r['id']} hiçbir alıntıya dayanmıyor")
        if not r["quran"]:
            raise SystemExit(f"{r['id']} ayet dayanağı taşımıyor")
        kullanilan.update(r["quotations"])
    if var - kullanilan:
        raise SystemExit(f"hiçbir bulguya girmeyen alıntı: {sorted(var - kullanilan)}")

    # Metinde geçen her indeks atfı gerçekten bir kayda karşılık gelmeli.
    kayitli = {r["id"] for r in rows}
    for atif in sorted(set(ATIF_RE.findall(md))):
        if atif not in kayitli:
            raise SystemExit(f"metinde tanımsız indekse atıf var: {atif}")

    # §2 tablosu yalnız §3'ün eksenlerini listeler
    eksen: dict[str, dict[str, list[str]]] = {}
    for r in rows:
        if r["type"] in ("quotation", "finding") and r["section"].startswith("3."):
            eksen.setdefault(r["axis"], {}).setdefault(r["type"], []).append(r["id"])
    for ad, d in eksen.items():
        # Eksen adı satırın hangi sütununda olursa olsun bulunur.
        satir = next((l for l in md.splitlines() if l.startswith("|") and ad in _hucre(l)), None)
        if satir is None:
            raise SystemExit(f"§2 tablosunda '{ad}' satırı yok")
        hucre = _hucre(satir)
        for tip in ("quotation", "finding"):
            beklenen = _aralik(d.get(tip, []))
            if beklenen and beklenen not in hucre:
                raise SystemExit(f"§2/'{ad}': {beklenen} bekleniyordu — satır: {satir}")
    return sayilar


def check_annex(rows: list[dict]) -> int:
    """Eklerdeki her indeks atfı gerçek bir kayda karşılık gelmeli.

    Ekler ana metinden ayrı bir dosyada durur; ana metin yeniden numaralandığında
    ekler sessizce yanlış bulguya işaret edebilir. Bu denetim onu yakalar."""
    if not ANNEX_MD.exists():
        return 0
    kayitli = {r["id"] for r in rows}
    atiflar = set(ATIF_RE.findall(ANNEX_MD.read_text(encoding="utf-8")))
    eksik = sorted(a for a in atiflar if a not in kayitli)
    if eksik:
        raise SystemExit(f"eklerde tanımsız indekse atıf var: {eksik}")
    return len(atiflar)


# İngilizce eklerde indeks işaretleri çevrilir; kayıtların kimliği Türkçedir.
EN_ISARET = {"Quote": "Alıntı", "Verse": "Ayet", "Finding": "Bulgu"}
EN_ATIF_RE = re.compile(r"(?<![\w/-])(Quote|Verse|Finding)-(\d+)\b")
# İngilizce eklerde Türkçe asıl, çevirisinden hemen önce gelen tırnaklı dizedir;
# ön söz paragrafları ise "> " ile başlar, çevirileri "> [" ile.
EN_ASIL_RE = re.compile(r'"([^"]{6,})"\s+\[')


def check_annex_en(rows: list[dict]) -> tuple[int, int]:
    """İngilizce eklerin iki şeyi denetlenir.

    Biri, çevrilmiş indeks atıflarının (Quote-01, Bulgu-01'in karşılığı) gerçek
    bir kayda düşmesi. Öteki, belgede alıntılanabilir olarak duran Türkçe
    metnin — kitap cümleleri, lügat tanımları, 1931 ön sözü — Türkçe eklerdeki
    hâliyle birebir aynı olması: çeviri yazılırken elle kopyalanıyorlar ve
    sessizce bozulabilirler."""
    if not ANNEX_EN_MD.exists():
        return 0, 0
    en = ANNEX_EN_MD.read_text(encoding="utf-8")
    kayitli = {r["id"] for r in rows}
    atiflar = {f"{EN_ISARET[t]}-{n}" for t, n in EN_ATIF_RE.findall(en)}
    eksik = sorted(a for a in atiflar if a not in kayitli)
    if eksik:
        raise SystemExit(f"İngilizce eklerde tanımsız indekse atıf var: {eksik}")
    if not ANNEX_MD.exists():
        return len(atiflar), 0
    tr = ANNEX_MD.read_text(encoding="utf-8")
    asillar = EN_ASIL_RE.findall(en) + [
        satir[2:].strip()
        for satir in en.splitlines()
        if satir.startswith("> ") and not satir.startswith("> [") and satir[2:].strip()
    ]
    bozuk = [a for a in asillar if a not in tr]
    if bozuk:
        raise SystemExit(
            "İngilizce eklerdeki Türkçe asıl, Türkçe eklerde birebir bulunamadı: "
            + "; ".join(a[:70] for a in bozuk[:3])
        )
    return len(atiflar), len(asillar)


def _fold(s: str) -> str:
    tr = str.maketrans("çğıİöşüÇĞÖŞÜâîûÂÎÛ", "cgiiosucgosuaiuaiu")
    return re.sub(r"[*`_]", "", s).translate(tr).lower()


# ---------------------------------------------------------------------------


def main() -> None:
    if not REVIEW_MD.exists():
        print("    inceleme belgesi yok — atlandı")
        return

    md = REVIEW_MD.read_text(encoding="utf-8")
    corpus = corrected_pages()
    ayet_rows = parse_verses(md)
    ayetler = {r["id"]: r["reference"] for r in ayet_rows}
    rows = (
        parse_axis(md, corpus, "3.", ayetler)
        + parse_axis(md, corpus, "4.", ayetler)
        + ayet_rows
        + parse_claims(md)
        + parse_limits(md)
    )
    for r in rows:
        r["review_url"] = REVIEW_URL
        if REVIEW_DOI:
            r["review_doi"] = REVIEW_DOI
        r["license"] = "CC0-1.0"

    OUT_DIR.mkdir(exist_ok=True)
    write_jsonl(OUT_DIR / "bulgular.jsonl", rows)
    if WEB_DIR.exists():
        write_jsonl(WEB_DIR / "inceleme.jsonl", rows)
        # Aynı kayıtlar .json olarak da yazılır. Sebep tür: GitHub Pages
        # .jsonl uzantısını tanımadığı için application/octet-stream sunuyor ve
        # bazı getiriciler (dil modellerinin sayfa çekicileri dahil) o türü
        # okumayı reddedip indirmeye çalışıyor. .json ise application/json
        # olarak sunulur. Adres tektir, içerik aynıdır; JSONL satır satır
        # işlemek isteyen için durur.
        write_text(WEB_DIR / "inceleme.json",
                   json.dumps(rows, ensure_ascii=False, indent=1) + chr(10))

    n = check_index(md, rows)
    # Boş seriler yazılmaz: bir tip belgeden tamamen çıkarılmış olabilir.
    var = [(t, o, e, b) for t, o, e, b in SERI if n[t]]
    print(
        "    indeks: "
        + ", ".join(
            _aralik([_isaret(o, b, 1), _isaret(o, b, n[t])]) for t, o, _, b in var
        )
        + " eksiksiz ve sıralı; §2 tablosundaki eksen aralıklarıyla tutarlı"
    )
    print("    " + ", ".join(f"{n[t]} {e}" for t, _, e, _b in var))

    checked = [r for r in rows if r["type"] == "quotation"]
    ok = sum(1 for r in checked if r["verified"])
    print(f"    alıntı doğrulaması: {ok}/{len(checked)} künyesindeki sayfada birebir bulundu")
    for r in checked:
        if not r["verified"]:
            print(f"      DOĞRULANMADI  {r['id']}  s.{r['printed_page']}  {r['quote'][:60]}…")

    n_ek = check_annex(rows)
    if n_ek:
        print(f"    ekler: {ANNEX_MD.name} — {n_ek} indeks atfının hepsi ana metinde var")

    n_ek_en, n_asil = check_annex_en(rows)
    if n_ek_en:
        print(f"    ekler (İngilizce): {n_ek_en} indeks atfı yerinde, "
              f"{n_asil} Türkçe asıl Türkçe eklerle birebir")

    en_ok, en_total, en_bad = check_translation(corpus)
    if en_total:
        print(f"    İngilizce sürüm: {en_ok}/{en_total} Türkçe alıntı kaynakla birebir")
        for line in en_bad:
            print(f"      DOĞRULANMADI  {line}")


if __name__ == "__main__":
    main()
