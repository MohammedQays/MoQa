import pywikibot
import re
import toolforge

# Site setup
site = pywikibot.Site('ar', 'wikipedia')

# SQL query
query = """
/* longstubs.rs SLOW_OK */
SELECT
    page_title,
    page_len
FROM page
INNER JOIN categorylinks
    ON categorylinks.cl_from = page.page_id
INNER JOIN linktarget
    ON categorylinks.cl_target_id = linktarget.lt_id
WHERE
    linktarget.lt_title LIKE 'بذرة%'
    AND page.page_namespace = 0
    AND page.page_len > 4000
GROUP BY page_title, page_len
ORDER BY page_len DESC
LIMIT 1000;
"""

conn = toolforge.connect('arwiki', 'analytics')
cursor = conn.cursor()

print("run the query...")

cursor.execute(query)
results = cursor.fetchall()

print("Query finished, bot run...")

# Stub template pattern
stub_template_regex = re.compile(r'\{\{\s*بذرة[^{}]*\}\}', re.IGNORECASE)

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page = pywikibot.Page(site, title)

    try:
        if not page.exists() or page.isRedirectPage():
            continue

        old_text = page.text
        new_text, count = stub_template_regex.subn('', old_text)

        if count > 0:
            page.text = new_text
            page.save(summary="بوت:إزالة قالب بذرة")

    except Exception:
        pass  # Ignore any errors without printing

cursor.close()
conn.close()

