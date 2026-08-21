"""08 — Korpus kalite ve tutarlılık raporu üretir.

Bir kaynağın "yapay zekâya hazır" olması, güvenilirliğinin *ölçülebilir*
olmasını gerektirir. Bu betik hiçbir şeyi düzeltmez; yalnız ölçer ve
kusurları açıkça raporlar:

  * sayfa numarası sürekliliği (boşluk, tekrar, parite ihlali)
  * sayfa numarası güven dağılımı (okundu / çıkarıldı / şüpheli)
  * OCR sağlık göstergeleri (bozuk karakter oranı, çok kısa kelime oranı)
  * boş ve numarasız sayfalar

Çıktı: docs/KALITE-RAPORU.md, data/<slug>/quality.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, META_DIR, ROOT, Book, read_jsonl, write_json, write_text  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
BOOKMETA = {b["slug"]: b for b in META["books"]}

# Türkçe metinde beklenmeyen karakterler: OCR bozulmasının işareti.
JUNK_RE = re.compile(r"[^\w\s.,;:!?'\"()\[\]«»—–\-/%&°ºª]", re.UNICODE)
WORD_RE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû]+")


def ocr_health(text: str) -> dict:
    words = WORD_RE.findall(text)
    if not words:
        return {"words": 0, "junk_ratio": 0.0, "short_word_ratio": 0.0, "avg_word_len": 0.0}
    junk = len(JUNK_RE.findall(text))
    short = sum(1 for w in words if len(w) <= 2)
    return {
        "words": len(words),
        "junk_ratio": round(junk / max(len(text), 1), 4),
        "short_word_ratio": round(short / len(words), 4),
        "avg_word_len": round(sum(len(w) for w in words) / len(words), 2),
    }


def analyse(book: Book) -> dict:
    rows = list(read_jsonl(book.out_dir / "pages.jsonl"))
    numbered = [r for r in rows if r.get("printed_page")]
    nums = sorted(r["printed_page"] for r in numbered)

    gaps: list[int] = []
    if nums:
        present = set(nums)
        gaps = [n for n in range(min(nums), max(nums) + 1) if n not in present]

    dup = [n for n, c in Counter(nums).items() if c > 1]

    parity_bad = [
        {"page": r["printed_page"], "side": r["side"], "pdf_page": r["pdf_page"] + 1}
        for r in numbered
        if (r["side"] == "verso" and r["printed_page"] % 2 == 1)
        or (r["side"] == "recto" and r["printed_page"] % 2 == 0)
    ]

    full = "\n".join(r["text"] for r in rows)
    health = ocr_health(full)

    per_page_health = [ocr_health(r["text"]) for r in rows if not r["is_empty"]]
    worst = sorted(
        (
            {"page_id": r["page_id"], "printed_page": r.get("printed_page"), **ocr_health(r["text"])}
            for r in rows
            if not r["is_empty"] and len(r["text"]) > 200
        ),
        key=lambda d: -d["junk_ratio"],
    )[:10]

    conf = Counter(r.get("page_confidence") or "yok" for r in rows)

    return {
        "book": book.slug,
        "title": BOOKMETA[book.slug]["title_full"],
        "physical_pages": len(rows),
        "empty_pages": sum(1 for r in rows if r["is_empty"]),
        "numbered_pages": len(numbered),
        "unnumbered_pages": len(rows) - len(numbered),
        "roman_pages": sum(1 for r in rows if r.get("printed_roman")),
        "page_range": [min(nums), max(nums)] if nums else None,
        "missing_page_numbers": gaps,
        "n_missing": len(gaps),
        "duplicate_page_numbers": sorted(dup),
        "parity_violations": parity_bad,
        "confidence": dict(conf),
        "characters": sum(r["n_chars"] for r in rows),
        "ocr_health_overall": health,
        "pages_analysed": len(per_page_health),
        "worst_ocr_pages": worst,
    }


def main() -> None:
    reports = []
    for book in BOOKS:
        rep = analyse(book)
        write_json(book.out_dir / "quality.json", rep)
        reports.append(rep)
        print(f"    {book.slug}: {rep['numbered_pages']} numaralı sayfa, "
              f"{rep['n_missing']} eksik, {len(rep['parity_violations'])} parite ihlali")

    md = ["# Korpus Kalite Raporu", ""]
    md.append("Bu rapor otomatik üretilmiştir (`build/08_verify.py`). Hiçbir düzeltme yapılmaz; ")
    md.append("yalnız ölçüm ve kusur bildirimi içerir.")
    md.append("")
    md.append("## Genel")
    md.append("")
    md.append("| Cilt | Fiziksel sayfa | Numaralı | Numarasız | Boş | Sayfa aralığı | Karakter |")
    md.append("|---|---:|---:|---:|---:|---|---:|")
    for r in reports:
        rng = f"{r['page_range'][0]}–{r['page_range'][1]}" if r["page_range"] else "—"
        md.append(
            f"| {r['title']} | {r['physical_pages']} | {r['numbered_pages']} | "
            f"{r['unnumbered_pages']} | {r['empty_pages']} | {rng} | {r['characters']:,} |"
        )
    md.append("")
    md.append("## Sayfa numarası güven dağılımı")
    md.append("")
    md.append("`ocr` = taramadan doğrudan okundu · `inferred` = sayfa dizisinden çıkarıldı · ")
    md.append("`uncertain` = tek/çift beklentisine uymuyor, teyit gerekir")
    md.append("")
    md.append("| Cilt | ocr | inferred | uncertain | yok |")
    md.append("|---|---:|---:|---:|---:|")
    for r in reports:
        c = r["confidence"]
        md.append(
            f"| {r['title']} | {c.get('ocr', 0)} | {c.get('inferred', 0)} | "
            f"{c.get('uncertain', 0)} | {c.get('yok', 0)} |"
        )
    md.append("")
    md.append("## Tutarlılık")
    md.append("")
    for r in reports:
        md.append(f"### {r['title']}")
        md.append("")
        md.append(f"- Eksik sayfa numarası: **{r['n_missing']}**")
        if r["missing_page_numbers"]:
            preview = ", ".join(str(x) for x in r["missing_page_numbers"][:40])
            more = " …" if r["n_missing"] > 40 else ""
            md.append(f"  - {preview}{more}")
            md.append(
                "  - Bu numaralar genellikle metin dışı **levha sayfalarına** (renkli tablo, "
                "harita, resim) denk gelir; kitapta o numara basılı olmayabilir."
            )
        md.append(f"- Tekrarlanan sayfa numarası: **{len(r['duplicate_page_numbers'])}** "
                  f"{r['duplicate_page_numbers'][:20] if r['duplicate_page_numbers'] else ''}")
        md.append(f"- Parite ihlali (sol sayfa tek / sağ sayfa çift): **{len(r['parity_violations'])}**")
        if r["parity_violations"]:
            md.append(f"  - {r['parity_violations'][:10]}")
        md.append("")
    md.append("## OCR sağlık göstergeleri")
    md.append("")
    md.append("`junk_ratio` = tanınmayan karakter oranı · `short_word_ratio` = 1-2 harflik ")
    md.append("kelime oranı (yüksekse metin parçalanmış demektir)")
    md.append("")
    md.append("| Cilt | Kelime | junk_ratio | short_word_ratio | ort. kelime uzunluğu |")
    md.append("|---|---:|---:|---:|---:|")
    for r in reports:
        h = r["ocr_health_overall"]
        md.append(
            f"| {r['title']} | {h['words']:,} | {h['junk_ratio']} | "
            f"{h['short_word_ratio']} | {h['avg_word_len']} |"
        )
    md.append("")
    md.append("### En bozuk 10 sayfa (cilt başına)")
    md.append("")
    for r in reports:
        md.append(f"**{r['title']}**")
        md.append("")
        md.append("| Sayfa | junk_ratio | kelime |")
        md.append("|---|---:|---:|")
        for w in r["worst_ocr_pages"]:
            md.append(f"| {w.get('printed_page') or w['page_id']} | {w['junk_ratio']} | {w['words']} |")
        md.append("")
    md.append("## Bilinen sınırlar")
    md.append("")
    md.append(
        "- Metin **elle düzeltilmemiş OCR** çıktısıdır. 1931 imlası ve Osmanlı Türkçesi "
        "kelime dağarcığı hata oranını yükseltir.\n"
        "- Kenar boşluğundaki **omuz başlıkları** gövde metnine karışabilir.\n"
        "- **Resim altı yazıları** ve harita etiketleri eksik veya bozuk olabilir.\n"
        "- Kaynak tarama 150 DPI'dır; daha yüksek çözünürlüklü bir tarama, yeniden OCR ile "
        "kaliteyi belirgin biçimde artırır.\n"
        "- Numarasız **levha sayfaları** sayfa dizisinde boşluk olarak görünür."
    )
    write_text(ROOT / "docs" / "KALITE-RAPORU.md", "\n".join(md) + "\n")
    print("    docs/KALITE-RAPORU.md yazıldı")


if __name__ == "__main__":
    main()
