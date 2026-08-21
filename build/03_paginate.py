"""03 — Her fiziksel kitap sayfasına kesin basılı sayfa numarası atar.

Yaklaşım: OCR ile okunan sayfa numaraları *çapa* kabul edilir, fakat tek başına
güvenilmez (levha sayfaları numarasızdır, bazı başlıklar okunmaz, OCR yanılır).
Bunun yerine şu kısıtlar birlikte çözülür:

  * Ardışık yarım sayfalar arasında basılı numara birer birer artar.
  * Sol sayfa (verso) çift, sağ sayfa (recto) tek numaralıdır.
  * Metin dışı levhalar (renkli tablo, harita) numarasızdır ve diziyi kaydırır;
    bu yüzden ofset kitap boyunca parça parça sabittir, tek bir sabit değil.

Yerel çoğunluk (mod) uzlaşmasıyla hatalı OCR çapaları elenir, kalanlardan
sabit-ofset segmentleri kurulur ve numaralar bu segmentlerden türetilir.

Çıktı: data/<slug>/pages.jsonl  (nihai, alıntılanabilir sayfa kayıtları)
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BOOKS,
    Book,
    collapse_ws,
    dehyphenate,
    is_watermark,
    read_jsonl,
    roman_to_int,
    write_json,
    write_jsonl,
)

# Yerel uzlaşma penceresi (çapa sayısı, tek taraf).
WINDOW = 6
# Bir segmentin geçerli sayılması için gereken en az çapa sayısı.
MIN_SEGMENT_ANCHORS = 3
# Şerit içinde aynı satır sayılacak normalize dikey tolerans.
ROW_TOL = 0.12

# OCR'ın Türkçe büyük İ/Ç/Ş harflerini karıştırdığı yaygın running head'ler.
HEAD_CANON = {
    "ICINDEKILER": "İÇİNDEKİLER",
    "ICINDEKILEB": "İÇİNDEKİLER",
    "TARIH": "TARİH",
    "TARIF": "TARİH",
    "ISLAM TARIHI": "İSLAM TARİHİ",
    "ESKIZAMANDAN ORTAZAMANA GIRERKEN": "ESKİZAMANDAN ORTAZAMANA GİRERKEN",
    "IBRANILER": "İBRANİLER",
    "BESER TARIHINE GIRIS": "BEŞER TARİHİNE GİRİŞ",
}


def canon_head(h: str | None) -> str | None:
    """Running head'i sadeleştirir ve bilinen biçimlere eşler."""
    if not h:
        return None
    key = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü ]", "", h).strip()
    key = re.sub(r"\s+", " ", key).upper()
    key = key.replace("İ", "I").replace("Ç", "C").replace("Ş", "S")
    if key in HEAD_CANON:
        return HEAD_CANON[key]
    return re.sub(r"\s+", " ", h).strip() or None


def upper_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def parse_header(dets: list[dict], side: str) -> tuple[int | None, str | None, str | None]:
    """Şeritteki tanımalardan üst bilgi satırını konuma göre ayıklar.

    Şerit gövde metninin ilk satırını da kapsayabildiği için yalnız en üstteki
    (filigran dışı) satır üst bilgi kabul edilir. Sayfa numarası dış kenardadır:
    verso'da solda, recto'da sağda.
    """
    usable = [d for d in dets if d.get("t", "").strip() and not is_watermark(d["t"])]
    if not usable:
        return None, None, None

    ymin = min(d["yc"] for d in usable)
    row = [d for d in usable if d["yc"] <= ymin + ROW_TOL]

    nums: list[tuple[float, int]] = []
    romans: list[tuple[float, str]] = []
    words: list[tuple[float, str]] = []

    for d in row:
        for tok in d["t"].split():
            c = tok.strip(".,;:()[]{}|-—–_'\"`°*")
            if not c:
                continue
            if c.isdigit():
                n = int(c)
                if 0 < n < 1200:
                    nums.append((d["xc"], n))
                continue
            if re.fullmatch(r"[IVXLCivxlc]{1,7}", c) and roman_to_int(c.upper()):
                romans.append((d["xc"], c.upper()))
                continue
            words.append((d["xc"], c))

    # Sayfa numarası dış kenarda olmalı: verso -> en solda, recto -> en sağda
    page_num = None
    if nums:
        nums.sort(key=lambda t: t[0])
        page_num = nums[0][1] if side == "verso" else nums[-1][1]

    roman = None
    if romans and page_num is None:
        romans.sort(key=lambda t: t[0])
        roman = romans[0][1] if side == "verso" else romans[-1][1]

    head_txt = " ".join(w for _, w in sorted(words, key=lambda t: t[0])).strip()
    head = canon_head(head_txt) if head_txt and upper_ratio(head_txt) >= 0.5 else None
    if head and len(head) < 3:
        head = None
    return page_num, roman, head


def expected_parity(side: str) -> int | None:
    """verso -> çift (0), recto -> tek (1)."""
    if side == "verso":
        return 0
    if side == "recto":
        return 1
    return None


def consensus_filter(anchors: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Yerel moda uymayan çapaları (OCR hatalarını) eler."""
    if not anchors:
        return []
    offsets = [p - i for i, p in anchors]
    kept: list[tuple[int, int]] = []
    for k, (i, p) in enumerate(anchors):
        lo = max(0, k - WINDOW)
        hi = min(len(anchors), k + WINDOW + 1)
        local = Counter(offsets[lo:hi])
        mode, count = local.most_common(1)[0]
        # Pencerede en az iki çapa aynı ofseti doğrulamalı
        if offsets[k] == mode and count >= 2:
            kept.append((i, p))
        elif count < 2 and offsets[k] == mode:
            kept.append((i, p))
    return kept


def monotonic_filter(anchors: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Sayfa numaraları kitap boyunca *artmak* zorundadır; aykırıları eler.

    Kitapların arkasındaki levha bölümünde ayrı bir numaralandırma (şekil
    numaraları) vardır ve üst bilgi OCR'ı bunları sayfa numarası sanır. Bu
    sahte dizi, gerçek gövde dizisinden çok daha kısadır; bu yüzden en uzun
    artan altdizi alınarak elenir.
    """
    if not anchors:
        return []
    # Patience sorting ile en uzun kesin artan altdizi
    tails: list[int] = []          # tails[k] = k+1 uzunluklu dizinin son öğesinin indeksi
    prev: list[int] = [-1] * len(anchors)
    import bisect

    vals: list[int] = []
    for i, (_, p) in enumerate(anchors):
        k = bisect.bisect_left(vals, p)
        if k == len(vals):
            vals.append(p)
            tails.append(i)
        else:
            vals[k] = p
            tails[k] = i
        prev[i] = tails[k - 1] if k > 0 else -1

    out: list[tuple[int, int]] = []
    cur = tails[-1] if tails else -1
    while cur != -1:
        out.append(anchors[cur])
        cur = prev[cur]
    out.reverse()
    return out


def build_segments(anchors: list[tuple[int, int]]) -> list[dict]:
    """Sabit ofsetli ardışık çapa gruplarını segmentlere ayırır."""
    segments: list[dict] = []
    cur: list[tuple[int, int]] = []
    cur_off: int | None = None
    for i, p in anchors:
        off = p - i
        if cur_off is None or off == cur_off:
            cur_off = off
            cur.append((i, p))
        else:
            segments.append({"offset": cur_off, "anchors": cur})
            cur, cur_off = [(i, p)], off
    if cur:
        segments.append({"offset": cur_off, "anchors": cur})

    out = []
    for seg in segments:
        idxs = [i for i, _ in seg["anchors"]]
        out.append(
            {
                "offset": seg["offset"],
                "start": min(idxs),
                "end": max(idxs),
                "n_anchors": len(idxs),
            }
        )
    return out


def assign_numbers(rows: list[dict], segments: list[dict]) -> None:
    """Segmentlere göre her satıra printed_page ve güven düzeyi yazar."""
    strong = [s for s in segments if s["n_anchors"] >= MIN_SEGMENT_ANCHORS]
    for i, row in enumerate(rows):
        if row.get("printed_page") is not None:
            continue
        seg = next((s for s in strong if s["start"] <= i <= s["end"]), None)
        if seg is None:
            # En yakın güçlü segmentin dışına taşan sayfa: levha ya da ön bölüm
            continue
        num = i + seg["offset"]
        par = expected_parity(row["side"])
        if par is not None and num % 2 != par:
            row["page_confidence"] = "uncertain"
            row["printed_page"] = num
            continue
        row["printed_page"] = num
        row["page_confidence"] = "inferred"


def process_book(book: Book) -> dict:
    raw = {(r["pdf_page"], r["side"]): r for r in read_jsonl(book.out_dir / "raw_pages.jsonl")}
    hdr_path = book.out_dir / "headers.jsonl"
    headers = {}
    if hdr_path.exists():
        headers = {(h["pdf_page"], h["side"]): h for h in read_jsonl(hdr_path)}

    rows: list[dict] = []
    for key in sorted(raw.keys(), key=lambda k: (k[0], {"verso": 0, "single": 0, "recto": 1}[k[1]])):
        r = raw[key]
        h = headers.get(key, {})
        num, roman, head = parse_header(h.get("dets", []), r["side"])
        rows.append(
            {
                "book": book.slug,
                "pdf_page": r["pdf_page"],
                "side": r["side"],
                "printed_page": num,
                "printed_roman": roman,
                "running_head": head,
                "page_confidence": "ocr" if num else None,
                "clip": r["clip"],
                "page_width": r["page_width"],
                "page_height": r["page_height"],
                "lines": r["lines"],
            }
        )

    # --- Çapaları topla, parite ve makullük süz -------------------------------
    anchors: list[tuple[int, int]] = []
    for i, row in enumerate(rows):
        p = row["printed_page"]
        if p is None or not (0 < p < 1200):
            continue
        par = expected_parity(row["side"])
        if par is not None and p % 2 != par:
            row["printed_page"] = None
            row["page_confidence"] = None
            continue
        anchors.append((i, p))

    raw_anchor_count = len(anchors)
    anchors = consensus_filter(anchors)
    after_consensus = len(anchors)
    anchors = monotonic_filter(anchors)

    # Uzlaşmayı geçemeyen çapaları düşür
    good = {i for i, _ in anchors}
    for i, row in enumerate(rows):
        if row["page_confidence"] == "ocr" and i not in good:
            row["printed_page"] = None
            row["page_confidence"] = None

    segments = build_segments(anchors)
    assign_numbers(rows, segments)

    # --- Metni derle ---------------------------------------------------------
    for row in rows:
        lines = row.pop("lines")
        row["text"] = collapse_ws(dehyphenate(lines))
        row["n_chars"] = len(row["text"])
        row["is_empty"] = row["n_chars"] < 40
        if row["printed_page"] is not None:
            row["citation"] = f"{book.title} {book.volume} ({book.year}), s. {row['printed_page']}"
            row["page_id"] = f"{book.slug}-p{row['printed_page']:04d}"
        elif row["printed_roman"]:
            row["citation"] = f"{book.title} {book.volume} ({book.year}), s. {row['printed_roman']}"
            row["page_id"] = f"{book.slug}-r{row['printed_roman']}"
        else:
            row["citation"] = (
                f"{book.title} {book.volume} ({book.year}), "
                f"numarasız sayfa (tarama {row['pdf_page'] + 1}{row['side'][0]})"
            )
            row["page_id"] = f"{book.slug}-u{row['pdf_page']:03d}{row['side'][0]}"
        row["scan_ref"] = {"pdf_page_1based": row["pdf_page"] + 1, "side": row["side"]}

    write_jsonl(book.out_dir / "pages.jsonl", rows)

    numbered = [r for r in rows if r["printed_page"]]
    stats = {
        "halves": len(rows),
        "raw_anchors": raw_anchor_count,
        "anchors_after_consensus": after_consensus,
        "anchors_after_monotonic": len(anchors),
        "segments": len(segments),
        "strong_segments": len([s for s in segments if s["n_anchors"] >= MIN_SEGMENT_ANCHORS]),
        "numbered": len(numbered),
        "by_ocr": sum(1 for r in rows if r["page_confidence"] == "ocr"),
        "inferred": sum(1 for r in rows if r["page_confidence"] == "inferred"),
        "uncertain": sum(1 for r in rows if r["page_confidence"] == "uncertain"),
        "unnumbered": sum(1 for r in rows if r["printed_page"] is None),
        "empty_pages": sum(1 for r in rows if r["is_empty"]),
        "page_range": (
            f"{min(r['printed_page'] for r in numbered)}-{max(r['printed_page'] for r in numbered)}"
            if numbered
            else "-"
        ),
        "duplicate_numbers": len(numbered) - len({r["printed_page"] for r in numbered}),
        "total_chars": sum(r["n_chars"] for r in rows),
    }
    write_json(book.out_dir / "pagination_report.json", {"stats": stats, "segments": segments})
    return stats


def main() -> None:
    for book in BOOKS:
        print(f"--- {book.full_title}")
        for k, v in process_book(book).items():
            print(f"    {k:24s} {v}")


if __name__ == "__main__":
    main()
