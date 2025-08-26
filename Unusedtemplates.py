import pywikibot
import toolforge
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    base_report_title = "ويكيبيديا:تقارير قاعدة البيانات/قوالب غير مستخدمة"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"  # اجعلها yes للمعاينة فقط

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

# إعداد التاريخ الحالي
now = datetime.now(timezone.utc)
time_part = now.strftime("%H:%M")
day = str(int(now.strftime("%d")))
month_ar = arabic_months[now.strftime("%m")]
year = now.strftime("%Y")
formatted_time = f"{time_part}، {day} {month_ar} {year} (ت ع م)"

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
    AND page_title NOT REGEXP '/(شرح|ملعب|مختبر|rater-data\\.js)$'
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

# تقسيم النتائج إلى أجزاء فرعية (1000 نتيجة لكل صفحة)
chunk_size = 1000
chunks = [results[i:i+chunk_size] for i in range(0, len(results), chunk_size)]

# توليد الصفحات الفرعية فقط
for i, chunk in enumerate(chunks, start=1):
    subpage_title = f"{settings.base_report_title}/{i}"
    content = f"""قوالب غير مستخدمة؛ البيانات حتى الساعة <onlyinclude>{formatted_time}</onlyinclude>. يُحدَّث هذا التقرير يوميًا.

{{| class="wikitable sortable"
|- style="white-space: nowrap;"
! رقم
! القالب
! تاريخ الإنشاء
! آخر تعديل
! المؤلفون الفريدون
! المراجعات
"""

    for idx, row in enumerate(chunk, start=1):
        title = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
        first = format_timestamp_arabic(row[2])
        latest = format_timestamp_arabic(row[3])
        authors = row[4]
        revisions = row[5]
        content += f"|-\n| {idx} || [[:قالب:{title.replace('_', ' ')}]] || {first} || {latest} || {authors} || {revisions}\n"

    content += "|}"

    page = pywikibot.Page(site, subpage_title)
    if settings.debug == "no":
        page.text = content
        page.save(settings.editsumm)
    else:
        print(f"== Preview of {subpage_title} ==\n{content}")
