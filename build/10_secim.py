"""10 — Seçilmiş bölümleri ayrı bir alt korpus olarak çıkarır.

Bütün korpus 750 sayfadır ve elle düzeltilmesi gerçekçi değildir. Bu adım,
üzerinde fiilen çalışılacak iki bölümü ayırır; böylece OCR düzeltmesi,
Vikikaynak'a taşıma ve tematik inceleme yönetilebilir bir hacimde yapılır.

Aşağıdaki iki aralık **kapanmıştır**: her ikisinin de her sayfası taranmış
aslıyla karşılaştırılmıştır (129 sayfa) ve kapsamın genişletilmesi
planlanmamaktadır. Aralık büyütülecek olursa, yalnız fiilen istinsah edilmiş
sayfalar kapsanmalıdır: burayı ham OCR sayfalarını içerecek şekilde önden
açmak, düzeltilmemiş metni "düzeltilmiş" diye yayımlamak olur.

Kapsam yalnız **gövde metnidir**. Resimler, harita ve levhalar dahil değildir
(onlar build/09_images.py işidir); resim altı yazıları taramada gövde metnine
karışmışsa metinde görünebilir, KALITE.md bunu ölçer.

Sayfa sınırları (pdf_page, side) çifti ile tanımlanır. Basılı sayfa numarası
değil, fizikî tarama konumu esas alınır: bölüm açılış sayfalarında numara
basılmadığı için (ör. Tarih I s. 1) numaraya dayalı seçim eksik kalırdı.

Çıktı: secim/<bolum>/ ve secim/KALITE.md
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import META_DIR, ROOT, read_jsonl, write_json, write_text  # noqa: E402

# 08_verify.py rakamla başladığı için normal import edilemez; ölçütü kopyalamak
# yerine oradan alıyoruz ki iki yerde birbirinden ayrı düşmesin.
_spec = importlib.util.spec_from_file_location("verify08", Path(__file__).resolve().parent / "08_verify.py")
_verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_verify)
ocr_health = _verify.ocr_health

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
BOOKMETA = {b["slug"]: b for b in META["books"]}

OUT = ROOT / "secim"

# Sıra içi konum: açık kitap taramasında sol sayfa (verso) sağdan (recto) öncedir.
SIDE_ORDER = {"verso": 0, "recto": 1}

SELECTIONS = [
    {
        "slug": "beser-tarihine-giris",
        "book": "tarih-1-1931",
        "heading": "BEŞER TARİHİNE GİRİŞ",
        "start": (22, "recto"),   # basılı s. 1 — bölüm açılışı, numara basılmamış
        "end": (36, "verso"),     # basılı s. 24
        "printed_range": [1, 24],
        "note": "Tarih I'in giriş bölümü: tarih kavramı, insanlığın kökeni ve "
                "tarihten evelki zamanların sınıflandırması.",
    },
    {
        "slug": "islam-tarihi",
        "book": "tarih-2-1931",
        "heading": "İSLAM TARİHİ",
        # Bölümün tamamı: basılı s. 79-184. Bölüm s. 184'te sayfa ortasında
        # biter; ardından katlanır Endülüs haritası, sonra numarasız 185'te
        # "XV — İLK MÜSLÜMAN TÜRK DEVLETLERİ" açılır. Aralık onar sayfalık
        # partiler hâlinde, istinsah ilerledikçe buraya kadar genişletilmiştir.
        "start": (69, "recto"),   # basılı s. 79
        "end": (130, "verso"),    # basılı s. 184 — bölümün son sayfası
        "printed_range": [79, 184],
        "note": "Tarih II'nin İslam tarihi bölümü: Arap yarımadası, İslamın "
                "doğuşu ve ilk yayılışı.",
    },
]


def sort_key(row: dict) -> tuple:
    return (row["pdf_page"], SIDE_ORDER.get(row["side"], 9))


def select(rows: list[dict], start: tuple, end: tuple) -> list[dict]:
    lo = (start[0], SIDE_ORDER[start[1]])
    hi = (end[0], SIDE_ORDER[end[1]])
    return sorted([r for r in rows if lo <= sort_key(r) <= hi], key=sort_key)


def scan_unit(row: dict) -> str:
    """Fizikî tarama birimi etiketi (u031r). page_id'nin son parçasıdır."""
    return row["page_id"].rsplit("-", 1)[-1]


def infer_number(picked: list[dict], i: int, printed: set[int]) -> int | None:
    """Numarasız sayfaya, ancak dizi tek bir olasılık bırakıyorsa numara verir.

    Kural: sayfadan hemen sonra basılı N numaralı sayfa geliyorsa bu sayfa
    N-1'dir. Bölüm açılış sayfalarında numara basılmaz (Tarih I s. 1 böyledir);
    kural onları kurtarır.

    İki emniyet kaydı:
      * Çıkarılan numara seçimde zaten basılı olarak varsa çıkarım yapılmaz.
        Levha kümelerinin ortasındaki yüzler aksi hâlde mevcut bir numarayı
        ikinci kez üretir (ör. Tarih II'de gerçek s. 80 ile çakışma).
      * Araya birden çok numarasız yüz giren levha kümelerinde de çıkarım
        yapılmaz: dört fizikî yüz bir numaralık boşluğa sığmaz.
    """
    if i + 1 >= len(picked):
        return None
    nxt = picked[i + 1].get("printed_page")
    if not nxt:
        return None
    prv = picked[i - 1].get("printed_page") if i > 0 else None
    if prv is not None and prv != nxt - 2:
        return None
    cand = nxt - 1
    return None if cand in printed else cand


# Gövde metni sayılmayan sayfa: boş ya da yalnız levha gürültüsü. Bu iki eşik,
# ölçülen değerlere göre seçilmiştir; s019r gibi sayfalar 29 "kelime"lik
# tanınmamış çizim gürültüsü taşır, gerçek metin sayfalarının en zayıfı bile
# 100 kelimenin üstündedir.
def is_plate(health: dict) -> bool:
    return health["words"] < 20 or health["avg_word_len"] < 3.0


# Ölçüt, yer adlarıyla dolu bir haritayı gövde metni sanabilir: katlanır
# levhanın bir yarısı yüzlerce kısa ad taşır, kelime sayısı da ortalama kelime
# uzunluğu da eşiği aşar. Bu yüzler taramaya bakılarak elle işaretlenmiştir.
ELLE_LEVHA = {
    ("islam-tarihi", "u089v"),  # "İslâm imparatorluğunun umumi haritası", sol yarı
    ("islam-tarihi", "u089r"),  # ayni haritanın sağ yarısı
    ("islam-tarihi", "u121r"),  # "İslâm istilâsı" haritası (s. 168 ile 169 arasında)
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    report = ["# Seçilmiş bölümlerin kalite ölçümü", ""]
    report.append("Otomatik üretilmiştir (`build/10_secim.py`). Hiçbir düzeltme yapılmaz.")
    report.append("`junk_ratio` bozuk karakter oranı, `short_word_ratio` iki harften")
    report.append("kısa kelime oranıdır; ikisinin de yüksek olduğu sayfa önce elden geçmelidir.")
    report.append("")
    index = []

    for sel in SELECTIONS:
        rows = list(read_jsonl(ROOT / "data" / sel["book"] / "pages.jsonl"))
        picked = select(rows, tuple(sel["start"]), tuple(sel["end"]))
        bm = BOOKMETA[sel["book"]]

        d = OUT / sel["slug"]
        (d / "metin").mkdir(parents=True, exist_ok=True)

        full, jsonl, worst, plates = [], [], [], []
        full.append(f"{sel['heading']} — {bm['title_full']}")
        full.append(f"{bm['publisher']}, {bm['place']}, {bm['year']}. "
                    f"Basılı s. {sel['printed_range'][0]}-{sel['printed_range'][1]}.")
        full.append("")

        printed_set = {r["printed_page"] for r in picked if r.get("printed_page")}

        for i, r in enumerate(picked):
            text = r.get("text") or ""
            health = ocr_health(text)
            printed = r.get("printed_page")
            inferred = None
            if not printed:
                inferred = infer_number(picked, i, printed_set)

            num = printed or inferred
            tag = f"s{num:03d}" if num else scan_unit(r)
            plate = is_plate(health) or (sel["slug"], scan_unit(r)) in ELLE_LEVHA

            if plate:
                plates.append({"label": tag, "pdf_page_viewer": r["pdf_page"] + 1,
                               "side": r["side"], "n_chars": r["n_chars"],
                               "words": health["words"]})
            else:
                write_text(d / "metin" / f"{tag}.txt", text)
                # Çıpa, numaranın nereden geldiğini saklamaz: basılı numara ile
                # diziden çıkarılan numara alıntıda aynı ağırlıkta sayılamaz.
                if printed:
                    full.append(f"[[s. {printed}]]")
                elif inferred:
                    full.append(f"[[s. {inferred} (çıkarım — sayfada numara basılı değil)]]")
                else:
                    full.append(f"[[{tag} (numarasız)]]")
                full.append(text)
                full.append("")
                worst.append((health["junk_ratio"], health["short_word_ratio"], tag, health))

            rec = {
                "page_id": r["page_id"],
                "book": r["book"],
                "printed_page": printed,
                "inferred_page": inferred,
                "label": tag,
                "is_plate": plate,
                "pdf_page": r["pdf_page"],
                "pdf_page_viewer": r["pdf_page"] + 1,
                "side": r["side"],
                "page_confidence": "inferred" if inferred else r["page_confidence"],
                "running_head": r.get("running_head"),
                "citation": r["citation"],
                "scan_ref": r["scan_ref"],
                "n_chars": r["n_chars"],
                "ocr_health": health,
                "text": text,
            }
            jsonl.append(rec)

        write_text(d / "tam.txt", "\n".join(full))
        write_text(d / "sayfalar.jsonl",
                   "\n".join(json.dumps(x, ensure_ascii=False) for x in jsonl) + "\n")

        body = [x for x in jsonl if not x["is_plate"]]
        chars = sum(x["n_chars"] for x in body)
        words = sum(x["ocr_health"]["words"] for x in body)
        meta = {
            "slug": sel["slug"],
            "book": sel["book"],
            "book_title": bm["title_full"],
            "heading": sel["heading"],
            "note": sel["note"],
            "printed_range": sel["printed_range"],
            "pdf_page_viewer_range": [sel["start"][0] + 1, sel["end"][0] + 1],
            "pages_body": len(body),
            "pages_physical": len(jsonl),
            "characters": chars,
            "words": words,
            "plates_excluded": plates,
            "scope_note": "Yalnız gövde metni. Resim, harita ve levhalar dahil değildir; "
                          "gövde metni taşımayan levha yüzleri tam.txt ve metin/ dışında "
                          "bırakılmış, sayfalar.jsonl içinde is_plate ile işaretlenmiştir.",
            "license": META["rights"]["derived_dataset_license"],
        }
        write_json(d / "kunye.json", meta)
        index.append(meta)

        report.append(f"## {sel['heading']} ({sel['book']}, s. "
                      f"{sel['printed_range'][0]}-{sel['printed_range'][1]})")
        report.append("")
        report.append(f"- Gövde metni sayfası: **{len(body)}** · karakter: **{chars:,}** · "
                      f"kelime: **{words:,}**")
        report.append(f"- Fizikî tarama yüzü: {len(jsonl)} "
                      f"(dışarıda bırakılan levha: {len(plates)})")
        report.append(f"- Kaynak taramada: {sel['start'][0] + 1}-{sel['end'][0] + 1}. PDF sayfası")
        if plates:
            report.append(f"- Levha olarak ayrılanlar: "
                          + ", ".join(f"{p['label']} (PDF {p['pdf_page_viewer']})" for p in plates))
        report.append("")
        report.append("En çok düzeltme isteyen 5 sayfa:")
        report.append("")
        report.append("| Sayfa | Kelime | junk_ratio | short_word_ratio | ort. kelime uz. |")
        report.append("|---|---|---|---|---|")
        for _, _, tag, h in sorted(worst, reverse=True)[:5]:
            report.append(f"| {tag} | {h['words']} | {h['junk_ratio']} | "
                          f"{h['short_word_ratio']} | {h['avg_word_len']} |")
        report.append("")

        print(f"    {sel['slug']}: {len(jsonl)} sayfa, {chars} karakter")

    write_json(OUT / "index.json", {"selections": index})
    write_text(OUT / "KALITE.md", "\n".join(report))
    print(f"    secim/ yazıldı ({len(index)} bölüm)")


if __name__ == "__main__":
    main()
