"""19 — Ana ad alanındaki cilt ve bölüm sayfalarını Vikikaynak'a yazar.

    python build/19_vikikaynak_bolum.py          # ne yazılacağını göster
    python build/19_vikikaynak_bolum.py --yaz    # yaz

Bu adım 18'den *sonra* çalıştırılır: `<pages>` etiketi Sayfa: ad alanındaki
metni çeker, sayfalar girilmemişken bölüm sayfası boş görünür.

Cilt başına iki sayfa üretilir — cildin kendisi (istinsah edilen bölümü
gösteren kısa bir giriş) ve bölümün kendisi. Cildin tamamı istinsah edilmediği
için cilt sayfası bütün içindekileri değil yalnız o bölümü listeler.

Sayfa aralığı elle yazılmaz: `secim/index.json` içindeki basılı aralık,
18_vikikaynak_yukle.KITAPLAR içindeki Commons ofsetiyle toplanır. Bölüm
genişlerse iki dosya da kendiliğinden doğru aralığı verir.

Kimlik ve çakışma koruması 18. adımdan gelir; oradaki açıklamalar geçerlidir.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "vikikaynak_yukle", Path(__file__).resolve().parent / "18_vikikaynak_yukle.py")
y18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(y18)

OZET = "bölüm sayfası oluşturuldu (istinsah edilen sayfalardan)"

# Cilt sayfasının notundaki basım künyesi; Dizin sayfalarındaki Remarks ile aynı.
BASIM = "Maarif Vekâleti, İstanbul, Devlet Matbaası, 1931. Liseler için resmî tarih ders kitabı."

BOLUM_ADI = {"beser-tarihine-giris": "Beşer Tarihine Giriş", "islam-tarihi": "İslâm Tarihi"}

# Eser sahibi sayfası. {{eser başlığı}} şablonu "eser sahibi" alanını Kişi: ad
# alanına bağlar; sayfa yoksa dört sayfada birden kırmızı bağlantı görünür.
# Cemiyet tüzel kişidir, doğum/ölüm yılı alanları bilerek boş bırakılır; 1935'te
# ad değişikliği olmuştur, kurum sona ermemiştir.
KISI_BASLIK = "Kişi:Türk Tarihi Tetkik Cemiyeti"


def kisi_sayfasi(ciltler: list[str]) -> str:
    eserler = chr(10).join(f"* [[{c}]] (1931)" for c in ciltler)
    return f"""{{{{Kişi
 |ismi                = Türk Tarihi Tetkik Cemiyeti
 |soyismi             =
 |soyismi başharfi    = T
 |açıklamalar         = 1930'da kurulan, 1935'te [[:w:Türk Tarih Kurumu|Türk Tarih Kurumu]] adını alan kurum. Maarif Vekâleti Millî Talim ve Terbiye Dairesinin emriyle hazırladığı ''Tarih'' serisi 1931-1941 arasında Türkiye'de liselerde resmî tarih ders kitabı olarak okutulmuştur.
 |vikipedi_bağlantısı = Türk Tarih Kurumu
}}}}

== Eserleri ==
{eserler}"""


def sayfalar() -> list[tuple[str, str]]:
    secim = json.loads((ROOT / "secim" / "index.json").read_text(encoding="utf-8"))["selections"]
    cikti: list[tuple[str, str]] = [
        (KISI_BASLIK, kisi_sayfasi([s["book_title"] for s in secim]))
    ]
    for s in secim:
        dosya, ofset = y18.KITAPLAR[s["slug"]]
        bas, son = s["printed_range"]
        cilt = s["book_title"]
        bolum = BOLUM_ADI[s["slug"]]
        aralik = f"basılı s. {bas}-{son}"

        cikti.append((cilt, f"""{{{{eser başlığı
 | önceki      =
 | sonraki     =
 | başlık      ={cilt}
 | bölüm       =
 | eser sahibi =Türk Tarihi Tetkik Cemiyeti
 | notlar      ={BASIM} Bu ciltten şimdilik yalnız aşağıdaki bölüm istinsah edilmiştir.
}}}}

* [[{cilt}/{bolum}|{bolum}]] ({aralik})

{{{{eser son
 |telif={{{{KM-Türkiye-isimsiz}}}}
 |kaynak=[[Dizin:{dosya}]]
}}}}"""))

        cikti.append((f"{cilt}/{bolum}", f"""{{{{eser başlığı
 | önceki      =
 | sonraki     =
 | başlık      ={cilt}
 | bölüm       ={bolum}
 | eser sahibi =Türk Tarihi Tetkik Cemiyeti
 | notlar      ={BASIM} {aralik[0].upper()}{aralik[1:]}.
}}}}

<pages index="{dosya}" from={bas + ofset} to={son + ofset} />

{{{{eser son
 |telif={{{{KM-Türkiye-isimsiz}}}}
 |kaynak=[[Dizin:{dosya}]]
}}}}"""))
    return cikti


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="gerçekten yaz (yoksa yalnız rapor)")
    ap.add_argument("--zorla", action="store_true", help="var olan sayfaların üzerine de yaz")
    a = ap.parse_args()

    isler = sayfalar()
    if not a.yaz:
        print(f"    {len(isler)} sayfa yazılacak (kuru çalıştırma — hiçbir şey yazılmadı)")
        for baslik, govde in isler:
            print(f"\n    === {baslik} ===")
            print("\n".join("      " + s for s in govde.splitlines()))
        print("\n    yazmak için:  python build/19_vikikaynak_bolum.py --yaz")
        return

    y18.oturum_ac()
    tok = y18.istek({"action": "query", "meta": "tokens", "type": "csrf"})["query"]["tokens"]["csrftoken"]

    for baslik, govde in isler:
        mevcut = y18.sayfa_getir(baslik)
        if mevcut is not None and not a.zorla:
            if mevcut.strip() == govde.strip():
                print(f"      aynı, dokunulmadı  {baslik}")
            else:
                print(f"      ATLANDI (sayfa var, içeriği farklı)  {baslik}")
            continue
        for deneme in range(4):
            ozet = "eser sahibi sayfası oluşturuldu" if baslik == KISI_BASLIK else OZET
            d = y18.istek({"action": "edit"},
                          {"title": baslik, "text": govde, "summary": ozet, "token": tok})
            if d.get("error", {}).get("code") != "ratelimited":
                break
            sure = y18.BEKLE * (deneme + 2)
            print(f"      hız sınırı — {sure:.0f} sn bekleniyor  {baslik}")
            time.sleep(sure)
        if d.get("edit", {}).get("result") == "Success":
            print(f"      yazıldı  {baslik}")
        else:
            print(f"      HATA  {baslik}: {d.get('error', d)}")
        time.sleep(y18.BEKLE)


if __name__ == "__main__":
    main()
