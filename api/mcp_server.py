"""Tarih Ders Kitapları (1931) — MCP sunucusu.

Bu sunucu, Claude / ChatGPT / diğer ajanların korpusu *doğrudan* sorgulamasını
sağlar: model metni tahmin etmek yerine sayfayı gerçekten okur ve doğru sayfa
numarasıyla alıntı yapar.

Kurulum:
    pip install "mcp[cli]"

Claude Desktop / Claude Code yapılandırmasına eklemek için:

    {
      "mcpServers": {
        "tarih-1931": {
          "command": "python",
          "args": ["MUTLAK/YOL/api/mcp_server.py"]
        }
      }
    }
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "MCP paketi bulunamadı. Kurmak için:  pip install \"mcp[cli]\""
    ) from exc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
META = json.loads((ROOT / "metadata" / "books.json").read_text(encoding="utf-8"))
BOOKMETA = {b["slug"]: b for b in META["books"]}

FOLD = str.maketrans("âÂîÎûÛİIıÜüÖöÇçŞşĞğ", "aaiiuuiiiuuooccssgg")


def fold(s: str) -> str:
    return s.translate(FOLD).lower()


@lru_cache(maxsize=1)
def pages() -> list[dict]:
    rows = []
    for slug in BOOKMETA:
        p = DATA / slug / "pages.jsonl"
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    r["_f"] = fold(r.get("text", ""))
                    rows.append(r)
    return rows


@lru_cache(maxsize=1)
def concordance() -> list[dict]:
    p = ROOT / "thematic" / "din-konkordans.jsonl"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


mcp = FastMCP("tarih-1931")


@mcp.tool()
def kitaplari_listele() -> str:
    """1931 basımı resmî lise Tarih ders kitaplarının listesini ve künyelerini verir."""
    out = []
    for slug, bm in BOOKMETA.items():
        rows = [r for r in pages() if r["book"] == slug]
        nums = [r["printed_page"] for r in rows if r.get("printed_page")]
        out.append(
            {
                "slug": slug,
                "baslik": bm["title_full"],
                "yil": bm["year"],
                "yayinci": bm["publisher"],
                "yer": bm["place"],
                "onay": bm["approval"],
                "sayfa_araligi": [min(nums), max(nums)] if nums else None,
                "kaynak_tarama": bm["ttk_url"],
            }
        )
    return json.dumps(
        {"kurumsal_yazar": META["collection"]["corporate_author"], "kitaplar": out},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def sayfa_getir(kitap: str, sayfa: int) -> str:
    """Belirli bir basılı sayfanın tam metnini künyesiyle döner.

    Args:
        kitap: 'tarih-1-1931' veya 'tarih-2-1931'
        sayfa: kitapta basılı sayfa numarası
    """
    for r in pages():
        if r["book"] == kitap and r.get("printed_page") == sayfa:
            return json.dumps(
                {
                    "kunye": r["citation"],
                    "sayfa_kimligi": r["page_id"],
                    "bolum": r.get("running_head"),
                    "numara_guveni": r.get("page_confidence"),
                    "tarama_referansi": r["scan_ref"],
                    "metin": r["text"],
                    "uyari": "Metin düzeltilmemiş OCR çıktısıdır.",
                },
                ensure_ascii=False,
                indent=2,
            )
    return json.dumps({"hata": f"{kitap} içinde {sayfa}. sayfa bulunamadı"}, ensure_ascii=False)


@mcp.tool()
def ara(sorgu: str, kitap: str = "", limit: int = 15) -> str:
    """Kitaplarda tam metin araması yapar (Türkçe aksan ve büyük/küçük harf duyarsız).

    Args:
        sorgu: aranacak kelime veya ifade
        kitap: isteğe bağlı; 'tarih-1-1931' veya 'tarih-2-1931'
        limit: en fazla kaç sonuç döneceği
    """
    ft = fold(sorgu)
    res = []
    for r in pages():
        if kitap and r["book"] != kitap:
            continue
        i = r["_f"].find(ft)
        if i < 0:
            continue
        s = max(0, i - 180)
        res.append(
            {
                "kunye": r["citation"],
                "sayfa_kimligi": r["page_id"],
                "bolum": r.get("running_head"),
                "gecis_sayisi": r["_f"].count(ft),
                "alinti": "…" + " ".join(r["text"][s : i + 300].split()) + "…",
            }
        )
        if len(res) >= limit:
            break
    return json.dumps({"sorgu": sorgu, "bulunan": len(res), "sonuclar": res}, ensure_ascii=False, indent=2)


@mcp.tool()
def din_konkordansi(tema: str = "", kitap: str = "", limit: int = 40) -> str:
    """Din ve inanç konulu pasajların kavram dizinini sorgular.

    Args:
        tema: din-genel | dinin-mensei | islam | hiristiyanlik | musevilik |
              diger-dinler | taassup-ve-akil | laiklik-ve-devlet  (boş = hepsi)
        kitap: isteğe bağlı cilt kimliği
        limit: en fazla kaç pasaj döneceği
    """
    rows = concordance()
    temalar = sorted({r["theme"] for r in rows})
    if tema:
        rows = [r for r in rows if r["theme"] == tema]
    if kitap:
        rows = [r for r in rows if r["book"] == kitap]
    return json.dumps(
        {
            "mevcut_temalar": temalar,
            "uyari": "Mekanik anahtar kelime eşleşmesidir; yorum içermez, yanlış pozitif olabilir.",
            "bulunan": len(rows),
            "pasajlar": [
                {
                    "kunye": r["citation"],
                    "tema": r["theme"],
                    "terimler": r["terms"],
                    "cumle": r["sentence"],
                    "onceki": r["context_before"],
                    "sonraki": r["context_after"],
                }
                for r in rows[:limit]
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def bolum_haritasi(kitap: str) -> str:
    """Bir cildin bölüm başlıklarını ve sayfa aralıklarını döner."""
    p = DATA / kitap / "structure.json"
    if not p.exists():
        return json.dumps({"hata": f"{kitap} bulunamadı"}, ensure_ascii=False)
    return p.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def findings() -> list[dict]:
    p = ROOT / "inceleme" / "bulgular.jsonl"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


@mcp.tool()
def dogrulanmis_sayfalar() -> str:
    """Elle düzeltilmiş sayfaların listesi.

    Korpusun tamamı ham OCR'dır; bu sayfalar taranmış aslıyla karşılaştırılarak
    düzeltilmiştir. Alıntı yapılacaksa bunlar tercih edilmelidir."""
    rows = [r for r in pages() if r.get("text_source") == "corrected"]
    rows.sort(key=lambda r: (r["book"], r.get("printed_page") or 0))
    return json.dumps(
        {
            "aciklama": "Taranmış aslıyla karşılaştırılarak elle düzeltilmiş sayfalar. "
            "Ham OCR metni her kayıtta text_ocr alanında saklanır.",
            "sayfa_sayisi": len(rows),
            "sayfalar": [
                {
                    "kitap": r["book"],
                    "basili_sayfa": r.get("printed_page"),
                    "kunye": r["citation"],
                    "sayfa_kimligi": r["page_id"],
                    "karakter": r.get("n_chars"),
                }
                for r in rows
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def inceleme_bulgulari(tip: str = "", eksen: str = "", sayfa: int = 0, limit: int = 25) -> str:
    """1931 metni ile İslam itikadını karşılaştıran incelemenin iddiaları.

    Her kayıt birebir alıntı, basılı sayfa, güç derecesi ve kaynak sayfanın
    adresini taşır; `verified` alanı alıntının o sayfada birebir bulunduğunun
    makine ile denetlendiğini gösterir.

    tip:   finding  — bulgu (eksen eksen karşılaştırma)
           positive — metnin İslam'a olumlu ve saygılı olduğu yerler
           limit    — metne dayanarak SÖYLENEMEYECEK olanlar
    eksen: bulgu ekseni içinde arar (ör. "vahiy", "yaratılış")
    sayfa: yalnız o basılı sayfaya ait kayıtlar

    Bir iddiayı aktarırken `limit` kayıtlarını da okuyunuz: inceleme, metnin
    desteklemediği çıkarımları açıkça reddeder ve bu liste alıntılanırken
    çıkarılmamalıdır."""
    rows = findings()
    if not rows:
        return json.dumps(
            {"hata": "bulgular.jsonl yok — önce python build/06b_inceleme.py çalıştırın"},
            ensure_ascii=False,
        )
    if tip:
        rows = [r for r in rows if r["type"] == tip]
    if eksen:
        f = fold(eksen)
        rows = [r for r in rows if f in fold(r.get("axis") or "")]
    if sayfa:
        rows = [r for r in rows if r.get("printed_page") == sayfa]
    total = len(rows)
    return json.dumps(
        {
            "kaynak": "docs/inceleme.md — CC0 1.0",
            "uyari": "İnceleme yorumlu bir çalışmadır; güç dereceleri ve 'limit' "
            "kayıtları onun kendi sınırlarıdır.",
            "eslesme": total,
            "gosterilen": min(total, limit),
            "kayitlar": rows[:limit],
        },
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
