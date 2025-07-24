import pywikibot
import toolforge
import re
import json
import os

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال تحويلات قوالب."
    debug = "yes"  # "no" للحفظ، "yes" للطباعة فقط
    edit_limit = 10
    redirects_file = "redirects.json"

# ----------------- المرحلة 1: استخراج التحويلات -----------------
def fetch_redirects_and_save():
    conn = toolforge.connect(settings.lang, 'analytics')
    query = """
    SELECT
      p1.page_title AS redirect_title,
      rd.rd_title AS target_title
    FROM
      page AS p1
    JOIN
      categorylinks AS cl ON cl.cl_from = p1.page_id
    JOIN
      redirect AS rd ON rd.rd_from = p1.page_id
    WHERE
      cl.cl_to = "تحويلات_قوالب_من_لغات_بديلة"
      AND p1.page_namespace = 10
      AND rd.rd_namespace = 10;
    """

    with conn.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    redirect_map = {
        row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]:
        row[1].decode('utf-8') if isinstance(row[1], bytes) else row[1]
        for row in results
    }

    with open(settings.redirects_file, "w", encoding="utf-8") as f:
        json.dump(redirect_map, f, ensure_ascii=False, indent=2)

# ----------------- المرحلة 2: تحميل الملف ومعالجة الصفحات -----------------
def make_template_pattern(template_name):
    name_pattern = re.escape(template_name.replace('_', ' '))
    return re.compile(r'(?s)\{\{\s*' + name_pattern + r'\b(.*?)\}\}', re.IGNORECASE)

def replace_templates(text, redirect_map):
    replaced = False
    for redirect, target in redirect_map.items():
        pattern = make_template_pattern(redirect)
        text, count = pattern.subn(r'{{' + target.replace('_', ' ') + r'\1}}', text)
        if count > 0:
            replaced = True
    return text, replaced

def process_pages():
    site = pywikibot.Site()

    with open(settings.redirects_file, "r", encoding="utf-8") as f:
        redirect_map = json.load(f)

    all_template_titles = [f"Template:{k}" for k in redirect_map.keys()]
    processed_titles = set()
    edit_count = 0

    for title in all_template_titles:
        if edit_count >= settings.edit_limit:
            break

        template_page = pywikibot.Page(site, title)

        try:
            ref_pages = template_page.getReferences(only_template_inclusion=True, follow_redirects=False)
        except Exception:
            continue

        for page in ref_pages:
            if edit_count >= settings.edit_limit:
                break
            if page.title() in processed_titles:
                continue

            try:
                if not page.exists() or page.isRedirectPage():
                    continue

                original_text = page.text
                new_text, changed = replace_templates(original_text, redirect_map)

                if changed:
                    if settings.debug == "no":
                        page.text = new_text
                        page.save(settings.editsumm)
                    processed_titles.add(page.title())
                    edit_count += 1
            except Exception:
                continue

# ----------------- تشغيل المراحل -----------------
if not os.path.exists(settings.redirects_file):
    fetch_redirects_and_save()

process_pages()
