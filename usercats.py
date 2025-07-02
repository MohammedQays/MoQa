import pywikibot
import toolforge

# إعدادات البوت
class settings:
    lang = 'arwiki'
    base_report_title = "ويكيبيديا:تقارير قاعدة البيانات/تصنيفات مستخدمون"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"  # اجعلها "yes" للتجربة دون نشر

# الاستعلام المطلوب
query = """
SELECT
  page_title
FROM
  page
WHERE
  page_namespace = 14
  AND CONVERT(page_title USING utf8mb4) RLIKE '(?i)(ويكيبيديون|مستخدمون|مساهمون)';
"""

# الاتصال بقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# تقسيم النتائج إلى صفحات فرعية بحجم 200
titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]
chunk_size = 200
chunks = [titles[i:i + chunk_size] for i in range(0, len(titles), chunk_size)]

# إنشاء الصفحات الفرعية فقط
for i, chunk in enumerate(chunks, start=1):
    subpage_title = f"{settings.base_report_title}/{i}"
    content = """__NOTOC__

{{أرقام صفوف ثابتة}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! التصنيف
"""
    for title in chunk:
        content += f"|-\n| [[:تصنيف:{title.replace('_', ' ')}]]\n"

    content += "|}"

    # نشر الصفحة الفرعية
    page = pywikibot.Page(site, subpage_title)
    if settings.debug == "no":
        page.text = content
        page.save(settings.editsumm)
    else:
        print(f"== Preview of {subpage_title} ==\n" + content)
