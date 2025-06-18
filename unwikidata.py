import pywikibot
import toolforge
from datetime import datetime, timezone
import unicodedata  # استيراد مكتبة normalizer

# إعدادات البوت
class settings:
    lang = 'arwiki'
    report_title = "مستخدم:Mohammed Qays/ويكي بيانات"
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
formatted_time = f"<onlyinclude>{time_part}، {day} {month_ar} {year} (ت ع م)</onlyinclude>"

# استعلام SQL مع تنسيق التاريخ العربي
query = """
SELECT
  p.page_title,
  COALESCE(creator.actor_name, '') AS creator_user,
  DATE_FORMAT(MIN(r.rev_timestamp), '%d-%m-%Y') AS creation_date,
  COALESCE(editor.actor_name, '') AS last_editor_user,
  DATE_FORMAT(MAX(r.rev_timestamp), '%d-%m-%Y') AS last_edit_date
FROM page p
LEFT JOIN page_props pp ON p.page_id = pp.pp_page AND pp.pp_propname = 'wikibase_item'
JOIN revision r ON r.rev_page = p.page_id
LEFT JOIN actor creator ON creator.actor_id = (
  SELECT rev_actor FROM revision
  WHERE rev_page = p.page_id
  ORDER BY rev_timestamp ASC
  LIMIT 1
)
LEFT JOIN actor editor ON editor.actor_id = (
  SELECT rev_actor FROM revision
  WHERE rev_page = p.page_id
  ORDER BY rev_timestamp DESC
  LIMIT 1
)
WHERE pp.pp_propname IS NULL
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
GROUP BY p.page_id, p.page_title
LIMIT 1000;
"""

# الاتصال
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# بناء محتوى التقرير
content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''الصفحات التي لا تحتوي على ويكي بيانات. تشير القائمة إلى الصفحات التي لم يتم ربطها بأي عنصر ويكي بيانات.'''
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
! العنوان
! تاريخ الإنشاء
! منشئ المقال
! آخر تعديل
! آخر محرر
"""

for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    creation_date = row[2]
    creator_user = f"{{{{مس|{row[1].decode('utf-8') if isinstance(row[1], bytes) else row[1]}}}}}" if row[1] else "غير معروف"
    last_edit_date = row[4]
    last_editor_user = f"{{{{مس|{row[3].decode('utf-8') if isinstance(row[3], bytes) else row[3]}}}}}" if row[3] else "غير معروف"

    # تنظيف النصوص باستخدام normalizer
    creator_user = unicodedata.normalize('NFC', creator_user)
    last_editor_user = unicodedata.normalize('NFC', last_editor_user)

    content += f"|-\n| [[{title.replace('_', ' ')}]] || {creation_date} || {creator_user} || {last_edit_date} || {last_editor_user}\n"

content += "|}\n</div>\n</center>\n"

# نشر التقرير
page = pywikibot.Page(site, settings.report_title)
if settings.debug == "no":
    page.text = content
    page.save(settings.editsumm)
else:
    print("== Preview ==\n" + content)



