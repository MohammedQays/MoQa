import pywikibot
import toolforge
from datetime import datetime, timezone

class settings:
    lang = 'arwiki'
    report_title = "مستخدم:Mohammed Qays/أفلام"
    editsumm = "[[وب:بوت|بوت]]: تحديث قائمة."
    debug = "no"

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

site = pywikibot.Site()

# الاتصال بقاعدة enwiki_p على cluster analytics
conn = toolforge.connect('enwiki_p', cluster='analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

content = """{| class="wikitable sortable"
|-
! عدد الوصلات !! العنصر !! الاسم في ويكيبيديا الإنجليزية !! الاسم العربي في ويكي بيانات !! الإجراء المُقترح
"""

for idx, row in enumerate(results, start=1):
    qid = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    arabic_name = ""
    content += f"""|-
{{{{مستخدم:FShbib/المقالات الآلية/فيلم/مقترح
| qid = {qid}
| arabic = {arabic_name}
}}}}
"""

content += "|}"

page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
