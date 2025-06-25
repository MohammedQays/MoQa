import pywikibot
import toolforge
from pywikibot import pagegenerators
from wikitextparser import parse
import re
from datetime import datetime, timezone

# إعدادات عامة
class settings:
    lang = 'arwiki'
    category = "تصنيف:صفحات تقارير عبر البوت"
    editsumm = "[[وب:بوت|بوت]]: تحديث تقرير قاعدة البيانات."
    debug = "no"

# التاريخ بالعربية
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

# دوال مساعدة
def parse_template(wikitext):
    parsed = parse(wikitext)
    for t in parsed.templates:
        if t.name.strip() == "تقرير قاعدة البيانات":
            return {p.name.strip(): p.value.strip() for p in t.arguments}
    raise ValueError("قالب غير موجود")

def parse_links_option(option_str):
    link_map = {}
    if not option_str:
        return link_map
    for part in option_str.split(','):
        if ':' in part:
            col, ns = part.split(':')
        else:
            col, ns = part.strip(), '0'
        link_map[int(col.strip()) - 1] = int(ns.strip())
    return link_map

def wikify(value, ns):
    if ns == 2:
        return f"[[مستخدم:{value}|{value}]]"
    elif ns == 0:
        return f"[[{value}]]"
    else:
        return value

def build_table(results, links, numbering, headers):
    if not results:
        return "| لا توجد نتائج"
    table = ['{| class="wikitable"', "|-"]
    if numbering:
        table.append("! #")
    table.extend([f"! {h}" for h in headers])
    for idx, row in enumerate(results, start=1):
        table.append("|-")
        if numbering:
            table.append(f"| {idx}")
        for i, h in enumerate(headers):
            val = row[i]
            if isinstance(val, bytes):
                val = val.decode("utf-8")
            if isinstance(val, str) and re.match(r'^\d{14}$', val):
                dt = datetime.strptime(val, '%Y%m%d%H%M%S')
                val = dt.strftime('%Y-%m-%d %H:%M:%S')
            if links.get(i) is not None:
                val = wikify(val, links[i])
            table.append(f"| {val}")
    table.append("|}")
    return "\n".join(table)

# الاتصال بالموسوعة وقاعدة البيانات
site = pywikibot.Site()
cat = pywikibot.Category(site, settings.category)
pages = list(pagegenerators.CategorizedPageGenerator(cat))
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ التقارير
for page in pages:
    text = page.text
    try:
        params = parse_template(text)
    except Exception:
        continue

    if params.get("تحديث", "").strip() != "نعم":
        continue

    interval_param = params.get("الفاصل", "").strip()
    if interval_param.isdigit():
        interval_days = int(interval_param)
        try:
            last_rev = page.latest_revision
            last_user = last_rev.user
            last_ts = last_rev.timestamp
            now = datetime.now(timezone.utc)
            if last_user and 'bot' in last_user.lower():
                time_diff = now - last_ts
                if time_diff.days < interval_days:
                    continue
        except Exception:
            pass

    query = params.get("استعلام", "").strip()
    if not query:
        continue

    limit_param = params.get("حد_الصفحات", "").strip()
    limit = int(limit_param) if limit_param.isdigit() else 50
    links = parse_links_option(params.get("وصلات", ""))
    numbering = params.get("ترقيم", "").strip().lower() in ["نعم", "1", "true"]

    with conn.cursor() as cursor:
        q_with_limit = re.sub(r'limit\s+\d+', '', query, flags=re.IGNORECASE)
        q_with_limit += f"\nLIMIT {limit}"
        try:
            cursor.execute(q_with_limit)
            results = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
        except Exception:
            continue

    table_text = build_table(results, links, numbering, headers)

    # استخراج القالب الكامل لتعديله
    template_match = re.search(r'(\{\{تقرير قاعدة البيانات.*?\}\})', text, flags=re.DOTALL)
    if not template_match:
        continue

    template_text = template_match.group(1)
    updated_template_text = re.sub(r'\|تحديث\s*=\s*نعم', '|تحديث = لا', template_text)

    # بناء محتوى التقرير الجديد
    report_content = (
        f"{updated_template_text}\n"
        f"\n'''حَدَّث [[مستخدم:MoQabot|MoQabot]] هذه القائمة في : {formatted_time}'''\n"
        f"{table_text}\n"
        f"{{{{نهاية تقرير قاعدة البيانات}}}}"
    )

    # استبدال المحتوى السابق بالكامل من البداية للنهاية
    new_text = re.sub(
        r'\{\{تقرير قاعدة البيانات.*?\}\}.*?\{\{نهاية تقرير قاعدة البيانات\}\}',
        report_content,
        text,
        flags=re.DOTALL
    )

    if settings.debug == "no":
        page.text = new_text
        try:
            page.save(settings.editsumm)
        except Exception:
            continue
