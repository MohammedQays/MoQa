import pywikibot
import toolforge
import re

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال تحويلات قوالب من لغات بديلة بأسمائها الأصلية."
    debug = "yes"  # اجعلها "no" للحفظ، أو "yes" للطباعة فقط (بدون تنبيه)

# الاتصال بقاعدة البيانات
conn = toolforge.connect(settings.lang, 'analytics')
site = pywikibot.Site()

# الاستعلام لجلب القوالب التحويلية ووجهاتها
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

# تحويل النتيجة إلى قاموس {قالب_تحويل: قالب_أصلي}
redirect_map = {
    row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]:
    row[1].decode('utf-8') if isinstance(row[1], bytes) else row[1]
    for row in results
}

# تعبير منتظم للكشف عن القوالب بجميع أشكالها
def make_template_pattern(template_name):
    name_pattern = re.escape(template_name.replace('_', ' '))
    return re.compile(
        r'(?s)\{\{\s*' + name_pattern + r'\b(.*?)\}\}',
        re.IGNORECASE
    )

# دالة لاستبدال أسماء القوالب داخل النص
def replace_templates(text, redirect_map):
    replaced = False
    for redirect, target in redirect_map.items():
        pattern = make_template_pattern(redirect)
        text, count = pattern.subn(r'{{' + target.replace('_', ' ') + r'\1}}', text)
        if count > 0:
            replaced = True
    return text, replaced

# عدد التعديلات التجريبية
edit_count = 0
edit_limit = 20  # التعديل على 20 صفحة فقط

# معالجة كل قالب تحويل
for redirect_title, target_title in redirect_map.items():
    template_redirect = f"Template:{redirect_title}"
    template_page = pywikibot.Page(site, template_redirect)

    ref_pages = template_page.getReferences(only_template_inclusion=True, follow_redirects=False)

    for page in ref_pages:
        if edit_count >= edit_limit:
            break
        try:
            if not page.exists() or page.isRedirectPage():
                continue

            original_text = page.text
            new_text, changed = replace_templates(original_text, {redirect_title: target_title})

            if changed:
                if settings.debug == "no":
                    page.text = new_text
                    page.save(settings.editsumm)
                edit_count += 1

        except Exception:
            continue
