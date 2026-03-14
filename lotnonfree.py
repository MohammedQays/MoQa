import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/صفحات تستعمل ملفات غير حرة بشكل زائد"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

# قائمة بأسماء الشهور بالعربية
arabic_months = {
    "January": "يناير",
    "February": "فبراير",
    "March": "مارس",
    "April": "أبريل",
    "May": "مايو",
    "June": "يونيو",
    "July": "يوليو",
    "August": "أغسطس",
    "September": "سبتمبر",
    "October": "أكتوبر",
    "November": "نوفمبر",
    "December": "ديسمبر",
}

# الحصول على الوقت الحالي بصيغة ت ع م
now = datetime.now(timezone.utc)
time_part = now.strftime("%H:%M")
day = str(int(now.strftime("%d")))  # إزالة الصفر من اليسار
month_en = now.strftime("%B")
month_ar = arabic_months[month_en]
year = now.strftime("%Y")
formatted_time = f"<onlyinclude>{time_part}، {day} {month_ar} {year} (ت ع م)</onlyinclude>"

# الاتصال بقاعدة البيانات
query = """
SELECT
  imgtmp.page_namespace,
  imgtmp.page_title,
  COUNT(*) AS num_links
FROM
  page AS pg1
JOIN categorylinks cl ON cl.cl_from = pg1.page_id
JOIN linktarget lt ON lt.lt_id = cl.cl_target_id
JOIN (
    SELECT
      pg2.page_namespace,
      pg2.page_title,
      il_to
    FROM page AS pg2
    JOIN imagelinks ON il_from = pg2.page_id
) AS imgtmp ON imgtmp.il_to = pg1.page_title
WHERE
  pg1.page_namespace = 6
  AND lt.lt_title = 'جميع_الملفات_غير_الحرة'
  AND imgtmp.page_namespace IN (0)
GROUP BY
  imgtmp.page_namespace,
  imgtmp.page_title
HAVING COUNT(*) > 6
ORDER BY COUNT(*) DESC;
"""

wiki = pywikibot.Site()

connectSuccess = False
tries = 0

while not connectSuccess:
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        print("Executing query...")
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        connectSuccess = True
        print("Query executed successfully.")
    except Exception as e:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        print("Error: ", e)
        tries += 1
        if tries > 5:
            print("Failed after several tries.")
            raise SystemExit(e)

# بناء محتوى الصفحة
page_content = f"""الصفحات التي تحتوي على عدد غير معتاد من الملفات غير الحرة؛ البيانات محدثة حتى الساعة {formatted_time}. يعمل البوت على تحديث هذا التقرير كل 7 أيام.

{{{{أرقام صفوف ثابتة}}}}
{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! الصفحة
!عدد الملفات غير الحرة
"""

for row in results:
    ns = row[0]
    title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
    count = row[2]

    # استخدام تنسيق مناسب للـ Namespace
    if ns == 0:
        full_title = f"[[{title}]]"
    else:
        namespace = wiki.namespaces[ns]
        full_title = f"[[{namespace}{title}]]"

    page_content += f"|-\n| {full_title} || {count}\n"

page_content += "|}"

# كتابة التقرير إلى ويكيبيديا
report_page = pywikibot.Page(wiki, settings.report_title)

if settings.debug == "no":
    try:
        report_page.text = page_content
        report_page.save(settings.editsumm)
        print(f"Report saved to {settings.report_title}")
    except Exception as e:
        print(f"Error while saving: {e}")
else:
    print("== Final Report Preview ==\n" + page_content)

