"""Tarih Ders Kitapları (1931) — salt-okunur REST API.

Yalnız Python standart kütüphanesini kullanır; ek bağımlılık gerektirmez.

    python api/server.py --port 8000

Uç noktalar için: http://localhost:8000/openapi.yaml  ve  /  (kısa yardım)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
META = json.loads((ROOT / "metadata" / "books.json").read_text(encoding="utf-8"))
BOOKMETA = {b["slug"]: b for b in META["books"]}

FOLD = str.maketrans("âÂîÎûÛİIıÜüÖöÇçŞşĞğ", "aaiiuuiiiuuooccssgg")


def fold(s: str) -> str:
    return s.translate(FOLD).lower()


@lru_cache(maxsize=1)
def load_pages() -> list[dict]:
    rows: list[dict] = []
    for slug in BOOKMETA:
        p = DATA / slug / "pages.jsonl"
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    r["_folded"] = fold(r.get("text", ""))
                    rows.append(r)
    return rows


@lru_cache(maxsize=1)
def load_concordance() -> list[dict]:
    p = ROOT / "thematic" / "din-konkordans.jsonl"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def public(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------


def h_books(_q) -> dict:
    out = []
    for slug, bm in BOOKMETA.items():
        pages = [r for r in load_pages() if r["book"] == slug]
        nums = [r["printed_page"] for r in pages if r.get("printed_page")]
        out.append(
            {
                "slug": slug,
                "title": bm["title_full"],
                "year": bm["year"],
                "publisher": bm["publisher"],
                "place": bm["place"],
                "approval": bm["approval"],
                "source_scan": bm["ttk_url"],
                "physical_pages": len(pages),
                "printed_page_range": [min(nums), max(nums)] if nums else None,
            }
        )
    return {"collection": META["collection"]["name"], "books": out}


def h_book(slug: str) -> dict:
    if slug not in BOOKMETA:
        raise KeyError(slug)
    structure = DATA / slug / "structure.json"
    return {
        "book": BOOKMETA[slug],
        "structure": json.loads(structure.read_text(encoding="utf-8"))["sections"]
        if structure.exists()
        else [],
    }


def h_page(slug: str, n: int) -> dict:
    for r in load_pages():
        if r["book"] == slug and r.get("printed_page") == n:
            return public(r)
    raise KeyError(f"{slug}/{n}")


def h_search(q: dict) -> dict:
    term = (q.get("q", [""])[0] or "").strip()
    if not term:
        return {"error": "q parametresi gerekli"}
    book = q.get("book", [None])[0]
    limit = min(int(q.get("limit", ["25"])[0]), 200)
    ft = fold(term)
    results = []
    for r in load_pages():
        if book and r["book"] != book:
            continue
        idx = r["_folded"].find(ft)
        if idx < 0:
            continue
        start = max(0, idx - 160)
        results.append(
            {
                "book": r["book"],
                "printed_page": r.get("printed_page"),
                "page_id": r["page_id"],
                "citation": r["citation"],
                "running_head": r.get("running_head"),
                "page_confidence": r.get("page_confidence"),
                "snippet": "…" + " ".join(r["text"][start : idx + 260].split()) + "…",
                "n_occurrences": r["_folded"].count(ft),
            }
        )
        if len(results) >= limit:
            break
    return {"query": term, "count": len(results), "results": results}


def h_concordance(q: dict) -> dict:
    theme = q.get("theme", [None])[0]
    book = q.get("book", [None])[0]
    limit = min(int(q.get("limit", ["50"])[0]), 500)
    rows = load_concordance()
    if theme:
        rows = [r for r in rows if r["theme"] == theme]
    if book:
        rows = [r for r in rows if r["book"] == book]
    themes = sorted({r["theme"] for r in load_concordance()})
    return {"themes": themes, "count": len(rows), "results": rows[:limit]}


ROUTES = [
    (re.compile(r"^/books/?$"), lambda m, q: h_books(q)),
    (re.compile(r"^/books/([\w-]+)/?$"), lambda m, q: h_book(m.group(1))),
    (re.compile(r"^/books/([\w-]+)/pages/(\d+)/?$"), lambda m, q: h_page(m.group(1), int(m.group(2)))),
    (re.compile(r"^/search/?$"), lambda m, q: h_search(q)),
    (re.compile(r"^/concordance/?$"), lambda m, q: h_concordance(q)),
]

HELP = {
    "name": "Tarih Ders Kitapları (1931) API",
    "description": "Türk Tarihi Tetkik Cemiyeti tarafından hazırlanan resmî lise tarih ders "
    "kitaplarının sayfa sayfa alıntılanabilir tam metni.",
    "endpoints": {
        "GET /books": "Ciltlerin listesi",
        "GET /books/{slug}": "Cilt künyesi ve bölüm haritası",
        "GET /books/{slug}/pages/{n}": "Basılı sayfa numarasına göre tam sayfa metni",
        "GET /search?q=...&book=...&limit=": "Tam metin arama (Türkçe aksan duyarsız)",
        "GET /concordance?theme=...&book=...": "Din/inanç kavram dizini",
    },
    "note": "Metinler düzeltilmemiş OCR çıktısıdır; her yanıt tarama referansı içerir.",
    "license": META["rights"]["derived_dataset_license"],
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, obj, code=200) -> None:
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/help"):
            return self._send(HELP)
        if u.path == "/openapi.yaml":
            spec = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/yaml; charset=utf-8")
            self.send_header("Content-Length", str(len(spec)))
            self.end_headers()
            return self.wfile.write(spec)
        for pat, fn in ROUTES:
            m = pat.match(u.path)
            if m:
                try:
                    return self._send(fn(m, q))
                except KeyError as e:
                    return self._send({"error": "bulunamadı", "detail": str(e)}, 404)
                except Exception as e:  # noqa: BLE001
                    return self._send({"error": "sunucu hatası", "detail": str(e)}, 500)
        self._send({"error": "bilinmeyen uç nokta", "see": "/"}, 404)

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    n = len(load_pages())
    print(f"{n} sayfa yüklendi. http://{a.host}:{a.port}/ adresinde dinleniyor…")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
