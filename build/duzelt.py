"""OCR düzeltme arayüzü — taranmış sayfa solda, metin sağda.

    python build/duzelt.py                 # tarayıcıda http://localhost:8800
    python build/duzelt.py --port 9000
    python build/duzelt.py --bolum islam-tarihi

Yalnız yerelde çalışır ve yalnız localhost'a bağlanır; yayımlanan sitenin
parçası değildir. Kaydedilen metin `corrections/<slug>/<page_id>.txt` dosyasına
yazılır, `build/03b_corrections.py` onu korpusa işler.

Sayfa görüntüsü kaynak PDF'ten anlık üretilir (pages.jsonl'deki `clip`
koordinatıyla, açık kitap taramasından tek kitap sayfası kırpılarak). Görüntü
dosyaları diske yazılmaz; depoyu şişirmemesi için istek anında üretilir.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import threading
import webbrowser
from datetime import date
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS_BY_SLUG, ROOT, read_jsonl  # noqa: E402

CORR = ROOT / "corrections"
SECIM = ROOT / "secim"
IMG_WIDTH = 1600


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Çalışma listesi
# ---------------------------------------------------------------------------

def load_worklist(only: str | None) -> list[dict]:
    """secim/ altındaki bölümlerin gövde sayfalarını sırayla döndürür."""
    index = json.loads((SECIM / "index.json").read_text(encoding="utf-8"))
    items: list[dict] = []
    for sel in index["selections"]:
        if only and sel["slug"] != only:
            continue
        rows = [json.loads(l) for l in
                (SECIM / sel["slug"] / "sayfalar.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        for r in rows:
            if r["is_plate"]:
                continue          # levha: düzeltilecek gövde metni yok
            items.append({
                "bolum": sel["slug"],
                "bolum_adi": sel["heading"],
                "book": r["book"],
                "key": r["page_id"].rsplit("-", 1)[-1],
                "label": r["label"],
                "printed_page": r["printed_page"],
                "inferred_page": r["inferred_page"],
                "pdf_page": r["pdf_page"],
                "side": r["side"],
                "citation": r["citation"],
            })
    return items


@lru_cache(maxsize=8)
def page_rows(slug: str) -> dict:
    """pages.jsonl kayıtları, page_id son parçasına göre."""
    book = BOOKS_BY_SLUG[slug]
    return {r["page_id"].rsplit("-", 1)[-1]: r
            for r in read_jsonl(book.out_dir / "pages.jsonl")}


def ocr_text(slug: str, key: str) -> str:
    """Ham OCR metni. Düzeltme uygulanmışsa saklanan asıl metin döner."""
    row = page_rows(slug).get(key, {})
    return row.get("text_ocr", row.get("text", "")) or ""


def current_text(slug: str, key: str) -> tuple[str, bool]:
    f = CORR / slug / f"{key}.txt"
    if f.exists():
        return f.read_text(encoding="utf-8"), True
    return ocr_text(slug, key), False


# ---------------------------------------------------------------------------
# Görüntü
# ---------------------------------------------------------------------------

_docs: dict[str, pymupdf.Document] = {}
_lock = threading.Lock()


def render(slug: str, key: str) -> bytes:
    row = page_rows(slug).get(key)
    if not row:
        return b""
    with _lock:
        if slug not in _docs:
            _docs[slug] = pymupdf.open(BOOKS_BY_SLUG[slug].pdf_path)
        doc = _docs[slug]
        page = doc[row["pdf_page"]]
        clip = pymupdf.Rect(*row["clip"])
        zoom = IMG_WIDTH / max(clip.width, 1)
        pm = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        return pm.tobytes("jpeg", jpg_quality=85)


# ---------------------------------------------------------------------------
# Kaydetme
# ---------------------------------------------------------------------------

def save(slug: str, key: str, text: str) -> dict:
    d = CORR / slug
    d.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n").strip() + "\n"
    (d / f"{key}.txt").write_text(text, encoding="utf-8", newline="\n")

    mpath = d / "manifest.json"
    man = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    man.setdefault("$comment",
                   "Düzeltmelerin hangi OCR metni üzerine yapıldığını saklar. "
                   "build/03b_corrections.py bayatlamayı buradan denetler.")
    man.setdefault("pages", {})
    man["pages"][key] = {
        "ocr_sha1": sha1(ocr_text(slug, key)),
        "corrected_sha1": sha1(text.strip()),
        "updated": date.today().isoformat(),
    }
    mpath.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
    return {"ok": True, "key": key}


def revert(slug: str, key: str) -> dict:
    f = CORR / slug / f"{key}.txt"
    if f.exists():
        f.unlink()
    mpath = CORR / slug / "manifest.json"
    if mpath.exists():
        man = json.loads(mpath.read_text(encoding="utf-8"))
        man.get("pages", {}).pop(key, None)
        mpath.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8", newline="\n")
    return {"ok": True, "key": key, "reverted": True}


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """
*{box-sizing:border-box} html,body{margin:0;height:100%}
body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;background:#14130f;color:#ece7dd;
     display:flex;flex-direction:column}
header{display:flex;gap:14px;align-items:center;padding:8px 14px;background:#1e1c15;
       border-bottom:1px solid #332f26;flex-wrap:wrap}
header b{font-size:15px} .sp{flex:1}
a,button{font:inherit;color:#ece7dd;background:#2b2820;border:1px solid #443f33;
         border-radius:6px;padding:5px 11px;text-decoration:none;cursor:pointer}
button.primary{background:#7a4a2b;border-color:#96603c}
button:disabled{opacity:.45;cursor:default}
.durum{font-size:13px;color:#a49c90;min-width:15ch}
.durum.ok{color:#8fbf7a} .durum.bekliyor{color:#d6a77a}
main{flex:1;display:flex;min-height:0}
.sol{flex:1;overflow:auto;background:#0d0c09;display:flex;justify-content:center;align-items:flex-start}
.sol img{max-width:100%;height:auto;display:block}
.sag{flex:1;display:flex;flex-direction:column;border-left:1px solid #332f26;min-width:0}
textarea{flex:1;width:100%;resize:none;border:0;outline:0;padding:16px 18px;
         background:#16150f;color:#ece7dd;font:15px/1.75 'Cascadia Mono',Consolas,monospace;
         white-space:pre-wrap}
.alt{padding:6px 14px;background:#1e1c15;border-top:1px solid #332f26;font-size:12.5px;color:#a49c90;
     display:flex;gap:16px;flex-wrap:wrap}
.liste{padding:18px 22px;overflow:auto}
.liste h2{font-size:16px;margin:22px 0 10px}
.liste a{display:inline-block;margin:2px;padding:5px 9px;min-width:56px;text-align:center}
.liste a.done{background:#274420;border-color:#3c6631}
.zoom{display:flex;gap:6px;align-items:center}
kbd{background:#2b2820;border:1px solid #443f33;border-radius:4px;padding:1px 5px;font-size:11.5px}
"""


def page_html(items: list[dict], i: int) -> str:
    it = items[i]
    text, corrected = current_text(it["book"], it["key"])
    prev_i, next_i = (i - 1 if i > 0 else None), (i + 1 if i + 1 < len(items) else None)
    num = it["printed_page"] or it["inferred_page"]
    baslik = f"s. {num}" + ("" if it["printed_page"] else " (çıkarım)")

    nav = ""
    if prev_i is not None:
        nav += f'<a href="/s/{prev_i}">← önceki</a>'
    if next_i is not None:
        nav += f'<a href="/s/{next_i}">sonraki →</a>'

    return f"""<!doctype html><html lang="tr"><meta charset="utf-8">
<title>{html.escape(baslik)} — {html.escape(it['bolum_adi'])}</title>
<style>{CSS}</style>
<header>
  <a href="/">☰ liste</a>
  <b>{html.escape(it['bolum_adi'])} · {html.escape(baslik)}</b>
  <span class="durum {'ok' if corrected else ''}" id="durum">{'düzeltilmiş' if corrected else 'ham OCR'}</span>
  <span class="sp"></span>
  <span class="zoom"><button onclick="zoom(-1)">−</button><button onclick="zoom(1)">+</button></span>
  {nav}
  <button class="primary" id="kaydet" onclick="kaydet()">Kaydet <kbd>Ctrl+S</kbd></button>
  <button onclick="geriAl()" {'' if corrected else 'disabled'}>Düzeltmeyi sil</button>
</header>
<main>
  <div class="sol" id="sol"><img id="im" src="/gorsel/{it['book']}/{it['key']}.jpg" alt="tarama"></div>
  <div class="sag">
    <textarea id="t" spellcheck="false">{html.escape(text)}</textarea>
    <div class="alt">
      <span>{html.escape(it['citation'])}</span>
      <span>PDF s. {it['pdf_page'] + 1} · {it['side']}</span>
      <span>{i + 1}/{len(items)}</span>
      <span id="sayac"></span>
    </div>
  </div>
</main>
<script>
const K = {json.dumps({"book": it["book"], "key": it["key"]})};
const t = document.getElementById('t'), durum = document.getElementById('durum');
let kirli = false, z = 1;

t.addEventListener('input', () => {{ kirli = true; durum.textContent = 'kaydedilmedi';
  durum.className = 'durum bekliyor'; say(); }});
function say() {{ document.getElementById('sayac').textContent = t.value.length + ' karakter'; }}
say();

function zoom(d) {{ z = Math.max(.4, Math.min(3, z + d * .2));
  document.getElementById('im').style.width = (z * 100) + '%'; }}

async function kaydet() {{
  const r = await fetch('/kaydet', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ ...K, text: t.value }}) }});
  if (r.ok) {{ kirli = false; durum.textContent = 'kaydedildi'; durum.className = 'durum ok'; }}
  else {{ durum.textContent = 'HATA'; durum.className = 'durum bekliyor'; }}
}}

async function geriAl() {{
  if (!confirm('Bu sayfanın düzeltmesi silinsin ve ham OCR metnine dönülsün mü?')) return;
  await fetch('/geri-al', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify(K) }});
  location.reload();
}}

document.addEventListener('keydown', e => {{
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {{ e.preventDefault(); kaydet(); }}
  if (e.altKey && e.key === 'ArrowRight') {{ const a = document.querySelector('a[href="/s/{next_i}"]'); if (a) a.click(); }}
  if (e.altKey && e.key === 'ArrowLeft') {{ const a = document.querySelector('a[href="/s/{prev_i}"]'); if (a) a.click(); }}
}});
window.addEventListener('beforeunload', e => {{ if (kirli) {{ e.preventDefault(); e.returnValue = ''; }} }});
</script></html>"""


def list_html(items: list[dict]) -> str:
    groups: dict[str, list[tuple[int, dict]]] = {}
    for i, it in enumerate(items):
        groups.setdefault(it["bolum_adi"], []).append((i, it))

    body = ['<div class="liste"><h1>OCR düzeltme</h1>',
            '<p>Taranmış sayfa solda, metin sağda. <kbd>Ctrl+S</kbd> kaydeder, '
            '<kbd>Alt</kbd>+<kbd>←</kbd>/<kbd>→</kbd> sayfa değiştirir. '
            'Yeşil kutular düzeltilmiş sayfalardır.</p>']
    for adi, lst in groups.items():
        done = sum(1 for _, it in lst if (CORR / it["book"] / f"{it['key']}.txt").exists())
        body.append(f"<h2>{html.escape(adi)} — {done}/{len(lst)} düzeltildi</h2><div>")
        for i, it in lst:
            num = it["printed_page"] or it["inferred_page"]
            cls = "done" if (CORR / it["book"] / f"{it['key']}.txt").exists() else ""
            body.append(f'<a class="{cls}" href="/s/{i}">{num}</a>')
        body.append("</div>")
    body.append("</div>")
    return (f'<!doctype html><html lang="tr"><meta charset="utf-8"><title>OCR düzeltme</title>'
            f"<style>{CSS}</style>" + "".join(body) + "</html>")


# ---------------------------------------------------------------------------
# Sunucu
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    items: list[dict] = []

    def log_message(self, *a):  # sessiz
        pass

    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, "text/html; charset=utf-8",
                              list_html(self.items).encode("utf-8"))
        if path.startswith("/s/"):
            try:
                i = int(path[3:])
                it = self.items[i]
            except (ValueError, IndexError):
                return self._send(404, "text/plain; charset=utf-8", b"sayfa yok")
            return self._send(200, "text/html; charset=utf-8",
                              page_html(self.items, i).encode("utf-8"))
        if path.startswith("/gorsel/"):
            parts = path[len("/gorsel/"):].split("/")
            if len(parts) == 2:
                img = render(parts[0], parts[1].removesuffix(".jpg"))
                if img:
                    return self._send(200, "image/jpeg", img)
            return self._send(404, "text/plain; charset=utf-8", b"gorsel yok")
        self._send(404, "text/plain; charset=utf-8", b"yok")

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) or b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            # Gövde UTF-8 JSON değil. Bağlantıyı düşürmek yerine söyleyip geç.
            return self._send(400, "application/json",
                              json.dumps({"ok": False, "hata": str(e)}).encode("utf-8"))
        slug, key = data.get("book"), data.get("key")
        if slug not in BOOKS_BY_SLUG or not key:
            return self._send(400, "application/json", b'{"ok":false}')
        if path == "/kaydet":
            res = save(slug, key, data.get("text", ""))
        elif path == "/geri-al":
            res = revert(slug, key)
        else:
            return self._send(404, "application/json", b'{"ok":false}')
        self._send(200, "application/json", json.dumps(res).encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--bolum", default=None, help="yalnız bu bölüm (secim/ slug'ı)")
    ap.add_argument("--tarayici-acma", action="store_true")
    args = ap.parse_args()

    if not (SECIM / "index.json").exists():
        sys.exit("secim/index.json yok — önce: python build/10_secim.py")

    items = load_worklist(args.bolum)
    if not items:
        sys.exit("Düzeltilecek sayfa bulunamadı.")
    Handler.items = items

    url = f"http://localhost:{args.port}/"
    print(f"  {len(items)} sayfa hazır — {url}")
    print("  Kapatmak için Ctrl+C")
    if not args.tarayici_acma:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  kapatıldı")


if __name__ == "__main__":
    main()
