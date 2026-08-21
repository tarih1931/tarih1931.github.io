"""18 — İstinsah edilmiş sayfaları Vikikaynak'a "Sayfa:" ad alanına yazar.

    python build/18_vikikaynak_yukle.py                 # ne yapılacağını göster, yazma
    python build/18_vikikaynak_yukle.py --yaz           # yaz
    python build/18_vikikaynak_yukle.py --yaz --sayfa 106,107

Metinler `vikikaynak/<bolum>/<commons>.txt` altındadır ve taranmış asılla
karşılaştırılarak elle istinsah edilmiştir (bkz. 12_vikikaynak.py). Bu adım
onları olduğu gibi yükler; metne dokunmaz.

**Kimlik.** Betik parola ne ister ne saklar; hazır duranı okur. Sıra:

  1. https://tr.wikisource.org/wiki/Special:BotPasswords
  2. Yeni bot adı: tarih-1931-istinsah
     İzinler: "Var olan sayfaları düzenle" ve "Yeni sayfalar oluştur"
  3. "Oluştur" → kullanıcı adı ve parola **bir kez** gösterilir
  4. İki satır hâlinde şu dosyaya yazın (başka bir şey olmasın):
         C:\\Users\\<kullanıcı>\\.wikisource-bot
             Kullanici@tarih-1931-istinsah
             abc123...   (32 karakterlik bot parolası, ayraçsız)
     ya da WIKISOURCE_BOT / WIKISOURCE_BOT_PASSWORD ortam değişkenlerine koyun.

Parola hiçbir yerde ekrana basılmaz, günlüğe yazılmaz, depoya girmez.

**Kalite kademesi.** Sayfa: ad alanında kalite, sayfa metninin en başındaki
<pagequality> etiketinde durur. Betik onu seviye 3 (İstinsah) olarak ekler;
dosyalarımızda bu etiket yoktur, çünkü kademe metnin bir parçası değildir.

**Çakışma koruması.** Sayfa daha önce başkasınca düzenlenmişse ve içeriği
bizimkinden farklıysa, --zorla verilmedikçe atlanır: başkasının emeğini
sessizce silmektense durup bildirmek yeğdir. Zaten aynıysa dokunulmaz.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

API = "https://tr.wikisource.org/w/api.php"
KADEME = 3  # İstinsah
BEKLE = 10.0  # saniye; yeni hesapların düzenleme hızı sınırı dakikada ~8'dir

KITAPLAR = {
    "beser-tarihine-giris": ("Tarih I Tarihtenevelki Zamanlar ve Eski Zamanlar.pdf", 33),
    "islam-tarihi": ("Tarih II Ortazamanlar.pdf", 22),
}

OZET = ("taranmış asılla karşılaştırılarak istinsah edildi "
        "(kaynak: 10.5281/zenodo.21963507)")

_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))
_op.addheaders = [("User-Agent", "tarih-1931-istinsah/1.0 (tr.wikisource; toplu istinsah)")]


def _ayikla(v: str) -> str:
    """Yer tutucu ayracı, tırnak ve boşlukları temizler."""
    v = v.strip()
    while len(v) >= 2 and ((v[0], v[-1]) in {("<", ">"), ('"', '"'), ("'", "'")}):
        v = v[1:-1].strip()
    return v.replace(" ", "")


def kimlik() -> tuple[str, str]:
    ad = os.environ.get("WIKISOURCE_BOT", "")
    pw = os.environ.get("WIKISOURCE_BOT_PASSWORD", "")
    if not (ad and pw):
        d = Path(os.path.expanduser("~")) / ".wikisource-bot"
        if d.exists():
            # utf-8-sig: Not Defteri dosyayı BOM ile kaydeder, BOM kullanıcı
            # adının başına yapışır ve oturum sessizce reddedilir.
            satir = [s.strip() for s in d.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
            if len(satir) >= 2:
                ad, pw = satir[0], satir[1]
    # Talimattaki <...> yer tutucusu, tırnak ya da okunurluk için konmuş
    # boşluklar değeri bozar. Bot parolası [a-z0-9]{32} olduğundan bunları
    # atmak güvenlidir; kullanıcı adında da ayraç aranmaz.
    ad, pw = (_ayikla(ad), _ayikla(pw))
    if not (ad and pw):
        raise SystemExit(
            "    Vikikaynak bot kimliği bulunamadı.\n"
            "    ~/.wikisource-bot dosyasına iki satır yazın (kullanıcı adı, parola)\n"
            "    ya da WIKISOURCE_BOT / WIKISOURCE_BOT_PASSWORD kullanın.\n"
            "    Bot parolası: https://tr.wikisource.org/wiki/Special:BotPasswords"
        )
    return ad, pw


def istek(param: dict, post: dict | None = None) -> dict:
    url = API + "?" + urllib.parse.urlencode(param | {"format": "json", "formatversion": "2"})
    veri = urllib.parse.urlencode(post).encode() if post else None
    try:
        with _op.open(urllib.request.Request(url, data=veri), timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"    API hatası {e.code}: {e.read().decode(errors='replace')[:300]}")


def oturum_ac() -> str:
    ad, pw = kimlik()
    t = istek({"action": "query", "meta": "tokens", "type": "login"})
    d = istek({"action": "login"},
              {"lgname": ad, "lgpassword": pw,
               "lgtoken": t["query"]["tokens"]["logintoken"]})
    if d.get("login", {}).get("result") != "Success":
        # Sebep basılır ama parola asla basılmaz.
        raise SystemExit(
            f"    oturum açılamadı: {d.get('login', {}).get('reason', d)}\n"
            "    MediaWiki bu iletiyi biçim hatasında da, bot hiç yokken de verir.\n"
            "    Special:BotPasswords listesinde botun adını ve dosyadaki '@' sonrasını\n"
            "    harfi harfine karşılaştırın; şüphe varsa parolayı sıfırlayıp yeniden yazın."
        )
    kullanici = d["login"]["lgusername"]
    print(f"    oturum: {kullanici}")
    return kullanici


def sayfa_getir(baslik: str) -> str | None:
    d = istek({"action": "query", "prop": "revisions", "rvprop": "content",
               "rvslots": "main", "titles": baslik})
    p = d["query"]["pages"][0]
    if p.get("missing"):
        return None
    return p["revisions"][0]["slots"]["main"]["content"]


def govde(icerik: str, kullanici: str) -> str:
    """Kalite etiketini ilk <noinclude> içine, en başa yerleştirir."""
    etiket = f'<pagequality level="{KADEME}" user="{kullanici}" />'
    if icerik.startswith("<noinclude>"):
        return icerik.replace("<noinclude>", f"<noinclude>{etiket}", 1)
    return f"<noinclude>{etiket}</noinclude>" + icerik


def ozdes(a: str, b: str) -> bool:
    """Kaydedilen metinle bizimkini karşılaştırır.

    ProofreadPage sayfayı üstbilgi/gövde/altbilgi diye üçe ayırıp yeniden
    diziyor; bu sırada gövde ile altbilgi arasındaki satır sonu düşüyor.
    Kayıp değil, wiki'nin kanonik biçimi — hesaba katılmazsa kendi
    yüklediğimiz sayfa bir sonraki koşuda "değişmiş" görünür ve atlanır.
    """
    def kir(s: str) -> str:
        s = re.sub(r'<pagequality[^>]*/>', "", s)
        return re.sub(r"\n(?=<noinclude>)", "", s).strip()
    return kir(a) == kir(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="gerçekten yaz (yoksa yalnız rapor)")
    ap.add_argument("--zorla", action="store_true",
                    help="içeriği farklı olan mevcut sayfaların da üzerine yaz")
    ap.add_argument("--sayfa", default="", help="yalnız bu commons sayfaları (virgülle)")
    a = ap.parse_args()
    secili = {int(x) for x in a.sayfa.split(",") if x.strip()} if a.sayfa else None

    isler = []
    for slug, (dosya, _ofs) in KITAPLAR.items():
        for p in sorted((ROOT / "vikikaynak" / slug).glob("*.txt")):
            n = int(p.stem)
            if secili and n not in secili:
                continue
            isler.append((f"Sayfa:{dosya}/{n}", p, n))

    if not a.yaz:
        print(f"    {len(isler)} sayfa yazılacak (kuru çalıştırma — hiçbir şey yazılmadı)")
        for baslik, p, _ in isler:
            print(f"      {baslik}  <- {p.relative_to(ROOT)}")
        print("\n    yazmak için:  python build/18_vikikaynak_yukle.py --yaz")
        return

    kullanici = oturum_ac()
    tok = istek({"action": "query", "meta": "tokens", "type": "csrf"})["query"]["tokens"]["csrftoken"]

    yazildi = atlandi = ayni = 0
    for baslik, p, n in isler:
        yeni = govde(p.read_text(encoding="utf-8"), kullanici)
        mevcut = sayfa_getir(baslik)
        if mevcut is not None:
            if ozdes(mevcut, yeni):
                print(f"      aynı, dokunulmadı  {baslik}")
                ayni += 1
                continue
            if not a.zorla and not re.search(r'pagequality level="[01]"', mevcut):
                print(f"      ATLANDI (başkası düzenlemiş, kademe >1)  {baslik}")
                atlandi += 1
                continue
        # MediaWiki'de mantıksal parametreler VARLIKLARIYLA doğrudur: "nocreate=0"
        # yazmak da "yeni sayfa açma" demektir ve olmayan sayfada missingtitle
        # verir. O yüzden hiç gönderilmiyor.
        #
        # bot=1 de gönderilmiyor: hesap işaretli bir bot değil ve düzenlemelerin
        # Son değişiklikler'de görünmesi doğrusu — devriyeden gizlemek olmaz.
        # Yeni hesapların düzenleme hızı sınırlıdır (ratelimited). Sınıra
        # girince beklemek yeterli; hata sayıp geçmek 8 sayfayı yarıda
        # bırakıyordu.
        for deneme in range(6):
            d = istek({"action": "edit"},
                      {"title": baslik, "text": yeni, "summary": OZET, "token": tok})
            if d.get("edit", {}).get("result") == "Success":
                break
            if d.get("error", {}).get("code") == "ratelimited":
                sure = BEKLE * (deneme + 2)
                print(f"      hız sınırı — {sure:.0f} sn bekleniyor  {baslik}")
                time.sleep(sure)
                continue
            break
        if d.get("edit", {}).get("result") != "Success":
            print(f"      HATA  {baslik}: {d.get('error', d)}")
            atlandi += 1
        else:
            print(f"      yazıldı  {baslik}")
            yazildi += 1
        time.sleep(BEKLE)

    print(f"\n    {yazildi} yazıldı, {ayni} zaten aynı, {atlandi} atlandı")


if __name__ == "__main__":
    main()
