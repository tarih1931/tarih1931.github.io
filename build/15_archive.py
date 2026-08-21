"""15 — 1931 taramalarını Internet Archive'a yükler.

    python build/15_archive.py            # ne yapılacağını göster, yükleme yapma
    python build/15_archive.py --upload   # yükle
    python build/15_archive.py --kunye    # yalnız künyeyi tazele (dosya yüklenmez)
    python build/15_archive.py --inceleme # incelemeyi ayrı bir öğe olarak yükle

`--kunye`, yayımlanmış öğelerin künyesini yerinde günceller: 106 MB'lık PDF
yeniden gönderilmez. Kanal adresleri ya da açıklama değiştiğinde kullanılır.

Kimlik doğrulama bu betiğin işi değildir. Bir kez, kendi terminalinizde:

    ia configure

komutunu çalıştırıp archive.org e-posta ve parolanızı girersiniz; kimlik
`~/.config/internetarchive/ia.ini` dosyasında durur. Betik yalnız o oturumu
kullanır, parola veya anahtar tutmaz.

**Beyaz liste koruması.** `PDF/` klasöründe telifli modern kitaplar da vardır
(bkz. .gitignore ve docs/HAKLAR.md §4). Bu betik klasörü hiç taramaz: yalnız
metadata/books.json içindeki `source_pdf` alanlarında adı geçen dosyaları
yükler. Başka bir dosyaya erişmesi mümkün değildir. HuggingFace'te bir kez
bütün klasör yüklendiği için bu koruma bilinçlidir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import META_DIR, ROOT  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
RIGHTS = META["rights"]
SRC = META["source_repository"]
CHANNELS = META.get("channels", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"

# Kamu malı eser için doğru işaret CC0 değil, Public Domain Mark'tır: CC0 bir
# hak devri beyanıdır, oysa 1931 eseri koruma süresi dolduğu için zaten kamu
# malıdır. Türetilmiş veri kümesinin CC0 olduğu açıklamada belirtilir.
PD_MARK = "https://creativecommons.org/publicdomain/mark/1.0/"


def kimlik(book: dict) -> str:
    return f"{book['slug']}-ttk"


# İnceleme, korpustan ayrı bir çalışmadır ve kendi DOI'sini taşır; arşivde de
# ayrı bir öğe olarak durur. Aynı öğeye koymak, incelemeyi 106 MB'lık taramanın
# eki gibi gösterirdi ve arşivin tam metin araması onu ayrı bir eser saymazdı.
INCELEME_KIMLIK = "tarih-1931-islam-incelemesi"
INCELEME_PAKET = ROOT / "inceleme" / "yayin"
# Arşivdeki ad -> paketteki ad. İngilizce nüsha bilerek "review-" ile başlar:
# archive.org okuyucusu öğedeki PDF'leri **ada göre** sıralayıp ilkini açar
# (files.xml içindeki orig_sort), yükleme sırasına bakmaz. "inceleme-en.pdf"
# alfabetik olarak "inceleme-tr.pdf"ten önce geldiği için sayfa İngilizce
# açılıyordu. Adlar sitedeki inceleme.html / review.html düzeniyle de aynı.
INCELEME_DOSYALAR = {
    "inceleme-tr.pdf": "inceleme-tr.pdf",
    "inceleme-tr.md": "inceleme-tr.md",
    "review-en.pdf": "inceleme-en.pdf",
    "review-en.md": "inceleme-en.md",
    "bulgular.jsonl": "bulgular.jsonl",
}


def kunye(book: dict) -> dict:
    return {
        "mediatype": "texts",
        "title": book["title_full"],
        "creator": COLL["corporate_author"]["name_1931"],
        "publisher": f"{book['publisher']} — {book['printer']}",
        "date": str(book["year"]),
        "year": str(book["year"]),
        "language": "Turkish",
        "subject": COLL["subjects"] + COLL["subjects_lcsh"],
        "licenseurl": PD_MARK,
        "rights": "Kamu malı — koruma süresi dolmuştur (FSEK m.27).",
        "source": book["ttk_url"],
        # Açıklamadaki adres insan içindir; tarayıcı ve toplayıcı bunu okumaz.
        # external-identifier, öğeyi DOI'ye ve Wikidata öğesine makine
        # okuyabilecek biçimde bağlar.
        "external-identifier": [
            *([f"urn:doi:{COLL['doi']}"] if COLL.get("doi") else []),
            *([f"urn:wikidata:{book['wikidata']}"] if book.get("wikidata") else []),
        ],
        "description": (
            f"{COLL['description']} Bu öğe serinin {book['volume']}. cildidir "
            f"({book['title_full']}).\n\n"
            f"{book['approval']} {book['illustrations_statement']}.\n\n"
            f"Tarama: {SRC['name']}, yer no. {SRC['call_number']}.\n\n"
            f"Bu taramadan üretilmiş, sayfa sayfa alıntılanabilir makine-okunabilir "
            f"tam metin ve künyeler: {BASE_URL}\n"
            f"Veri kümesi DOI: https://doi.org/{COLL['doi']} (türetilmiş veri "
            f"{RIGHTS['derived_dataset_license']} ile kamuya bırakılmıştır).\n\n"
            f"Aynı metin başka yerlerde de durur — veri kümesi: "
            f"{CHANNELS.get('huggingface', '')}"
            + (f"\nVikikaynak (elle düzeltilmiş bölümlerin istinsahı): "
               f"{book['wikisource_work']}" if book.get("wikisource_work") else "")
            + (f"\nWikidata: https://www.wikidata.org/wiki/{book['wikidata']}"
               if book.get("wikidata") else "")
        ),
    }


def hedefler() -> list[tuple[dict, Path]]:
    """Yüklenecek dosyalar — yalnız books.json'da adı geçenler."""
    out = []
    for b in META["books"]:
        p = ROOT / b["source_pdf"]
        if not p.exists():
            print(f"    UYARI: {b['source_pdf']} yok, atlandı")
            continue
        out.append((b, p))
    return out


def oturum():
    try:
        import internetarchive as ia
    except ImportError:
        raise SystemExit("    internetarchive kurulu değil:  pip install internetarchive")
    s = ia.get_session()
    if not (s.config.get("s3") or {}).get("access"):
        raise SystemExit(
            "    archive.org oturumu yok.\n"
            "    Kendi terminalinizde bir kez:  ia configure"
        )
    return ia


def _inceleme_ozet() -> tuple[str, str]:
    """İncelemenin kendi özet paragrafları (TR + EN), bağlantı ve vurgularıyla.

    Açıklama burada elle yazılırsa belge değiştikçe sessizce eskiyor ve arşivdeki
    özet, kaydın kendi metniyle örtüşmüyor. Kaynak tektir: docs/inceleme.md.
    16_inceleme_yayin aynı paragrafı Zenodo künyesi ve PDF kapağı için de
    oradan çıkarır; o çıkarıcıyı yeniden yazmak yerine ödünç alıyoruz.
    """
    import importlib.util
    yol = Path(__file__).resolve().parent / "16_inceleme_yayin.py"
    spec = importlib.util.spec_from_file_location("y16", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.ozet_html(m.HAM_TR), m.ozet_html(m.HAM_EN)


def inceleme_kunyesi() -> dict:
    inc = META.get("review") or {}
    ozet_tr, ozet_en = _inceleme_ozet()
    return {
        "mediatype": "texts",
        "title": inc["title"],
        "creator": inc.get("author") or "Anonim",
        "date": "2026-08-16",
        "year": "2026",
        "language": ["Turkish", "English"],
        "licenseurl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "subject": [
            "Türk Tarih Tezi", "Din tarihi — Ders kitaplarında sunumu", "İslam itikadı",
            "Tarih — Ders kitapları — Türkiye", "Islam--Doctrines",
            "Education--Turkey--History--20th century",
        ],
        "external-identifier": [f"urn:doi:{inc['doi']}"] if inc.get("doi") else [],
        "description": (
            f"<p><strong>Özet:</strong> {ozet_tr}</p>"
            f"<p><strong>Abstract (English):</strong> {ozet_en}</p>"
            "<p>Türkçe aslı ve İngilizce sürümü birlikte verilmiştir (PDF + Markdown). "
            "Her alıntı basılı sayfa künyelidir ve kaynak metne karşı makine ile "
            "doğrulanmıştır; <code>bulgular.jsonl</code> iddiaları makine-okunabilir "
            "biçimde taşır.</p>"
            "<p>"
            f'DOI: <a href="https://doi.org/{inc.get("doi", "")}">https://doi.org/{inc.get("doi", "")}</a><br>'
            f'Çevrimiçi sürüm: <a href="{BASE_URL}/inceleme.html">{BASE_URL}/inceleme.html</a> &middot; <a href="{BASE_URL}/review.html">English</a></p>'
            "<p>İncelemenin dayandığı düzeltilmiş metin ve korpus: "
            f'<a href="https://doi.org/{COLL.get("doi", "")}">https://doi.org/{COLL.get("doi", "")}</a><br>'
            "Taranmış asıllar: "
            '<a href="https://archive.org/details/tarih-1-1931-ttk">Tarih I</a> ve '
            '<a href="https://archive.org/details/tarih-2-1931-ttk">Tarih II</a></p>'
        ),
    }


def inceleme_yukle(yalniz_kunye: bool = False) -> None:
    """İncelemeyi ayrı bir arşiv öğesi olarak yükler (yalnız beyaz listedeki dosyalar).

    `--kunye` ile birlikte verilirse dosya gönderilmez, yalnız künye tazelenir.
    """
    if yalniz_kunye:
        ia = oturum()
        item = ia.get_item(INCELEME_KIMLIK)
        if not item.exists:
            raise SystemExit(f"    {INCELEME_KIMLIK}: öğe yok")
        r = item.modify_metadata(inceleme_kunyesi())
        print(f"    {INCELEME_KIMLIK}: künye tazelendi (HTTP {getattr(r, 'status_code', r)})")
        return
    eksik = [y for y in INCELEME_DOSYALAR.values() if not (INCELEME_PAKET / y).exists()]
    if eksik:
        raise SystemExit(f"    yayın paketi eksik: {eksik}")
    ia = oturum()
    dosyalar = {ad: str(INCELEME_PAKET / y) for ad, y in INCELEME_DOSYALAR.items()}
    boyut = sum((INCELEME_PAKET / y).stat().st_size for y in INCELEME_DOSYALAR.values()) / 1048576
    print(f"    {INCELEME_KIMLIK} yükleniyor — {len(dosyalar)} dosya, {boyut:.1f} MB")
    r = ia.upload(INCELEME_KIMLIK, files=dosyalar, metadata=inceleme_kunyesi(),
                  retries=3, checksum=True, verbose=True)
    print(f"      HTTP {[x.status_code for x in r]}  ->  "
          f"https://archive.org/details/{INCELEME_KIMLIK}")


def kunye_tazele() -> None:
    """Yayımlanmış öğelerin künyesini yerinde günceller; dosya göndermez."""
    ia = oturum()
    for b in META["books"]:
        ident = kimlik(b)
        item = ia.get_item(ident)
        if not item.exists:
            print(f"    {ident}: öğe yok — atlandı")
            continue
        r = item.modify_metadata(kunye(b))
        kod = getattr(r, "status_code", r)
        print(f"    {ident}: HTTP {kod}  ->  https://archive.org/details/{ident}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true", help="gerçekten yükle")
    ap.add_argument("--kunye", action="store_true",
                    help="yalnız künyeyi tazele; dosya yüklenmez")
    ap.add_argument("--inceleme", action="store_true",
                    help="incelemeyi ayrı bir öğe olarak yükle")
    args = ap.parse_args()

    if args.inceleme:
        inceleme_yukle(yalniz_kunye=args.kunye)
        return

    if args.kunye:
        kunye_tazele()
        return

    isler = hedefler()
    for b, p in isler:
        mb = p.stat().st_size / 1048576
        print(f"    {kimlik(b):20} <- {b['source_pdf']}  ({mb:.0f} MB)")
        print(f"      başlık: {b['title_full']}")
    if not isler:
        raise SystemExit("    yüklenecek dosya yok")

    if not args.upload:
        print("\n    yüklemek için:  python build/15_archive.py --upload")
        return

    ia = oturum()
    for b, p in isler:
        ident = kimlik(b)
        print(f"\n    {ident} yükleniyor…")
        r = ia.upload(ident, files=[str(p)], metadata=kunye(b), retries=3, verbose=True)
        durum = [x.status_code for x in r]
        print(f"      HTTP {durum}  ->  https://archive.org/details/{ident}")


if __name__ == "__main__":
    main()
