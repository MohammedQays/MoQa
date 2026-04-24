import pywikibot
import toolforge
import re
import json

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: توحيد قوالب اللغات إلى {{اللغة}}"
    debug = "no"

# تحميل JSON من صفحة الويكي
def load_lang_map(site):
    page = pywikibot.Page(site, "User:Mohammed_Qays/language.json")
    text = page.get().strip()

    try:
        raw = json.loads(text)
        mapping = {}

        # تحويل الشكل الجديد إلى mapping عكسي
        for code, names in raw.items():
            for name in names:
                mapping[name] = code

        return mapping

    except Exception as e:
        print(f"❌ خطأ في قراءة JSON: {e}")
        return {}

site = pywikibot.Site()
site.login()

# تحميل القاموس
lang_map = load_lang_map(site)

if not lang_map:
    print("❌ لم يتم تحميل أي بيانات، إيقاف التشغيل")
    exit()

# بناء قائمة القوالب للاستعلام
template_list_sql = ','.join(f'"{t}"' for t in lang_map.keys())

query = f"""
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
  AND lt.lt_title IN ({template_list_sql})
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
ORDER BY p.page_title ASC
LIMIT 100;
"""

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [
    row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    for row in results
]

# بناء regex بعد تحميل القاموس
template_pattern = re.compile(
    r'{{\s*(' + '|'.join(map(re.escape, lang_map.keys())) + r')\s*\|\s*(.*?)\s*}}',
    re.DOTALL
)

bold_italic_pattern = re.compile(r"[']{2,5}")

def replace_lang_templates(text):
    def replacer(match):
        template_name = match.group(1)
        content = match.group(2)

        code = lang_map.get(template_name)

        if not code:
            return match.group(0)

        # تنظيف التنسيق
        clean_content = bold_italic_pattern.sub('', content).strip()

        return f"({{{{اللغة|{code}|{clean_content}}}}})"

    return template_pattern.sub(replacer, text)

# التنفيذ
for title in titles:
    page = pywikibot.Page(site, title.replace('_', ' '))

    try:
        text = page.get()
        new_text = replace_lang_templates(text)

        if new_text != text:
            if settings.debug == "no":
                page.text = new_text
                page.save(settings.editsumm)
            else:
                print(f"🔍 تجربة: {title}")

    except pywikibot.NoPageError:
        pass
    except pywikibot.IsRedirectPageError:
        pass
    except Exception as e:
        print(f"❌ خطأ في {title}: {e}")
