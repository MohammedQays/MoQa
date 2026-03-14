# conflictedfiles.py

import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/ملفات ذات تصنيف متضارب"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"  # اجعلها "yes" للمعاينة فقط بدون حفظ

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
  p.page_title
FROM page p
JOIN categorylinks c1 ON c1.cl_from = p.page_id
JOIN linktarget lt1 ON lt1.lt_id = c1.cl_target_id
JOIN categorylinks c2 ON c2.cl_from = p.page_id
JOIN linktarget lt2 ON lt2.lt_id = c2.cl_target_id
WHERE
  p.page_namespace = 6
  AND lt1.lt_title = 'جميع_الملفات_الحرة'
  AND lt2.lt_title = 'جميع_الملفات_غير_الحرة';
"""

# الاتصال بويكي وقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
page_content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''الملفات المدرجة في تصنيفي [[:تصنيف:جميع الملفات الحرة]] و[[:تصنيف:جميع الملفات غير الحرة]] في آنٍ واحد.'''
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
! الملف
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    file_link = f"[[:ملف:{title.replace('_', ' ')}]]"
    page_content += f"|-\n| {file_link}\n"

page_content += "|}\n</div>\n</center>"

# نشر التقرير
report_page = pywikibot.Page(site, settings.report_title)

if settings.debug == "no":
    report_page.text = page_content
    report_page.save(settings.editsumm)
    print("تم تحديث التقرير.")
else:
    print("== Preview ==\n" + page_content)

