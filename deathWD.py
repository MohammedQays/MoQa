from SPARQLWrapper import SPARQLWrapper, JSON
import pywikibot

# استعلام SPARQL
sparql_query = """
SELECT ?item ?itemLabel ?dod ?img ?placeLabel WHERE {
  ?item wdt:P570 ?dod .
  FILTER (?dod > "2016-10-20T00:00:00Z"^^xsd:dateTime) .
  FILTER (?dod > (NOW() - "P32D"^^xsd:duration) && ?dod < NOW()) .
  ?item wdt:P31 wd:Q5 .
  OPTIONAL { ?item wdt:P18 ?img. }
  OPTIONAL { ?item wdt:P20 ?place. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en". }
}
ORDER BY DESC(?dod)
LIMIT 20
"""

# تنفيذ الاستعلام
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setQuery(sparql_query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# إعداد pywikibot
site = pywikibot.Site("ar", "wikipedia")
repo = site.data_repository()

# بداية النص
output = "<noinclude>__NOINDEX__</noinclude>\n"

for result in results["results"]["bindings"]:
    qid = result["item"]["value"].split("/")[-1]
    label_raw = result.get("itemLabel", {}).get("value", "")
    dod = result.get("dod", {}).get("value", "")[:10]
    img_name = result.get("img", {}).get("value", "").split("/")[-1].replace(" ", "_") if "img" in result else ""
    place = result.get("placeLabel", {}).get("value", "") if "placeLabel" in result else ""

    img_code = f"[[ملف:{img_name}|مركز|130px]]" if img_name else ""

    try:
        item = pywikibot.ItemPage(repo, qid)
        item.get()
        sitelinks = item.sitelinks

        # فقط إذا كانت المقالة موجودة في ويكيبيديا العربية
        if "arwiki" in sitelinks:
            label_code = f"[[{sitelinks['arwiki'].title}]]"
        else:
            label_code = label_raw

    except Exception as e:
        print(f"خطأ في معالجة العنصر {qid}: {e}")
        label_code = label_raw

    # بناء القالب
    output += "{{مستخدم:Mohammed Qays/معرض ويكي بيانات\n"
    output += f"| p18 = {img_code}\n"
    output += f"| label = {label_code}\n"
    output += f"| p570 = {dod}\n"
    output += f"| p20 = {place}\n"
    output += f"| qid = {qid}\n"
    output += "}}\n\n"

# تحديث صفحة ويكيبيديا
page = pywikibot.Page(site, "ويكيبيديا:تقارير قاعدة البيانات/وفيات حديثة/معرض")
page.text = output
page.save(summary="بوت: تحديث")
