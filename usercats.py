import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    base_report_title = "ويكيبيديا:تقارير قاعدة البيانات/تصنيفات مستخدمون"
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
  page_title
FROM
  page
WHERE
  page_namespace = 14
  AND CONVERT(page_title USING utf8mb4) RLIKE '(?i)(ويكيبيديون|مستخدمون|مساهمون)';
"""

# الاتصال بقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# تقسيم النتائج إلى صفحات كل واحدة بها 200 نتيجة
titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]
chunk_size = 200
chunks = [titles[i:i + chunk_size] for i in range(0, len(titles), chunk_size)]

# إنشاء الصفحات الفرعية فقط
for i, chunk in enumerate(chunks, start=1):
    subpage_title = f"{settings.base_report_title}/{i}"
    content = f"""<center>
<div class="skin-invert" style="background: #E5E4E2; padding: 0.5em; font-family: Traditional Arabic; font-size: 130%; -moz-border-radius: 0.3em; border-radius: 0.3em;">
'''تصنيفات مرتبطة بالمستخدمين'''
<onlyinclude>
'''تم التحديث بواسطة [[مستخدم:MoQabot|MoQabot]] في: {formatted_time}'''
</onlyinclude>
</div>
</center>

__NOTOC__
{{{{أرقام صفوف ثابتة}}}}

{{| class="wikitable sortable static-row-numbers static-row-header-text"
! التصنيف
"""
    for title in chunk:
        content += f"|-\n| [[:تصنيف:{title.replace('_', ' ')}]]\n"
    content += "|}"

    # نشر الصفحة الفرعية فقط
    page = pywikibot.Page(site, subpage_title)
    if settings.debug == "no":
        page.text = content
        page.save(settings.editsumm)
    else:
        print(f"== Preview of {subpage_title} ==\n" + content)
