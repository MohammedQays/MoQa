import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/تحويلات قسم مكسورة"
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

# استعلام SQL المعدل لاختيار التحويلات التي تحتوي على #
query = """
SELECT
  page.page_id,
  redirect.rd_title AS target_title,
  GROUP_CONCAT(CONCAT(page.page_id, '|', page.page_title) SEPARATOR '\n') AS redirects
FROM
  page
JOIN redirect
  ON redirect.rd_from = page.page_id
WHERE
  page.page_namespace = 0
  AND redirect.rd_title LIKE '%#%'
GROUP BY
  redirect.rd_title
LIMIT 4500;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# رأس الصفحة + تنسيق العرض
page_content = """<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''تحويلات تشير إلى أقسام غير موجودة'''
<onlyinclude>
'''حَدَّث [[مستخدم:MoQabot|MoQabot]] هذه القائمة في : {formatted_time} '''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; -moz-border-radius: 0.3em; border-radius: 0.3em;">
__NOTOC__

{{| class="wikitable sortable plainlinks" style="text-align: right;"
|- style="white-space:nowrap;"
! ت.
! التحويلة
! الهدف
! الروابط<br />الواردة
! المشاهدات
! الحد الأقصى<br />مشاهدات/روابط
""".format(formatted_time=formatted_time)

# توليد الصفوف
index = 1
for row in results:
    page_id = row[0]
    target_title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
    redirect_data = row[2].decode("utf-8") if isinstance(row[2], bytes) else row[2]
    redirect_lines = redirect_data.strip().split("\n")

    for line in redirect_lines:
        parts = line.split('|')
        if len(parts) != 2:
            continue
        pid, title = parts
        title_display = title.replace('_', ' ')

        page_content += """|- style="vertical-align: top;"
| {index}
| [{{{{fullurl:{title_display}|redirect=no}}}} {title_display}]
| [[{target_title}]]
| —
| —
| —
""".format(index=index, title_display=title_display, target_title=target_title)

        index += 1

# نهاية الجدول
page_content += "\n|}\n</div>\n</center>"

# نشر أو معاينة التقرير
report_page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    report_page.text = page_content
    report_page.save(settings.editsumm)
    print("تم تحديث التقرير.")
else:
    print("== Preview ==\n" + page_content)


