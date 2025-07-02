import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/صفحات في نطاق المستخدم ليس لها حساب مسجل"
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

# استعلام Ownerless pages in user space
query = """
SELECT
  page.page_namespace,
  page.page_title,
  page.page_len,
  rev.rev_timestamp,
  actor.actor_name
FROM
  page
LEFT JOIN user ON user.user_name = REPLACE(SUBSTRING_INDEX(page.page_title, '/', 1), '_', ' ')
LEFT JOIN revision AS rev ON rev.rev_page = page.page_id
LEFT JOIN actor ON actor.actor_id = rev.rev_actor
WHERE
  page.page_namespace IN (2, 3)
  AND page.page_is_redirect = 0
  AND user.user_name IS NULL
  AND rev.rev_timestamp = (
    SELECT MIN(rev2.rev_timestamp)
    FROM revision AS rev2
    WHERE rev2.rev_page = page.page_id
  )
ORDER BY
  page.page_len DESC
LIMIT 500;
"""

site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''صفحات المستخدمين التي لا يملكها أي مستخدم مسجل'''
<onlyinclude>
'''حُدِّث التقرير بواسطة [[مستخدم:MoQabot|MoQabot]] في: {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; -moz-border-radius: 0.3em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! صفحة المستخدم
! حجم الصفحة (بايت)
! اسم المنشئ
! تاريخ الإنشاء
"""

for row in results:
    ns = row[0]
    title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
    page_len = row[2]

    ts_raw = row[3]
    if isinstance(ts_raw, bytes):
        ts_raw = ts_raw.decode("utf-8")
    # تحويل الطابع الزمني rev_timestamp من الصيغة yyyymmddhhmmss إلى datetime
    rev_timestamp_dt = datetime.strptime(ts_raw, "%Y%m%d%H%M%S") if ts_raw else None
    rev_timestamp = rev_timestamp_dt.strftime("%Y-%m-%d %H:%M") if rev_timestamp_dt else "غير معروف"

    actor = row[4].decode("utf-8") if (row[4] and isinstance(row[4], bytes)) else (row[4] or "غير معروف")

    content += f"|-\n| [[مستخدم:{title.replace('_', ' ')}]] || {page_len} || {actor} || {rev_timestamp}\n"

content += "|}\n</div>\n</center>\n"

page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
