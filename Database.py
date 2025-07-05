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
        part = part.strip()
        if ':' in part:
            col, ns = part.split(':')
            col_index = int(col.strip()) - 1
            ns_index = int(ns.strip())
        else:
            col_index = int(part.strip()) - 1
            ns_index = 0
        link_map[col_index] = ns_index
    return link_map

def wikify(value, ns):
    if ns == 0:
        return f"[[{value}]]"
    elif ns == 1:
        return f"[[نقاش:{value}|{value}]]"
    elif ns == 2:
        return f"[[مستخدم:{value}|{value}]]"
    elif ns == 3:
        return f"[[نقاش المستخدم:{value}|{value}]]"
    elif ns == 4:
        return f"[[ويكيبيديا:{value}|{value}]]"
    elif ns == 5:
        return f"[[نقاش ويكيبيديا:{value}|{value}]]"
    elif ns == 6:
        return f"[[ملف:{value}|{value}]]"
    elif ns == 7:
        return f"[[نقاش الملف:{value}|{value}]]"
    elif ns == 8:
        return f"[[ميدياويكي:{value}|{value}]]"
    elif ns == 9:
        return f"[[نقاش ميدياويكي:{value}|{value}]]"
    elif ns == 10:
        return f"[[قالب:{value}|{value}]]"
    elif ns == 11:
        return f"[[نقاش القالب:{value}|{value}]]"
    elif ns == 12:
        return f"[[مساعدة:{value}|{value}]]"
    elif ns == 13:
        return f"[[نقاش المساعدة:{value}|{value}]]"
    elif ns == 14:
        return f"[[تصنيف:{value}|{value}]]"
    elif ns == 15:
        return f"[[نقاش التصنيف:{value}|{value}]]"
    elif ns == 100:
        return f"[[بوابة:{value}|{value}]]"
    elif ns == 101:
        return f"[[نقاش البوابة:{value}|{value}]]"
    elif ns == 828:
        return f"[[وحدة:{value}|{value}]]"
    elif ns == 829:
        return f"[[نقاش الوحدة:{value}|{value}]]"
    else:
        return value

def build_table(results, links, numbering, headers):
    if not results:
        return "| لا توجد نتائج"
    table = ['{| class="wikitable sortable" style="text-align:right; direction:rtl;"', "|-"]
    if numbering:
        table.append("! #")
    table.extend([f"! {h}" for h in headers])
    for idx, row in enumerate(results, start=1):
        table.append("|-")
        if numbering:
            table.append(f"| {idx}")
        for i, _ in enumerate(headers):
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

# تنفيذ
site = pywikibot.Site()
cat = pywikibot.Category(site, settings.category)
pages = list(pagegenerators.CategorizedPageGenerator(cat))

for page in pages:
    text = page.text
    try:
        params = parse_template(text)
    except Exception:
        continue

    update_flag = params.get("تحديث", "").strip().lower()
    if update_flag not in ["نعم", "yes", "1", "true"]:
        continue

    interval_param = params.get("الفاصل", "").strip()
    if interval_param.isdigit():
        interval_days = int(interval_param)
        try:
            last_rev = page.latest_revision
            last_user = last_rev.user
            last_ts = last_rev.timestamp
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
    limit = int(limit_param) if limit_param.isdigit() else 100
    links = parse_links_option(params.get("وصلات", ""))
    numbering = params.get("ترقيم", "").strip().lower() in ["نعم", "1", "true"]

    # تحديد قاعدة البيانات
    db_name = params.get("قاعدة_بيانات", "").strip() or "arwiki_p"

    try:
        conn = toolforge.connect(db_name, 'analytics')
    except Exception as e:
        print(f"فشل الاتصال بقاعدة البيانات {db_name}: {e}")
        continue

    with conn.cursor() as cursor:
        q_clean = re.sub(r'limit\s+\d+\s*;?', '', query, flags=re.IGNORECASE).strip().rstrip(';')
        q_with_limit = f"{q_clean} LIMIT {limit}"

        try:
            cursor.execute(q_with_limit)
            results = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
        except Exception as e:
            print(f"خطأ في تنفيذ الاستعلام: {e}")
            continue

    # بناء الجدول
    result_text = f"\n'''حَدَّث [[مستخدم:MoQabot|MoQabot]] هذه القائمة في : {formatted_time}'''\n"
    result_text += build_table(results, links, numbering, headers)
    result_text += "\n{{نهاية تقرير قاعدة البيانات}}"

    # تعطيل التحديث بعد التنفيذ
    text = re.sub(r'(\{\{تقرير قاعدة البيانات[^\}]*?)\|تحديث\s*=\s*نعم', r'\1|تحديث = لا', text, flags=re.DOTALL)

    # استبدال النتائج القديمة بالجديدة
    new_text = re.sub(
        r'(\{\{تقرير قاعدة البيانات.*?\}\})(.*?)\{\{نهاية تقرير قاعدة البيانات\}\}',
        r'\1' + result_text,
        text,
        flags=re.DOTALL
    )

    if settings.debug == "no":
        page.text = new_text
        try:
            page.save(settings.editsumm)
        except Exception as e:
            print(f"فشل حفظ الصفحة {page.title()}: {e}")
            continue
