"""11 — Seçilmiş bölümlerin sayfa sınırlarını birleştirip akıcı metin üretir.

Basılı kitapta kelimeler sayfa sonunda bölünür: bir sayfa "...nok" ile biter,
sonraki "tai nazarından" ile başlar. Sayfa sayfa üretilen metin bu bölünmeyi
olduğu gibi taşır; alıntı için doğrudur, fakat okumak ve dil modeline vermek
için bozuktur — model "nok" ve "tai" diye iki kelime görür.

**Sezgisel kural kullanılmaz.** "Önceki sayfa noktalama ile bitmiyor + sonraki
küçük harfle başlıyor" ölçütü denendi ve yanlış çıktı: "Herakliyüs İranlıları
yenip" + "istirdat ettiği" gibi iki tamam kelimeyi de bitiştirip "yenipistirdat"
üretiyordu. Otuz sekiz sayfada yalnız 21 sınır vardır; hepsi tek tek okunmuş ve
kararı aşağıdaki tabloya yazılmıştır. Yeni bölüm eklenirse tablo genişletilir;
tabloda karşılığı olmayan sınır için betik hata verir, sessizce tahmin etmez.

    python build/11_birlesik.py

Çıktı: secim/<bolum>/okuma.txt, okuma.md, cipalar.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, write_text  # noqa: E402

SECIM = ROOT / "secim"

# Sayfa sınırı kararları. Anahtar: (bölüm, o sınırla BAŞLAYAN sayfanın numarası).
#   bitisik  — kelime sayfa sonunda bölünmüş, iki parça birleştirilir
#   bosluk   — iki tamam kelime, araya boşluk konur
#   paragraf — önceki sayfa cümleyi/paragrafı bitirmiş
KARARLAR = {
    ("beser-tarihine-giris", 2): ("bitisik", "far + zettiler → farzettiler"),
    ("beser-tarihine-giris", 3): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 4): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 5): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 6): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 7): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 8): ("bitisik", "tah + mini → tahmini"),
    ("beser-tarihine-giris", 9): ("bosluk", "'Bu sayede' + 'gelecek' — ikisi de tamam"),
    ("beser-tarihine-giris", 10): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 11): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 12): ("paragraf", "cümle bitmiş, madde işareti e) ile başlıyor"),
    ("beser-tarihine-giris", 13): ("bitisik", "bulunmuş + tur → bulunmuştur"),
    ("beser-tarihine-giris", 14): ("bosluk", "taammüm + etti — birleşik fiil, ayrı yazılır"),
    ("beser-tarihine-giris", 15): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 16): ("bitisik", "Orta + asyadan → Ortaasyadan (kitabın imlası)"),
    ("beser-tarihine-giris", 17): ("bitisik", "biri + birini → biribirini (kitabın imlası)"),
    ("beser-tarihine-giris", 18): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 19): ("bosluk", "'lisan' + 'bugün' — ikisi de tamam"),
    ("beser-tarihine-giris", 20): ("bosluk", "'Dimağdan murat.' + 'onun' — nokta OCR hatası, virgül olmalı"),
    ("beser-tarihine-giris", 21): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 22): ("paragraf", "cümle bitmiş"),
    ("beser-tarihine-giris", 23): ("bitisik", "gökyü + zünden → gökyüzünden"),
    ("beser-tarihine-giris", 24): ("bitisik", "İptidaî in + sanda → insanda"),
    ("islam-tarihi", 80): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 81): ("bitisik", "Seba + da → Sebada"),
    ("islam-tarihi", 82): ("bitisik", "başlı + caları → başlıcaları"),
    ("islam-tarihi", 84): ("paragraf", "araya levha girmiş (s. 83), cümle bitmiş"),
    ("islam-tarihi", 85): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 86): ("bosluk", "'etrafında' + 'muharebelerin' — ikisi de tamam"),
    ("islam-tarihi", 87): ("bitisik", "Roma + lılardı → Romalılardı"),
    ("islam-tarihi", 88): ("bosluk", "'yenip' + 'istirdat' — ikisi de tamam"),
    ("islam-tarihi", 89): ("bitisik", "baba + sından → babasından"),
    ("islam-tarihi", 90): ("bitisik", "nok + tai → noktai"),
    ("islam-tarihi", 91): ("bosluk", "'ilham' + 'aldıklarına' — ikisi de tamam"),
    ("islam-tarihi", 92): ("bitisik", "getir + mektedir → getirmektedir"),
    ("islam-tarihi", 93): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 94): ("paragraf", "cümle bitmiş, 'C.' başlığı ile açılıyor"),
    ("islam-tarihi", 95): ("bitisik", "Müslü + manlar → Müslümanlar"),
    ("islam-tarihi", 96): ("bosluk", "'bütün suları' + 'toplıyan' — cümle sürüyor"),
    ("islam-tarihi", 97): ("bosluk", "'yaygaracılar,' + 'pişman' — cümle sürüyor"),
    ("islam-tarihi", 98): ("bitisik", "çıka + rak → çıkarak"),
    ("islam-tarihi", 99): ("bosluk", "'anlaşıldı.' + 'Fakat' — paragraf sürüyor"),
    ("islam-tarihi", 100): ("bosluk", "'İlk harekete' + 'geçen' — cümle sürüyor"),
    ("islam-tarihi", 101): ("bosluk", "Selmanı + Farisî — iki kelimelik ad"),
    ("islam-tarihi", 102): ("bosluk", "'ricat ederken' + 'o kadar' — cümle sürüyor"),
    ("islam-tarihi", 103): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 104): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 105): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 106): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 107): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 108): ("bosluk", "'tesadüf eden' + 'Halit bin Velit' — cümle sürüyor"),
    ("islam-tarihi", 109): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 110): ("bosluk", "'budur. Bu' + 'seferin' — cümle sürüyor"),
    ("islam-tarihi", 111): ("bitisik", "ora + da → orada"),
    ("islam-tarihi", 112): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 113): ("paragraf", "araya katlanır harita levhası girmiş (u089), cümle bitmiş"),
    ("islam-tarihi", 114): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 115): ("bosluk", "'bulundukları' + 'sırada' — ikisi de tamam"),
    ("islam-tarihi", 116): ("bosluk", "'Bu hareket' + 'o zamana kadar' — cümle sürüyor"),
    ("islam-tarihi", 117): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 118): ("bitisik", "Ebu + bekir → Ebubekir"),
    ("islam-tarihi", 119): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 120): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 121): ("bitisik", "mağ + lûp → mağlûp"),
    ("islam-tarihi", 122): ("bosluk", "'toplanan' + 'birtakım' — cümle sürüyor"),
    ("islam-tarihi", 123): ("bosluk", "'askerlere' + 'mızraklarının' — cümle sürüyor"),
    ("islam-tarihi", 124): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 125): ("bosluk", "'Ömer' + 'devrinde' — cümle sürüyor"),
    ("islam-tarihi", 126): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 127): ("bosluk", "ilân + etmiş — birleşik fiil, ayrı yazılır"),
    ("islam-tarihi", 128): ("bosluk", "ana + dillerini — tirelenmemiş, iki kelime"),
    ("islam-tarihi", 129): ("bosluk", "'akınlar yaptı.' + 'Fakat' — araya levhalar girmiş (u098r-u100v), paragraf sürüyor"),
    ("islam-tarihi", 130): ("bosluk", "'Yezit III.' + 'Velit II. yi' — cümle sürüyor"),
    ("islam-tarihi", 131): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdede 'büyük' + 'Atlas Denizi' sürüyor"),
    ("islam-tarihi", 132): ("bitisik", "şar + kı → şarkı"),
    ("islam-tarihi", 133): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor (önceki sayfa dipnotla bitiyor)"),
    ("islam-tarihi", 134): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdedeki şöh + ret bölünmesi birleştirilemiyor"),
    ("islam-tarihi", 135): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdedeki ol + duğu bölünmesi birleştirilemiyor"),
    ("islam-tarihi", 136): ("bosluk", "'kıt'asını' + 'istilâ etti' — cümle sürüyor"),
    ("islam-tarihi", 137): ("bosluk", "'Musa bin Nasirin' + 'oğlu' — araya levhalar girmiş (u104r-u105v), cümle sürüyor"),
    ("islam-tarihi", 138): ("bitisik", "ken + disinin → kendisinin"),
    ("islam-tarihi", 139): ("bosluk", "'ırmaklarını' + 'geçti' — cümle sürüyor"),
    ("islam-tarihi", 140): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdede 'neticelerden' + 'mahrum' sürüyor"),
    ("islam-tarihi", 141): ("bitisik", "katlia + mından → katliamından"),
    ("islam-tarihi", 142): ("bitisik", "kıyı + ları → kıyıları"),
    ("islam-tarihi", 143): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 144): ("bosluk", "'bulunabiliyorlardı.' + 'Nihayet' — girintisiz, paragraf sürüyor"),
    ("islam-tarihi", 145): ("bosluk", "'başka bir şey' + 'bırakmıyan' — cümle sürüyor"),
    ("islam-tarihi", 146): ("bosluk", "'şehirler bile' + 'fırsat buldukça' — cümle sürüyor"),
    ("islam-tarihi", 147): ("bosluk", "'ve küçük' + 'türk beyliklerini' — cümle sürüyor"),
    ("islam-tarihi", 148): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 149): ("bitisik", "hudu + duna → hududuna"),
    ("islam-tarihi", 150): ("paragraf", "cümle bitmiş, yan başlıkla açılıyor"),
    ("islam-tarihi", 151): ("bitisik", "bu + lunan → bulunan"),
    ("islam-tarihi", 152): ("bitisik", "durgun + luğu → durgunluğu"),
    ("islam-tarihi", 153): ("bosluk", "'Halife' + 'Muktedir' — cümle sürüyor"),
    ("islam-tarihi", 154): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 155): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 156): ("bitisik", "aldı + lar → aldılar"),
    ("islam-tarihi", 157): ("bosluk", "'ordudaki Türkler,' + 'gerek askerlik' — cümle sürüyor"),
    ("islam-tarihi", 158): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 159): ("bitisik", "mın + takada → mıntakada"),
    ("islam-tarihi", 160): ("bosluk", "'Bağdatta yaşayan' + 'meşhur' — cümle sürüyor"),
    ("islam-tarihi", 161): ("bitisik", "hare + ketleri → hareketleri"),
    ("islam-tarihi", 162): ("bosluk", "'Musa dinini kabul' + 'ettikten' — cümle sürüyor"),
    ("islam-tarihi", 163): ("bitisik", "haricin + de → haricinde"),
    ("islam-tarihi", 164): ("bosluk", "'ilmini islâmlar' + 'arasında' — cümle sürüyor"),
    ("islam-tarihi", 165): ("bitisik", "kıs + mı → kısmı"),
    ("islam-tarihi", 166): ("bosluk", "'halledilirdi.' + 'Ayrıca' — girintisiz, paragraf sürüyor"),
    ("islam-tarihi", 167): ("paragraf", "cümle bitmiş, sayfa girintiyle açılıyor"),
    ("islam-tarihi", 168): ("bosluk", "'değiştirerek arap' + 'kabileleri' — cümle sürüyor"),
    ("islam-tarihi", 169): ("bitisik", "müd + det → müddet; araya harita levhası girmiş (u121r)"),
    ("islam-tarihi", 170): ("paragraf", "cümle bitmiş"),
    ("islam-tarihi", 171): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdedeki Pi + rene bölünmesi birleştirilemiyor"),
    ("islam-tarihi", 172): ("bitisik", "aldı + lar → aldılar"),
    ("islam-tarihi", 173): ("paragraf", "önceki sayfa dipnotla bitiyor; gövdede 'sürmeye' + 'başlıyan' sürüyor"),
    ("islam-tarihi", 174): ("bosluk", "'Tek bayrak' + 'altında' — cümle sürüyor"),
    ("islam-tarihi", 175): ("bosluk", "'iltihakile daha' + 'ziyade' — cümle sürüyor"),
    ("islam-tarihi", 176): ("bitisik", "Abdürrahmanül + muzaffer → Abdürrahmanülmuzaffer"),
    ("islam-tarihi", 177): ("bosluk", "'yüksek' + 'mevki' — ikisi de tamam"),
    ("islam-tarihi", 178): ("bitisik", "dökü + lüyordu → dökülüyordu"),
    ("islam-tarihi", 179): ("bitisik", "yük + sek → yüksek"),
    ("islam-tarihi", 180): ("paragraf", "önceki sayfa bölüm sonunda bitiyor, yan başlıkla açılıyor"),
    ("islam-tarihi", 181): ("bosluk", "'yerine geçti. Fakat' + 'müşkülât' — cümle sürüyor"),
    ("islam-tarihi", 182): ("bosluk", "'Murabıtları imdada' + 'çağırdılar' — cümle sürüyor"),
    ("islam-tarihi", 183): ("bosluk", "'hareket eden' + 'Ferdinant - İzabel' — cümle sürüyor"),
    ("islam-tarihi", 184): ("bosluk", "'Abbat ailesidir. Bütün' + 'Tavaifi Mülûk' — cümle sürüyor"),
}

AYIRICI = {"bitisik": "", "bosluk": " ", "paragraf": "\n\n"}


def kelime_sonu(metin: str, konum: int) -> int:
    """Verilen konumdan sonraki ilk boşluğun yerini döndürür.

    Bitişik birleştirmede sayfa çıpası kelimenin ortasına düşmemelidir; çıpa
    kelime tamamlandıktan sonraya alınır.
    """
    i = konum
    while i < len(metin) and not metin[i].isspace():
        i += 1
    return i


def isle(slug: str) -> dict:
    d = SECIM / slug
    kunye = json.loads((d / "kunye.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in (d / "sayfalar.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    govde = [r for r in rows if not r["is_plate"]]

    parcalar: list[str] = []
    cipalar: list[dict] = []
    konum = 0
    sayac = {"bitisik": 0, "bosluk": 0, "paragraf": 0}

    for i, r in enumerate(govde):
        metin = (r["text"] or "").strip()
        num = r["printed_page"] or r["inferred_page"]
        tur = None

        if i > 0:
            anahtar = (slug, num)
            if anahtar not in KARARLAR:
                raise SystemExit(
                    f"HATA: {slug} s.{num} için sayfa sınırı kararı yok.\n"
                    f"  önceki sayfa sonu : …{parcalar[-1][-60:]!r}\n"
                    f"  bu sayfanın başı  : {metin[:60]!r}…\n"
                    f"Kararı build/11_birlesik.py içindeki KARARLAR tablosuna ekleyin."
                )
            tur, _ = KARARLAR[anahtar]
            sayac[tur] += 1
            parcalar.append(AYIRICI[tur])
            konum += len(AYIRICI[tur])

        cipalar.append({
            "printed_page": r["printed_page"],
            "inferred_page": r["inferred_page"],
            "page_id": r["page_id"],
            "offset": konum,
            "sinir": tur,
            "citation": r["citation"],
        })
        parcalar.append(metin)
        konum += len(metin)

    tam = "".join(parcalar)

    # Çıpaları yerleştir (sondan başa, offsetler kaymasın).
    govdeli = tam
    for c in reversed(cipalar):
        num = c["printed_page"] or c["inferred_page"]
        if c["sinir"] == "bitisik":
            # Kelime bütün kalsın: çıpa kelimenin bitiminden sonraya.
            yer = kelime_sonu(tam, c["offset"])
            etiket = f" [[s. {num}]]"
        else:
            yer = c["offset"]
            etiket = f"[[s. {num}]]\n" if c["sinir"] != "bosluk" else f"[[s. {num}]] "
        govdeli = govdeli[:yer] + etiket + govdeli[yer:]

    basli = [
        f"{kunye['heading']} — {kunye['book_title']}",
        "Türk Tarihi Tetkik Cemiyeti, Maarif Vekâleti, İstanbul, Devlet Matbaası, 1931.",
        f"Basılı s. {kunye['printed_range'][0]}-{kunye['printed_range'][1]}. "
        f"Metin taranmış nüshadan çıkarılıp sayfa sayfa elle düzeltilmiştir; 1931 imlası korunmuştur.",
        "",
        "[[s. N]] işaretleri basılı sayfa başlangıcını gösterir. Kelimesi sayfa sonunda",
        "bölünmüş yerlerde kelime bütün bırakılmış, çıpa kelimeden sonraya alınmıştır;",
        "orada sayfa numarası kelimenin bittiği yeri değil, sonraki sayfanın başladığı",
        "yeri gösterir.",
        "=" * 70,
        "",
    ]
    write_text(d / "okuma.txt", "\n".join(basli) + govdeli.strip() + "\n")

    md = [
        f"# {kunye['heading']}", "",
        f"*{kunye['book_title']}* — Türk Tarihi Tetkik Cemiyeti, Maarif Vekâleti, "
        f"İstanbul, Devlet Matbaası, 1931. Basılı s. "
        f"{kunye['printed_range'][0]}-{kunye['printed_range'][1]}.", "",
        "> Metin taranmış nüshadan çıkarılmış ve sayfa sayfa elle düzeltilmiştir. "
        "1931 imlası korunmuştur.", "", "---", "",
    ]
    write_text(d / "okuma.md", "\n".join(md) + govdeli.strip() + "\n")

    write_text(d / "cipalar.json",
               json.dumps({"slug": slug, "anchors": cipalar}, ensure_ascii=False, indent=1) + "\n")

    return {"slug": slug, "sayfa": len(govde), "karakter": len(tam), **sayac}


def main() -> None:
    index = json.loads((SECIM / "index.json").read_text(encoding="utf-8"))
    for sel in index["selections"]:
        r = isle(sel["slug"])
        print(f"    {r['slug']}: {r['sayfa']} sayfa · {r['karakter']} karakter · "
              f"sınır: {r['bitisik']} bitişik, {r['bosluk']} boşluk, {r['paragraf']} paragraf")


if __name__ == "__main__":
    main()
