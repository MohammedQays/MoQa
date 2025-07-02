import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/ملفات غير حرة كثيرة الاستخدام"
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
  page_title,
  COUNT(*)
FROM
  imagelinks
  JOIN (
    SELECT
      page_id,
      page_title
    FROM
      page
      JOIN categorylinks ON cl_from = page_id
    WHERE
      cl_to = 'جميع_الملفات_غير_الحرة'
      AND page_namespace = 6
  ) AS pgtmp ON pgtmp.page_title = il_to
GROUP BY
  il_to
HAVING
  COUNT(*) > 4
ORDER BY
  COUNT(*) DESC
  LIMIT 100;
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
'''الملفات غير الحرة المستخدمة في أكثر من أربع صفحات.'''
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
! الملف
! عدد الاستخدامات
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    count = row[1]
    content += f"|-\n| [[:ملف:{title.replace('_', ' ')}]] || {count}\n"

content += "|}\n</div>\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
