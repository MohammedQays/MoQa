import pywikibot
import toolforge
import re
from pywikibot.exceptions import NoPageError, IsRedirectPageError

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح كلمة فيلم إلى فلم."
    debug = "no"   # غيّر إلى "yes" لعرض الفروقات دون حفظ

query = """
SELECT
  p.page_title
FROM
  page AS p
JOIN
  categorylinks AS cl
  ON cl.cl_from = p.page_id
WHERE
  cl.cl_to = 'قوالب_بذرة_فيلم'
  AND p.page_namespace = 10
  AND p.page_is_redirect = 0
  LIMIT 5;
"""

conn = toolforge.connect(settings.lang, 'analytics')
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]

site = pywikibot.Site()
site.login()

TEMPLATE_NS_NAME = site.namespace(10)

pattern = re.compile(r"فيلم")

def fix_text(text: str) -> str:
    return pattern.sub("فلم", text)

processed = 0
edited = 0
skipped = 0

for title in titles:
    processed += 1
    full_title = f"{TEMPLATE_NS_NAME}:{title.replace('_', ' ')}"  
    page = pywikibot.Page(site, full_title)
    try:
        if page.isRedirectPage():
            skipped += 1
            continue

        text = page.get()
        new_text = fix_text(text)

        if new_text != text:
            if settings.debug.lower() == "no":
                page.text = new_text
                page.save(settings.editsumm, minor=True, quiet=True)
            else:
                print(f"سيعدل: {full_title}\n---قبل---\n{text}\n---بعد---\n{new_text}\n")
            edited += 1
        else:
            skipped += 1

    except (NoPageError, IsRedirectPageError):
        skipped += 1
        continue
    except Exception as e:
        skipped += 1
        print(f"خطأ في {full_title}: {e}")

print(f"تمت معالجة: {processed} | عُدّل: {edited} | تخطّي/بدون تغيير: {skipped}")
