import pywikibot
import toolforge
import re
from collections import defaultdict
from datetime import datetime, timezone

# إعدادات البوت
class settings:
    lang = 'arwiki'
    target_page = "مستخدم:Mohammed Qays/ملعب 21"
    editsumm = "[[وب:بوت|بوت]]: تصنيف مقالات مرجع معجمي حسب الرمز"
    debug = "no"

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

# الرموز المعتمدة
symbols = [
    "إحاطة", "أسماء", "أعلام", "الأندلس", "بلدان", "بواب", "ت", "تاج", "تفسير", "تكملة", "ث",
    "الجامع", "حتي", "حياة", "الحيوان", "دي", "ديوان", "الروض", "الشهابي", "ص", "طبي موحد", "ع",
    "عجائب", "العقار", "عمدة", "غ", "ق", "كبير", "ل", "لاروس", "م", "محكم", "محيط", "محيط المحيط",
    "مرعشي", "مزهر", "مصطلحات", "معاني", "معلمة", "مغني أكبر", "مقالات", "منهل", "مورد",
    "مورد حديث", "موسوعة", "نفح", "نزهة", "وسيط"
]

# تنفيذ الاستعلام
query = """
SELECT DISTINCT 
  p.page_title
FROM 
  templatelinks AS tl
JOIN 
  linktarget AS lt ON tl.tl_target_id = lt.lt_id
JOIN 
  page AS p ON tl.tl_from = p.page_id
WHERE 
  lt.lt_namespace = 10
  AND lt.lt_title IN ("مرجع_معجمي", "مرمع")
  AND p.page_namespace = 0
LIMIT 1000;
"""

site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تخزين النتائج
categorized = defaultdict(set)

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    pages = cursor.fetchall()

# معالجة كل مقالة
for row in pages:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    try:
        page = pywikibot.Page(site, title)
        text = page.text
    except Exception as e:
        print(f"تخطي [[{title}]] بسبب: {e}")
        continue

    # استخراج قوالب مرجع معجمي
    for match in re.finditer(r"\{\{مرجع معجمي\|([^|{}\n]+).*?\}\}", text):
        symbol = match.group(1).strip()
        if symbol in symbols:
            categorized[symbol].add(title)

# بناء المحتوى الجديد للصفحة
content = f"""<div class="plainlinks" style="background: #E5E4E2; padding: 0.5em;">
'''تحديث تلقائي باستخدام البوت بتاريخ {formatted_time}'''
</div>

__NOTOC__
"""

for symbol in symbols:
    if symbol in categorized:
        content += f"\n== {symbol} ==\n"
        for t in sorted(categorized[symbol]):
            content += f"# [[{t}]]\n"

# نشر أو معاينة
target = pywikibot.Page(site, settings.target_page)
if settings.debug == "no":
    target.text = content
    target.save(settings.editsumm)
else:
    print(content)
