import pywikibot
import toolforge
import json
import re
import unicodedata
import mwparserfromhell

# ===================== إعدادات البوت =====================

class Settings:
    lang = "ar"
    dbname = "arwiki"
    debug = "yes"
    editsumm = "[[وب:بوت|بوت]]: تحديث صندوق معلومات (تجريبي)"

site_ar = pywikibot.Site(Settings.lang, "wikipedia")
site_en = pywikibot.Site("en", "wikipedia")

# ===================== تحميل الملفات =====================

with open("nameteams.json", "r", encoding="utf-8") as f:
    club_map = json.load(f)

with open("natfootballteam.json", "r", encoding="utf-8") as f:
    nat_map = json.load(f)

data_page = pywikibot.Page(site_ar, "مستخدم:Mohammed Qays/datateams.json")
data_config = json.loads(data_page.text)

text_replacements = data_config.get("text_replacements", {})
fields_config = data_config.get("fields", {})

# ===================== أدوات مساعدة =====================

def normalize_text(text):
    return unicodedata.normalize("NFC", text.strip())

def extract_link_value(value):
    match = re.search(r'\[\[(.*?)\]\]', value)
    if not match:
        return value.strip()
    content = match.group(1)
    if "|" in content:
        return content.split("|")[0].strip()
    return content.strip()

def apply_text_replacements(value):
    for en_txt, ar_txt in text_replacements.items():
        value = value.replace(en_txt, ar_txt)
    return value

# ===================== تحويل القيم بالكامل =====================

def convert_value_full(value, mapping):
    """
    تحويل أي حقل (نادي أو منتخب) مع الحفاظ على كل النصوص خارج الروابط
    """
    value = normalize_text(value)

    # تقسيم النص للحفاظ على الروابط منفصلة
    parts = re.split(r'(\[\[.*?\]\])', value)
    new_parts = []

    for part in parts:
        if part.startswith('[[') and part.endswith(']]'):
            en_name = extract_link_value(part)
            if en_name in mapping:
                data = mapping[en_name]
                if data.get("link"):
                    new_part = data["link"]
                elif data.get("ar"):
                    new_part = f"[[{data['ar']}]]"
                elif data.get("qid"):
                    new_part = f"{{{{Ill-WD2|id={data['qid']}|en=true}}}}"
                else:
                    new_part = en_name
            else:
                new_part = en_name
            new_parts.append(new_part)
        else:
            # نصوص خارج الروابط
            new_parts.append(part)

    full_text = ''.join(new_parts)
    full_text = apply_text_replacements(full_text)

    return full_text

def convert_club(value):
    return convert_value_full(value, club_map)

def convert_national_team(value):
    return convert_value_full(value, nat_map)

# ===================== تنسيق القالب بشكل عمودي =====================

def format_template(template):
    name = str(template.name).strip()
    lines = ["{{" + name]
    for param in template.params:
        pname = str(param.name).strip()
        pvalue = str(param.value).strip()
        lines.append(f"  |{pname}={pvalue}")
    lines.append("}}")
    return "\n".join(lines)

# ===================== جلب المقالات =====================

QUERY_ARTICLES = """
SELECT DISTINCT
  p.page_title AS article_title_ar,
  ll.ll_title AS article_title_en,
  p.page_len AS article_size
FROM
  templatelinks AS tl
JOIN
  linktarget AS lt ON tl.tl_target_id = lt.lt_id
JOIN
  page AS p ON tl.tl_from = p.page_id
JOIN
  langlinks AS ll ON ll.ll_from = p.page_id
WHERE
  lt.lt_namespace = 10
  AND lt.lt_title = "صندوق_معلومات_سيرة_كرة_قدم"
  AND p.page_namespace = 0
  AND ll.ll_lang = 'en'
ORDER BY p.page_len ASC
LIMIT 50;
"""

def fetch_articles():
    conn = toolforge.connect(Settings.dbname)
    with conn.cursor() as cursor:
        cursor.execute(QUERY_ARTICLES)
        rows = cursor.fetchall()
        return [
            (
                row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0],
                row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1],
                row[2]
            )
            for row in rows
        ]

# ===================== معالجة المقالة =====================

def process_article(title_ar, title_en):

    page_ar = pywikibot.Page(site_ar, title_ar)
    page_en = pywikibot.Page(site_en, title_en)

    if not page_ar.exists() or not page_en.exists():
        return

    text_ar = page_ar.text
    text_en = page_en.text

    wikicode_ar = mwparserfromhell.parse(text_ar)
    wikicode_en = mwparserfromhell.parse(text_en)

    template_ar = None
    template_en = None

    for t in wikicode_ar.filter_templates():
        if "صندوق معلومات سيرة كرة قدم" in t.name.strip():
            template_ar = t
            break

    for t in wikicode_en.filter_templates():
        if "Infobox football biography" in t.name.strip():
            template_en = t
            break

    if not template_ar or not template_en:
        return

    updated = False

    for en_field, ar_field in fields_config.items():
        if template_en.has(en_field):
            en_value = str(template_en.get(en_field).value).strip()

            if "nationalteam" in en_field:
                value = convert_national_team(en_value)
            elif "club" in en_field:
                value = convert_club(en_value)
            else:
                value = normalize_text(apply_text_replacements(en_value))

            if template_ar.has(ar_field):
                if str(template_ar.get(ar_field).value).strip() != value:
                    template_ar.get(ar_field).value = value
                    updated = True
            else:
                template_ar.add(ar_field, value)
                updated = True

    if updated:
        formatted_template = format_template(template_ar)
        old_template_text = str(template_ar)
        new_text = str(wikicode_ar).replace(old_template_text, formatted_template, 1)

        if Settings.debug == "yes":
            print(f"\n=== Preview: {title_ar} ===\n")
            print(new_text)
            print("\n============================\n")
        else:
            page_ar.text = new_text
            page_ar.save(Settings.editsumm)

# ===================== التشغيل =====================

if __name__ == "__main__":
    articles = fetch_articles()
    for ar_title, en_title, _ in articles:
        process_article(ar_title, en_title)
        
