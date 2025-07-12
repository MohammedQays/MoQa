import toolforge
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

class Settings:
    lang = "enwiki"
    report_page = "مستخدم:Mohammed Qays/أفلام"
    edit_summary = "[[وب:بوت|بوت]]: تحديث قائمة."

# استعلام قاعدة بيانات ويكيبيديا الإنجليزية
query = """
SELECT
    pp.pp_value AS wikidata_id
FROM page AS en_page
INNER JOIN categorylinks AS cl ON en_page.page_id = cl.cl_from
LEFT JOIN page_props AS pp ON pp.pp_page = en_page.page_id AND pp.pp_propname = 'wikibase_item'
WHERE
    en_page.page_namespace = 0
    AND en_page.page_is_redirect = 0
    AND en_page.page_len > 5
    AND cl.cl_to = '2024_films'
    AND NOT EXISTS (
        SELECT 1
        FROM langlinks AS ar_lang
        WHERE ar_lang.ll_lang = 'ar'
          AND ar_lang.ll_from = en_page.page_id
    )
GROUP BY en_page.page_id
ORDER BY en_page.page_touched DESC, en_page.page_title
LIMIT 100;
"""

def fetch_wikidata_ids():
    conn = toolforge.connect(Settings.lang)
    with conn.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    # استخراج qids وتحويل bytes الى str اذا لزم الأمر
    qids = []
    for row in results:
        qid = row[0]
        if isinstance(qid, bytes):
            qid = qid.decode("utf-8")
        if qid:
            qids.append(qid)
    return qids

def fetch_labels(qids):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)

    labels = {}

    # تقسيم إلى دفعات صغيرة (مثلاً 50)
    batch_size = 50
    for i in range(0, len(qids), batch_size):
        batch = qids[i:i+batch_size]
        values = " ".join(f"wd:{qid}" for qid in batch)
        sparql_query = f"""
        SELECT ?item ?itemLabel WHERE {{
          VALUES ?item {{ {values} }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        sparql.setQuery(sparql_query)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            qid = result["item"]["value"].split("/")[-1]
            label = result.get("itemLabel", {}).get("value", qid)
            labels[qid] = label
    return labels

def build_wiki_table(qids, labels):
    content = """{| class="wikitable sortable" 
|-
! عدد الوصلات !! العنصر !! الاسم في ويكيبيديا الإنجليزية !! الاسم العربي في ويكي بيانات !! الإجراء المُقترح
|-
"""
    for qid in qids:
        en_label = labels.get(qid, qid)
        # ملاحظة: لم نطلب عدد الوصلات من SPARQL هنا، لو تريد يمكن إضافته لاحقًا
        content += f"""{{{{مستخدم:FShbib/المقالات الآلية/فيلم/مقترح
| qid = {qid}
| arabic = {en_label}
}}}}

"""
    content += "|}"
    return content

def main():
    site = pywikibot.Site("ar", "wikipedia")
    qids = fetch_wikidata_ids()
    if not qids:
        print("لم يتم العثور على معرفات ويكي بيانات.")
        return

    labels = fetch_labels(qids)
    content = build_wiki_table(qids, labels)

    page = pywikibot.Page(site, Settings.report_page)
    page.text = content
    page.save(Settings.edit_summary)
    print(f"تم تحديث الصفحة: {Settings.report_page}")

if __name__ == "__main__":
    main()
