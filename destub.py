import pywikibot
import re
import toolforge

site = pywikibot.Site('ar', 'wikipedia')
site.login()

# الاستعلام
query = """
SELECT page_title
FROM linktarget
JOIN categorylinks ON cl_target_id = lt_id
JOIN page ON page_id = cl_from
WHERE lt_namespace = 14
  AND lt_title = 'جميع_مقالات_البذور'
  AND page_namespace = 0
  AND page_len > 3000
  AND NOT EXISTS (
    SELECT 1
    FROM categorylinks
    JOIN linktarget ON lt_id = cl_target_id
    WHERE cl_from = page_id
      AND lt_namespace = 14
      AND lt_title = 'بذور_طويلة_ذات_نثر_قصير'
  )
ORDER BY page_len DESC
LIMIT 50000;
"""

# الاتصال
conn = toolforge.connect('arwiki', 'analytics')
cursor = conn.cursor()

cursor.execute(query)
results = cursor.fetchall()

stub_regex = re.compile(r'\{\{\s*بذرة[^}]*\}\}\s*', re.IGNORECASE)

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page = pywikibot.Page(site, title)

    try:
        if not page.exists() or page.isRedirectPage():
            continue

        old_text = page.text
        new_text = stub_regex.sub('', old_text)
        new_text = re.sub(r'\n{3,}', '\n\n', new_text).strip()

        if old_text != new_text:
            page.text = new_text
            page.save(summary='بوت: إزالة قالب بذرة')

    except Exception:
        pass

cursor.close()
conn.close()
