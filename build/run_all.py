"""Tüm işleme hattını sırayla çalıştırır.

    python build/run_all.py            # baştan sona
    python build/run_all.py --skip-ocr # başlık OCR'ını atla (uzun sürer)

Adımlar birbirine bağımlıdır; sıra değiştirilmemelidir.
"""
from __future__ import annotations

import argparse
import runpy
import sys
import time
from pathlib import Path

BUILD = Path(__file__).resolve().parent

STEPS = [
    ("01_extract.py", "Çift sayfa taramalarını tek tek kitap sayfalarına ayır"),
    ("02_headers.py", "Sayfa numaralarını ve bölüm başlıklarını yeniden OCR et"),
    ("03_paginate.py", "Basılı sayfa numaralarını çöz ve doğrula"),
    ("03b_corrections.py", "Elle yapılmış OCR düzeltmelerini uygula"),
    ("04_emit.py", "Metin, JSONL, TEI-XML ve RAG parçalarını üret"),
    ("05_metadata.py", "Tüm metadata şemalarını üret"),
    ("06_web.py", "AI-taranabilir statik siteyi üret"),
    ("06b_inceleme.py", "İnceleme iddialarını kayda dök ve alıntıları doğrula"),
    ("07_thematic.py", "Din/inanç kavram dizinini üret"),
    ("08_verify.py", "Kalite ve tutarlılık raporunu üret"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-ocr", action="store_true", help="02_headers.py adımını atla")
    ap.add_argument("--from", dest="start", default="", help="Bu adımdan itibaren çalıştır")
    args = ap.parse_args()

    started = not args.start
    for script, desc in STEPS:
        if not started:
            if script.startswith(args.start):
                started = True
            else:
                continue
        if args.skip_ocr and script == "02_headers.py":
            print(f"\n=== {script} — ATLANDI ===")
            continue
        print(f"\n=== {script} — {desc} ===", flush=True)
        t0 = time.time()
        sys.argv = [script]
        runpy.run_path(str(BUILD / script), run_name="__main__")
        print(f"    ({time.time() - t0:.0f}s)")

    print("\nHat tamamlandı.")


if __name__ == "__main__":
    main()
