"""12 — Düzeltilmiş sayfaları Vikikaynak "Sayfa:" ad alanı biçimine çevirir.

Vikikaynak'ta bu iki kitabın taraması **zaten** Commons'ta ve "Dizin:" sayfaları
kuruludur. Yapılacak iş yükleme değil, mevcut dizine bağlı Sayfa: sayfalarını
doldurmaktır.

Sayfa eşlemesi ampirik olarak tespit edilmiştir — Commons'taki tarama bizim
kaynak PDF'imizden farklıdır (tek sayfa taraması, farklı ön bölüm):

    Commons sayfası = basılı sayfa + OFSET

    Tarih I  : ofset 33   (Commons 34 = basılı 1,  Commons 44 = basılı 11)
    Tarih II : ofset 22   (Commons 106 = basılı 84, Commons 115 = basılı 93)

Doğrulama: Commons 34 "HALİN MAZİ İLE ALÂKASI" ile başlar (bizim s001),
Commons 44 "Bu devirde insanlar, iptidaî ve sefilâne" (bizim s011),
Commons 115 "MUHAMMET MEDİNEDE" (bizim s093).

Üretilen biçim, tr.wikisource'un fiilî teamülüne uyar:
  * üstbilgi <noinclude> içinde {{rh}} ile cari başlık ve sayfa numarası
  * sayfa sonunda bölünen kelimeler {{ysb}}/{{yss}} çiftiyle
  * paragraf sayfa sonunda bitiyorsa altbilgide {{nop}}
  * basılı sayfa numarası gövdeye ASLA yazılmaz (Yardım:Sayfa numaraları)

    python build/12_vikikaynak.py            # yalnız değişmemiş dosyaları tazele
    python build/12_vikikaynak.py --zorla    # elle istinsah edilenlerin de üzerine yaz

**Üretilen metin taslaktır.** Bir dosya sonradan taramayla karşılaştırılıp elle
istinsah edilmiş olabilir; o düzeltmelerin bir kısmı korpusta hiç durmaz —
italikler, “…„ tırnakları, {{sic}} işaretleri, cari başlıktaki şapkalar ve
noktalama öncesi ince boşluk yalnız burada yaşar. Bu yüzden betik, içeriği
üreteceğinden farklı olan bir dosyanın üzerine yazmaz; adını basıp geçer.
Gerçekten taslağa dönmek isteniyorsa --zorla gerekir.

Çıktı: vikikaynak/<kitap>/<commons_sayfa>.txt ve vikikaynak/YUKLEME.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, write_text  # noqa: E402

SECIM = ROOT / "secim"
OUT = ROOT / "vikikaynak"

KITAPLAR = {
    "beser-tarihine-giris": {
        "dosya": "Tarih I Tarihtenevelki Zamanlar ve Eski Zamanlar.pdf",
        "ofset": 33,
        "bolum": "BEŞER TARİHİNE GİRİŞ",
        # Basılı 1-11 Vikikaynak'ta Kibele tarafından istinsah edilmişti;
        # bu adım onlar için dosya ÜRETMEZ.
        #
        # Sebep, metinlerinin doğru olması değil. 2026-08-18'de korpus
        # taramayla düzeltildikten sonra iki nüsha karşılaştırıldı ve
        # örtüşmedikleri görüldü: 26 kelimede 34 yerde şapka eksikti
        # (tabii/tabiî, mahlük/mahlûk, hicri/hicrî …) ve 12 kelime düzeyinde
        # fark vardı (HAYA'TIN, tarihle/tarihte, 50 bin/50,000 …). Karşılaştırma
        # bizim üç hatamızı da buldu: bakıyelerine, düşen bir "olan", fazladan
        # bir virgül.
        #
        # O 55 düzeltme aynı gün Vikikaynak'ta doğrudan uygulandı — sayfanın
        # tamamı bizim metnimizle DEĞİŞTİRİLMEDİ, yalnız kelimeler düzeltildi.
        # Kibele'nin biçimlendirmesi (üstbilgi düzeni, sayfa sonu tireleri)
        # kasten korundu; onlar hata değil, ayrı bir teamül. Bu yüzden burada
        # üretilecek bir dosya yok: o sayfaların kaynağı Vikikaynak'ın kendisi.
        "mevcut": set(range(1, 12)),
        # Basılı 12-24 (Sayfa/45-57) bu depodan yüklendi ve tamamı kalite
        # seviyesi 3 "İstinsah edildi" ile işaretli. Yapılacak iş kalmadı;
        # taslak dosyalar yüklenenin kaydı olarak durur.
        "yuklendi": set(range(12, 25)),
    },
    "islam-tarihi": {
        "dosya": "Tarih II Ortazamanlar.pdf",
        "ofset": 22,
        "bolum": "İSLAM TARİHİ",
        # 2026-08-19'da tr.wikisource API'sinden canlı ölçüldü (list=allpages,
        # ad alanı 250): Sayfa/101-115 var, 116 ve sonrası yok. 101-115
        # (basılı 79-93) bu depodan yüklendi; örneklenen sayfaların hepsi
        # kalite seviyesi 3 "İstinsah edildi". Bir önceki ölçümde (2026-08-18)
        # bunların 89-93'ü anonim ham OCR idi; artık ham OCR kalmadı.
        #
        # Basılı 94-184 (Sayfa/116-206) Vikikaynak'ta HİÇ yok: hepsi yeni sayfa.
        "mevcut": set(),
        "yuklendi": set(range(79, 94)),
        "ham_ocr": set(),
    },
}

# 1931 basımının kendi dizgi hataları. Taramada birebir böyle basılmıştır;
# düzeltilmez, {{sic}} ile işaretlenir. Her biri tarama görüntüsünden teyit
# edilmiştir — bizim OCR hatalarımızdan ayırt edilerek.
SIC = {
    "islam-tarihi": [("Milâttaan", 80), ("isiâmiyeti", 89)],
}

# Bölüm içi ara başlıklar: kısa ve tamamı büyük harf olan satırlar.
BASLIK = re.compile(r"^[^a-zçğıöşü]{3,60}$")


def baslik_mi(satir: str) -> bool:
    s = satir.strip()
    if not s or len(s) > 60:
        return False
    harf = [c for c in s if c.isalpha()]
    return bool(harf) and all(c.isupper() for c in harf)


def rh(printed: int, side: str, bolum: str) -> str:
    """Cari başlık. Çift sayfa (verso) solda numara, tek sayfa (recto) sağda."""
    if side == "verso":
        return f"{{{{rh|'''{printed}'''|'''TARİH'''|}}}}"
    return f"{{{{rh||'''{bolum}'''|'''{printed}'''}}}}"


def govde(metin: str) -> str:
    out = []
    for satir in metin.strip().split("\n"):
        s = satir.strip()
        if not s:
            out.append("")
        elif baslik_mi(s):
            out.append(f"'''{s}'''")
        else:
            out.append(s)
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--zorla",
        action="store_true",
        help="elle değiştirilmiş dosyaların da üzerine yaz (istinsah kaybolur)",
    )
    zorla = ap.parse_args().zorla

    kararlar = _kararlari_al()
    OUT.mkdir(exist_ok=True)
    liste = []
    korunan: list[str] = []

    for slug, cfg in KITAPLAR.items():
        d = SECIM / slug
        rows = [json.loads(l) for l in (d / "sayfalar.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        hedef = OUT / slug
        hedef.mkdir(parents=True, exist_ok=True)

        # Levhalar rapora girer ama sıraya girmez: sayfa sınırı kararları
        # gövde sayfalarının ardışıklığına göre verilmiştir.
        for r in rows:
            if r["is_plate"]:
                p = r["printed_page"] or r["inferred_page"]
                liste.append({
                    "kitap": cfg["dosya"],
                    "commons": (p + cfg["ofset"]) if p else None,
                    "basili": p, "durum": "levha — metin yok", "dosya": None,
                })
        rows = [r for r in rows if not r["is_plate"]]

        for i, r in enumerate(rows):
            printed = r["printed_page"] or r["inferred_page"]
            if not printed:
                continue
            commons = printed + cfg["ofset"]

            if printed in cfg["mevcut"]:
                liste.append({
                    "kitap": cfg["dosya"], "commons": commons, "basili": printed,
                    "durum": "ZATEN İSTİNSAH EDİLMİŞ — dokunma", "dosya": None,
                })
                continue

            g = govde(r["text"] or "")

            # Basımın kendi hatalarını {{sic}} ile işaretle.
            for kelime, sayfa in SIC.get(slug, []):
                if sayfa == printed and kelime in g:
                    g = g.replace(kelime, f"{{{{sic|{kelime}}}}}")

            # Sonraki sayfa bu sayfanın son kelimesini bölüyor mu?
            sonraki = rows[i + 1] if i + 1 < len(rows) else None
            son_num = (sonraki.get("printed_page") or sonraki.get("inferred_page")) if sonraki else None
            if son_num and kararlar.get((slug, son_num)) == "bitisik":
                ilk_parca = g.rstrip().split()[-1]
                ikinci = (sonraki["text"] or "").strip().split()[0].rstrip(".,;:")
                tam_kelime = ilk_parca + ikinci
                g = g.rstrip()[: -len(ilk_parca)] + f"{{{{ysb|{ilk_parca}|{tam_kelime}}}}}"

            # Bu sayfa, önceki sayfanın böldüğü kelimeyle mi başlıyor?
            if kararlar.get((slug, printed)) == "bitisik" and i > 0:
                onceki = rows[i - 1]
                ilk_parca = (onceki["text"] or "").strip().split()[-1]
                ikinci = g.lstrip().split()[0]
                tam_kelime = ilk_parca + ikinci.rstrip(".,;:")
                g = f"{{{{yss|{ikinci}|{tam_kelime}}}}}" + g.lstrip()[len(ikinci):]

            altbilgi = "{{nop}}" if kararlar.get((slug, son_num)) == "paragraf" else ""

            icerik = (
                f"<noinclude>{rh(printed, r['side'], cfg['bolum'])}</noinclude>\n"
                f"{g}\n"
                f"<noinclude>{altbilgi}</noinclude>\n"
            )
            ad = f"{commons:03d}.txt"
            p = hedef / ad
            # Üretilen metin bir taslaktır; dosya sonradan taramayla
            # karşılaştırılıp elle istinsah edilmiş olabilir. O düzeltmeler
            # (italik, “…„, {{sic}}, başlıktaki şapkalar, noktalama öncesi
            # ince boşluk) korpusta durmaz, yalnız burada durur — üzerine
            # yazmak onları sessizce yok eder.
            if p.exists() and p.read_text(encoding="utf-8") != icerik and not zorla:
                korunan.append(f"vikikaynak/{slug}/{ad}")
            else:
                write_text(p, icerik)

            # Yüklenmiş sayfa için yapıştırılacak dosya gösterilmez: liste iş
            # listesidir, biten işi yeniden yaptırmamalıdır.
            if printed in cfg.get("yuklendi", set()):
                durum, dosya = "YÜKLENDİ — İstinsah edildi", None
            elif printed in cfg.get("ham_ocr", set()):
                durum, dosya = "ham OCR üzerine yazılacak", f"vikikaynak/{slug}/{ad}"
            else:
                durum, dosya = "yeni sayfa", f"vikikaynak/{slug}/{ad}"
            liste.append({
                "kitap": cfg["dosya"], "commons": commons, "basili": printed,
                "durum": durum, "dosya": dosya,
            })

    _yukleme_listesi(liste)
    yeni = sum(1 for x in liste if x["durum"] == "yeni sayfa")
    uzerine = sum(1 for x in liste if x["durum"] == "ham OCR üzerine yazılacak")
    yuklu = sum(1 for x in liste if x["durum"] == "YÜKLENDİ — İstinsah edildi")
    atla = sum(1 for x in liste if x["dosya"] is None) - yuklu
    print(f"    {yeni} yeni sayfa, {uzerine} ham OCR üzerine, "
          f"{yuklu} yüklenmiş, {atla} atlanan")
    if korunan:
        print(f"    {len(korunan)} dosya KORUNDU — elle değiştirilmiş, üzerine yazılmadı:")
        for k in korunan:
            print(f"      {k}")
        print("      Üretilen taslağı gerçekten istiyorsanız: --zorla")
    print(f"    vikikaynak/YUKLEME.md yazıldı")


def _kararlari_al() -> dict:
    """11_birlesik.py'deki sayfa sınırı kararlarını yeniden kullanır."""
    import importlib.util
    p = Path(__file__).resolve().parent / "11_birlesik.py"
    spec = importlib.util.spec_from_file_location("birlesik", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return {k: v[0] for k, v in m.KARARLAR.items()}


def _yukleme_listesi(liste: list[dict]) -> None:
    L = ["# Vikikaynak yükleme listesi", "",
         "Otomatik üretildi (`build/12_vikikaynak.py`). Her satır bir Vikikaynak",
         "sayfasıdır. Sayfa adresini tarayıcıda açın, içeriği ilgili dosyadan",
         "yapıştırın, kaydedin.", "",
         "Sayfa kalitesini **İstinsah edildi** olarak işaretlemeyi unutmayın.", ""]
    for kitap in sorted({x["kitap"] for x in liste}):
        L.append(f"## {kitap}")
        L.append("")
        L.append("| Basılı s. | Vikikaynak sayfası | Durum | Yapıştırılacak dosya |")
        L.append("|---|---|---|---|")
        satirlar = [y for y in liste if y["kitap"] == kitap]
        # Numarası olmayan levhalar bir satırda toplanır; tek tek listelenmeleri
        # tabloyu "None" bağlantılarıyla doldururdu.
        numarasiz = sum(1 for y in satirlar if y["commons"] is None)
        for x in sorted([y for y in satirlar if y["commons"] is not None],
                        key=lambda y: y["commons"]):
            url = ("https://tr.wikisource.org/wiki/Sayfa:"
                   + kitap.replace(" ", "_") + f"/{x['commons']}")
            dosya = f"`{x['dosya']}`" if x["dosya"] else "—"
            L.append(f"| {x['basili']} | [{x['commons']}]({url}) | {x['durum']} | {dosya} |")
        L.append("")
        if numarasiz:
            L.append(f"Ayrıca {numarasiz} numarasız levha yüzü var (bölüm arasına "
                     f"girmiş tam sayfa resimler); metin taşımadıkları için "
                     f"listelenmemiştir.")
            L.append("")
    write_text(OUT / "YUKLEME.md", "\n".join(L))


if __name__ == "__main__":
    main()
