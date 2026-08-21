"""01 — Taranmış PDF'ten fiziksel kitap sayfalarını çıkarır.

Kaynak PDF'lerde her PDF sayfası bir *açık kitap* (çift sayfa / spread)
taramasıdır. Bu betik:
  1. Cilt payını (gutter) tespit edip sol (verso) ve sağ (recto) sayfayı ayırır,
  2. "TÜRK TARİH KURUMU" filigranını ve kütüphane damgalarını atar,
  3. Satırları koordinatlarına göre gerçek okuma sırasına dizer,
  4. Basılı sayfa numarasını ve sayfa üst başlığını (running head) okur,
  5. Her fiziksel kitap sayfası için bir kayıt üretir.

Çıktı: data/<slug>/raw_pages.jsonl
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    BOOKS,
    Book,
    is_noise_line,
    is_watermark,
    roman_to_int,
    write_jsonl,
)

# Bir PDF sayfasının çift sayfa sayılması için en/boy oranı eşiği.
SPREAD_ASPECT = 1.15
# Aynı satır sayılacak dikey tolerans (punto yüksekliğinin kabaca yarısı).
LINE_TOL = 4.0


def detect_gutter(width: float, line_boxes: list[tuple[float, float]]) -> float:
    """Sayfanın ortasındaki en geniş boş dikey bandın merkezini bulur."""
    lo, hi = width * 0.33, width * 0.67
    step = 2.0
    n = int((hi - lo) / step) + 1
    occupied = [False] * n
    for x0, x1 in line_boxes:
        i0 = max(0, int((x0 - lo) / step))
        i1 = min(n - 1, int((x1 - lo) / step))
        for i in range(i0, i1 + 1):
            occupied[i] = True

    best_len = best_start = -1
    cur_start = None
    for i, occ in enumerate(occupied + [True]):
        if not occ:
            if cur_start is None:
                cur_start = i
        else:
            if cur_start is not None:
                if i - cur_start > best_len:
                    best_len, best_start = i - cur_start, cur_start
                cur_start = None
    if best_len <= 0:
        return width / 2.0
    return lo + (best_start + best_len / 2.0) * step


def collect_lines(page: pymupdf.Page) -> list[dict]:
    """Sayfadaki tüm metin satırlarını bbox'larıyla toplar."""
    data = page.get_text("dict")
    lines: list[dict] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = [
                {
                    "text": s["text"],
                    "x0": s["bbox"][0],
                    "x1": s["bbox"][2],
                    "y0": s["bbox"][1],
                    "y1": s["bbox"][3],
                    "size": s.get("size", 0.0),
                }
                for s in line.get("spans", [])
                if s.get("text", "").strip()
            ]
            if not spans:
                continue
            lines.append(
                {
                    "spans": spans,
                    "x0": min(s["x0"] for s in spans),
                    "x1": max(s["x1"] for s in spans),
                    "y0": min(s["y0"] for s in spans),
                    "y1": max(s["y1"] for s in spans),
                }
            )
    return lines


def split_line_at(line: dict, gutter: float) -> tuple[dict | None, dict | None]:
    """Cilt payını aşan bir satırı span düzeyinde ikiye böler."""
    left = [s for s in line["spans"] if (s["x0"] + s["x1"]) / 2 < gutter]
    right = [s for s in line["spans"] if (s["x0"] + s["x1"]) / 2 >= gutter]

    def rebuild(spans):
        if not spans:
            return None
        return {
            "spans": spans,
            "x0": min(s["x0"] for s in spans),
            "x1": max(s["x1"] for s in spans),
            "y0": min(s["y0"] for s in spans),
            "y1": max(s["y1"] for s in spans),
        }

    return rebuild(left), rebuild(right)


def line_text(line: dict) -> str:
    """Bir satırın span'lerini soldan sağa birleştirir."""
    spans = sorted(line["spans"], key=lambda s: s["x0"])
    parts: list[str] = []
    prev_x1 = None
    for s in spans:
        t = s["text"]
        if prev_x1 is not None and s["x0"] - prev_x1 > 1.0 and parts and not parts[-1].endswith(" "):
            parts.append(" ")
        parts.append(t)
        prev_x1 = s["x1"]
    return "".join(parts).strip()


def group_rows(lines: list[dict]) -> list[list[dict]]:
    """Aynı basılı satıra ait parçaları tek bir satırda toplar.

    Kaynak OCR, iki yana yaslanmış dizgide kelime araları geniş olduğu için tek
    bir basılı satırı çoğu kez birkaç ayrı bloğa böler ("İptidaî insan," /
    "hemen adeta her şeyden" / "korkuyordu;"). Bunlar birleştirilmezse hem metin
    parçalı görünür hem de satır sonu tirelemesi düzgün onarılamaz.

    Ölçüt: dikey örtüşme, iki parçanın kısa olanının yüksekliğinin yarısından
    fazlaysa aynı satır sayılır.
    """
    if not lines:
        return []
    ordered = sorted(lines, key=lambda ln: (ln["y0"], ln["x0"]))
    rows: list[list[dict]] = [[ordered[0]]]

    for ln in ordered[1:]:
        cur = rows[-1]
        top = min(x["y0"] for x in cur)
        bot = max(x["y1"] for x in cur)
        overlap = min(bot, ln["y1"]) - max(top, ln["y0"])
        shortest = min(bot - top, ln["y1"] - ln["y0"])
        if shortest > 0 and overlap > shortest * 0.5:
            cur.append(ln)
        else:
            rows.append([ln])

    for r in rows:
        r.sort(key=lambda ln: ln["x0"])
    return rows


def row_text(row: list[dict]) -> str:
    """Bir basılı satırın parçalarını soldan sağa birleştirir."""
    return " ".join(t for t in (line_text(ln) for ln in row) if t).strip()


def extract_page_number(texts: list[str], side: str) -> tuple[int | None, str | None, str | None]:
    """Üst bilgi satırından basılı sayfa numarasını ve running head'i ayıklar.

    Sol (verso) sayfada numara solda, sağ (recto) sayfada sağdadır.
    Dönen: (arap rakamı, roma rakamı metni, running head)
    """
    for idx in range(min(3, len(texts))):
        t = texts[idx].strip()
        if not t or len(t) > 80:
            continue
        tokens = t.split()
        if not tokens:
            continue
        head_token = tokens[0] if side == "verso" else tokens[-1]
        rest = tokens[1:] if side == "verso" else tokens[:-1]
        cand = head_token.strip(".,;:()[]|")
        if cand.isdigit():
            num = int(cand)
            if 0 < num < 2000:
                return num, None, " ".join(rest).strip() or None
        rv = roman_to_int(cand)
        if rv is not None and len(cand) <= 7:
            return None, cand.upper(), " ".join(rest).strip() or None
    return None, None, None


def process_book(book: Book) -> dict:
    doc = pymupdf.open(book.pdf_path)
    records: list[dict] = []
    stats = {"pdf_pages": doc.page_count, "spreads": 0, "singles": 0}

    for pno in range(doc.page_count):
        page = doc[pno]
        w, h = page.rect.width, page.rect.height
        is_spread = (w / h) > SPREAD_ASPECT

        lines = collect_lines(page)
        # Filigran ve gürültüyü at
        lines = [ln for ln in lines if not is_watermark(line_text(ln))]

        if is_spread:
            stats["spreads"] += 1
            gutter = detect_gutter(w, [(ln["x0"], ln["x1"]) for ln in lines])
            left_lines: list[dict] = []
            right_lines: list[dict] = []
            for ln in lines:
                if ln["x0"] < gutter < ln["x1"]:
                    l, r = split_line_at(ln, gutter)
                    if l:
                        left_lines.append(l)
                    if r:
                        right_lines.append(r)
                elif (ln["x0"] + ln["x1"]) / 2 < gutter:
                    left_lines.append(ln)
                else:
                    right_lines.append(ln)
            halves = [
                ("verso", left_lines, (0.0, 0.0, gutter, h)),
                ("recto", right_lines, (gutter, 0.0, w, h)),
            ]
        else:
            stats["singles"] += 1
            gutter = None
            halves = [("single", lines, (0.0, 0.0, w, h))]

        for side, hl, clip in halves:
            texts = [row_text(r) for r in group_rows(hl)]
            texts = [t for t in texts if t]
            kept = [t for t in texts if not is_noise_line(t)]
            page_num, roman, head = extract_page_number(texts, side)
            records.append(
                {
                    "book": book.slug,
                    "pdf_page": pno,          # 0-tabanlı PDF sayfası
                    "side": side,             # verso | recto | single
                    "printed_page": page_num,
                    "printed_roman": roman,
                    "running_head": head,
                    "clip": [round(c, 2) for c in clip],
                    "page_width": round(w, 2),
                    "page_height": round(h, 2),
                    "gutter": round(gutter, 2) if gutter else None,
                    "n_lines": len(kept),
                    "lines": kept,
                    "lines_raw": texts,
                }
            )

    doc.close()
    out = book.out_dir / "raw_pages.jsonl"
    write_jsonl(out, records)
    stats["records"] = len(records)
    stats["with_page_number"] = sum(1 for r in records if r["printed_page"])
    stats["with_roman"] = sum(1 for r in records if r["printed_roman"])
    stats["empty"] = sum(1 for r in records if r["n_lines"] == 0)
    return stats


def main() -> None:
    for book in BOOKS:
        print(f"--- {book.full_title} ({book.year})")
        st = process_book(book)
        for k, v in st.items():
            print(f"    {k:20s} {v}")


if __name__ == "__main__":
    main()
