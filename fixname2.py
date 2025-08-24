import pywikibot
import toolforge
import re
from pywikibot.exceptions import NoPageError, IsRedirectPageError

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح كلمة فيلم إلى فلم."
    debug = "no"  # "yes" لمراجعة قبل الحفظ

# استعلام تكراري للحصول على التصنيفات + جميع التصنيفات الفرعية
query = """
WITH RECURSIVE subcats AS (
    SELECT page_id, page_title
    FROM page
    WHERE page_namespace = 14
      AND page_title = 'بذرة_فيلم'
    UNION ALL
    SELECT p.page_id, p.page_title
    FROM page p
    JOIN categorylinks cl ON cl.cl_from = p.page_id
    JOIN subcats s ON cl.cl_to = s.page_title
    WHERE p.page_namespace = 14
)
SELECT DISTINCT
  p.page_namespace,
  p.page_title
FROM page p
JOIN categorylinks cl ON cl.cl_from = p.page_id
JOIN subcats s ON cl.cl_to = s.page_title
WHERE p.page_namespace = 14
  AND p.page_is_redirect = 0;
"""

# الاتصال بقاعدة Toolforge
conn = toolforge.connect(settings.lang, 'analytics')
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

site = pywikibot.Site()
site.login()

# اسم نطاق التصنيفات المحلي
CATEGORY_NS_NAME = site.namespace(14)  # عادة "تصنيف"

# استبدال "فيلم" → "فلم"
pattern = re.compile(r"فيلم")

def fix_text(text: str) -> str:
    return pattern.sub("فلم", text)

processed = 0
edited = 0
skipped = 0

for ns, title in results:
    processed += 1
    full_title = f"{CATEGORY_NS_NAME}:{title.replace('_', ' ')}"
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
