"""13 — HuggingFace'e yüklenecek klasörü hazırlar (ve isteğe bağlı yükler).

    python build/13_huggingface.py            # yalnız klasörü hazırla
    python build/13_huggingface.py --upload   # hazırla ve HuggingFace'e yükle

Veri depoda ikinci kez tutulmaz: bu adım klasörü hattın mevcut çıktılarından
toplar.

**Klasör depo ağacının DIŞINA üretilir** (`<depo>/../<depo adı>-hf`). Sebebi
somut bir kazadır: klasör depo kökünde üretildiğinde, yükleme sırasında bütün
çalışma dizinini göndermek çok kolay oluyor ve o ağaçta `PDF/` altındaki
telifli modern kitaplar da bulunuyor (bkz. .gitignore ve docs/HAKLAR.md §4).
Ayrı bir dizinde telifli dosyalar fizikî olarak erişilemez; yanlışlıkla
"hepsini yükle" demek zararsız hâle gelir.

Ek olarak her üretimden sonra `dogrula()` çalışır: klasörde beklenenden başka
dosya varsa betik hata verir ve yükleme yapılmaz.

Düzen bilinçlidir: doğrulanmış alt korpus ve incelemenin bulguları, ham OCR'dan
**ayrı config** olarak durur. Aksi hâlde 954 sayfalık düzeltilmemiş metin ile
129 sayfalık elle doğrulanmış metin tek havuzda karışır ve ikincisinin değeri
görünmez olur.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, META_DIR, ROOT, write_text  # noqa: E402

OUT = ROOT.parent / f"{ROOT.name}-hf"
REPO_ID = "asayimusa19/tarih-ders-kitaplari-1931"
META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
RIGHTS = META["rights"]
BOOKMETA = {b["slug"]: b for b in META["books"]}
CHANNELS = META.get("channels", {})
REVIEW = META.get("review", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"


def selections() -> list[dict]:
    p = ROOT / "secim" / "index.json"
    return json.loads(p.read_text(encoding="utf-8")).get("selections", []) if p.exists() else []


def card() -> str:
    sels = selections()
    n_corr = sum(s.get("pages_body", 0) for s in sels)
    cfg = ["configs:"]

    cfg.append("  - config_name: sayfalar")
    cfg.append("    description: Tüm korpus, sayfa düzeyinde. Düzeltilmemiş OCR.")
    cfg.append("    data_files:")
    for b in BOOKS:
        cfg.append(f"      - split: {b.slug.replace('-', '_')}")
        cfg.append(f"        path: sayfalar/{b.slug}.jsonl")

    if sels:
        cfg.append("  - config_name: dogrulanmis")
        cfg.append("    description: Taranmış aslıyla karşılaştırılarak elle düzeltilmiş sayfalar.")
        cfg.append("    data_files:")
        for s in sels:
            cfg.append(f"      - split: {s['slug'].replace('-', '_')}")
            cfg.append(f"        path: dogrulanmis/{s['slug']}.jsonl")

    cfg.append("  - config_name: parcalar")
    cfg.append("    description: RAG parçaları; her parça sayfa aralığı künyeli.")
    cfg.append("    data_files:")
    for b in BOOKS:
        cfg.append(f"      - split: {b.slug.replace('-', '_')}")
        cfg.append(f"        path: parcalar/{b.slug}.jsonl")

    if (ROOT / "inceleme" / "bulgular.jsonl").exists():
        cfg.append("  - config_name: inceleme")
        cfg.append("    description: İncelemenin iddiaları; her kayıt kaynak sayfaya bağlı.")
        cfg.append("    data_files:")
        cfg.append("      - split: bulgular")
        cfg.append("        path: inceleme/bulgular.jsonl")

    if INCELEME_TR.exists():
        cfg.append("  - config_name: inceleme-metin")
        cfg.append("    description: İncelemenin tam metni, bölüm bölüm (Türkçe ve İngilizce).")
        cfg.append("    data_files:")
        for dil in ("tr", "en"):
            cfg.append(f"      - split: {dil}")
            cfg.append(f"        path: inceleme/metin-{dil}.jsonl")

    yaml = [
        "---",
        "license: cc0-1.0",
        "language:",
        "  - tr",
        f"pretty_name: {COLL['name']} — makine-okunabilir tam metin",
        "task_categories:",
        "  - text-generation",
        "  - text-retrieval",
        "tags:",
        "  - history",
        "  - turkish",
        "  - ocr",
        "  - public-domain",
        "  - textbooks",
        '  - "1931"',  # tırnaksız yazılırsa YAML sayı olarak ayrıştırır, HF reddeder
        "size_categories:",
        "  - 1K<n<10K",
        *cfg,
        "---",
        "",
    ]

    md = [
        f"# {COLL['name']} — makine-okunabilir tam metin",
        "",
        COLL["description"],
        "",
        "Her basılı sayfa ayrı bir kayıttır: kalıcı kimliği, hazır künyesi ve kaynak",
        "taramadaki tam konumu vardır. Bir iddia basılı sayfaya kadar izlenebilir.",
        "",
        "## Config'ler",
        "",
        "| Config | Ne | Metin kalitesi |",
        "|---|---|---|",
        "| `sayfalar` | İki cildin tamamı, sayfa düzeyinde | **Düzeltilmemiş OCR** |",
        f"| `dogrulanmis` | İki bölüm, {n_corr} sayfa | **Elle düzeltilmiş** — taramayla karşılaştırılmış |",
        "| `parcalar` | RAG parçaları, sayfa aralığı künyeli | Düzeltilmemiş OCR |",
        "| `inceleme` | Metne dayalı incelemenin iddiaları | — |",
        "| `inceleme-metin` | Aynı incelemenin tam metni ve ekleri, bölüm bölüm (TR + EN) | — |",
        "",
        "> Alıntı yapacaksanız `dogrulanmis` config'ini tercih ediniz. Korpusun geri",
        "> kalanı 150 DPI taramadan çıkarılmış, elle düzeltilmemiş OCR çıktısıdır;",
        "> 1931 imlası ve Osmanlı Türkçesi kelime dağarcığı hata oranını yükseltir.",
        "",
        "## Kitaplar",
        "",
    ]
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        md += [
            f"**{bm['title_full']}** — {bm['place']}, {bm['year']}. {bm['publisher']}.",
            f"{bm['approval']}",
            f"Kaynak tarama: {bm['ttk_url']}",
            "",
        ]

    if sels:
        md += ["## Doğrulanmış bölümler", ""]
        for s in sels:
            lo, hi = s["printed_range"]
            md.append(
                f"- **{s['heading']}** — {s['book_title'].split(':')[0]}, basılı s. {lo}-{hi}, "
                f"{s.get('pages_body', 0)} sayfa, {s.get('words', 0)} kelime"
            )
        md += [
            "",
            "Ham OCR metni bu kayıtlarda `text_ocr` alanında saklanır; her düzeltme",
            "denetlenebilir. Düzeltilmiş kayıtlar `text_source=corrected` ile işaretlidir.",
            "",
        ]

    # Kartta incelemenin yalnız config'leri anlatılıyordu; metnin okunabilir
    # sürümüne hiçbir yerden bağlantı yoktu. Veri kümesi kartı çoğu okuyucunun
    # bu çalışmayı gördüğü tek yerdir: iddiaları JSONL olarak indirmeden önce
    # incelemenin kendisini okuyabilmesi gerekir.
    md += [
        "## İnceleme",
        "",
        "İncelemenin okunabilir tam metni sitede durur; aşağıdaki config'ler onun",
        "makine-okunabilir parçalarıdır.",
        "",
        f"- Türkçe: {BASE_URL}/inceleme.html",
    ]
    if INCELEME_EN.exists():
        md.append(f"- İngilizce: {BASE_URL}/review.html")
    md += [
        "",
        "`inceleme` config'i, yukarıdaki bölümler üzerine yapılmış karşılaştırmalı bir",
        "incelemenin iddialarını taşır. Her kayıt birebir alıntıyı, basılı sayfayı, güç",
        "derecesini (kesin/güçlü/orta/zayıf) ve kaynak sayfanın adresini içerir;",
        "`verified` alanı alıntının o sayfada birebir bulunduğunun makine ile",
        "denetlendiğini gösterir.",
        "",
        "`inceleme-metin` config'i aynı çalışmanın **tam metnini ve eklerini** taşır:",
        "bölüm başlığı, gövde metni, dil, DOI, hangi belgeden geldiği (`belge`: ana",
        "metin / ekler) ve kaynak sayfanın adresi. İddialar tek",
        "başına okunduğunda gerekçe ve yöntem görünmez; bu config o eksiği kapatır.",
        "Ekler (Ek A ayet dosyaları, Ek B terim dosyaları, Ek C ön söz ve heyet",
        "sayfaları, Ek D hükümlerin dayanak tipi) ana metnin bölümlerinden sonra",
        "gelir ve kendi kaynak adresini taşır.",
        "",
        "Kayıt tipleri: `quotation` (Alıntı-01…, kitaptan birebir aktarılan pasaj —",
        "doğrulanan budur), `verse` (Ayet-01…, bulgunun dayandığı ayet), `finding`",
        "(Bulgu-01…, alıntı ile ayetin birlikte değerlendirilmesinden çıkan kanaat;",
        "dayandığı alıntı ve ayetler kayıtlıdır), `claim` (Öz-01…, kitabın sarih",
        "lafzını özetleyen maddeler).",
        "",
        "## Haklar",
        "",
        f"- Kaynak eser kamu malıdır ({RIGHTS['statement_uri']}).",
        f"- Türetilmiş veri ve kod: **{RIGHTS['derived_dataset_license']}**.",
        f"- Taramalar: {META['source_repository']['name']}, yer no. "
        f"`{META['source_repository']['call_number']}`.",
        "",
        "## Atıf",
        "",
    ]
    if COLL.get("doi"):
        md += [
            f"> {COLL['corporate_author']['name_1931']} "
            f"({BOOKMETA[BOOKS[0].slug]['year']}). {COLL['name']} — makine-okunabilir "
            f"tam metin. Zenodo. https://doi.org/{COLL['doi']}",
            "",
            "DOI bütün sürümleri temsil eder ve daima en sonuncusuna çözümlenir.",
            "",
        ]
    if REVIEW.get("doi"):
        md += [
            "`inceleme` config'indeki çalışma ayrı bir yayındır ve kendi DOI'sini "
            f"taşır: https://doi.org/{REVIEW['doi']}",
            "",
        ]

    # Aynı korpusun durduğu diğer yerler. Veri kümesi kartı çoğu okuyucunun bu
    # projeyi gördüğü tek yerdir; kanalları saymazsa okuyucu ne taramaya, ne
    # arşiv nüshasına, ne de istinsaha ulaşabilir.
    md += ["## Yayın kanalları", "", f"- Site: {BASE_URL}"]
    if CHANNELS.get("repository"):
        md.append(f"- Depo (işleme hattı ve düzeltmeler): {CHANNELS['repository']}")
    if COLL.get("doi"):
        md.append(f"- Zenodo arşivi: https://doi.org/{COLL['doi']}")
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("internet_archive"):
            md.append(f"- Internet Archive — {bm['title']} {bm['volume']} taraması: "
                      f"{bm['internet_archive']}")
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("wikisource_work"):
            md.append(f"- Vikikaynak — {bm['title']} {bm['volume']} istinsahı: "
                      f"{bm['wikisource_work']}")
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        if bm.get("wikidata"):
            md.append(f"- Wikidata — {bm['title']} {bm['volume']}: "
                      f"https://www.wikidata.org/wiki/{bm['wikidata']}")
    if REVIEW.get("internet_archive"):
        md.append(f"- Internet Archive — inceleme: {REVIEW['internet_archive']}")
    if REVIEW.get("wikidata"):
        md.append(f"- Wikidata — inceleme: https://www.wikidata.org/wiki/{REVIEW['wikidata']}")
    md.append("")
    return "\n".join(yaml + md)


INCELEME_TR = ROOT / "docs" / "inceleme.md"
INCELEME_EN = ROOT / "docs" / "REVIEW-EN.md"
# Ekler ana metnin ardından aynı akışa girer: aynı çalışmanın parçasıdır,
# aynı DOI'yi taşır, yalnız kaynak adresi ayrıdır.
INCELEME_EK_TR = ROOT / "docs" / "inceleme-ekler.md"
INCELEME_EK_EN = ROOT / "docs" / "REVIEW-APPENDICES-EN.md"
# (dosya, site sayfası, ilk "## " başlığından önceki kısmın adı)
BELGELER = {
    "tr": ((INCELEME_TR, "inceleme.html", "Özet, kapsam ve yöntem"),
           (INCELEME_EK_TR, "inceleme-ekler.html", "Eklerin özeti")),
    "en": ((INCELEME_EN, "review.html", "Abstract, scope and method"),
           (INCELEME_EK_EN, "review-appendices.html", "Abstract of the appendices")),
}


def metin_kayitlari(yol: Path, dil: str, sayfa: str, onsoz: str, sira0: int = 0) -> list[dict]:
    """İnceleme metnini bölüm bölüm kayda çevirir.

    Bulgular (`bulgular.jsonl`) incelemenin iddialarını taşır ama metnin
    kendisini taşımaz; gerekçe, yöntem ve tartışma orada yoktur. Bir model
    yalnız iddiaları okuduğunda çalışmayı değil, çıktısını görür. Bu yüzden
    tam metin de veri kümesine girer — bölüm bölüm, çünkü tek parça bir
    belge çoğu eğitim ve erişim hattında kesilir.
    """
    if not yol.exists():
        return []
    inc = META.get("review") or {}
    url = f"{BASE_URL}/{sayfa}"
    # İlk "## " başlığından önceki kısım özet, kapsam ve yöntemdir; başlıksız
    # kalırsa kayıt adsız görünür.
    kayitlar, baslik, govde, sira = [], onsoz, [], sira0

    def ekle() -> None:
        nonlocal sira
        metin = "\n".join(govde).strip()
        if not metin:
            return
        sira += 1
        kayitlar.append({
            "dil": dil,
            "bolum_sira": sira,
            "bolum": baslik,
            "metin": metin,
            "eser": inc.get("title") if dil == "tr" else inc.get("title_en"),
            "belge": "ekler" if "ekler" in sayfa or "appendices" in sayfa else "ana metin",
            "yazar": inc.get("author"),
            "doi": inc.get("doi"),
            "kaynak_url": url,
            "lisans": RIGHTS["derived_dataset_license"],
        })

    for satir in yol.read_text(encoding="utf-8").splitlines():
        if satir.startswith("## "):
            ekle()
            baslik, govde = satir[3:].strip(), []
        else:
            govde.append(satir)
    ekle()
    return kayitlar


def dogrula(beklenen: set[str]) -> None:
    """Klasörde beklenenden başka dosya varsa durdurur.

    Telifli eser, .git artığı veya gözden kaçmış büyük bir dosya buraya
    sızarsa yükleme yapılmadan hata verilir."""
    var = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
    fazla, eksik = var - beklenen, beklenen - var
    riskli = {f for f in var if f.lower().endswith((".pdf", ".mhtml", ".zip")) or f.startswith(".git")}
    if fazla or eksik or riskli:
        print("\n    DURDURULDU — klasör beklenen içerikte değil:")
        for etiket, küme in (("fazla", fazla), ("eksik", eksik), ("riskli", riskli)):
            if küme:
                print(f"      {etiket}: {sorted(küme)}")
        raise SystemExit(1)


def yukle(commit_message: str) -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit("    huggingface_hub kurulu değil:  pip install huggingface_hub")
    api = HfApi()
    try:
        kim = api.whoami().get("name")
    except Exception:
        raise SystemExit("    HuggingFace oturumu yok. Kendi hesabınızla:  huggingface-cli login")
    print(f"    oturum: {kim} -> {REPO_ID}")
    info = api.upload_folder(
        folder_path=str(OUT),
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message=commit_message,
    )
    print(f"    yüklendi: {info.commit_url}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true", help="hazırladıktan sonra HuggingFace'e yükle")
    ap.add_argument("--mesaj", default="Veri kümesi güncellendi", help="commit mesajı")
    args = ap.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "sayfalar").mkdir(parents=True)
    (OUT / "parcalar").mkdir(parents=True)

    beklenen: set[str] = set()

    def kopyala(src: Path, rel: str) -> None:
        """Kaynağı klasöre alır ve beklenen dosya listesine yazar."""
        if not src.exists():
            return
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        beklenen.add(rel)

    for b in BOOKS:
        kopyala(b.out_dir / "pages.jsonl", f"sayfalar/{b.slug}.jsonl")
        kopyala(b.out_dir / "chunks.jsonl", f"parcalar/{b.slug}.jsonl")

    for s in selections():
        kopyala(ROOT / "secim" / s["slug"] / "sayfalar.jsonl", f"dogrulanmis/{s['slug']}.jsonl")

    kopyala(ROOT / "inceleme" / "bulgular.jsonl", "inceleme/bulgular.jsonl")

    for dil, belgeler in BELGELER.items():
        kayitlar: list[dict] = []
        for yol, sayfa, onsoz in belgeler:
            kayitlar += metin_kayitlari(yol, dil, sayfa, onsoz, len(kayitlar))
        if not kayitlar:
            continue
        rel = f"inceleme/metin-{dil}.jsonl"
        (OUT / "inceleme").mkdir(parents=True, exist_ok=True)
        write_text(OUT / rel, "\n".join(json.dumps(k, ensure_ascii=False) for k in kayitlar) + "\n")
        beklenen.add(rel)

    write_text(OUT / "README.md", card())
    beklenen.add("README.md")

    dogrula(beklenen)

    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"    hazır — {len(beklenen) - 1} veri dosyası + veri kümesi kartı, {total / 1048576:.1f} MB")
    print(f"    klasör: {OUT}   (depo ağacının dışında)")

    if args.upload:
        yukle(args.mesaj)
    else:
        print("    yüklemek için:  python build/13_huggingface.py --upload")


if __name__ == "__main__":
    main()
