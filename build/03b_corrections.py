"""03b — Elle yapılmış OCR düzeltmelerini korpusa işler.

Sorun: hat, metni her çalıştırmada PDF'ten yeniden çıkarır. Elle düzeltilen bir
sayfa, bir sonraki `run_all.py` çağrısında sessizce eski hâline döner.

Çözüm: düzeltmeler `corrections/` altında ayrı ve kalıcı olarak durur; bu adım
onları `pages.jsonl` üzerine uygular. 04-08 arası adımların tamamı pages.jsonl'i
okuduğu için düz metin, TEI, RAG parçaları, site ve kavram dizini düzeltilmiş
metni kendiliğinden devralır.

Dosya düzeni:

    corrections/<slug>/<page_id>.txt    düzeltilmiş tam sayfa metni
    corrections/<slug>/manifest.json    hangi düzeltme hangi OCR üstüne yazıldı

`page_id` sayfanın kalıcı kimliğidir: basılı numaralı sayfalarda `p0042`,
numarasız sayfalarda tarama birimi (`u031r`). pages.jsonl'deki `page_id`
alanının son parçasıdır.

**Bayatlama denetimi.** Manifest, düzeltmenin hangi OCR metni üzerine yapıldığını
sha1 ile saklar. Hattın ilk adımları değişir de aynı sayfanın OCR çıktısı
başkalaşırsa, düzeltme artık başka bir metnin üstüne yazılıyor demektir. Bu
durumda düzeltme yine uygulanır ama `correction_stale` işaretlenir ve uyarı
basılır: sessizce yanlış metin üretmektense gürültü çıkarmak yeğdir.

    python build/03b_corrections.py            # uygula
    python build/03b_corrections.py --rapor     # yalnız durum bildir, yazma
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, ROOT, Book, read_jsonl, write_json, write_jsonl  # noqa: E402

CORR_DIR = ROOT / "corrections"


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def page_key(row: dict) -> str:
    """pages.jsonl kaydının düzeltme dosyası adı (page_id'nin son parçası)."""
    return row["page_id"].rsplit("-", 1)[-1]


def load_manifest(slug: str) -> dict:
    p = CORR_DIR / slug / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8")).get("pages", {})


def apply_book(book: Book, write: bool) -> dict:
    src = book.out_dir / "pages.jsonl"
    if not src.exists():
        return {"slug": book.slug, "error": "pages.jsonl yok — önce 01-03 çalıştırın"}

    rows = list(read_jsonl(src))
    manifest = load_manifest(book.slug)
    corr_dir = CORR_DIR / book.slug

    applied, reverted, stale, orphan = 0, 0, [], []
    seen: set[str] = set()

    for row in rows:
        key = page_key(row)
        f = corr_dir / f"{key}.txt"
        if not f.exists():
            # Düzeltme geri alınmışsa metin ham OCR'a döner ve işaretler silinir.
            if "text_ocr" in row:
                row["text"] = row.pop("text_ocr")
                row["n_chars"] = len(row["text"])
                row["is_empty"] = not row["text"].strip()
                reverted += 1
            row.pop("text_source", None)
            row.pop("corrected_at", None)
            row.pop("correction_stale", None)
            continue

        seen.add(key)
        corrected = f.read_text(encoding="utf-8").strip()
        if not corrected:
            orphan.append(f"{key} (boş dosya)")
            continue

        # Ham OCR metni kayıtta saklanır. Bu adım pages.jsonl'i yerinde
        # değiştirdiği için, aksi hâlde ikinci çalıştırmada karşılaştırılacak
        # "OCR metni" zaten düzeltilmiş metin olurdu ve her sayfa bayat görünürdü.
        if "text_ocr" not in row:
            row["text_ocr"] = row["text"]

        ocr_now = sha1(row["text_ocr"] or "")
        rec = manifest.get(key, {})
        is_stale = bool(rec.get("ocr_sha1")) and rec["ocr_sha1"] != ocr_now

        row["text"] = corrected
        row["n_chars"] = len(corrected)
        row["is_empty"] = not corrected
        row["text_source"] = "corrected"
        row["corrected_at"] = rec.get("updated", date.today().isoformat())
        if is_stale:
            row["correction_stale"] = True
            stale.append(key)
        else:
            row.pop("correction_stale", None)
        applied += 1

    # Karşılığı olmayan düzeltme dosyaları: yanlış adlandırma ya da silinmiş sayfa.
    if corr_dir.exists():
        for f in sorted(corr_dir.glob("*.txt")):
            if f.stem not in seen:
                orphan.append(f"{f.stem} (pages.jsonl'de karşılığı yok)")

    if write and (applied or reverted):
        write_jsonl(src, rows)

    return {
        "slug": book.slug,
        "pages": len(rows),
        "applied": applied,
        "reverted": reverted,
        "stale": stale,
        "orphan": orphan,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapor", action="store_true", help="Yalnız durumu bildir, dosya yazma")
    args = ap.parse_args()

    CORR_DIR.mkdir(exist_ok=True)
    total = 0
    for book in BOOKS:
        rep = apply_book(book, write=not args.rapor)
        if rep.get("error"):
            print(f"    {rep['slug']}: {rep['error']}")
            continue
        total += rep["applied"]
        print(f"    {rep['slug']}: {rep['applied']} düzeltilmiş sayfa uygulandı "
              f"({rep['pages']} sayfa içinde)")
        if rep["reverted"]:
            print(f"      {rep['reverted']} sayfa ham OCR'a döndürüldü "
                  f"(düzeltme dosyası silinmiş)")
        if rep["stale"]:
            print(f"      UYARI — altındaki OCR metni değişmiş: {', '.join(rep['stale'])}")
            print("      Düzeltmeyi taramayla yeniden karşılaştırın.")
        for o in rep["orphan"]:
            print(f"      UYARI — karşılıksız düzeltme dosyası: {o}")

    if total == 0:
        print("    Düzeltme yok — corrections/ boş. Hat OCR çıktısını olduğu gibi kullanıyor.")


if __name__ == "__main__":
    main()
