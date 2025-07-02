import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/أخطاء الربط"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"  # اجعلها "yes" للتجربة دون نشر

# إعداد التاريخ بالتنسيق العربي
arabic_months = {
    "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل",
    "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس",
    "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر",
}
now = datetime.now(timezone.utc)
time_part = now.strftime("%H:%M")
day = str(int(now.strftime("%d")))
month_ar = arabic_months[now.strftime("%B")]
year = now.strftime("%Y")
formatted_time = f"{time_part}، {day} {month_ar} {year} (ت ع م)"

# استعلام SQL مع ترتيب تنازلي
query = """
SELECT
  p1.page_title,
  COUNT(*) AS count
FROM
  page AS p1
  JOIN categorylinks ON p1.page_id = cl_from
  JOIN linktarget ON p1.page_title = lt_title AND lt_namespace = 0
  JOIN pagelinks ON pl_target_id = lt_id
  JOIN page AS p2 ON pl_from = p2.page_id AND p2.page_namespace = 0
WHERE
  p1.page_namespace = 0
  AND p1.page_is_redirect = 1
  AND cl_to = 'تحويلات'
  AND NOT(p1.page_id = p2.page_id)
GROUP BY
  p1.page_title
ORDER BY
  count DESC
LIMIT 1000;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''أخطاء ربط داخلية عبر تحويلات خاطئة. تشير القائمة إلى صفحات ترتبط مباشرةً بتحويلات بدلًا من المقالات الأصلية.'''
<onlyinclude>
'''حَدَّث [[مستخدم:MoQabot|MoQabot]] هذه القائمة في : {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; -moz-border-radius: 0.3em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! العنوان
! عدد مرات الربط الخاطئ
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    count = row[1]
    content += f"|-\n| [[{title.replace('_', ' ')}]] || {count}\n"

content += "|}\n</div>\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
