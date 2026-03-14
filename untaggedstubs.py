import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/البذور غير الموسومة"
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
  ((p.page_len / 6.0) / 300 * 40) + (p.page_len / 4000 * 60) AS score
FROM page p
WHERE
  p.page_namespace = 0
  AND p.page_len BETWEEN 1000 AND 4000
  AND p.page_touched >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
  AND p.page_title NOT LIKE '%(توضيح)%'
  AND p.page_id NOT IN (
    SELECT cl.cl_from
    FROM categorylinks cl
    JOIN linktarget lt ON lt.lt_id = cl.cl_target_id
    WHERE lt.lt_title IN (
      'صفحات_مجموعات_صيغ_كيميائية_مفهرسة',
      'جميع_المقالات_غير_المراجعة',
      'جميع_صفحات_توضيح_المقالات',
      'تحويلات_من_لغات_بديلة'
    ) OR lt.lt_title LIKE 'بذرة%'
  )
ORDER BY
  score DESC
LIMIT 1000;
"""

# الاتصال بويكيبيديا وقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
content = f"""بُذور غير مُعَلَّمة (مُقتصرة على أول 1000 مُدخل)؛ البيانات حتى الساعة {formatted_time}. يُحدَّث هذا التقرير كل 7 أيام.

<center>
{{{{أرقام صفوف ثابتة}}}}
{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! العنوان
! الحجم بالكيلوبايت
! عدد الكلمات (تقديري)
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page_len = int(row[1])
    score = round(row[2])
    kb_size = round(page_len / 1024, 1)
    content += f"|-\n|[[{title.replace('_', ' ')}]]\n|{kb_size}\n|{score}\n"

content += "|}\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)


