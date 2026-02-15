#!/usr/bin/env python3
import pywikibot
import toolforge
import mwparserfromhell

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: إزالة قالب بطاقة عامة."
    debug = "no"  # اجعلها "yes" للتجربة بدون حفظ

query = '''
SELECT DISTINCT p.page_title
FROM templatelinks AS tl
JOIN linktarget AS lt ON tl.tl_target_id = lt.lt_id
JOIN page AS p ON tl.tl_from = p.page_id
WHERE lt.lt_namespace = 10
AND lt.lt_title = 'بطاقة_عامة'
AND p.page_namespace = 0
LIMIT 10;
'''

def execute_query():
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        conn.close()
        return results
    except Exception:
        return []

def remove_infobox_template(text):
    """
    يزيل قالب بطاقة عامة بالكامل
    حتى لو احتوى قوالب متداخلة داخله
    """
    code = mwparserfromhell.parse(text)

    templates_to_remove = []

    for template in code.filter_templates():
        name = str(template.name).strip().replace("_", " ")
        if name.lower() == "بطاقة عامة":
            templates_to_remove.append(template)

    for template in templates_to_remove:
        code.remove(template)

    return str(code).strip()

def remove_template_from_page(title, site):
    page = pywikibot.Page(site, title)

    if not page.exists():
        return

    old_text = page.text
    new_text = remove_infobox_template(old_text)

    if old_text != new_text:
        if settings.debug == "no":
            page.text = new_text
            page.save(summary=settings.editsumm)
        else:
            print(f"تم تعديل: {title}")

def main():
    site = pywikibot.Site('ar', 'wikipedia')
    results = execute_query()

    for row in results:
        title = row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]
        title = title.replace("_", " ")
        remove_template_from_page(title, site)

if __name__ == "__main__":
    main()
