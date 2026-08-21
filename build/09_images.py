"""09 — Doğrulama için sayfa görüntülerini dışa aktarır (isteğe bağlı adım).

Bir alıntının doğruluğu ancak basılı sayfaya bakılarak teyit edilebilir. Bu
betik her *kitap sayfası* için ayrı bir JPEG üretir; web sitesinde metnin yanında
gösterilebilir ya da elle kontrol için kullanılabilir.

Varsayılan olarak hattın parçası DEĞİLDİR: iki cilt için ~1.180 görüntü üretir
ve kalite ayarına göre 80-350 MB yer kaplar.

    python build/09_images.py                # varsayılan: kalite 70, genişlik 1400
    python build/09_images.py --width 1000 --quality 60
    python build/09_images.py --pages 48,49,156
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, Book, read_jsonl  # noqa: E402


def export(book: Book, width: int, quality: int, only: set[int] | None) -> int:
    rows = list(read_jsonl(book.out_dir / "pages.jsonl"))
    out_dir = book.out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book.pdf_path)
    n = 0

    for row in rows:
        if only is not None and row.get("printed_page") not in only:
            continue
        if row["is_empty"] and only is None:
            continue
        page = doc[row["pdf_page"]]
        x0, y0, x1, y1 = row["clip"]
        clip = pymupdf.Rect(x0, y0, x1, y1)
        zoom = width / max(clip.width, 1)
        pm = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        name = (
            f"p{row['printed_page']:04d}.jpg"
            if row.get("printed_page")
            else f"{row['page_id'].split('-')[-1]}.jpg"
        )
        pm.pil_save(out_dir / name, format="JPEG", quality=quality, optimize=True)
        n += 1
        if n % 100 == 0:
            print(f"    {n} görüntü…", flush=True)

    doc.close()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=1400, help="piksel cinsinden hedef genişlik")
    ap.add_argument("--quality", type=int, default=70, help="JPEG kalitesi 1-95")
    ap.add_argument("--pages", default="", help="yalnız bu basılı sayfalar, virgülle")
    a = ap.parse_args()
    only = {int(x) for x in a.pages.split(",") if x.strip()} if a.pages else None

    total = 0
    for book in BOOKS:
        print(f"--- {book.full_title}")
        n = export(book, a.width, a.quality, only)
        print(f"    {n} görüntü -> {book.out_dir / 'images'}")
        total += n
    print(f"\nToplam {total} görüntü.")


if __name__ == "__main__":
    main()
