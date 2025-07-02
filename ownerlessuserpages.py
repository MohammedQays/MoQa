import pywikibot
import toolforge
from datetime import datetime, timezone

class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/صفحات في نطاق المستخدم ليس لها حساب مسجل"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

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
  page.page_namespace, page.page_len DESC
LIMIT 1000;
"""

site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# تقسيم النتائج حسب النطاق
results_by_ns = {2: [], 3: []}
for row in results:
    ns = row[0]
    if ns in results_by_ns:
        results_by_ns[ns].append(row)

# عنوان كل نطاق بالعربية
namespace_titles = {
    2: "صفحات المستخدمين (مستخدم:)",
    3: "صفحات نقاش المستخدمين (نقاش المستخدم:)",
}

content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; border-radius: 0.3em;">
'''صفحات المستخدمين التي لا يملكها أي مستخدم مسجل'''
<onlyinclude>
'''حُدِّث التقرير بواسطة [[مستخدم:MoQabot|MoQabot]] في: {formatted_time}'''
</onlyinclude>
</div>
</center>
"""

for ns in [2, 3]:
    rows = results_by_ns[ns]
    if not rows:
        continue
    content += f"""
<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; border-radius: 0.3em;">
== {namespace_titles[ns]} ==

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! صفحة المستخدم
! حجم الصفحة (بايت)
! اسم المنشئ
! تاريخ الإنشاء
"""

    for row in rows:
        ns, title, page_len, ts_raw, actor_raw = row

        title = title.decode("utf-8") if isinstance(title, bytes) else title
        actor = actor_raw.decode("utf-8") if (actor_raw and isinstance(actor_raw, bytes)) else (actor_raw or "غير معروف")

        if ts_raw:
            ts_raw = ts_raw.decode("utf-8") if isinstance(ts_raw, bytes) else ts_raw
            try:
                rev_timestamp_dt = datetime.strptime(ts_raw, "%Y%m%d%H%M%S")
                rev_timestamp = rev_timestamp_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                rev_timestamp = "غير معروف"
        else:
            rev_timestamp = "غير معروف"

        ns_prefix = "مستخدم" if ns == 2 else "نقاش المستخدم"
        page_link = f"[[{ns_prefix}:{title.replace('_', ' ')}]]"

        content += f"|-\n| {page_link} || {page_len} || {actor} || {rev_timestamp}\n"

    content += "|}\n</div>\n</center>\n"

page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
