import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/قوالب تحوي ملفات غير حرة"
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

# الاستعلام المطلوب
query = """
SELECT
  imgtmp.page_title,
  COUNT(cl_to)
FROM
  page AS pg1
  JOIN categorylinks ON cl_from = pg1.page_id
  JOIN (
    SELECT
      pg2.page_namespace,
      pg2.page_title,
      il_to
    FROM
      page AS pg2
      JOIN imagelinks ON il_from = page_id
    WHERE
      pg2.page_namespace = 10
  ) AS imgtmp ON il_to = pg1.page_title
WHERE
  pg1.page_namespace = 6
  AND cl_to = 'جميع_الملفات_غير_الحرة'
GROUP BY
  imgtmp.page_namespace,
  imgtmp.page_title
ORDER BY
  COUNT(cl_to) ASC;
"""

# الاتصال بقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''قوالب تحوي ملفات غير حرة'''
<onlyinclude>
'''حُدِّثت هذه القائمة بواسطة [[مستخدم:MoQabot|MoQabot]] في : {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; -moz-border-radius: 0.3em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! القالب
! عدد الملفات غير الحرة
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    count = row[1]
    content += f"|-\n| [[قالب:{title.replace('_', ' ')}]] || {count}\n"

content += "|}\n</div>\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
