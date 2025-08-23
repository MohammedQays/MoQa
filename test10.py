import pywikibot
import toolforge
import re

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح قالب"
    debug = "no"

query = """
SELECT
  p.page_title
FROM
  page AS p
JOIN
  categorylinks AS cl
  ON cl.cl_from = p.page_id
WHERE
  cl.cl_to = 'قالب_اتحاد_ألعاب_القوى_يستخدم_بيانات_كما_في_ويكي_بيانات'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0;
"""

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]

site = pywikibot.Site()
site.login()

# النمط يلتقط فقط القالب المستهدف
pattern = re.compile(r'{{\s*اتحاد ألعاب القوى\s*\|\s*(?:id\s*=\s*)?\d+\s*}}')

def fix_template(text):
    return pattern.sub("{{اتحاد ألعاب القوى}}", text)

for title in titles:
    page = pywikibot.Page(site, title.replace('_', ' '))
    try:
        text = page.get()
        new_text = fix_template(text)
        if new_text != text:
            if settings.debug == "no":
                page.text = new_text
                page.save(settings.editsumm)
    except (pywikibot.NoPageError, pywikibot.IsRedirectPageError):
        pass
    except Exception as e:
        print(f"خطأ في {title}: {e}")
