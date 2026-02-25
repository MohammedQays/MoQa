import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "ويكيبيديا:تقارير قاعدة البيانات/قوالب تحوي وصلات لصفحات التوضيح"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

# الوقت الحالي
now = datetime.now(timezone.utc)
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
formatted_time = f"{now.strftime('%H:%M')}، {int(now.strftime('%d'))} {arabic_months[now.strftime('%B')]} {now.strftime('%Y')} (ت ع م)"

# الاستعلام
query = """
SELECT
  pltmp.page_title AS template_title,
  pltmp.lt_title AS disambiguation_title,
  (
    SELECT COUNT(*)
    FROM templatelinks
    JOIN linktarget ON tl_target_id = lt_id
    WHERE lt_namespace = 10
      AND lt_title = pltmp.page_title
  ) AS transclusions_count
FROM
  (
    SELECT
      page_namespace,
      page_title,
      lt_namespace,
      lt_title
    FROM page
    JOIN pagelinks ON pl_from = page_id
    JOIN linktarget ON pl_target_id = lt_id
    WHERE page_namespace = 10
      AND lt_namespace = 0
  ) AS pltmp
JOIN page AS pg2
  ON pltmp.lt_namespace = pg2.page_namespace
  AND pltmp.lt_title = pg2.page_title
WHERE EXISTS (
    SELECT 1
    FROM categorylinks
    WHERE pg2.page_id = cl_from
      AND cl_to = 'جميع_صفحات_التوضيح'
)
ORDER BY transclusions_count DESC;
"""

wiki = pywikibot.Site()
connectSuccess = False
tries = 0

while not connectSuccess:
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        connectSuccess = True
    except Exception as e:
        tries += 1
        if tries > 5:
            raise SystemExit(e)

# بناء محتوى الصفحة
page_content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; border-radius: 0.3em;">
'''قائمة بالقوالب التي تحتوي على وصلات إلى صفحات توضيح.'''
<onlyinclude>
'''حَدَّث [[مستخدم:MoQabot|MoQabot]] هذه القائمة في : {formatted_time}'''
</onlyinclude>
</div>
</center>

<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; border-radius: 0.3em;">
__NOTOC__

{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! القالب
! صفحة التوضيح
! عدد التضمينات
"""

for row in results:
    template_title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    disamb_title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
    transclusions = row[2]

    template_link = f"[[قالب:{template_title}|{template_title}]]"
    disamb_link = f"[[{disamb_title}]]"

    page_content += f"|-\n| {template_link} || {disamb_link} || {transclusions}\n"

page_content += "|}\n</div>\n</center>"

report_page = pywikibot.Page(wiki, settings.report_title)

if settings.debug == "no":
    report_page.text = page_content
    report_page.save(settings.editsumm)
else:
    print(page_content)
