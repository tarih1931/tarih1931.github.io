"""20 — Yeni ve değişen adresleri IndexNow ile arama motorlarına bildirir.

    python build/20_indexnow.py            # ne bildirileceğini göster
    python build/20_indexnow.py --gonder   # bildir

IndexNow, Bing ve Yandex'in kabul ettiği bir bildirim protokolüdür: hesap,
doğrulama paneli ya da bekleme istemez. Bir anahtar dosyası sitede durur,
adresler tek bir POST ile bildirilir. Bing'e düşen içerik Copilot'a ve kısmen
başka arama tabanlı asistanlara da gider; Google IndexNow'ı kullanmaz, oranın
yolu Search Console'dur.

**Anahtar `dogrulama/` altındadır** ve site üretilirken `web/` köküne kopyalanır
(bkz. 06_web.py). Dosyanın adı anahtarın kendisidir, içeriği de aynı dizedir;
protokol bunu böyle ister. Anahtar dosyası siteden düşerse bildirimler sessizce
reddedilir.

Alt dizinde yayımlanan siteler için `keyLocation` şarttır: anahtar dosyası,
bildirilen adreslerin bulunduğu dizinde (ya da üstünde) durmalıdır. Bu depoda
site alan adının kökünde yayınlanır, anahtar da köke kopyalanır.

Bildirilen adres listesi dar tutulur: 954 sayfanın tamamını her seferinde
bildirmek protokolün kötüye kullanımıdır. Buradaki liste incelemenin ve
korpusun giriş noktalarıdır; geri kalanı site haritasından bulunur.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import META_DIR, ROOT  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
CHANNELS = META.get("channels", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"
UC_NOKTA = "https://api.indexnow.org/IndexNow"

# Bildirilecek giriş noktaları.
YOLLAR = [
    "/",
    "/inceleme.html",
    "/inceleme-kapsamli.html",
    "/review.html",
    "/inceleme.pdf",
    "/inceleme-kapsamli.pdf",
    "/review.pdf",
    "/inceleme-ekler.html",
    "/review-appendices.html",
    "/inceleme.md",
    "/inceleme-kapsamli.md",
    "/review.md",
    "/inceleme-ekler.md",
    "/review-appendices.md",
    "/duzeltilmis.html",
    "/veri.html",
    "/hakkinda.html",
    "/llms.txt",
    "/sitemap.xml",
]


def anahtar() -> tuple[str, str]:
    """(anahtar, anahtar dosyasının adresi). Dosya adı anahtarın kendisidir."""
    dg = ROOT / "dogrulama"
    adaylar = [p for p in sorted(dg.glob("*.txt")) if p.stem == p.read_text(encoding="utf-8").strip()]
    if not adaylar:
        raise SystemExit(
            "    IndexNow anahtarı yok.\n"
            "    dogrulama/<anahtar>.txt oluşturun; dosyanın içeriği de aynı dize olmalı."
        )
    p = adaylar[0]
    return p.stem, f"{BASE_URL}/{p.name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gonder", action="store_true", help="gerçekten bildir")
    args = ap.parse_args()

    k, konum = anahtar()
    adresler = [f"{BASE_URL}{y}" if y != "/" else f"{BASE_URL}/" for y in YOLLAR]
    print(f"    anahtar dosyası: {konum}")
    print(f"    {len(adresler)} adres bildirilecek:")
    for a in adresler:
        print(f"      {a}")
    if not args.gonder:
        print("\n    bildirmek için:  python build/20_indexnow.py --gonder")
        return

    govde = json.dumps({
        "host": BASE_URL.split("//", 1)[1].split("/", 1)[0],
        "key": k,
        "keyLocation": konum,
        "urlList": adresler,
    }).encode()
    r = urllib.request.Request(UC_NOKTA, data=govde, method="POST")
    r.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(r, timeout=60) as y:
            print(f"    HTTP {y.status} — bildirildi")
    except urllib.error.HTTPError as e:
        # 400/403/422: anahtar bulunamadı ya da adresler host ile uyuşmuyor.
        print(f"    HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")


if __name__ == "__main__":
    main()
