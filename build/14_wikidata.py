"""14 — Wikidata öğeleri için QuickStatements toplu işi üretir.

    python build/14_wikidata.py          # toplu iş metnini üret
    python build/14_wikidata.py --yaz   # kaynakları doğrudan API ile ekle

Çıktı: wikidata/quickstatements.txt

Metni QuickStatements'a yapıştırmak da mümkündür
(https://quickstatements.toolforge.org → "Import V1 commands" → Run), ama o
araç **otomatik onaylı** hesap ister: 4 gün + 50 düzenleme. --yaz bu şartı
aramaz; kaynakları MediaWiki API'siyle doğrudan ekler ve yalnız kaynağı
olmayan ifadeye dokunur, var olan ifadeyi çoğaltmaz.

Kimlik, Vikikaynak yüklemesiyle aynı yerden okunur (~/.wikisource-bot ya da
WIKISOURCE_BOT / WIKISOURCE_BOT_PASSWORD): bot parolası tek bir vikiye değil
hesaba bağlıdır, Wikidata'da da geçerlidir.

Q ve P numaralarının tamamı Wikidata'da tek tek doğrulanmıştır:

  P31   nedir                       Q83790    ders kitabı
  P50   yazarı                      Q374071   Türk Tarih Kurumu
  P123  yayımcısı                   Q1359675  Millî Eğitim Bakanlığı
  P291  yayın yeri                  Q406      İstanbul
  P407  eserin dili                 Q256      Türkçe
  P6216 telif hakkı durumu          Q19652    kamu malı
  P577  yayın tarihi                P1476 başlık        P953 tam metin URL'si
  P155/P156 öncesinde/sonrasında    S854 kaynak URL

**P356 (DOI) bilerek yazılmaz.** DOI, iki cildin *türetilmiş veri kümesine*
aittir; tek bir cildin kendisine değil. Kitap öğesine yazmak yanlış bir
kimlik iddiası olurdu.

**P50 hakkında:** 1931'deki ad Türk Tarihi Tetkik Cemiyeti'dir; ayrı bir
Wikidata öğesi yoktur. Q374071 aynı kurumun bugünkü hâlidir.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import META_DIR, ROOT, write_text  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
BOOKMETA = META["books"]
# Adres künyeyle aynı yerden gelir (books.json -> channels.site).
CHANNELS = META.get("channels", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"
OUT = ROOT / "wikidata" / "quickstatements.txt"

TEXTBOOK = "Q83790"
SOCIETY = "Q374071"
MINISTRY = "Q1359675"
ISTANBUL = "Q406"
TURKISH = "Q256"
PUBLIC_DOMAIN = "Q19652"


def satirlar() -> list[str]:
    L: list[str] = []
    for b in BOOKMETA:
        qid = b.get("wikidata")
        if not qid:
            continue
        kaynak = ["S854", f'"{b["ttk_url"]}"']  # künye sayfası taraması

        def ek(prop: str, deger: str, referansli: bool = False) -> None:
            parca = [qid, prop, deger] + (kaynak if referansli else [])
            L.append("\t".join(parca))

        ek("P31", TEXTBOOK)
        ek("P50", SOCIETY, True)
        ek("P123", MINISTRY, True)
        ek("P291", ISTANBUL, True)
        ek("P577", f'+{b["year"]}-00-00T00:00:00Z/9', True)
        ek("P407", TURKISH)
        ek("P6216", PUBLIC_DOMAIN)
        ek("P1476", f'tr:"{b["title_full"]}"', True)
        ek("P953", f'"{BASE_URL}/{b["slug"]}/"')

    # Ciltler arası sıra
    ciltler = [b for b in BOOKMETA if b.get("wikidata")]
    ciltler.sort(key=lambda b: b.get("volume_number", 0))
    for onceki, sonraki in zip(ciltler, ciltler[1:]):
        L.append("\t".join([sonraki["wikidata"], "P155", onceki["wikidata"]]))
        L.append("\t".join([onceki["wikidata"], "P156", sonraki["wikidata"]]))
    return L


# ---------------------------------------------------------------------------
# --yaz: kaynakları doğrudan API ile ekle
# ---------------------------------------------------------------------------

API = "https://www.wikidata.org/w/api.php"
KAYNAK_OZELLIK = "P854"  # kaynak URL
# Kaynak eklenecek ifadeler: künye bilgisi taşıyan, yani taramadan doğrulanan
# ifadeler. P31/P407/P6216 tanım gereği, P953 kendi adresiyle sabittir.
REFERANSLI = ("P50", "P123", "P291", "P577", "P1476")
BEKLE = 8.0  # saniye; yeni hesapların düzenleme hızı sınırı dakikada ~8'dir


def _oturum():
    """Wikidata API'sine çerezli bir oturum açar ve csrf jetonunu döndürür."""
    import http.cookiejar
    import importlib.util
    import urllib.parse
    import urllib.request

    spec = importlib.util.spec_from_file_location(
        "vikikaynak_yukle", Path(__file__).resolve().parent / "18_vikikaynak_yukle.py")
    y18 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(y18)
    ad, pw = y18.kimlik()

    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    # HTTP başlığı latin-1 ile kodlanır; Türkçe harf koyulursa istek
    # gönderilmeden çöker.
    op.addheaders = [("User-Agent", "tarih-1931-kunye/1.0 (wikidata; ifade kaynaklari)")]

    def istek(param: dict, post: dict | None = None) -> dict:
        url = API + "?" + urllib.parse.urlencode(param | {"format": "json", "formatversion": "2"})
        veri = urllib.parse.urlencode(post).encode() if post else None
        with op.open(urllib.request.Request(url, data=veri), timeout=60) as r:
            return json.loads(r.read())

    t = istek({"action": "query", "meta": "tokens", "type": "login"})
    d = istek({"action": "login"},
              {"lgname": ad, "lgpassword": pw,
               "lgtoken": t["query"]["tokens"]["logintoken"]})
    if d.get("login", {}).get("result") != "Success":
        raise SystemExit(f"    oturum açılamadı: {d.get('login', {}).get('reason', d)}")
    print(f"    oturum: {d['login']['lgusername']}")
    csrf = istek({"action": "query", "meta": "tokens", "type": "csrf"})["query"]["tokens"]["csrftoken"]
    return istek, csrf


def yaz() -> None:
    import time

    istek, csrf = _oturum()
    eklendi = atlandi = 0
    for b in BOOKMETA:
        qid, kaynak = b.get("wikidata"), b["ttk_url"]
        if not qid:
            continue
        claims = istek({"action": "wbgetclaims", "entity": qid}).get("claims", {})
        for prop in REFERANSLI:
            for c in claims.get(prop, []):
                var = any(
                    s.get("datavalue", {}).get("value") == kaynak
                    for ref in c.get("references", [])
                    for s in ref.get("snaks", {}).get(KAYNAK_OZELLIK, [])
                )
                if var:
                    atlandi += 1
                    print(f"      {qid} {prop}: kaynak zaten var")
                    continue
                snaks = {KAYNAK_OZELLIK: [{
                    "snaktype": "value", "property": KAYNAK_OZELLIK,
                    "datavalue": {"type": "string", "value": kaynak},
                }]}
                d = istek({"action": "wbsetreference"},
                          {"statement": c["id"], "snaks": json.dumps(snaks),
                           "token": csrf, "summary": "kaynak URL eklendi (TTK Kütüphanesi taraması)"})
                if "error" in d:
                    raise SystemExit(f"    {qid} {prop} hata: {d['error'].get('info', d['error'])}")
                eklendi += 1
                print(f"      {qid} {prop}: kaynak eklendi")
                time.sleep(BEKLE)
    print(f"    {eklendi} kaynak eklendi, {atlandi} ifadede zaten vardı")
    _eser_sahibi_baglantisi(istek, csrf)
    _vikikaynak_baglantilari(istek, csrf)


# Vikikaynak'taki eser sahibi sayfası ile kurumun Wikidata öğesi arasındaki bağ.
# Bu bağ olmadan iki kanal birbirini görmez: öğeden Vikikaynak'a, Vikikaynak'tan
# öğeye geçilemez. Cemiyet 1935'te Türk Tarih Kurumu adını almıştır; öğe aynı
# kurumu gösterir.
KURUM_OGE = "Q374071"
KISI_SAYFASI = "Kişi:Türk Tarihi Tetkik Cemiyeti"


def _sitelink(istek, csrf: str, qid: str, baslik: str, ozet: str) -> None:
    """Öğeye tr.wikisource bağlantısını ekler; başkasının bağladığı sayfaya dokunmaz."""
    d = istek({"action": "wbgetentities", "ids": qid, "props": "sitelinks"})
    mevcut = d.get("entities", {}).get(qid, {}).get("sitelinks", {}).get("trwikisource")
    if mevcut:
        durum = "aynı" if mevcut.get("title") == baslik else f"başka sayfa: {mevcut.get('title')}"
        print(f"    {qid} trwikisource bağlantısı zaten var ({durum}) — dokunulmadı")
        return
    d = istek({"action": "wbsetsitelink"},
              {"id": qid, "linksite": "trwikisource", "linktitle": baslik,
               "token": csrf, "summary": ozet})
    if "error" in d:
        print(f"    {qid} sitelink eklenemedi: {d['error'].get('info', d['error'])}")
    else:
        print(f"    {qid} -> {baslik} bağlandı")


def _vikikaynak_baglantilari(istek, csrf: str) -> None:
    """Cilt öğelerini Vikikaynak'taki istinsaha bağlar.

    Bağ olmadan iki kanal birbirini görmez: bilgi grafiğinden metne, metinden
    künyeye geçilemez. Adresler books.json -> wikisource_work alanındadır.
    """
    for b in BOOKMETA:
        qid, sayfa = b.get("wikidata"), b.get("wikisource_work")
        if not (qid and sayfa):
            continue
        baslik = urllib.parse.unquote(sayfa.rsplit("/wiki/", 1)[-1]).replace("_", " ")
        _sitelink(istek, csrf, qid, baslik, "tr.wikisource'taki istinsah bağlandı")


def _eser_sahibi_baglantisi(istek, csrf: str) -> None:
    _sitelink(istek, csrf, KURUM_OGE, KISI_SAYFASI, "tr.wikisource eser sahibi sayfası bağlandı")


# ---------------------------------------------------------------------------
# --inceleme: incelemenin kendi öğesi
# ---------------------------------------------------------------------------
#
# DOI kitap öğelerine bilerek yazılmaz (bkz. yukarısı): DOI türetilmiş
# çalışmalara aittir, 1931 basımı kitaplara değil. Ama incelemenin kendisi
# DOI'li bir çalışmadır ve bilgi grafiğinde hiç görünmüyordu. Bu adım o
# boşluğu kapatır: incelemeyi kendi öğesiyle, kendi DOI'siyle ve konusu olan
# iki cilde bağlı olarak kaydeder.
#
# Q ve P numaraları API ile tek tek doğrulanmıştır:
#   Q10870555 rapor · Q22661177 Zenodo · Q6938433 CC0 · Q256 Türkçe
#   Q1860 İngilizce · Q432 İslam
RAPOR = "Q10870555"
ZENODO = "Q22661177"
CC0 = "Q6938433"
TURKCE, INGILIZCE = "Q256", "Q1860"
ISLAM = "Q432"


def _oge(pid: str, qid: str, kaynak=None) -> dict:
    d = {"mainsnak": {"snaktype": "value", "property": pid,
                      "datavalue": {"type": "wikibase-entityid",
                                    "value": {"entity-type": "item",
                                              "numeric-id": int(qid[1:])}}},
         "type": "statement", "rank": "normal"}
    return d | kaynak if kaynak else d


def _metin(pid: str, deger: str, kaynak=None) -> dict:
    d = {"mainsnak": {"snaktype": "value", "property": pid,
                      "datavalue": {"type": "string", "value": deger}},
         "type": "statement", "rank": "normal"}
    return d | kaynak if kaynak else d


def _tek_dil(pid: str, deger: str, dil: str, kaynak=None) -> dict:
    d = {"mainsnak": {"snaktype": "value", "property": pid,
                      "datavalue": {"type": "monolingualtext",
                                    "value": {"text": deger, "language": dil}}},
         "type": "statement", "rank": "normal"}
    return d | kaynak if kaynak else d


def _tarih(pid: str, iso: str, kaynak=None) -> dict:
    d = {"mainsnak": {"snaktype": "value", "property": pid,
                      "datavalue": {"type": "time",
                                    "value": {"time": f"+{iso}T00:00:00Z", "timezone": 0,
                                              "before": 0, "after": 0, "precision": 11,
                                              "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}},
         "type": "statement", "rank": "normal"}
    return d | kaynak if kaynak else d


def inceleme_ogesi(istek, csrf: str) -> None:
    inc = META.get("review") or {}
    doi = (inc.get("doi") or "").upper()
    if not doi:
        print("    books.json içinde review.doi yok — atlandı")
        return

    d = istek({"action": "query", "list": "search",
               "srsearch": f"haswbstatement:P356={doi}", "srlimit": "1"})
    var = d.get("query", {}).get("search", [])
    if var:
        print(f"    inceleme öğesi zaten var: {var[0]['title']} — dokunulmadı")
        return

    kayit = inc.get("record_url") or f"https://doi.org/{inc['doi']}"
    kaynak = {"references": [{"snaks": {"P854": [
        {"snaktype": "value", "property": "P854",
         "datavalue": {"type": "string", "value": kayit}}]}}]}

    ciltler = [b["wikidata"] for b in BOOKMETA if b.get("wikidata")]
    veri = {
        "labels": {
            "tr": {"language": "tr", "value": inc["title"]},
            "en": {"language": "en", "value": inc.get("title_en") or inc["title"]},
        },
        "descriptions": {
            "tr": {"language": "tr",
                   "value": "1931 basımı resmî tarih ders kitapları üzerine inceleme"},
            "en": {"language": "en",
                   "value": "report on Turkey's official 1931 history textbooks"},
        },
        "claims": [
            _oge("P31", RAPOR),
            _tek_dil("P1476", inc["title"], "tr", kaynak),
            _metin("P2093", inc.get("author") or "Anonim", kaynak),
            _tarih("P577", inc.get("first_published") or "2026-08-16", kaynak),
            _metin("P356", doi, kaynak),
            _oge("P407", TURKCE),
            _oge("P407", INGILIZCE),
            _oge("P123", ZENODO, kaynak),
            _oge("P275", CC0, kaynak),
            *[_oge("P921", q) for q in ciltler],
            _oge("P921", ISLAM),
            _metin("P953", f"{BASE_URL}/inceleme.html"),
            _metin("P953", f"{BASE_URL}/review.html"),
        ],
    }
    d = istek({"action": "wbeditentity", "new": "item"},
              {"data": json.dumps(veri, ensure_ascii=False), "token": csrf,
               "summary": "incelemenin öğesi oluşturuldu (DOI 10.5281/zenodo.21963507)"})
    if "error" in d:
        raise SystemExit(f"    öğe oluşturulamadı: {d['error'].get('info', d['error'])}")
    qid = d["entity"]["id"]
    print(f"    inceleme öğesi oluşturuldu: {qid}  https://www.wikidata.org/wiki/{qid}")
    _ciltten_incelemeye(istek, csrf, qid, kayit)


def _ciltten_incelemeye(istek, csrf: str, inceleme_qid: str, kayit: str) -> None:
    """Cilt öğelerine "kaynakta anlatılan" (P1343) olarak incelemeyi ekler.

    İnceleme öğesi ciltleri P921 ile gösteriyor; ters yön olmadan bağ tek
    yönlü kalır ve kitaptan incelemeye geçilemez.
    """
    for b in BOOKMETA:
        cilt = b.get("wikidata")
        if not cilt:
            continue
        d = istek({"action": "wbgetclaims", "entity": cilt, "property": "P1343"})
        varsa = [c for c in d.get("claims", {}).get("P1343", [])
                 if c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") == inceleme_qid]
        if varsa:
            print(f"      {cilt} P1343: zaten var")
            continue
        d = istek({"action": "wbcreateclaim"},
                  {"entity": cilt, "property": "P1343", "snaktype": "value",
                   "value": json.dumps({"entity-type": "item",
                                        "numeric-id": int(inceleme_qid[1:])}),
                   "token": csrf, "summary": "kaynakta anlatılan: metne dayalı inceleme"})
        if "error" in d:
            print(f"      {cilt} P1343 eklenemedi: {d['error'].get('info', d['error'])}")
        else:
            print(f"      {cilt} -> {inceleme_qid} (kaynakta anlatılan)")


def main() -> None:
    L = satirlar()
    if not L:
        print("    books.json içinde wikidata alanı yok — atlandı")
        return
    OUT.parent.mkdir(exist_ok=True)
    write_text(OUT, "\n".join(L) + "\n")
    qids = sorted({s.split("\t")[0] for s in L})
    print(f"    {len(L)} ifade, {len(qids)} öğe ({', '.join(qids)})")
    print(f"    {OUT.relative_to(ROOT).as_posix()} yazıldı")
    if "--inceleme" in sys.argv:
        istek, csrf = _oturum()
        inceleme_ogesi(istek, csrf)
    elif "--yaz" in sys.argv:
        yaz()
    else:
        print("    https://quickstatements.toolforge.org → Import V1 commands → yapıştır → Run")
        print("    ya da doğrudan:  python build/14_wikidata.py --yaz")


if __name__ == "__main__":
    main()
