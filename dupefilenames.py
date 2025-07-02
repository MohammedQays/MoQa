import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/أسماء ملفات مكررة إلى حد كبير"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

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

# استعلام SQL
query = """
SELECT
  LOWER(CONVERT(page_title USING utf8mb4)),
  GROUP_CONCAT(CONVERT(page_title USING utf8mb4) SEPARATOR '|'),
  COUNT(*)
FROM page
WHERE page_namespace = 6
AND page_is_redirect = 0
GROUP BY 1
HAVING COUNT(*) > 1
LIMIT 1000;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء التقرير
page_content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''ملفات لها نفس الاسم تقريبًا (باعتبار الأحرف الصغيرة) دون أن تكون تحويلات.'''
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
! أسماء الملفات المشابهة
! عدد التكرارات
! اسم الملف
"""

for row in results:
    lowercase_name = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    all_names = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
    count = row[2]
    file_links = [f"[[:ملف:{name.replace('_', ' ')}]]" for name in all_names.split("|")]
    files_column = "<br>".join(file_links)
    page_content += f"|-\n| {lowercase_name} || {count} || {files_column}\n"

page_content += "|}\n</div>\n</center>"

# نشر التقرير
report_page = pywikibot.Page(site, settings.report_title)

if settings.debug == "no":
    report_page.text = page_content
    report_page.save(settings.editsumm)
    print("تم تحديث التقرير.")
else:
    print("== Preview ==\n" + page_content)


