import pywikibot
import re
import toolforge

# Site setup
site = pywikibot.Site('ar', 'wikipedia')

# SQL query to get the articles
query = """
SELECT
  page_title,
  page_len,
  ((page_len / 6.0) / 300 * 40) + (page_len / 4000 * 60) AS score
FROM
  page
WHERE
  page_namespace = 0
  AND page_len BETWEEN 1000 AND 4000
  AND page_touched >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
  AND page_title NOT LIKE '%(توضيح)%'
  AND page_id NOT IN (
    SELECT cl_from
    FROM categorylinks
    WHERE cl_to IN (
      'صفحات_مجموعات_صيغ_كيميائية_مفهرسة',
      'جميع_المقالات_غير_المراجعة',
      'جميع_صفحات_توضيح_المقالات',
      'تحويلات_من_لغات_بديلة'
    ) OR cl_to LIKE 'بذرة%'
  )
ORDER BY
  score DESC
LIMIT 1000;
"""

conn = toolforge.connect('arwiki', 'analytics')
cursor = conn.cursor()

print("Run the query...")

cursor.execute(query)
results = cursor.fetchall()

print("Query finished, bot started...")

# Stub template regex
stub_template = "{{بذرة}}"
portal_template = "{{شريط بوابات|}}"
category_regex = re.compile(r'\[\[تصنيف:[^\]]*\]\]', re.IGNORECASE)

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page = pywikibot.Page(site, title)

    try:
        if not page.exists() or page.isRedirectPage():
            continue

        old_text = page.text

        # If the page contains the portal template, place the stub after it
        if portal_template in old_text:
            portal_pos = old_text.find(portal_template) + len(portal_template)
            new_text = old_text[:portal_pos] + "\n" + stub_template + "\n" + old_text[portal_pos:]
        elif category_regex.search(old_text):
            new_text = category_regex.sub(stub_template + "\n\\g<0>", old_text, count=1)
        else:
            new_text = old_text + "\n" + stub_template

        if old_text != new_text:
            page.text = new_text
            page.save(summary="بوت: إضافة قالب بذرة")

    except Exception:
        pass

cursor.close()
conn.close()
