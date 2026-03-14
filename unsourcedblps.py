import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/سير أشخاص أحياء تحتوي على معلومات غير موثقة"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

# إعداد التاريخ
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
JOIN templatelinks tl ON tl.tl_from = p.page_id
JOIN linktarget lt_templ ON lt_templ.lt_id = tl.tl_target_id
JOIN categorylinks cl ON cl.cl_from = p.page_id
JOIN linktarget lt_cat ON lt_cat.lt_id = cl.cl_target_id
WHERE
  lt_cat.lt_title = 'أشخاص_أحياء'
  AND lt_templ.lt_namespace = 10
  AND lt_templ.lt_title = 'بحاجة_لمصدر'
  AND p.page_namespace = 0
LIMIT 500;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
page_content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''الصفحات في [[:تصنيف:أشخاص أحياء]] التي فيها [[قالب:بحاجة لمصدر]] (عرض أول 500 فقط).'''
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
! المقالة
"""

# إضافة الصفوف
for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    display_title = title.replace('_', ' ')
    page_content += f"|-\n| {{{{صت|1={display_title}}}}}\n"

page_content += "|}\n</div>\n</center>"

# نشر الصفحة
report_page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    report_page.text = page_content
    report_page.save(settings.editsumm)
else:
    print("== Preview ==\n" + page_content)


