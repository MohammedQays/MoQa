import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/المقالات الأكثر تحريرا في الشهر الماضي"
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

# الوقت الحالي
now = datetime.now(timezone.utc)
time_part = now.strftime("%H:%M")
day = str(int(now.strftime("%d")))
month_en = now.strftime("%B")
month_ar = arabic_months[month_en]
year = now.strftime("%Y")
formatted_time = f"{time_part}، {day} {month_ar} {year} (ت ع م)"

# SQL query
query = """
SELECT
  page_title AS Title,
  COUNT(rev_id) AS Revisions
FROM page
JOIN revision ON page_id = rev_page
WHERE rev_timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND page_namespace = 0
GROUP BY page_title
ORDER BY Revisions DESC
LIMIT 100;
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

# بناء محتوى التقرير
page_content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''قائمة بأكثر المقالات التي حُررت في ويكيبيديا العربية خلال الثلاثين يومًا الماضية.'''
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
! الصفحة
! عدد التعديلات
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    revisions_count = row[1]
    page_link = f"[[{title}]]"
    page_content += f"|-\n| {page_link} || {revisions_count}\n"

page_content += "|}\n</div>\n</center>"

# نشر التقرير
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
