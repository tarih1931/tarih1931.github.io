"""04 — AI-ready korpus dosyalarını üretir.

Üretilenler (her kitap için):
  text/full.txt          sayfa işaretli düz metin  ([[s. 48]] beacon'ları)
  text/pNNNN.txt         sayfa başına düz metin
  <slug>.md              sayfa çıpalı Markdown
  <slug>.tei.xml         TEI P5 (bilimsel arşiv standardı, <pb n=".."/> ile)
  chunks.jsonl           RAG parçaları (her parça sayfa künyesini taşır)
  structure.json         running head'lerden türetilen bölüm haritası

Tasarım kararı: düz metin içinde de sayfa beacon'ları bırakılır. Böylece bir dil
modeli yalnız .txt dosyasını okusa bile hangi cümlenin hangi basılı sayfada
geçtiğini bilir ve doğru sayfa numarasıyla alıntı yapabilir.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, META_DIR, Book, read_jsonl, write_json, write_jsonl, write_text  # noqa: E402

CHUNK_TARGET = 1500
CHUNK_OVERLAP = 200

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
BOOKMETA = {b["slug"]: b for b in META["books"]}


def page_label(row: dict) -> str:
    if row["printed_page"] is not None:
        return str(row["printed_page"])
    if row["printed_roman"]:
        return row["printed_roman"]
    return f"[{row['pdf_page'] + 1}{row['side'][0]}]"


# ---------------------------------------------------------------------------
# Bölüm haritası
# ---------------------------------------------------------------------------

GENERIC_HEADS = {"TARİH", "TARIH"}


def build_structure(rows: list[dict]) -> list[dict]:
    """Ardışık aynı running head'lerden bölüm aralıkları çıkarır.

    Kitapların sağ sayfa üst bilgisi bölüm adını taşır (sol sayfa yalnız
    'TARİH' yazar). Bu yüzden bölüm haritası recto başlıklarından kurulur.
    """
    sections: list[dict] = []
    cur: dict | None = None
    for row in rows:
        head = row.get("running_head")
        if not head or head in GENERIC_HEADS:
            continue
        if cur and cur["heading"] == head:
            cur["end_page"] = row["printed_page"] or cur["end_page"]
            cur["n_pages"] += 1
            continue
        if cur:
            sections.append(cur)
        cur = {
            "heading": head,
            "start_page": row["printed_page"],
            "end_page": row["printed_page"],
            "start_pdf_page": row["pdf_page"] + 1,
            "n_pages": 1,
        }
    if cur:
        sections.append(cur)
    # Tek sayfalık gürültü başlıklarını ele
    return [s for s in sections if s["n_pages"] >= 2]


# ---------------------------------------------------------------------------
# Parçalama (RAG)
# ---------------------------------------------------------------------------


def build_chunks(book: Book, rows: list[dict]) -> list[dict]:
    """Sayfa sınırlarını kaybetmeden RAG parçaları üretir."""
    units: list[tuple[dict, str]] = []
    for row in rows:
        if row["is_empty"]:
            continue
        for para in re.split(r"\n{2,}", row["text"]):
            para = para.strip()
            if para:
                units.append((row, para))

    chunks: list[dict] = []
    buf: list[tuple[dict, str]] = []
    size = 0

    def flush() -> None:
        nonlocal buf, size
        if not buf:
            return
        text = "\n\n".join(p for _, p in buf)
        pages = [r for r, _ in buf]
        nums = [r["printed_page"] for r in pages if r["printed_page"] is not None]
        first, last = (min(nums), max(nums)) if nums else (None, None)
        if first is not None:
            cite = (
                f"{book.title} {book.volume} ({book.year}), s. {first}"
                if first == last
                else f"{book.title} {book.volume} ({book.year}), s. {first}-{last}"
            )
        else:
            cite = f"{book.title} {book.volume} ({book.year}), numarasız sayfa"
        chunks.append(
            {
                "chunk_id": f"{book.slug}-c{len(chunks) + 1:04d}",
                "book": book.slug,
                "book_title": f"{book.title} {book.volume}",
                "year": book.year,
                "page_start": first,
                "page_end": last,
                "page_ids": sorted({r["page_id"] for r in pages}),
                "running_head": next((r.get("running_head") for r in pages if r.get("running_head")), None),
                "citation": cite,
                "text": text,
                "n_chars": len(text),
            }
        )
        # örtüşme: son paragrafı taşı
        if len(buf) > 1 and len(buf[-1][1]) <= CHUNK_OVERLAP * 2:
            buf, size = [buf[-1]], len(buf[-1][1])
        else:
            buf, size = [], 0

    for row, para in units:
        if size and size + len(para) > CHUNK_TARGET:
            flush()
        buf.append((row, para))
        size += len(para)
    flush()
    return chunks


# ---------------------------------------------------------------------------
# TEI P5
# ---------------------------------------------------------------------------


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def build_tei(book: Book, rows: list[dict], sections: list[dict]) -> str:
    bm = BOOKMETA[book.slug]
    authors = "\n".join(
        f'          <author><persName type="printed">{esc(c["name_1931"])}</persName>'
        f'<persName type="modern">{esc(c["name_modern"])}</persName>'
        f'<roleName>{esc(c["role_1931"])}</roleName></author>'
        for c in COLL["contributors"]
    )
    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="tr">')
    parts.append("  <teiHeader>")
    parts.append("    <fileDesc>")
    parts.append("      <titleStmt>")
    parts.append(f'        <title type="main">{esc(bm["title_full"])}</title>')
    parts.append(f'        <title type="sub">{esc(COLL["name"])}</title>')
    parts.append(
        f'        <author type="corporate">{esc(COLL["corporate_author"]["name_1931"])}</author>'
    )
    parts.append(authors)
    parts.append("      </titleStmt>")
    parts.append("      <publicationStmt>")
    parts.append(f'        <publisher>{esc(bm["publisher"])}</publisher>')
    parts.append(f'        <pubPlace>{esc(bm["place"])}</pubPlace>')
    parts.append(f'        <date when="{bm["year"]}">{bm["year"]}</date>')
    parts.append(
        f'        <availability status="free"><licence target="{META["rights"]["derived_dataset_license_uri"]}">'
        f'{esc(META["rights"]["derived_dataset_license"])} (türetilmiş veri)</licence>'
        f"<p>{esc(META['rights']['reasoning'])}</p></availability>"
    )
    parts.append("      </publicationStmt>")
    parts.append("      <sourceDesc>")
    parts.append("        <bibl>")
    parts.append(f'          <title>{esc(bm["title_full"])}</title>')
    parts.append(f'          <publisher>{esc(bm["publisher"])}</publisher>')
    parts.append(f'          <pubPlace>{esc(bm["place"])}</pubPlace>')
    parts.append(f"          <date>{bm['year']}</date>")
    parts.append(f'          <note type="printer">{esc(bm["printer"])}</note>')
    parts.append(f'          <note type="approval">{esc(bm["approval"])}</note>')
    parts.append(f'          <note type="extent">{esc(bm["illustrations_statement"])}</note>')
    parts.append(f'          <idno type="ttk-item">{esc(bm["ttk_item_id"])}</idno>')
    parts.append(f'          <ref target="{esc(bm["ttk_url"])}">TTK Kütüphanesi</ref>')
    parts.append("        </bibl>")
    parts.append("      </sourceDesc>")
    parts.append("    </fileDesc>")
    parts.append("    <encodingDesc>")
    parts.append(
        "      <p>Metin, TTK taramasının gömülü OCR katmanından koordinat tabanlı olarak "
        "çıkarılmış; çift sayfa taramaları tek tek kitap sayfalarına ayrılmıştır. Basılı sayfa "
        "numaraları ve bölüm başlıkları, gömülü katmanda bulunmadığı için tarama görüntüsünden "
        "yeniden OCR edilmiştir. Metin düzeltilmemiş OCR çıktısıdır.</p>"
    )
    parts.append("    </encodingDesc>")
    parts.append("    <profileDesc>")
    parts.append('      <langUsage><language ident="tr">Türkçe (1931 imlası)</language></langUsage>')
    parts.append("      <textClass><keywords>")
    for s in COLL["subjects"]:
        parts.append(f"        <term>{esc(s)}</term>")
    parts.append("      </keywords></textClass>")
    parts.append("    </profileDesc>")
    parts.append("  </teiHeader>")
    parts.append("  <text><body>")

    sec_starts = {s["start_pdf_page"]: s for s in sections}
    open_div = False
    for row in rows:
        sec = sec_starts.get(row["pdf_page"] + 1)
        if sec and row["side"] == "recto":
            if open_div:
                parts.append("    </div>")
            parts.append(f'    <div type="section" n="{esc(sec["heading"])}">')
            parts.append(f"      <head>{esc(sec['heading'])}</head>")
            open_div = True
        n = page_label(row)
        conf = row.get("page_confidence") or "none"
        parts.append(
            f'      <pb n="{esc(n)}" xml:id="{esc(row["page_id"])}" '
            f'facs="#scan-{row["pdf_page"] + 1}-{row["side"]}" cert="{conf}"/>'
        )
        if row["is_empty"]:
            continue
        for para in re.split(r"\n{2,}", row["text"]):
            para = para.strip()
            if para:
                parts.append(f"      <p>{esc(para)}</p>")
    if open_div:
        parts.append("    </div>")
    parts.append("  </body></text>")
    parts.append("</TEI>")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------


def process_book(book: Book) -> dict:
    rows = list(read_jsonl(book.out_dir / "pages.jsonl"))
    bm = BOOKMETA[book.slug]
    sections = build_structure(rows)

    # --- düz metin ---------------------------------------------------------
    txt_dir = book.out_dir / "text"
    full: list[str] = []
    full.append(f"{bm['title_full']}")
    full.append(f"{COLL['corporate_author']['name_1931']} — {bm['publisher']}, {bm['place']}, {bm['year']}")
    full.append(f"Kaynak tarama: {bm['ttk_url']}")
    full.append(
        "Sayfa işaretleri [[s. N]] biçimindedir ve basılı sayfa numarasını gösterir; "
        "alıntı yaparken bu numarayı kullanınız."
    )
    full.append("=" * 70)
    full.append("")

    n_written = 0
    for row in rows:
        if row["is_empty"]:
            continue
        lbl = page_label(row)
        full.append(f"[[s. {lbl}]]")
        full.append(row["text"])
        full.append("")
        if row["printed_page"] is not None:
            write_text(txt_dir / f"p{row['printed_page']:04d}.txt", row["text"] + "\n")
            n_written += 1

    write_text(txt_dir / "full.txt", "\n".join(full))

    # --- Markdown ----------------------------------------------------------
    md: list[str] = [f"# {bm['title_full']}", ""]
    md.append(f"**{COLL['corporate_author']['name_1931']}** — {bm['publisher']}, {bm['place']}, {bm['year']}")
    md.append("")
    md.append(f"*{bm['approval']}*")
    md.append("")
    md.append(f"Kaynak tarama: <{bm['ttk_url']}>")
    md.append("")
    md.append("---")
    md.append("")
    cur_head = None
    for row in rows:
        if row["is_empty"]:
            continue
        h = row.get("running_head")
        if h and h not in GENERIC_HEADS and h != cur_head:
            md.append(f"## {h}")
            md.append("")
            cur_head = h
        lbl = page_label(row)
        md.append(f'<a id="{row["page_id"]}"></a>**[s. {lbl}]**')
        md.append("")
        md.append(row["text"])
        md.append("")
    write_text(book.out_dir / f"{book.slug}.md", "\n".join(md))

    # --- TEI ---------------------------------------------------------------
    write_text(book.out_dir / f"{book.slug}.tei.xml", build_tei(book, rows, sections))

    # --- chunks ------------------------------------------------------------
    chunks = build_chunks(book, rows)
    write_jsonl(book.out_dir / "chunks.jsonl", chunks)

    write_json(book.out_dir / "structure.json", {"book": book.slug, "sections": sections})

    return {
        "pages": len(rows),
        "page_txt_files": n_written,
        "sections": len(sections),
        "chunks": len(chunks),
        "chars": sum(r["n_chars"] for r in rows),
    }


def main() -> None:
    for book in BOOKS:
        print(f"--- {book.full_title}")
        for k, v in process_book(book).items():
            print(f"    {k:18s} {v}")


if __name__ == "__main__":
    main()
