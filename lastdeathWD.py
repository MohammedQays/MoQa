import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

# استعلام SPARQL لجلب الوفيات خلال آخر 10 أيام
sparql_query = """
SELECT ?item ?itemLabel ?date ?image ?birth ?firstNameLabel ?desc ?countryLabel ?pobLabel ?podLabel ?burialLabel WHERE {
  ?item wdt:P31 wd:Q5 ;
        wdt:P570 ?date .
  FILTER(?date >= NOW() - "P10D"^^xsd:duration && ?date <= NOW())
  OPTIONAL { ?item wdt:P18 ?image. }
  OPTIONAL { ?item wdt:P569 ?birth. }
  OPTIONAL { ?item wdt:P735 ?firstName. }
  OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc) = "ar") }
  OPTIONAL { ?item wdt:P27 ?country. }
  OPTIONAL { ?item wdt:P19 ?pob. }
  OPTIONAL { ?item wdt:P20 ?pod. }
  OPTIONAL { ?item wdt:P119 ?burial. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en". }
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
repo = site.data_repository()

# مجموعة لتخزين المعرفات التي تم إضافتها
added_qids = set()

# بناء الجدول
wikitable = """{| class='wikitable sortable' style='width:100%'
!المعرف
!الصورة
!الاسم
!تاريخ الولادة
!تاريخ الوفاة
!الاسم الأول
!الوصف
!بلد المواطنة
!مكان الولادة
!مكان الوفاة
!مكان الدفن
"""

for result in results["results"]["bindings"]:
    qid = result["item"]["value"].split("/")[-1]
    
    # إذا كانت الشخصية قد تم إضافتها مسبقًا، نتخطاها
    if qid in added_qids:
        continue
    
    added_qids.add(qid)
    
    label = result.get("itemLabel", {}).get("value", "")
    birth = result.get("birth", {}).get("value", "")[:10] if "birth" in result else ""
    date = result.get("date", {}).get("value", "")[:10]
    first = result.get("firstNameLabel", {}).get("value", "")
    desc = result.get("desc", {}).get("value", "")
    cntry = result.get("countryLabel", {}).get("value", "")
    pob = result.get("pobLabel", {}).get("value", "")
    pod = result.get("podLabel", {}).get("value", "")
    burial = result.get("burialLabel", {}).get("value", "")
    img = result.get("image", {}).get("value", "")
    img_file = f"[[ملف:{img.split('/')[-1]}|مركز|128px]]" if img else ""

    # محاولة ربط المقالة بمقالة ويكيبيديا العربية إن وُجدت
    try:
        item = pywikibot.ItemPage(repo, qid)
        item.get()
        sitelinks = item.sitelinks

        if "arwiki" in sitelinks:
            label_linked = f"[[{sitelinks['arwiki'].title}]]"
        else:
            label_linked = f"[[:d:{qid}|{label}]]"
    except:
        label_linked = f"[[:d:{qid}|{label}]]"

    # بناء الصف
    wikitable += f"""|-
| [[:d:{qid}|{qid}]]
| {img_file}
| {label_linked}
| {birth}
| {date}
| {first}
| {desc}
| {cntry}
| {pob}
| {pod}
| {burial}
"""

wikitable += "\n|}"

# تحديث صفحة ويكي
page = pywikibot.Page(site, "ويكيبيديا:تقارير قاعدة البيانات/وفيات حديثة/قائمة")
page.text = wikitable
page.save(summary="بوت: تحديث قائمة الوفيات")
