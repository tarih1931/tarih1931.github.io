"""17 — İncelemenin yayın paketini Zenodo'ya taslak kayıt olarak yükler.

    python build/17_zenodo_yukle.py                    # yeni kayıt taslağı aç
    python build/17_zenodo_yukle.py --yeni-surum 123   # var olan kaydın yeni sürümü
    python build/17_zenodo_yukle.py --yayimla          # taslağı yayımla (DOI kesinleşir)

Korpusun kendi kaydı da buradan sürdürülür:

    python build/17_zenodo_yukle.py --korpus --yeni-surum 22035196 --etiket v1.3.0

**Neden GitHub tümleşiği kullanılmıyor.** Zenodo'nun GitHub anahtarı kayıtları
depo başına tutar ve bir depo için ilk release'te yeni bir concept DOI üretir;
var olan bir kayda bağlanamaz. Depo 21.08.2026'da taşınınca (ad ve sahip
değişti, üstelik silinip yeniden açıldı) o yol korpusun kimliğini ikiye
bölecekti. Zip'i burada üretip jetonla yüklemek `10.5281/zenodo.21956339`
concept DOI'sini yaşatır; release'ler de saf GitHub kaydına döner ve sıraları
önemsizleşir.

Yayımlanmış bir kayıt güncellenecekse **daima --yeni-surum** kullanın. Yeni bir
kayıt açmak ayrı bir concept DOI üretir ve çalışmanın kimliğini ikiye böler.

Önce paketi üretin:  python build/16_inceleme_yayin.py

**Jeton.** Betik jetonu ne ister ne saklar; hazır duranı okur. Sıra:

  1. https://zenodo.org/account/settings/applications/tokens/new/
  2. Ad: tarih-1931-yukleme   Yetkiler: deposit:write ve deposit:actions
  3. "Create" → jeton **bir kez** gösterilir, kopyalayın
  4. Tek satır hâlinde şu dosyaya yazın (başka bir şey olmasın):
         C:\\Users\\<kullanıcı>\\.zenodo-token
     ya da ZENODO_TOKEN ortam değişkenine koyun.

Jeton hiçbir yerde ekrana basılmaz, günlüğe yazılmaz, depoya girmez.

**Yayımlama ayrı adımdır.** Zenodo'da yayımlamak geri alınamaz: DOI kesinleşir
ve dosyalar bir daha değiştirilemez. Bu yüzden betik varsayılan olarak yalnız
taslak bırakır; taslağı gözden geçirip ya arayüzden ya da --yayimla ile
yayımlarsınız.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

API = "https://zenodo.org/api"
PAKET = ROOT / "inceleme" / "yayin"
# Ekler kaydın parçasıdır: ayrı bir belgedir ama aynı DOI ve aynı sürüm altındadır.
YUKLENECEK = [
    "inceleme-tr.md", "inceleme-oz-tr.md", "inceleme-en.md",
    "inceleme-ekler-tr.md", "inceleme-ekler-en.md",
    "bulgular.jsonl",
    "inceleme-tr.pdf", "inceleme-oz-tr.pdf", "inceleme-en.pdf",
    "inceleme-ekler-tr.pdf", "inceleme-ekler-en.pdf",
]

# Korpus zip'i depo ağacının DIŞINA üretilir; 13_huggingface.py ile aynı
# gerekçe: üretilen paket çalışma ağacında durursa yanlışlıkla depoya girer.
KORPUS_KUNYE = ROOT / "metadata" / "zenodo.json"
KORPUS_CIKTI = ROOT.parent / f"{ROOT.name}-zenodo"


def jeton() -> str:
    t = os.environ.get("ZENODO_TOKEN")
    if not t:
        dosya = Path(os.path.expanduser("~")) / ".zenodo-token"
        if dosya.exists():
            t = dosya.read_text(encoding="utf-8").strip()
    if not t:
        raise SystemExit(
            "    Zenodo jetonu bulunamadı.\n"
            "    ZENODO_TOKEN ortam değişkenine koyun ya da ~/.zenodo-token dosyasına yazın.\n"
            "    Jeton: https://zenodo.org/account/settings/applications/tokens/new/\n"
            "    Gereken yetkiler: deposit:write, deposit:actions"
        )
    return t


def istek(yol: str, yontem: str = "GET", govde: dict | None = None, tam: str = "") -> dict:
    url = tam or f"{API}{yol}"
    veri = json.dumps(govde).encode() if govde is not None else None
    r = urllib.request.Request(url, data=veri, method=yontem)
    r.add_header("Authorization", f"Bearer {jeton()}")
    if veri:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=120) as y:
            ham = y.read()
            return json.loads(ham) if ham else {}
    except urllib.error.HTTPError as e:
        detay = e.read().decode(errors="replace")[:500]
        raise SystemExit(f"    Zenodo hatası {e.code}: {detay}")


def dosya_yukle(bucket: str, yol: Path) -> None:
    r = urllib.request.Request(f"{bucket}/{yol.name}", data=yol.read_bytes(), method="PUT")
    r.add_header("Authorization", f"Bearer {jeton()}")
    # Zenodo'nun bucket uç noktası başka bir tür kabul etmiyor: application/pdf
    # gönderildiğinde 415 döner.
    r.add_header("Content-Type", "application/octet-stream")
    try:
        with urllib.request.urlopen(r, timeout=300) as y:
            y.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"    {yol.name} yüklenemedi ({e.code}): {e.read().decode(errors='replace')[:300]}")


def olcu(yol: Path) -> str:
    n = yol.stat().st_size
    return f"{n / 1048576:7.2f} MB" if n >= 1048576 else f"{n / 1024:7.1f} KB"


def korpus_paketi(etiket: str) -> tuple[dict, list[Path]]:
    """Etiketin kaynak zip'ini üretir; künyeyi metadata/zenodo.json'dan alır.

    `git archive` yalnız **izlenen** dosyaları paketler. PDF/ altındaki telifli
    modern taramalar depoda olmadığı için zip'e girmeleri mümkün değildir; bu,
    13_huggingface.py'deki beyaz liste korumasının buradaki karşılığıdır.
    """
    import subprocess

    if not etiket:
        raise SystemExit("    --korpus için --etiket gerekir (ör. --etiket v1.3.0)")
    var = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{etiket}^{{commit}}"],
                         cwd=ROOT, capture_output=True, text=True)
    if var.returncode != 0:
        raise SystemExit(f"    etiket yok: {etiket}  (önce: git tag {etiket})")

    kunye = json.loads(KORPUS_KUNYE.read_text(encoding="utf-8"))
    surum = json.loads((ROOT / "metadata" / "books.json").read_text(encoding="utf-8"))
    beklenen = (surum.get("collection") or {}).get("version") or ""
    if beklenen and f"v{beklenen}" != etiket:
        raise SystemExit(
            f"    künye ile etiket ayrışıyor: collection.version={beklenen}, "
            f"etiket={etiket}\n"
            "    İkisi aynı olmalı; künyeler sürüm numarasını books.json'dan okur."
        )
    kunye["version"] = etiket

    # Paket adı yerel klasör adından değil depo adından gelir: klon başka bir
    # adla açılırsa arşivin adı değişmesin.
    depo = ((surum.get("channels") or {}).get("repository") or "").rstrip("/")
    ad = depo.rsplit("/", 1)[-1] or ROOT.name

    KORPUS_CIKTI.mkdir(parents=True, exist_ok=True)
    zip_yolu = KORPUS_CIKTI / f"{ad}-{etiket}.zip"
    subprocess.run(
        ["git", "archive", "--format=zip", f"--prefix={ad}-{etiket}/",
         "-o", str(zip_yolu), etiket],
        cwd=ROOT, check=True)
    print(f"    korpus zip'i üretildi: {zip_yolu.name}  {olcu(zip_yolu)}")
    print(f"    klasör: {KORPUS_CIKTI}   (depo ağacının dışında)")
    return kunye, [zip_yolu]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yayimla", action="store_true", help="taslağı yayımla — geri alınamaz")
    ap.add_argument("--taslak", default="", help="var olan taslağın kimliği (yeniden yüklemek için)")
    ap.add_argument(
        "--yeni-surum",
        default="",
        help="yayımlanmış kaydın kimliği; o kaydın YENİ SÜRÜMÜ açılır (concept DOI korunur)",
    )
    ap.add_argument(
        "--korpus",
        action="store_true",
        help="incelemeyi değil korpusun kaydını sürdür (etiketin kaynak zip'i)",
    )
    ap.add_argument("--etiket", default="", help="--korpus ile: paketlenecek git etiketi")
    ap.add_argument(
        "--kunye-guncelle",
        default="",
        help="yayımlanmış kaydın künyesini düzeltir; dosyalara ve DOI'ye dokunmaz",
    )
    args = ap.parse_args()

    if args.kunye_guncelle:
        # Zenodo yayımlanmış kaydın künyesini değiştirmeye izin verir; dosyalar
        # ve DOI sabit kalır. Yeni sürüm açmaya gerek yoktur.
        rid = args.kunye_guncelle
        istek(f"/deposit/depositions/{rid}/actions/edit", "POST")
        kunye = json.loads((PAKET / "zenodo.json").read_text(encoding="utf-8"))
        istek(f"/deposit/depositions/{rid}", "PUT", {"metadata": kunye})
        son = istek(f"/deposit/depositions/{rid}/actions/publish", "POST")
        print(f"    künye güncellendi: {rid}  DOI {son.get('doi')} (değişmedi)")
        print(f"    {son.get('links', {}).get('record_html', '')}")
        return

    if args.yayimla and args.taslak:
        # Betiğin kendi yönergesi bu: "--taslak <id> --yayimla". Buraya paket
        # seçimi karışmamalı. 21.08.2026'da karıştı: korpus taslağı bu komutla
        # yayımlanınca betik incelemenin paketini varsayıp beş dosyayı oraya
        # yükledi ve künyeyi incelemeninkiyle değiştirdi. Künye sonradan
        # düzeltildi ama dosyalar kalıcı — Zenodo yayımlanmış kaydın kovasını
        # kilitler. Gözden geçirilmiş taslak yalnız yayımlanır, yeniden
        # yüklenmez; içeriği değiştirmek isteyen taslağa ayrıca yükleme yapar.
        son = istek(f"/deposit/depositions/{args.taslak}/actions/publish", "POST")
        print(f"    YAYIMLANDI  DOI: {son.get('doi')}")
        print(f"    {son.get('links', {}).get('record_html')}")
        return

    if args.korpus:
        # Korpusun kimliği tektir. --yeni-surum olmadan çalıştırılırsa betik
        # aşağıda yeni bir kayıt açar ve korpus ikinci bir concept DOI kazanır;
        # bu yolu kapatmak için bu kip zaten var.
        if not (args.yeni_surum or args.taslak):
            raise SystemExit(
                "    --korpus, --yeni-surum ile kullanılır: yeni kayıt açmak korpusun\n"
                "    kimliğini ikiye böler. Son yayımlanmış sürüm 22035196 ise:\n"
                "      python build/17_zenodo_yukle.py --korpus --yeni-surum 22035196 --etiket vX.Y.Z"
            )
        kunye, yuklenecek = korpus_paketi(args.etiket)
    else:
        kunye_yolu = PAKET / "zenodo.json"
        if not kunye_yolu.exists():
            raise SystemExit("    paket yok — önce:  python build/16_inceleme_yayin.py")
        kunye = json.loads(kunye_yolu.read_text(encoding="utf-8"))

        eksik = [f for f in YUKLENECEK if not (PAKET / f).exists()]
        if eksik:
            raise SystemExit(f"    pakette eksik dosya: {eksik}")
        yuklenecek = [PAKET / f for f in YUKLENECEK]

    if args.yeni_surum:
        # Yeni sürüm, kaydın kimliğini korur: concept DOI aynı kalır, sürüm DOI
        # değişir. Taslak, önceki sürümün dosyalarıyla açılır; onlar silinmezse
        # eski ve yeni dosyalar yan yana kalır.
        ust = istek(f"/deposit/depositions/{args.yeni_surum}/actions/newversion", "POST")
        dep = istek("", tam=ust["links"]["latest_draft"])
        print(f"    yeni sürüm taslağı: {dep['id']}  (concept korunur)")
        for f in dep.get("files", []):
            istek(f"/deposit/depositions/{dep['id']}/files/{f['id']}", "DELETE")
            print(f"      devralınan dosya silindi  {f['filename']}")
    elif args.taslak:
        dep = istek(f"/deposit/depositions/{args.taslak}")
        print(f"    var olan taslak: {dep['id']}")
    else:
        dep = istek("/deposit/depositions", "POST", {})
        print(f"    taslak oluşturuldu: {dep['id']}")

    bucket = dep["links"]["bucket"]
    # Taslakta aynı içerikle duran dosya yeniden gönderilmez. Zenodo zaman zaman
    # 504 veriyor ve yükleme yarıda kalıyor; --taslak ile devam edildiğinde
    # kalanı yüklemek yeter. Ölçüt boyut DEĞİL md5'tir: yeni sürüm taslağı önceki
    # sürümün dosyalarını devralıyor ve PDF'ler yalnız kapak tarihinde ayrıldığında
    # boyut aynı kalabiliyor — boyuta bakan bir denetim eski nüshayı yayımlatırdı.
    duran = {f["filename"]: (f.get("checksum") or "").replace("md5:", "")
             for f in dep.get("files", [])}
    for yol in yuklenecek:
        if duran.get(yol.name) == hashlib.md5(yol.read_bytes()).hexdigest():
            print(f"      duruyor   {yol.name:24} {olcu(yol)}")
            continue
        dosya_yukle(bucket, yol)
        print(f"      yüklendi  {yol.name:24} {olcu(yol)}")

    dep = istek(f"/deposit/depositions/{dep['id']}", "PUT", {"metadata": kunye})
    print(f"    künye yazıldı: {kunye['title'][:60]}…")

    if args.yayimla:
        son = istek(f"/deposit/depositions/{dep['id']}/actions/publish", "POST")
        print(f"    YAYIMLANDI  DOI: {son.get('doi')}")
        print(f"    {son.get('links', {}).get('record_html')}")
    else:
        print()
        print(f"    Taslak hazır, HENÜZ YAYIMLANMADI:")
        print(f"      {dep['links'].get('html')}")
        print("    Gözden geçirin; yayımlamak için arayüzdeki Publish düğmesi ya da:")
        print(f"      python build/17_zenodo_yukle.py --taslak {dep['id']} --yayimla")


if __name__ == "__main__":
    main()
