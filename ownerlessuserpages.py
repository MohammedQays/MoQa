import pywikibot
import toolforge
from datetime import datetime, timezone

class settings:
    lang = 'arwiki'
    report_base = "ويكيبيديا:تقارير قاعدة البيانات/صفحات في نطاق المستخدم ليس لها حساب مسجل"
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

query_template = """
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
  page.page_namespace = {namespace}
  AND page.page_is_redirect = 0
  AND user.user_name IS NULL
  AND rev.rev_timestamp = (
    SELECT MIN(rev2.rev_timestamp)
    FROM revision AS rev2
    WHERE rev2.rev_page = page.page_id
  )
ORDER BY
  page.page_len DESC
LIMIT 1000;
"""

def make_report(namespace: int, page_title: str):
    ns_label = "مستخدم" if namespace == 2 else "نقاش المستخدم"
    query = query_template.format(namespace=namespace)
    conn = toolforge.connect(settings.lang, 'analytics')

    with conn.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; border-radius: 0.3em;">
'''صفحات في نطاق {ns_label} ليس لها [[خاص:ListUsers|حساب مسجل]]'''

'''حُدِّث التقرير بواسطة [[مستخدم:MoQabot|MoQabot]] في:<onlyinclude> {formatted_time} </onlyinclude>'''
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; border-radius: 0.3em;">

{{| class="wikitable"
! ت
! صفحة المستخدم
! حجم الصفحة (بايت)
! اسم المنشئ
! تاريخ الإنشاء
"""

    counter = 1
    for row in results:
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

        page_link = f"[[{ns_label}:{title.replace('_', ' ')}]]"
        content += f"|-\n| {counter} || {page_link} || {page_len} || {actor} || {rev_timestamp}\n"
        counter += 1

    content += "|}\n</div>\n</center>\n"

    site = pywikibot.Site()
    page = pywikibot.Page(site, page_title)
    if settings.debug == "no":
        page.text = content
        page.save(settings.editsumm)
    else:
        print(f"== Preview for {page_title} ==\n{content}")

# توليد التقارير لكلا النطاقين
make_report(namespace=2, page_title=f"{settings.report_base}/1")  # مستخدم
make_report(namespace=3, page_title=f"{settings.report_base}/2")  # نقاش المستخدم
