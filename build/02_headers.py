"""02 — Sayfa üst bilgilerini (running head + basılı sayfa numarası) yeniden OCR eder.

TTK taramalarının gömülü OCR katmanı, sayfa üst bilgilerini *atmıştır*: metin
katmanında ne sayfa numarası ne de bölüm başlığı vardır. Oysa bu bilgi taranmış
görüntüde fizikî olarak mevcuttur. Alıntılanabilirliğin tek dayanağı basılı
sayfa numarası olduğu için bu şerit RapidOCR ile yeniden okunur.

Şerit, sayfa yüksekliklerindeki değişkenliğe karşı bilerek geniş tutulur ve
gövde metninin ilk satırını da kapsayabilir; bu yüzden her tanımanın konumu
(kutu merkezi) da kaydedilir. Üst bilgi satırının gövdeden ayrıştırılması
konum bilgisiyle 03_paginate.py içinde yapılır.

Çıktı: data/<slug>/headers.jsonl   (her yarım sayfa için bir kayıt)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, Book, read_jsonl  # noqa: E402

# Üst bilgi şeridinin sayfa yüksekliğine oranla dikey sınırları.
BAND_TOP, BAND_BOTTOM = 0.040, 0.130
ZOOM = 4.0


def get_ocr():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def process_book(book: Book, ocr, log=print) -> None:
    rows = list(read_jsonl(book.out_dir / "raw_pages.jsonl"))
    out_path = book.out_dir / "headers.jsonl"

    done: set[tuple[int, str]] = set()
    if out_path.exists():
        for r in read_jsonl(out_path):
            done.add((r["pdf_page"], r["side"]))
        log(f"    {len(done)} kayıt mevcut, devam ediliyor")

    doc = pymupdf.open(book.pdf_path)
    t0 = time.time()
    n_new = 0

    with out_path.open("a", encoding="utf-8", newline="\n") as fh:
        for i, row in enumerate(rows):
            if (row["pdf_page"], row["side"]) in done:
                continue
            page = doc[row["pdf_page"]]
            x0, _, x1, _ = row["clip"]
            h = row["page_height"]
            y_top, y_bot = h * BAND_TOP, h * BAND_BOTTOM
            clip = pymupdf.Rect(x0, y_top, x1, y_bot)
            pm = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=clip)
            img = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
            img = img[:, :, :3]

            dets = []
            try:
                res, _ = ocr(img)
            except Exception as exc:  # noqa: BLE001
                res = None
                log(f"    OCR hatası pdf{row['pdf_page']} {row['side']}: {exc}")

            if res:
                for box, text, score in res:
                    ys = [pt[1] for pt in box]
                    xs = [pt[0] for pt in box]
                    dets.append(
                        {
                            "t": text,
                            "s": round(float(score), 3),
                            # şerit içinde 0..1 normalize konum
                            "yc": round((sum(ys) / len(ys)) / pm.height, 4),
                            "xc": round((sum(xs) / len(xs)) / pm.width, 4),
                            "h": round((max(ys) - min(ys)) / pm.height, 4),
                        }
                    )

            fh.write(
                json.dumps(
                    {
                        "pdf_page": row["pdf_page"],
                        "side": row["side"],
                        "band": [round(y_top, 2), round(y_bot, 2)],
                        "dets": dets,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            n_new += 1
            if n_new % 50 == 0:
                fh.flush()
                el = time.time() - t0
                log(f"    {i + 1}/{len(rows)} ({el:.0f}s, {n_new / el:.1f}/sn)")

    doc.close()
    log(f"    bitti: {n_new} yeni kayıt, {time.time() - t0:.0f}s")


def main() -> None:
    ocr = get_ocr()
    for book in BOOKS:
        print(f"--- {book.full_title}", flush=True)
        process_book(book, ocr, log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
