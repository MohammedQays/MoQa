#!/usr/bin/env python3
import pywikibot
import toolforge
import re

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: إزالة قالب وصف قصير."
    debug = "no"  # لتجربة بدون حفظ، اجعلها "yes"

# استعلام SQL لجلب المقالات التي تستخدم القالب أو تحويلاته
query = '''
SELECT DISTINCT page.page_title
FROM page
JOIN templatelinks ON templatelinks.tl_from = page.page_id
JOIN linktarget ON templatelinks.tl_target_id = linktarget.lt_id
WHERE page.page_namespace = 0
AND linktarget.lt_namespace = 10
AND linktarget.lt_title IN (
  'وصف_قصير', 'وصف_مختصر', 'Short_description'
);
'''

# التعبير المنتظم لإزالة القالب
template_variants = [
    "وصف قصير",
    "وصف_قصير",
    "وصف مختصر",
    "وصف_مختصر",
    "Short description",
    "Short_description"
]

template_regex = re.compile(
    r"\n?\s*\{\{\s*(?:%s)\s*(\|[^{}]*)?\s*\}\}" % "|".join(template_variants),
    re.IGNORECASE
)

def execute_query():
    """تنفيذ الاستعلام لاسترداد عناوين المقالات."""
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        conn.close()
        return results
    except Exception:
        return []

def remove_template_from_page(title, site):
    """يحذف القالب من المقالة إذا كان موجوداً."""
    page = pywikibot.Page(site, title)
    
    if not page.exists():
        return

    old_text = page.text
    new_text = template_regex.sub("", old_text).strip()

    if old_text != new_text and settings.debug == "no":
        page.text = new_text
        page.save(summary=settings.editsumm)

def main():
    site = pywikibot.Site('ar', 'wikipedia')
    results = execute_query()

    for row in results:
        title = row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]
        title = title.replace("_", " ")
        remove_template_from_page(title, site)

if __name__ == "__main__":
    main()
