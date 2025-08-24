import pywikibot
import toolforge
import re
from pywikibot.exceptions import NoPageError, IsRedirectPageError

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال 'فيلم' ← 'فلم'."
    debug = "no"   # غيّر إلى "yes" لو تريد مراجعة قبل الحفظ

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
  AND p.page_namespace = 10 -- فضاء القوالب
  AND p.page_is_redirect = 0;
"""

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]

site = pywikibot.Site()
site.login()

pattern = re.compile(r'فيلم')

def fix_text(text):
    return pattern.sub("فلم", text)

for title in titles:
    page = pywikibot.Page(site, title.replace('_', ' '))
    try:
        if page.isRedirectPage():
            continue
        text = page.get()
        new_text = fix_text(text)
        if new_text != text:
            if settings.debug == "no":
                page.text = new_text
                page.save(settings.editsumm)
            else:
                print(f"سيعدل: {title}\n---قبل---\n{text}\n---بعد---\n{new_text}\n")
    except (NoPageError, IsRedirectPageError):
        continue
    except Exception as e:
        print(f"خطأ في {title}: {e}")
