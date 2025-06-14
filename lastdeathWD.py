import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

# استعلام SPARQL لجلب المعرفات فقط للوفيات خلال آخر 10 أيام
sparql_query = """
SELECT ?item WHERE {
  ?item wdt:P31 wd:Q5 ;
        wdt:P570 ?date .
  FILTER(?date >= NOW() - "P10D"^^xsd:duration && ?date <= NOW())
}
ORDER BY DESC(?date)
LIMIT 1000
"""

# تنفيذ الاستعلام
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setQuery(sparql_query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# إعداد pywikibot
site = pywikibot.Site("ar", "wikipedia")

# بناء نص ويكي
content = "{{تر. جد. وفيات}}\n"

# مجموعة لتخزين المعرفات الفريدة
added_qids = set()

# إضافة المعرفات بالتنسيق المطلوب
for result in results["results"]["bindings"]:
    qid = result["item"]["value"].split("/")[-1]
    if qid not in added_qids:
        content += f"{{{{سط. جد. وفيات| {qid}}}}}\n"
        added_qids.add(qid)

content += "{{ذيل جدول}}"

# تحديث صفحة ويكي
page = pywikibot.Page(site, "ويكيبيديا:تقارير قاعدة البيانات/وفيات حديثة/قائمة")
page.text = content
page.save(summary="بوت: تحديث")
