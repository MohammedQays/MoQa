# lonstub.py

import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/أطول البذور"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"  # اجعلها "yes" للتجربة بدون نشر

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
formatted_time = f"<onlyinclude>{time_part}، {day} {month_ar} {year} (ت ع م)</onlyinclude>"

# استعلام SQL
query = """
SELECT
  p.page_title,
  p.page_len,
  ROUND(p.page_len / 6) AS word_count_estimate
FROM page p
JOIN categorylinks cl ON cl.cl_from = p.page_id
JOIN linktarget lt ON lt.lt_id = cl.cl_target_id
WHERE
  lt.lt_title LIKE 'بذرة%'
  AND p.page_namespace = 0
  AND p.page_len > 4000
GROUP BY
  p.page_title, p.page_len
ORDER BY
  p.page_len DESC
LIMIT 1000;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء المحتوى
content = f"""قائمة بأطول المقالات المُصنفة كبذور (أكثر من 4000 بايت)؛ البيانات حتى الساعة {formatted_time}.

<center>
{{{{أرقام صفوف ثابتة}}}}
{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! العنوان
! الحجم (بايت)
! عدد الكلمات (تقديري)
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page_len = int(row[1])
    words = int(row[2])
    content += f"|-\n|[[{title.replace('_', ' ')}]]\n|{page_len}\n|{words}\n"

content += "|}\n</center>\n"

# النشر
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)

