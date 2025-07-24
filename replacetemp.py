import pywikibot
import toolforge
import re

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال تحويلات قوالب من لغات بديلة بأسمائها الأصلية."
    debug = "yes"  # "no" للحفظ، أو "yes" للطباعة فقط
    edit_limit = 20

# الاتصال بقاعدة البيانات
conn = toolforge.connect(settings.lang, 'analytics')
site = pywikibot.Site()

# الاستعلام الجديد المعتمد على linktarget
query = """
SELECT
  target.lt_title AS original_template,
  redirect.lt_title AS redirect_template,
  trans.page_namespace AS page_namespace,
  trans.page_title AS page_title
FROM
  page AS redirect_page
JOIN
  categorylinks AS cl ON cl.cl_from = redirect_page.page_id
JOIN
  redirect AS rd ON rd.rd_from = redirect_page.page_id
JOIN
  linktarget AS redirect ON redirect.lt_namespace = redirect_page.page_namespace AND redirect.lt_title = redirect_page.page_title
JOIN
  linktarget AS target ON target.lt_namespace = rd.rd_namespace AND target.lt_title = rd.rd_title
JOIN
  templatelinks AS tl ON tl.tl_target_id = redirect.lt_id
JOIN
  page AS trans ON trans.page_id = tl.tl_from
WHERE
  cl.cl_to = "تحويلات_قوالب_من_لغات_بديلة"
  AND redirect.lt_namespace = 10
ORDER BY
  target.lt_title, trans.page_title
LIMIT 10;
"""

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# إعداد عداد التعديلات
edit_count = 0

# دالة لبناء التعبير المنتظم لأي قالب
def make_template_pattern(template_name):
    name_pattern = re.escape(template_name.replace('_', ' '))
    return re.compile(r'(?s)\{\{\s*' + name_pattern + r'\b(.*?)\}\}', re.IGNORECASE)

# دالة الاستبدال
def replace_template_once(text, from_template, to_template):
    pattern = make_template_pattern(from_template)
    new_text, count = pattern.subn(r'{{' + to_template.replace('_', ' ') + r'\1}}', text)
    return new_text, count > 0

# معالجة النتائج
seen_pages = set()  # لتفادي تكرار التعديل على نفس الصفحة

for row in results:
    if edit_count >= settings.edit_limit:
        break

    original_template = row[0]
    redirect_template = row[1]
    page_namespace = row[2]
    page_title = row[3]

    full_title = f"{page_title}" if page_namespace == 0 else f"{site.namespace(page_namespace)}:{page_title}"
    if full_title in seen_pages:
        continue

    page = pywikibot.Page(site, full_title)
    try:
        if not page.exists() or page.isRedirectPage():
            continue

        original_text = page.text
        new_text, changed = replace_template_once(original_text, redirect_template, original_template)

        if changed:
            if settings.debug == "no":
                page.text = new_text
                page.save(settings.editsumm)
            edit_count += 1
            seen_pages.add(full_title)

    except Exception:
        continue
