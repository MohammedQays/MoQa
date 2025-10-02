import pywikibot
import toolforge

# إعدادات البوت
class settings:
    editsumm = "[[وب:بوت|بوت]]: استيراد وحدة من الإنجليزية."
    debug = "no"  # اجعلها "no" للتشغيل الفعلي

# الاستعلام الجديد
query = """
SELECT DISTINCT
  CONCAT('[[:en:Module:', p.page_title, ']]') AS english_link,
  CONCAT('[[وحدة:', REPLACE(p.page_title, '_', ' '), ']]') AS arabic_suggested,
  p.page_title
FROM enwiki_p.page AS p
LEFT JOIN enwiki_p.langlinks AS ll
  ON ll.ll_from = p.page_id AND ll.ll_lang = 'ar'
LEFT JOIN enwiki_p.page_props AS pp
  ON pp.pp_page = p.page_id AND pp.pp_propname = 'wikibase_item'
WHERE p.page_namespace = 828
  AND p.page_title LIKE 'Location_map%'
  AND p.page_title NOT LIKE '%/doc%'
  AND p.page_title NOT LIKE '%/sandbox%'
  AND ll.ll_from IS NULL
  AND p.page_is_redirect = 0
  AND pp.pp_value IS NOT NULL
LIMIT 100;
"""

# الاتصال
site_en = pywikibot.Site('en', 'wikipedia')
site_ar = pywikibot.Site('ar', 'wikipedia')
conn = toolforge.connect('enwiki', 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# النتائج: (english_link, arabic_suggested, title)
titles = [row[2].decode("utf-8") if isinstance(row[2], bytes) else row[2] for row in results]

for title in titles:
    en_page = pywikibot.Page(site_en, f"Module:{title}")
    if not en_page.exists():
        continue

    text = en_page.text
    ar_title = f"وحدة:{title.replace('_', ' ')}"
    ar_page = pywikibot.Page(site_ar, ar_title)

    if ar_page.exists():
        print(f"✅ الصفحة موجودة مسبقًا: {ar_title}")
        continue

    if settings.debug == "no":
        ar_page.text = text
        ar_page.save(settings.editsumm)
        print(f"📄 أنشأت {ar_title}")
    else:
        print(f"== Preview إنشاء {ar_title} ==\n{text[:1000]}...\n")
