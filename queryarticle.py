import toolforge
import pywikibot

# الاتصال بقاعدة بيانات ويكيبيديا الإنجليزية
conn = toolforge.connect('enwiki')

query = """
SELECT
    en_page.page_title AS article_name,
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

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

# إعداد pywikibot
site = pywikibot.Site("ar", "wikipedia")

# بداية جدول ويكي
content = """{| class="wikitable sortable" 
|-
! عدد الوصلات !! العنصر !! الاسم في ويكيبيديا الإنجليزية !! الاسم العربي في ويكي بيانات !! الإجراء المُقترح
|-
"""

# إعداد مجموعة للعناصر الفريدة
processed_qids = set()

# فهرس الأعمدة
idx_article_name = columns.index("article_name")
idx_qid = columns.index("wikidata_id")

# ملء الجدول
for row in results:
    article_name = row[idx_article_name]
    qid = row[idx_qid]

    if not qid or qid in processed_qids:
        continue

    processed_qids.add(qid)
    en_title = article_name.replace("_", " ")

    content += f"""{{{{مستخدم:FShbib/المقالات الآلية/فيلم/مقترح
| qid = {qid}
| arabic = {en_title}
}}}}

"""

content += "|}"

# حفظ الصفحة
page = pywikibot.Page(site, "مستخدم:Mohammed Qays/أفلام")
page.text = content
page.save(summary="بوت: جلب قائمة")
