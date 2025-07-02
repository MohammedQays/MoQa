import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/تصانيف غير مصنفة"
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
  page_len,
  cat_pages,
  rev_timestamp,
  actor_name
FROM
  revision
  JOIN actor ON rev_actor = actor_id
  JOIN (
    SELECT
      page_id,
      page_title,
      page_len,
      cat_pages
    FROM
      category
      RIGHT JOIN page ON cat_title = page_title
      LEFT JOIN categorylinks ON page_id = cl_from
    WHERE
      cl_from IS NULL
      AND page_namespace = 14
      AND page_is_redirect = 0
  ) AS pagetmp ON rev_page = pagetmp.page_id
  AND rev_timestamp = (
    SELECT
      MAX(rev_timestamp)
    FROM
      revision AS last
    WHERE
      last.rev_page = pagetmp.page_id
  )
ORDER BY
  page_len DESC
LIMIT 500;
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
'''تصانيف غير مصنفة. هذه القائمة تشمل تصانيف في نطاق التصانيف ([[ويكيبيديا:تصنيف]]) لكنها غير موجودة في أي تصنيف آخر.'''
<onlyinclude>
'''حُدِّثت القائمة بواسطة [[مستخدم:MoQabot|MoQabot]] في: {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; -moz-border-radius: 0.3em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! التصنيف
! حجم الصفحة (بايت)
! عدد الصفحات في التصنيف
! آخر تعديل
! اسم المحرر
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page_len = row[1]
    cat_pages = row[2]
    
    ts_str = row[3].decode("utf-8") if isinstance(row[3], bytes) else row[3]
    rev_timestamp_dt = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
    rev_timestamp = rev_timestamp_dt.strftime("%Y-%m-%d %H:%M")
    
    actor = row[4]

    content += f"|-\n| [[:تصنيف:{title.replace('_', ' ')}]] || {page_len} || {cat_pages} || {rev_timestamp} || {actor}\n"

content += "|}\n</div>\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)
