"""05 — Bütün standart metadata şemalarını üretir.

Her şema farklı bir keşif kanalını açar:
  Dublin Core / OAI-DC  -> kütüphane toplayıcıları (harvester), Europeana, DPLA
  MARC21-XML            -> kütüphane katalogları (Koha, Alma, WorldCat)
  schema.org JSON-LD    -> Google, Bing arama motorları ve AI web araması
  DataCite XML          -> DOI tescili (Zenodo/DataCite üzerinden)
  Croissant             -> MLCommons ML veri kümesi standardı (HuggingFace okur)
  Frictionless          -> genel veri kümesi tanımı
  CITATION.cff          -> GitHub "Cite this repository" düğmesi
  zenodo.json           -> Zenodo yüklemesinde otomatik künye
                           (kopyası depo kökünde .zenodo.json — Zenodo oraya bakar)
"""
from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BOOKS, META_DIR, ROOT, read_jsonl, write_json, write_text  # noqa: E402

META = json.loads((META_DIR / "books.json").read_text(encoding="utf-8"))
COLL = META["collection"]
RIGHTS = META["rights"]
BOOKMETA = {b["slug"]: b for b in META["books"]}

# Yayın kanalları da künyeyle aynı yerden gelir (metadata/books.json ->
# channels); adres kodda ikinci bir yerde yazmaz.
CHANNELS = META.get("channels", {})
REVIEW = META.get("review", {})
BASE_URL = CHANNELS.get("site") or "https://tarih1931.github.io"
TODAY = date.today().isoformat()

# DOI, metadata/books.json içindeki collection.doi alanından gelir; kodda değil,
# yapılandırmada durur ve siteyi üreten adım da aynı yerden okur.
#
# Zenodo concept DOI kullanılır: bütün sürümleri temsil eder ve daima en
# sonuncusuna çözümlenir. Sürüme özel DOI (v1.0.0 için 10.5281/zenodo.21956340)
# künyelere yazılmaz; yeni sürümde eskiyeceği için atıf zincirini kırar.
#
# Alan boşsa veya yer tutucuysa DOI hiçbir künyeye yazılmaz: var olmayan bir
# tanımlayıcıyı schema.org/Croissant/Dublin Core içinde yayımlamak, arama
# motorlarına ve dil modellerine onu gerçekmiş gibi vermek olurdu.
DOI = COLL.get("doi") or None
if DOI and "X" in DOI:
    DOI = None

# Sürüm de aynı sebeple yapılandırmada durur: GitHub etiketiyle birlikte tek
# yerden değişsin, künyelerin ikisi birden eskimesin.
VERSION = COLL.get("version") or "1.0.0"


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def book_stats(slug: str) -> dict:
    path = ROOT / "data" / slug / "pages.jsonl"
    if not path.exists():
        return {}
    rows = list(read_jsonl(path))
    numbered = [r for r in rows if r.get("printed_page")]
    return {
        "physical_pages": len(rows),
        "numbered_pages": len(numbered),
        "first_page": min((r["printed_page"] for r in numbered), default=None),
        "last_page": max((r["printed_page"] for r in numbered), default=None),
        "characters": sum(r.get("n_chars", 0) for r in rows),
    }


def selections() -> list[dict]:
    """Elle düzeltilmiş bölümler. Künye metni buradan üretilir ki gerçeklikten
    kopmasın; secim/ yeniden üretildiğinde açıklama da kendiliğinden düzelir."""
    path = ROOT / "secim" / "index.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("selections", [])


def corrected_phrase() -> str:
    """"Tarih I “BEŞER TARİHİNE GİRİŞ” (basılı s. 1-24) ve …" biçiminde künye."""
    parts = []
    for s in selections():
        lo, hi = s["printed_range"]
        book = s["book_title"].split(":")[0].strip()
        parts.append(f'{book} “{s["heading"]}” (basılı s. {lo}-{hi})')
    return " ve ".join(parts)


def corrected_pages() -> int:
    return sum(s.get("pages_body", 0) for s in selections())


# ---------------------------------------------------------------------------
# Dublin Core (OAI-DC)
# ---------------------------------------------------------------------------


def dublin_core(slug: str) -> str:
    bm = BOOKMETA[slug]
    st = book_stats(slug)
    L = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"',
        '           xmlns:dc="http://purl.org/dc/elements/1.1/"',
        '           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '           xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ '
        'http://www.openarchives.org/OAI/2.0/oai_dc.xsd">',
        f'  <dc:title>{esc(bm["title_full"])}</dc:title>',
        f'  <dc:creator>{esc(COLL["corporate_author"]["name_1931"])}</dc:creator>',
    ]
    for c in COLL["contributors"]:
        L.append(f'  <dc:contributor>{esc(c["name_modern"])} ({esc(c["name_1931"])})</dc:contributor>')
    L += [
        f'  <dc:publisher>{esc(bm["publisher"])}</dc:publisher>',
        f'  <dc:date>{bm["year"]}</dc:date>',
        "  <dc:type>Text</dc:type>",
        "  <dc:type>Textbook</dc:type>",
        "  <dc:format>application/pdf</dc:format>",
        "  <dc:format>text/plain</dc:format>",
        "  <dc:format>application/tei+xml</dc:format>",
        f'  <dc:language>{COLL["language"]}</dc:language>',
        f'  <dc:source>{esc(bm["ttk_url"])}</dc:source>',
        f'  <dc:identifier>{esc(BASE_URL)}/{slug}/</dc:identifier>',
        *([f"  <dc:identifier>doi:{DOI}</dc:identifier>"] if DOI else []),
        f'  <dc:rights>{esc(RIGHTS["statement_uri"])}</dc:rights>',
        f'  <dc:rights>Türetilmiş veri: {esc(RIGHTS["derived_dataset_license"])}</dc:rights>',
    ]
    for s in COLL["subjects"]:
        L.append(f"  <dc:subject>{esc(s)}</dc:subject>")
    for s in COLL["subjects_lcsh"]:
        L.append(f"  <dc:subject>{esc(s)}</dc:subject>")
    desc = (
        f'{bm["title_full"]}. {COLL["corporate_author"]["name_1931"]} tarafından hazırlanıp '
        f'{bm["publisher"]} onayıyla Türkiye\'de liselerde resmî tarih ders kitabı '
        f'olarak okutulmuştur. {bm["approval"]} Bu kayıt, taranmış nüshadan üretilen '
        f'makine-okunabilir (OCR) tam metni tanımlar.'
    )
    L.append(f"  <dc:description>{esc(desc)}</dc:description>")
    if st:
        L.append(
            f'  <dc:extent>{st["physical_pages"]} fiziksel sayfa; '
            f'{st["characters"]} karakter</dc:extent>'
        )
    L.append(f'  <dc:relation>{esc(COLL["name"])}</dc:relation>')
    L.append("</oai_dc:dc>")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# MARC21-XML
# ---------------------------------------------------------------------------


def marc21(slug: str) -> str:
    bm = BOOKMETA[slug]
    st = book_stats(slug)
    L = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<collection xmlns="http://www.loc.gov/MARC21/slim">',
        "  <record>",
        "    <leader>00000nam a2200000 i 4500</leader>",
        '    <controlfield tag="008">'
        f'{TODAY[2:4]}{TODAY[5:7]}{TODAY[8:10]}s{bm["year"]}    tu a     b    000 0 tur d'
        "</controlfield>",
        '    <datafield tag="040" ind1=" " ind2=" ">',
        '      <subfield code="a">TR-AnTTK</subfield>',
        '      <subfield code="b">tur</subfield>',
        "    </datafield>",
        '    <datafield tag="110" ind1="2" ind2=" ">',
        f'      <subfield code="a">{esc(COLL["corporate_author"]["name_1931"])}.</subfield>',
        "    </datafield>",
        '    <datafield tag="245" ind1="1" ind2="0">',
        f'      <subfield code="a">{esc(bm["title"])} {esc(bm["volume"])} :</subfield>',
        f'      <subfield code="b">{esc(bm["subtitle"])}.</subfield>',
        "    </datafield>",
        '    <datafield tag="260" ind1=" " ind2=" ">',
        f'      <subfield code="a">{esc(bm["place"])} :</subfield>',
        f'      <subfield code="b">{esc(bm["publisher"])},</subfield>',
        f'      <subfield code="c">{bm["year"]}.</subfield>',
        "    </datafield>",
        '    <datafield tag="300" ind1=" " ind2=" ">',
        f'      <subfield code="a">{st.get("last_page", "?")} s. :</subfield>',
        f'      <subfield code="b">{esc(bm["illustrations_statement"])} ;</subfield>',
        '      <subfield code="c">24 cm.</subfield>',
        "    </datafield>",
        '    <datafield tag="500" ind1=" " ind2=" ">',
        f'      <subfield code="a">{esc(bm["approval"])}</subfield>',
        "    </datafield>",
        '    <datafield tag="546" ind1=" " ind2=" ">',
        f'      <subfield code="a">{esc(COLL["language_note"])}</subfield>',
        "    </datafield>",
    ]
    for c in COLL["contributors"]:
        L += [
            '    <datafield tag="700" ind1="1" ind2=" ">',
            f'      <subfield code="a">{esc(c["name_modern"])},</subfield>',
            f'      <subfield code="e">{esc(c["role"])}</subfield>',
            "    </datafield>",
        ]
    for s in COLL["subjects_lcsh"]:
        L += [
            '    <datafield tag="650" ind1=" " ind2="0">',
            f'      <subfield code="a">{esc(s)}</subfield>',
            "    </datafield>",
        ]
    L += [
        '    <datafield tag="856" ind1="4" ind2="0">',
        f'      <subfield code="u">{esc(bm["ttk_url"])}</subfield>',
        '      <subfield code="z">Kaynak tarama (TTK Kütüphanesi)</subfield>',
        "    </datafield>",
        '    <datafield tag="856" ind1="4" ind2="0">',
        f'      <subfield code="u">{esc(BASE_URL)}/{slug}/</subfield>',
        '      <subfield code="z">Makine-okunabilir tam metin</subfield>',
        "    </datafield>",
        "  </record>",
        "</collection>",
    ]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# schema.org JSON-LD
# ---------------------------------------------------------------------------


def schema_org(slug: str) -> dict:
    bm = BOOKMETA[slug]
    st = book_stats(slug)
    return {
        "@context": "https://schema.org",
        "@type": "Book",
        "@id": f"{BASE_URL}/{slug}/",
        "name": bm["title_full"],
        "alternateName": f"{bm['title']} {bm['volume']}",
        "bookEdition": bm["edition"],
        "datePublished": str(bm["year"]),
        "inLanguage": "tr",
        "numberOfPages": st.get("last_page"),
        "isPartOf": {"@type": "BookSeries", "name": COLL["name"], "numberOfVolumes": len(META["books"])},
        "author": {
            "@type": "Organization",
            "name": COLL["corporate_author"]["name_1931"],
            "alternateName": COLL["corporate_author"]["name_modern"],
        },
        "contributor": [
            {"@type": "Person", "name": c["name_modern"], "alternateName": c["name_1931"], "jobTitle": c["role_1931"]}
            for c in COLL["contributors"]
        ],
        "publisher": {"@type": "Organization", "name": bm["publisher"]},
        "locationCreated": {"@type": "Place", "name": bm["place"]},
        "about": COLL["subjects"],
        "keywords": ", ".join(COLL["subjects"] + COLL["subjects_lcsh"]),
        "genre": ["Ders kitabı", "Tarih"],
        "license": RIGHTS["derived_dataset_license_uri"],
        "usageInfo": RIGHTS["statement_uri"],
        "isAccessibleForFree": True,
        "identifier": (
            [{"@type": "PropertyValue", "propertyID": "DOI", "value": DOI}] if DOI else []
        )
        + [{"@type": "PropertyValue", "propertyID": "TTK-item", "value": bm["ttk_item_id"]}],
        "sameAs": [bm["ttk_url"]],
        "description": (
            f'{bm["title_full"]}, {COLL["corporate_author"]["name_1931"]} tarafından hazırlanmış ve '
            f'{bm["approval"]} Türkiye Cumhuriyeti liselerinde 1931-1941 arasında okutulan resmî '
            f'tarih ders kitabıdır. Bu sayfa, taranmış nüshadan üretilmiş, sayfa numaralarıyla '
            f'eşlenmiş makine-okunabilir tam metni sunar.'
        ),
        "encoding": [
            {"@type": "MediaObject", "encodingFormat": "text/plain", "contentUrl": f"{BASE_URL}/{slug}/full.txt"},
            {"@type": "MediaObject", "encodingFormat": "application/tei+xml", "contentUrl": f"{BASE_URL}/{slug}/{slug}.tei.xml"},
            {"@type": "MediaObject", "encodingFormat": "application/x-ndjson", "contentUrl": f"{BASE_URL}/{slug}/pages.jsonl"},
        ],
    }


# ---------------------------------------------------------------------------
# DataCite 4.5
# ---------------------------------------------------------------------------


def datacite() -> str:
    total = sum(book_stats(b.slug).get("characters", 0) for b in BOOKS)
    L = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<resource xmlns="http://datacite.org/schema/kernel-4"',
        '          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '          xsi:schemaLocation="http://datacite.org/schema/kernel-4 '
        'http://schema.datacite.org/meta/kernel-4.5/metadata.xsd">',
        # DataCite şeması identifier alanını zorunlu tutar. DOI henüz yokken
        # uydurma bir numara yerine, tescil iş akışlarının bildiği "atanacak"
        # değeri yazılır.
        f'  <identifier identifierType="DOI">{DOI or "(:tba)"}</identifier>',
        "  <creators>",
        '    <creator><creatorName nameType="Organizational">'
        f'{esc(COLL["corporate_author"]["name_1931"])}</creatorName></creator>',
        "  </creators>",
        "  <titles>",
        f'    <title xml:lang="tr">{esc(COLL["name"])} — makine-okunabilir tam metin</title>',
        f'    <title xml:lang="en" titleType="TranslatedTitle">{esc(COLL["name_en"])} — '
        "machine-readable full text</title>",
        "  </titles>",
        "  <publisher>Zenodo</publisher>",
        f"  <publicationYear>{TODAY[:4]}</publicationYear>",
        '  <resourceType resourceTypeGeneral="Text">Digitised historical textbook corpus</resourceType>',
        "  <subjects>",
    ]
    for s in COLL["subjects"] + COLL["subjects_lcsh"]:
        L.append(f"    <subject>{esc(s)}</subject>")
    L += [
        "  </subjects>",
        "  <contributors>",
    ]
    for c in COLL["contributors"]:
        L.append(
            f'    <contributor contributorType="Other"><contributorName>{esc(c["name_modern"])}'
            f"</contributorName></contributor>"
        )
    L += [
        "  </contributors>",
        "  <dates>",
        f'    <date dateType="Created">1931</date>',
        f'    <date dateType="Issued">{TODAY}</date>',
        "  </dates>",
        '  <language>tr</language>',
        "  <rightsList>",
        f'    <rights rightsURI="{RIGHTS["derived_dataset_license_uri"]}" '
        f'rightsIdentifier="cc0-1.0">Creative Commons Zero v1.0 Universal</rights>',
        f'    <rights rightsURI="{RIGHTS["statement_uri"]}">Kaynak eser: kamu malı (bkz. HAKLAR.md)</rights>',
        "  </rightsList>",
        "  <sizes>",
        f"    <size>{total} karakter</size>",
        f"    <size>{len(BOOKS)} cilt</size>",
        "  </sizes>",
        "  <formats>",
        "    <format>text/plain</format>",
        "    <format>application/x-ndjson</format>",
        "    <format>application/tei+xml</format>",
        "    <format>application/pdf</format>",
        "  </formats>",
        "  <descriptions>",
        '    <description descriptionType="Abstract" xml:lang="tr">'
        f'{esc(COLL["description"])} Bu veri kümesi, TTK Kütüphanesi taramalarından üretilmiş, '
        "basılı sayfa numaralarıyla eşlenmiş, alıntılanabilir makine-okunabilir tam metni içerir: "
        "sayfa düzeyinde JSONL, TEI-XML, düz metin ve RAG parçaları."
        "</description>",
        "  </descriptions>",
        "  <relatedIdentifiers>",
    ]
    for b in BOOKS:
        bm = BOOKMETA[b.slug]
        L.append(
            f'    <relatedIdentifier relatedIdentifierType="URL" relationType="IsDerivedFrom">'
            f'{esc(bm["ttk_url"])}</relatedIdentifier>'
        )
    L += ["  </relatedIdentifiers>", "</resource>"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Croissant (MLCommons) — HuggingFace veri kümesi standardı
# ---------------------------------------------------------------------------


def croissant() -> dict:
    dists = [
        {
            "@type": "cr:FileObject",
            "@id": f"{b.slug}-pages",
            "name": f"{b.slug}/pages.jsonl",
            "description": f"{BOOKMETA[b.slug]['title_full']} — sayfa düzeyinde kayıtlar",
            "contentUrl": f"{BASE_URL}/{b.slug}/pages.jsonl",
            "encodingFormat": "application/x-ndjson",
        }
        for b in BOOKS
    ]
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "dct": "http://purl.org/dc/terms/",
            "data": {"@id": "cr:data", "@type": "@json"},
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "field": "cr:field",
            "fileObject": "cr:fileObject",
            "recordSet": "cr:recordSet",
            "source": "cr:source",
            "extract": "cr:extract",
            "column": "cr:column",
        },
        "@type": "sc:Dataset",
        "name": "tarih-ders-kitaplari-1931",
        "description": COLL["description"],
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "license": RIGHTS["derived_dataset_license_uri"],
        "url": BASE_URL,
        "version": VERSION,
        "datePublished": TODAY,
        "inLanguage": "tr",
        "keywords": COLL["subjects"] + COLL["subjects_lcsh"],
        "citeAs": (
            f'Türk Tarihi Tetkik Cemiyeti (1931). {COLL["name"]} — makine-okunabilir tam metin. '
            + (f"DOI: {DOI}" if DOI else BASE_URL)
        ),
        "creator": {"@type": "Organization", "name": COLL["corporate_author"]["name_modern"]},
        "distribution": dists,
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": "pages",
                "name": "pages",
                "description": "Her kayıt bir basılı kitap sayfasıdır; alıntı künyesi taşır.",
                "field": [
                    {"@type": "cr:Field", "@id": "pages/page_id", "name": "page_id", "dataType": "sc:Text",
                     "description": "Sayfanın kalıcı kimliği"},
                    {"@type": "cr:Field", "@id": "pages/book", "name": "book", "dataType": "sc:Text",
                     "description": "Cilt kimliği"},
                    {"@type": "cr:Field", "@id": "pages/printed_page", "name": "printed_page",
                     "dataType": "sc:Integer", "description": "Kitapta basılı sayfa numarası"},
                    {"@type": "cr:Field", "@id": "pages/running_head", "name": "running_head",
                     "dataType": "sc:Text", "description": "Sayfa üst başlığı (bölüm adı)"},
                    {"@type": "cr:Field", "@id": "pages/text", "name": "text", "dataType": "sc:Text",
                     "description": "Sayfanın OCR tam metni"},
                    {"@type": "cr:Field", "@id": "pages/citation", "name": "citation", "dataType": "sc:Text",
                     "description": "Hazır alıntı dizesi"},
                    {"@type": "cr:Field", "@id": "pages/page_confidence", "name": "page_confidence",
                     "dataType": "sc:Text", "description": "Sayfa numarasının güven düzeyi: ocr | inferred | uncertain"},
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------


def citation_cff() -> str:
    L = [
        "cff-version: 1.2.0",
        'message: "Bu veri kümesini kullanırsanız lütfen aşağıdaki gibi atıf yapınız."',
        "title: >-",
        f'  {COLL["name"]} — makine-okunabilir tam metin',
        "type: dataset",
        "authors:",
        f'  - name: "{COLL["corporate_author"]["name_1931"]}"',
        "    alias: T.T.T.C.",
        f"date-released: {TODAY}",
        f"version: {VERSION}",
        f"license: {RIGHTS['derived_dataset_license']}",
        f"url: {BASE_URL}",
        *(
            [
                "identifiers:",
                "  - type: doi",
                f"    value: {DOI}",
                '    description: "Zenodo DOI\'si (tüm sürümler)"',
            ]
            if DOI
            else []
        ),
        "keywords:",
    ]
    for s in COLL["subjects"]:
        L.append(f'  - "{s}"')
    L.append("abstract: >-")
    L.append(f'  {COLL["description"]}')
    L.append(
        "  Veri kümesi, TTK Kütüphanesi taramalarından üretilmiş; çift sayfa taramaları tek tek"
    )
    L.append("  kitap sayfalarına ayrılmış, basılı sayfa numaraları yeniden OCR ile kurtarılmıştır.")
    return "\n".join(L) + "\n"


def related_identifiers() -> list[dict]:
    """Kaydın diğer yayın kanallarıyla bağı.

    Bağ tek yönlü kaldığında kaybolur: incelemenin kaydı korpusa
    ``isSupplementTo`` ile bağlıydı, korpus tarafında karşılığı yoktu; DataCite
    grafiğinde iki çalışma birbirini göstermiyordu. Buradaki her satır o
    eksiği kapatır.

    Wikidata öğeleri bilerek yazılmaz: o öğeler 1931 basımı *kitapları*
    tanımlar, bu veri kümesini değil. Kitap öğesine DOI yazmamakla aynı
    gerekçe (bkz. docs/KANALLAR.md §1).
    """
    rel: list[dict] = []
    # Kaynak: TTK katalog kaydı ve Internet Archive'daki tarama nüshası.
    for b in BOOKS:
        m = BOOKMETA[b.slug]
        rel.append({"identifier": m["ttk_url"], "relation": "isDerivedFrom", "scheme": "url"})
        if m.get("internet_archive"):
            rel.append({"identifier": m["internet_archive"],
                        "relation": "isDerivedFrom", "scheme": "url"})
    # İnceleme ayrı bir çalışmadır ve kendi concept DOI'sini taşır.
    if REVIEW.get("doi"):
        rel.append({"identifier": REVIEW["doi"], "relation": "isSupplementedBy", "scheme": "doi"})
    # Aynı verinin başka barındırıcıdaki nüshası / web sürümü.
    if CHANNELS.get("huggingface"):
        rel.append({"identifier": CHANNELS["huggingface"],
                    "relation": "isIdenticalTo", "scheme": "url"})
    if CHANNELS.get("site"):
        rel.append({"identifier": CHANNELS["site"], "relation": "isVariantFormOf", "scheme": "url"})
    # Vikikaynak'taki istinsah bu korpustan üretildi: kaynak biziz.
    for b in BOOKS:
        w = BOOKMETA[b.slug].get("wikisource_work")
        if w:
            rel.append({"identifier": w, "relation": "isSourceOf", "scheme": "url"})
    return rel


def zenodo_json() -> dict:
    return {
        "title": f'{COLL["name"]} — makine-okunabilir tam metin (Tarih I ve II, 1931)',
        "upload_type": "dataset",
        "description": (
            f'<p>{COLL["description"]}</p>'
            "<p>Bu yükleme, Türk Tarih Kurumu Kütüphanesi taramalarından üretilmiş, basılı sayfa "
            "numaralarıyla eşlenmiş makine-okunabilir tam metni içerir. Çift sayfa taramaları tek "
            "tek kitap sayfalarına ayrılmış; gömülü OCR katmanında bulunmayan sayfa numaraları ve "
            "bölüm başlıkları tarama görüntüsünden yeniden OCR edilmiştir.</p>"
            f"<p><strong>Elle doğrulanmış bölümler.</strong> Korpusun tamamı düzeltilmemiş OCR "
            f"çıktısıdır. İki bölüm — {corrected_phrase()}, toplam {corrected_pages()} sayfa — "
            "taranmış aslıyla sayfa sayfa karşılaştırılarak elle düzeltilmiştir. Ham OCR metni "
            "her kayıtta <code>text_ocr</code> alanında saklandığı için her düzeltme "
            "denetlenebilir; düzeltilmiş kayıtlar <code>text_source=corrected</code> ile "
            "işaretlidir.</p>"
            "<p><strong>İnceleme.</strong> Yükleme, bu bölümler üzerine yapılmış bir "
            "karşılaştırmalı incelemeyi içerir (<code>docs/inceleme-kapsamli.md</code>, "
            "öz metin <code>docs/inceleme.md</code>): "
            "1931 resmî tarih öğretisi ile İslam itikadının eksen eksen karşılaştırması. Her "
            "iddia sayfa künyeli birebir alıntıyla belgelenmiş, güç derecesiyle işaretlenmiş; "
            "metnin desteklemediği çıkarımlar ayrı bir bölümde açıkça listelenmiştir. "
            "İncelemenin iddiaları ayrıca makine-okunabilir olarak verilmiştir "
            "(<code>inceleme/bulgular.jsonl</code>): <em>alıntı</em> kayıtları birebir pasajı, "
            "basılı sayfayı ve kaynak sayfanın adresini taşır — her alıntının künyesindeki "
            "sayfada birebir bulunduğu üretim sırasında makine ile denetlenir; <em>bulgu</em> "
            "kayıtları ise o alıntıların Kur'an nassı karşısında değerlendirilmesinden çıkan "
            "kanaati, dayandığı alıntı ve ayetlerle birlikte verir. Ayrıca din ve inanç "
            "pasajlarının yorumsuz kavram dizini (<code>thematic/</code>) bulunmaktadır.</p>"
            "<p>Biçimler: sayfa düzeyinde JSONL, TEI-XML, sayfa işaretli düz metin, Markdown, "
            "RAG parçaları, Dublin Core / MARC21 / schema.org / Croissant metadata.</p>"
            f'<p>Çevrimiçi sürüm: <a href="{BASE_URL}">{BASE_URL}</a></p>'
        ),
        "creators": [
            {"name": COLL["corporate_author"]["name_1931"], "affiliation": "Türkiye Cumhuriyeti"}
        ],
        # Korpus konularına ek olarak bu yüklemenin kendi içeriğini (elle
        # doğrulanmış bölümler + karşılaştırmalı inceleme) tarif eden terimler.
        "keywords": COLL["subjects"]
        + COLL["subjects_lcsh"]
        + [
            "İslam itikadı",
            "Din ve devlet — Türkiye",
            "Elle doğrulanmış OCR",
            "Islam--Doctrines",
            "Digitised text corpus",
        ],
        "language": "tur",
        "access_right": "open",
        "license": "cc-zero",
        "related_identifiers": related_identifiers(),
        "notes": RIGHTS["reasoning"],
    }


def main() -> None:
    (META_DIR / "dublin-core").mkdir(parents=True, exist_ok=True)
    (META_DIR / "marc21").mkdir(parents=True, exist_ok=True)
    (META_DIR / "schema-org").mkdir(parents=True, exist_ok=True)

    for b in BOOKS:
        write_text(META_DIR / "dublin-core" / f"{b.slug}.xml", dublin_core(b.slug))
        write_text(META_DIR / "marc21" / f"{b.slug}.xml", marc21(b.slug))
        write_json(META_DIR / "schema-org" / f"{b.slug}.jsonld", schema_org(b.slug))
        print(f"    {b.slug}: DC + MARC21 + schema.org")

    write_text(META_DIR / "datacite.xml", datacite())
    write_json(META_DIR / "croissant.json", croissant())
    write_json(META_DIR / "zenodo.json", zenodo_json())
    # Zenodo künyeyi yalnız depo kökündeki .zenodo.json dosyasından okur; GitHub
    # sürümü arşivlenirken metadata/ altına bakmaz. Aynı içerik iki yere yazılır.
    write_json(ROOT / ".zenodo.json", zenodo_json())
    write_text(ROOT / "CITATION.cff", citation_cff())
    print("    datacite.xml, croissant.json, zenodo.json, .zenodo.json, CITATION.cff")


if __name__ == "__main__":
    main()
