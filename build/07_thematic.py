"""07 — Din ve inanç konulu pasajların kavram dizinini (konkordans) üretir.

Bu betik *yorum yapmaz*. Yalnızca anahtar kelime eşleşen cümleleri, bağlamıyla
ve kesin sayfa künyesiyle birlikte çıkarır. Amaç, "bu kitapta din şöyle
anlatılıyor" iddiasının kaynağına — basılı sayfaya — kadar izlenebilmesidir.

Eşleştirme tasarımı
-------------------
1931 imlası yüzünden karşılaştırma, uzunluğu koruyan bir harf katlaması
(â→a, İ/I/ı→i, ş→s ...) üzerinden yapılır. Türkçe eklemeli bir dil olduğu için
köke ek gelmesine izin verilir; fakat serbest ek toleransı kısa köklerde ağır
yanlış pozitif üretir ("büyü" kökü "büyük" ile, "İsa" kökü "işaret" ile
eşleşir). Bu yüzden her terim iki kipten biriyle tanımlanır:

    open   — kök yeterince uzun ve ayırt edici; ek almasına izin verilir
    closed — kısa/çok anlamlı kök; yalnız açıkça sayılan biçimler eşleşir

Ayrıca bilinen çakışmalar için genel bir dışlama listesi uygulanır.

Çıktı: thematic/din-konkordans.jsonl, thematic/din-konkordans.md,
       thematic/tema-istatistik.json
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BOOKS,
    META_DIR,
    ROOT,
    WEB_DIR,
    read_jsonl,
    write_json,
    write_jsonl,
    write_text,
)

THEMATIC_DIR = ROOT / "thematic"
META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
BOOKMETA = {b["slug"]: b for b in META["books"]}

FOLD = str.maketrans(
    "âÂîÎûÛİIıÜüÖöÇçŞşĞğéÉèÈàÀ",
    "aaiiuuiiiuuooccssggeeeeaa",
)


def fold(s: str) -> str:
    """Türkçe aksanları ve büyük/küçük farkını, uzunluğu bozmadan katlar."""
    return s.translate(FOLD).lower()


# Kökle başlayıp yanlış temaya düşen bilinen kelimeler (katlanmış biçimde).
EXCLUDE = {
    "buyuk", "buyugu", "buyuge", "buyukler", "buyuklerin", "buyukluk", "buyuklugu",
    "isaret", "isaretler", "isaretle", "isabet", "isale", "isan", "isandir",
    "budak", "budala", "budaklari",
    "dinle", "dinler_", "dinlemek", "dinleyen", "dinlendi", "dinlenme",
    "dinc", "dinar", "dinamik", "dindir", "dindirmek",
    "putperestlik_",  # yer tutucu; gerçek dışlama gerekmiyor
    "manisa", "manisada", "manisaya", "manevi", "manevra",
    "ilimi_",
    "akim", "akin", "akinci", "akinlar",
    "gazete", "gazeteci", "gazi", "gaziler",
    "mekke_",
}

# mode: "open"  -> köke ek gelebilir
#       "closed"-> yalnız sayılan biçimler
THEMES: dict[str, list[dict]] = {
    "din-genel": [
        {"m": "closed", "f": ["din", "dini", "dine", "dinin", "dinden", "dinle", "dinler",
                              "dinlerin", "dinleri", "dinlerde", "dinsel", "dinsiz", "dinsizlik",
                              "diniye", "diniyat"]},
        {"m": "open", "s": "diyanet"}, {"m": "open", "s": "itikat"}, {"m": "open", "s": "itikad"},
        {"m": "open", "s": "iman"}, {"m": "open", "s": "mabut"}, {"m": "open", "s": "mabet"},
        {"m": "open", "s": "mabed"}, {"m": "open", "s": "ibadet"}, {"m": "open", "s": "ayin"},
        {"m": "open", "s": "akide"}, {"m": "open", "s": "mezhep"}, {"m": "open", "s": "mezheb"},
        {"m": "open", "s": "tanri"}, {"m": "open", "s": "allah"}, {"m": "closed",
                                                                   "f": ["ilah", "ilahi", "ilaha", "ilahlar",
                                                                         "ilahlari", "ilahlarin", "uluhiyet"]},
        {"m": "open", "s": "ruhani"}, {"m": "open", "s": "kutsal"}, {"m": "open", "s": "mukaddes"},
    ],
    "dinin-mensei": [
        {"m": "open", "s": "hurafe"}, {"m": "open", "s": "efsane"}, {"m": "open", "s": "esatir"},
        {"m": "open", "s": "batil itikat"}, {"m": "open", "s": "sihir"}, {"m": "open", "s": "sihirbaz"},
        {"m": "open", "s": "buyucu"}, {"m": "open", "s": "buyule"}, {"m": "open", "s": "totem"},
        {"m": "closed", "f": ["put", "putu", "puta", "putlar", "putlari", "putlarin", "putlara"]},
        {"m": "open", "s": "putperest"}, {"m": "open", "s": "fetis"}, {"m": "open", "s": "animizm"},
        {"m": "open", "s": "din mense"}, {"m": "open", "s": "dinlerin mense"},
        {"m": "open", "s": "iptidai felsefe"}, {"m": "open", "s": "tabu"},
        {"m": "open", "s": "iptidai din"}, {"m": "open", "s": "ilk insanlarin"},
    ],
    "islam": [
        {"m": "open", "s": "islam"}, {"m": "open", "s": "musluman"}, {"m": "open", "s": "kuran"},
        {"m": "open", "s": "kur'an"}, {"m": "open", "s": "muhammed"}, {"m": "open", "s": "peygamber"},
        {"m": "open", "s": "halife"}, {"m": "open", "s": "hilafet"}, {"m": "open", "s": "hicret"},
        {"m": "closed", "f": ["kabe", "kabeye", "kabenin", "kabede"]},
        {"m": "open", "s": "hadis"}, {"m": "open", "s": "seriat"}, {"m": "open", "s": "sunni"},
        {"m": "open", "s": "tasavvuf"}, {"m": "open", "s": "tarikat"}, {"m": "open", "s": "cihat"},
        {"m": "open", "s": "sahabe"}, {"m": "open", "s": "imamet"}, {"m": "open", "s": "medrese"},
    ],
    "hiristiyanlik": [
        {"m": "open", "s": "hiristiyan"}, {"m": "open", "s": "incil"}, {"m": "open", "s": "kilise"},
        {"m": "closed", "f": ["papa", "papanin", "papaya", "papayi", "papalar", "papalik",
                              "papaligin", "papaliga"]},
        {"m": "open", "s": "ruhban"}, {"m": "open", "s": "rahip"}, {"m": "open", "s": "papaz"},
        {"m": "open", "s": "hacli"}, {"m": "open", "s": "katolik"}, {"m": "open", "s": "ortodoks"},
        {"m": "open", "s": "protestan"}, {"m": "open", "s": "manastir"}, {"m": "open", "s": "engizisyon"},
        {"m": "open", "s": "vaftiz"}, {"m": "open", "s": "misyoner"},
        {"m": "closed", "f": ["isa", "isanin", "isaya", "isayi", "isadan", "isanin"]},
        {"m": "open", "s": "hazreti isa"}, {"m": "open", "s": "nasrani"},
    ],
    "musevilik": [
        {"m": "open", "s": "yahudi"}, {"m": "open", "s": "musevi"}, {"m": "open", "s": "ibrani"},
        {"m": "open", "s": "tevrat"}, {"m": "open", "s": "beniisrail"}, {"m": "open", "s": "sinagog"},
        {"m": "open", "s": "haham"},
        {"m": "closed", "f": ["musa", "musanin", "musaya", "musayi", "musadan"]},
        {"m": "open", "s": "musa peygamber"}, {"m": "open", "s": "israil"},
    ],
    "diger-dinler": [
        {"m": "open", "s": "budizm"}, {"m": "open", "s": "budist"},
        {"m": "closed", "f": ["buda", "budanin", "budaya", "budayi"]},
        {"m": "open", "s": "brahman"}, {"m": "open", "s": "zerdust"}, {"m": "open", "s": "mecusi"},
        {"m": "open", "s": "saman"}, {"m": "open", "s": "samanizm"}, {"m": "open", "s": "maniheizm"},
        {"m": "open", "s": "mani dini"}, {"m": "open", "s": "konfucyus"}, {"m": "open", "s": "taoizm"},
        {"m": "open", "s": "hinduizm"}, {"m": "open", "s": "atesperest"}, {"m": "open", "s": "mazdek"},
    ],
    "taassup-ve-akil": [
        {"m": "open", "s": "taassup"}, {"m": "open", "s": "taassub"}, {"m": "open", "s": "mutaassip"},
        {"m": "open", "s": "softa"}, {"m": "open", "s": "cehalet"}, {"m": "open", "s": "skolastik"},
        {"m": "open", "s": "musbet ilim"}, {"m": "open", "s": "musbet"},
        {"m": "closed", "f": ["akil", "akli", "akla", "aklin", "akilla", "akliye", "akilci"]},
        {"m": "open", "s": "mantik"}, {"m": "open", "s": "irtica"}, {"m": "open", "s": "tenvir"},
        {"m": "open", "s": "hurafeperest"}, {"m": "open", "s": "safsata"},
    ],
    "laiklik-ve-devlet": [
        {"m": "open", "s": "laik"}, {"m": "open", "s": "teokra"}, {"m": "open", "s": "ummet"},
        {"m": "open", "s": "seyhulislam"}, {"m": "open", "s": "vakif"}, {"m": "open", "s": "din adam"},
        {"m": "open", "s": "ruhani sinif"}, {"m": "open", "s": "din ve devlet"},
        {"m": "open", "s": "dini idare"},
    ],
}


def build_patterns() -> dict[str, list[tuple[str, re.Pattern]]]:
    out: dict[str, list[tuple[str, re.Pattern]]] = {}
    for theme, terms in THEMES.items():
        pats: list[tuple[str, re.Pattern]] = []
        for t in terms:
            if t["m"] == "closed":
                forms = sorted({fold(f) for f in t["f"]}, key=len, reverse=True)
                alt = "|".join(re.escape(f) for f in forms)
                label = t["f"][0]
                pats.append((label, re.compile(rf"(?<![a-z0-9])(?:{alt})(?![a-z])")))
            else:
                f = fold(t["s"])
                esc = re.escape(f).replace(r"\ ", r"\s+")
                pats.append((t["s"], re.compile(rf"(?<![a-z0-9]){esc}[a-z]{{0,14}}(?![a-z])")))
        out[theme] = pats
    return out


PATTERNS = build_patterns()
WORD_RE = re.compile(r"[a-z']+")


def real_matches(pat: re.Pattern, folded: str) -> list[str]:
    """Dışlama listesindeki kelimeleri eleyerek gerçek eşleşmeleri döner."""
    return [m.group(0) for m in pat.finditer(folded) if m.group(0) not in EXCLUDE]


# --- cümleleme -------------------------------------------------------------
# Türkçede ':' ve ';' cümle bitirmez. Kısaltmalardan ("S. 3.") kaynaklanan
# yanlış bölünmeler, çok kısa parçaları öncekine iliştirerek onarılır.
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ\"“(])")
MIN_SENT = 30


def split_sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    parts = SENT_SPLIT.split(flat)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if out and len(p) < MIN_SENT:
            out[-1] = out[-1] + " " + p
        elif out and len(out[-1]) < MIN_SENT:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


def is_front_matter(row: dict) -> bool:
    """İçindekiler / künye sayfaları gövde metni sayılmaz."""
    if row.get("printed_roman"):
        return True
    if row.get("printed_page") is None:
        return True
    head = (row.get("running_head") or "").upper()
    return "İÇİNDEKİLER" in head or "ICINDEKILER" in head


def process() -> None:
    THEMATIC_DIR.mkdir(parents=True, exist_ok=True)
    hits: list[dict] = []
    stats: dict[str, Counter] = defaultdict(Counter)
    term_counts: dict[str, Counter] = defaultdict(Counter)
    pages_per_theme: dict[str, set] = defaultdict(set)
    skipped_front = 0

    for book in BOOKS:
        path = book.out_dir / "pages.jsonl"
        if not path.exists():
            continue
        for row in read_jsonl(path):
            if row["is_empty"]:
                continue
            front = is_front_matter(row)
            if front:
                skipped_front += 1
                continue

            text = row["text"]
            folded_page = fold(text)
            sents = split_sentences(text)
            folded_sents = [fold(s) for s in sents]

            for theme, pats in PATTERNS.items():
                page_terms: Counter = Counter()
                for label, pat in pats:
                    ms = real_matches(pat, folded_page)
                    if ms:
                        page_terms[label] += len(ms)
                if not page_terms:
                    continue

                stats[theme][book.slug] += sum(page_terms.values())
                term_counts[theme].update(page_terms)
                if row["printed_page"]:
                    pages_per_theme[theme].add((book.slug, row["printed_page"]))

                for i, fs in enumerate(folded_sents):
                    found = sorted({label for label, pat in pats if real_matches(pat, fs)})
                    if not found:
                        continue
                    hits.append(
                        {
                            "book": book.slug,
                            "book_title": f"{BOOKMETA[book.slug]['title']} {BOOKMETA[book.slug]['volume']}",
                            "year": BOOKMETA[book.slug]["year"],
                            "printed_page": row["printed_page"],
                            "page_id": row["page_id"],
                            "page_confidence": row.get("page_confidence"),
                            "running_head": row.get("running_head"),
                            "theme": theme,
                            "terms": found,
                            "context_before": sents[i - 1] if i > 0 else "",
                            "sentence": sents[i],
                            "context_after": sents[i + 1] if i + 1 < len(sents) else "",
                            "citation": row["citation"],
                            "scan_ref": row["scan_ref"],
                        }
                    )

    write_jsonl(THEMATIC_DIR / "din-konkordans.jsonl", hits)

    summary = {
        "aciklama": (
            "Mekanik anahtar kelime eşleşmesiyle üretilmiş kavram dizinidir; yorum içermez. "
            "Kısa ve çok anlamlı kökler yalnız açıkça sayılan biçimlerle eşleşir, uzun ve "
            "ayırt edici kökler ek almaya toleranslıdır. Buna rağmen yanlış pozitif kalabilir. "
            "Künye ve içindekiler sayfaları dışarıda bırakılmıştır. "
            "Her kaydı kendi sayfa bağlamında okuyunuz."
        ),
        "uretim": "build/07_thematic.py",
        "toplam_kayit": len(hits),
        "atlanan_on_bolum_sayfasi": skipped_front,
        "temalar": {
            theme: {
                "toplam_esleme": sum(stats[theme].values()),
                "kitaplara_gore": dict(stats[theme]),
                "farkli_sayfa": len(pages_per_theme[theme]),
                "en_sik_terimler": term_counts[theme].most_common(15),
            }
            for theme in THEMES
        },
    }
    write_json(THEMATIC_DIR / "tema-istatistik.json", summary)

    md: list[str] = ["# Din ve İnanç Konulu Pasajlar — Kavram Dizini", ""]
    md.append(
        "`Tarih I` ve `Tarih II` (1931) ciltlerinde din, inanç ve dinî kurumlarla ilgili geçen "
        "pasajların **birebir** ve **sayfa künyeli** dizinidir."
    )
    md.append("")
    md.append("> **Yöntem uyarısı.** Liste mekanik anahtar kelime eşleşmesiyle üretilmiştir;")
    md.append("> yorum içermez ve yanlış pozitif barındırabilir. Metin düzeltilmemiş OCR")
    md.append("> çıktısıdır. Alıntı yapmadan önce ilgili sayfayı kaynak taramadan teyit ediniz.")
    md.append("")
    md.append("## Özet")
    md.append("")
    md.append("| Tema | Eşleşme | Farklı sayfa | En sık terimler |")
    md.append("|---|---:|---:|---|")
    for theme in THEMES:
        top = ", ".join(f"{t} ({n})" for t, n in term_counts[theme].most_common(5))
        md.append(f"| `{theme}` | {sum(stats[theme].values())} | {len(pages_per_theme[theme])} | {top} |")
    md.append("")

    by_theme: dict[str, list[dict]] = defaultdict(list)
    for h in hits:
        by_theme[h["theme"]].append(h)

    for theme in THEMES:
        rows = by_theme.get(theme, [])
        if not rows:
            continue
        md.append(f"## {theme} ({len(rows)} pasaj)")
        md.append("")
        rows.sort(key=lambda r: (r["book"], r["printed_page"] or 0))
        for h in rows:
            md.append(f"**{h['citation']}**" + (f" — *{h['running_head']}*" if h["running_head"] else ""))
            md.append("")
            md.append(f"> {h['sentence']}")
            md.append("")
            md.append(
                f'<sub>terimler: {", ".join(h["terms"])} · `{h["page_id"]}` · '
                f'tarama {h["scan_ref"]["pdf_page_1based"]}{h["scan_ref"]["side"][0]}</sub>'
            )
            md.append("")
    write_text(THEMATIC_DIR / "din-konkordans.md", "\n".join(md))

    # Kavram dizini siteden de sunulur. Kopyayı bu adım yapar: 06_web web/
    # klasörünü sıfırdan kurar ve bu adımdan önce çalışır.
    if WEB_DIR.exists():
        for name in ("din-konkordans.md", "din-konkordans.jsonl"):
            src = THEMATIC_DIR / name
            if src.exists():
                shutil.copy2(src, WEB_DIR / name)

    print(f"    {len(hits)} pasaj, {len(THEMES)} tema ({skipped_front} ön bölüm sayfası atlandı)")
    for theme in THEMES:
        print(f"      {theme:22s} {sum(stats[theme].values()):5d} eşleşme, {len(pages_per_theme[theme]):4d} sayfa")


if __name__ == "__main__":
    process()
