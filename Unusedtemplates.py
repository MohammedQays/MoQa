import pywikibot
import toolforge
from datetime import datetime, timezone
import math

# إعدادات البوت
class settings:
    lang = 'arwiki'
    base_report_title = "ويكيبيديا:تقارير قاعدة البيانات/قوالب غير مستخدمة"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

# قائمة الشهور بالعربية
arabic_months = {
    "01": "يناير", "02": "فبراير", "03": "مارس", "04": "أبريل",
    "05": "مايو", "06": "يونيو", "07": "يوليو", "08": "أغسطس",
    "09": "سبتمبر", "10": "أكتوبر", "11": "نوفمبر", "12": "ديسمبر",
}

# تحويل طابع زمني إلى تاريخ بصيغة عربية
def format_timestamp_arabic(ts_bytes):
    ts = ts_bytes.decode("utf-8") if isinstance(ts_bytes, bytes) else ts_bytes
    if len(ts) >= 8:
        year = ts[:4]
        month = ts[4:6]
        day = str(int(ts[6:8]))
        return f"{day} {arabic_months.get(month, month)} {year}"
    return ts  # fallback

# الوقت الحالي
now = datetime.now(timezone.utc)
time_part = now.strftime("%H:%M")
day = str(int(now.strftime("%d")))
month_ar = arabic_months[now.strftime("%m")]
year = now.strftime("%Y")
formatted_time = f"<onlyinclude>{time_part}، {day} {month_ar} {year} (ت ع م)</onlyinclude>"

# الاستعلام
query = """
SELECT
    page_id,
    page_title,
    MIN(rev_timestamp) AS first_edit,
    MAX(rev_timestamp) AS latest_edit,
    COUNT(DISTINCT rev_actor) AS unique_authors,
    COUNT(rev_id) AS revisions
FROM
    page
LEFT JOIN linktarget ON page_namespace = lt_namespace AND page_title = lt_title
LEFT JOIN templatelinks ON tl_target_id = lt_id
LEFT JOIN revision ON page_id = rev_page
WHERE
    page_namespace = 10
    AND page_is_redirect = 0
    AND tl_target_id IS NULL
    AND page_title NOT IN (
        SELECT page_title
        FROM page
        JOIN categorylinks ON page_id = cl_from
        WHERE cl_to IN (
            'قوالب_تنسخ', 'قوالب_لا_تضمن', 'قوالب_مستخدم_لغات', 'مختبرات_قوالب', 'ملاعب_قوالب'
        )
        AND page_namespace = 10
    )
GROUP BY page_id, page_title
ORDER BY page_title ASC;
"""

# الاتصال بويكيبيديا وقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# تقسيم النتائج
chunk_size = 1000
chunks = [results[i:i+chunk_size] for i in range(0, len(results), chunk_size)]

# توليد الصفحات
page_titles = []
for i, chunk in enumerate(chunks, start=1):
    report_title = f"{settings.base_report_title}/{i}"
    page_titles.append(report_title)
    content = f"""قوالب غير مستخدمة؛ البيانات حتى الساعة {formatted_time}. يُحدَّث هذا التقرير يوميًا.

{{{{أرقام صفوف ثابتة}}}}
{{| class="wikitable sortable static-row-numbers static-row-header-text"
|- style="white-space: nowrap;"
! القالب
! تاريخ الإنشاء
! آخر تعديل
! المؤلفون الفريدون
! المراجعات
"""

    for row in chunk:
        title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
        first = format_timestamp_arabic(row[2])
        latest = format_timestamp_arabic(row[3])
        authors = row[4]
        revisions = row[5]
        content += f"|-\n| [[:قالب:{title}|{title.replace('_', ' ')}]] || {first} || {latest} || {authors} || {revisions}\n"

    content += "|}"

    page = pywikibot.Page(site, report_title)
    if settings.debug == "no":
        page.text = content
        page.save(settings.editsumm)
    else:
        print(f"== {report_title} ==\n{content}")

# إنشاء صفحة الفهرس
index_content = f"""قوالب غير مستخدمة؛ البيانات حتى الساعة {formatted_time}. يُحدَّث هذا التقرير يوميًا.

== الصفحات ==
"""
for idx, title in enumerate(page_titles, start=1):
    index_content += f"# [[{title}|صفحة {idx}]]\n"

index_page = pywikibot.Page(site, settings.base_report_title)
if settings.debug == "no":
    index_page.text = index_content
    index_page.save(settings.editsumm)
else:
    print("== Index Preview ==\n" + index_content)




