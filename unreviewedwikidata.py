import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/مقالات غير مراجعة غير مرتبطة بويكي بيانات"
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

# الاستعلام
query = """
SELECT
  p.page_title,
  MIN(r.rev_timestamp) AS creation_date
FROM page p
JOIN revision r
  ON r.rev_page = p.page_id
JOIN categorylinks cl
  ON cl.cl_from = p.page_id
JOIN linktarget lt
  ON lt.lt_id = cl.cl_target_id
WHERE lt.lt_title = 'جميع_المقالات_غير_المراجعة'
  AND lt.lt_namespace = 14
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND NOT EXISTS (
    SELECT 1
    FROM langlinks ll
    WHERE ll.ll_from = p.page_id
  )
GROUP BY p.page_id
ORDER BY creation_date ASC
LIMIT 1000;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# تحويل التاريخ
def format_ts(ts):
    ts = ts.decode() if isinstance(ts, bytes) else ts
    dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d")

# بناء التقرير
content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; border-radius: 0.3em;">
'''مقالات غير مراجعة غير مرتبطة بويكي بيانات'''
<onlyinclude>
'''حُدِّثت هذه القائمة بواسطة [[مستخدم:MoQabot|MoQabot]] في : {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! المقالة
! تاريخ الإنشاء
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    creation_date = format_ts(row[1])
    content += f"|-\n| [[{title.replace('_', ' ')}]] || {creation_date}\n"

content += "|}\n</div>\n</center>\n"

# نشر الصفحة
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
