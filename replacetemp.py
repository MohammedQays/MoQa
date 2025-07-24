import pywikibot
import toolforge
import re

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال القوالب التحويلية باسم القالب الأصلي."
    debug = "no"

query = """
SELECT
  p.page_title,
  rd.rd_title AS original_template,
  lt.lt_title AS redirect_template
FROM
  templatelinks AS tl
JOIN
  linktarget AS lt ON tl.tl_target_id = lt.lt_id
JOIN
  page AS tpl ON tpl.page_namespace = lt.lt_namespace AND tpl.page_title = lt.lt_title
JOIN
  categorylinks AS cl ON cl.cl_from = tpl.page_id
JOIN
  redirect AS rd ON rd.rd_from = tpl.page_id
JOIN
  page AS p ON p.page_id = tl.tl_from
WHERE
  cl.cl_to = "تحويلات_قوالب_من_لغات_بديلة"
  AND lt.lt_namespace = 10
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
LIMIT 200;
"""

conn = toolforge.connect(settings.lang, 'analytics')

page_templates = {}

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        page_title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
        original_template = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
        redirect_template = row[2].decode("utf-8") if isinstance(row[2], bytes) else row[2]

        if page_title not in page_templates:
            page_templates[page_title] = []
        page_templates[page_title].append((redirect_template, original_template))

site = pywikibot.Site()
site.login()

def make_template_regex(template_names):
    pattern_multiline = r'{{\s*(' + '|'.join(re.escape(t) for t in template_names) + r')\s*((?:\|.*?)*?)}}'
    return re.compile(pattern_multiline, re.DOTALL)

for page_title, tpl_list in page_templates.items():
    page = pywikibot.Page(site, page_title.replace('_', ' '))
    try:
        text = page.get()

        for redirect_tpl, original_tpl in tpl_list:
            regex = make_template_regex([redirect_tpl])

            def replacer(match):
                params = match.group(2) or ''
                return "{{{{{0}{1}}}}}".format(original_tpl, params)

            new_text = regex.sub(replacer, text)

            if new_text != text:
                text = new_text

        if text != page.get():
            if settings.debug == "no":
                page.text = text
                page.save(settings.editsumm)

    except:
        pass
