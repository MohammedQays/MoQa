import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

# استعلام SPARQL لجلب الأشخاص الأحياء الذين يصادف اليوم يوم ميلادهم
sparql_query = """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?birth ?image WHERE {
  ?date_node wikibase:timePrecision "11"^^xsd:integer .
  ?date_node wikibase:timeValue ?birth .
  FILTER (year(?birth) > 1902)
  FILTER (day(?birth) = day(now()))
  FILTER (month(?birth) = month(now()))
  ?item p:P569 [psv:P569 ?date_node] .
  ?item wdt:P31 wd:Q5 .

  OPTIONAL { ?item wdt:P570 ?dod }
  FILTER (!bound(?dod))

  OPTIONAL { ?item wdt:P18 ?image }
  ?article schema:about ?item ;
           schema:isPartOf <https://ar.wikipedia.org/> .

  SERVICE wikibase:label { bd:serviceParam wikibase:language "ar". }
}
ORDER BY DESC(?birth)
LIMIT 130
"""

# تنفيذ الاستعلام
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setQuery(sparql_query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# إعداد pywikibot
site = pywikibot.Site("ar", "wikipedia")
repo = site.data_repository()

# بداية محتوى الصفحة مع الجدول داخل وسم <center>
output = "<noinclude>__NOINDEX__</noinclude>\n"
output += "هذا التقرير يُحدّث آليًا بواسطة بوت. آخر تحديث في <onlyinclude>{{#time: H:i, j F Y | {{REVISIONTIMESTAMP:ويكيبيديا:تقارير قاعدة البيانات/أشخاص يصادف تاريخ ميلادهم اليوم}}}} (ت ع م)</onlyinclude>.\n\n"
output += "<center>\n"  # بداية التوسيط
output += "{| class='wikitable sortable' style='width:80%;'\n"
output += "!الصورة !! الاسم !! الوصف !! تاريخ الميلاد\n"

# مجموعة لتخزين المعرفات لتجنّب التكرار
added_qids = set()

for result in results["results"]["bindings"]:
    qid = result["item"]["value"].split("/")[-1]

    # تخطي العناصر المكررة
    if qid in added_qids:
        continue
    added_qids.add(qid)

    label = result.get("itemLabel", {}).get("value", "")
    description = result.get("itemDescription", {}).get("value", "")
    birth = result.get("birth", {}).get("value", "")[:10]
    img_url = result.get("image", {}).get("value", "")

    # إذا لم توجد صورة، استخدم صورة افتراضية
    if img_url:
        img_name = img_url.split("/")[-1].replace(" ", "_")
        img_code = f"[[ملف:{img_name}|وصلة=|100px]]"
    else:
        img_code = f"[[ملف:Sin_foto.svg|وصلة=|100px]]"  # الصورة الافتراضية

    # ربط المقالة بمقالة ويكيبيديا العربية
    label_linked = f"[[{label}]]"

    # بناء السطر في الجدول
    output += f"|-\n"
    output += f"| {img_code} || {label_linked} || {description} || {birth}\n"

# إغلاق الجدول
output += "|}\n"
output += "</center>\n"  # إغلاق التوسيط

# تحديث صفحة ويكي
page = pywikibot.Page(site, "ويكيبيديا:تقارير قاعدة البيانات/أشخاص يصادف تاريخ ميلادهم اليوم")
page.text = output
page.save(summary="بوت: تحديث.")
