import pywikibot
import toolforge
import mwparserfromhell

class settings:
    lang = "arwiki"
    editsumm = "[[وب:بوت|بوت]]: تصحيح استخدام الملفات."
    debug = "no"

query = """
SELECT
    p.page_id AS page_id,
    p.page_title AS article_title,
    rd.rd_title AS target_file,
    il.il_to AS redirect_file
FROM page p
JOIN imagelinks il ON il.il_from = p.page_id
JOIN page pf ON pf.page_title = il.il_to AND pf.page_namespace = 6
JOIN redirect rd ON rd.rd_from = pf.page_id
WHERE p.page_namespace = 0
LIMIT 2000;
"""

conn = toolforge.connect(settings.lang, 'analytics')
page_files = {}

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        page_id = row[0]
        article_title = row[1].decode() if isinstance(row[1], bytes) else row[1]
        target_file   = row[2].decode() if isinstance(row[2], bytes) else row[2]
        redirect_file = row[3].decode() if isinstance(row[3], bytes) else row[3]

        if article_title not in page_files:
            page_files[article_title] = []

        page_files[article_title].append((redirect_file, target_file))

site = pywikibot.Site()
site.login()

def normalize(name):
    return name.replace("_", " ").strip()

for title, replacements in page_files.items():
    try:
        page = pywikibot.Page(site, title)
        if not page.exists():
            continue

        text = page.get()
        code = mwparserfromhell.parse(text)

        changed = False

        for redirect_file, target_file in replacements:
            red = normalize(redirect_file)
            tgt = normalize(target_file)

            # 1) استبدال كل وصلات ملف
            for node in code.filter_wikilinks():
                if node.title.strip().lower().startswith("ملف:"):
                    name = node.title.split(":", 1)[1].strip()
                    if normalize(name).lower() == red.lower():
                        node.title = "ملف:" + tgt
                        changed = True

            # 2) استبدال الملفات داخل القوالب
            for tpl in code.filter_templates():
                for param in tpl.params:
                    val = param.value.strip_code().strip()
                    if normalize(val).lower() == red.lower():
                        param.value = tgt
                        changed = True

            # 3) استبدال النصوص العادية
            raw = str(code)
            if red in raw:
                code = mwparserfromhell.parse(
                    raw.replace(red, tgt)
                )
                changed = True

        final = str(code)

        if changed and final != text:
            if settings.debug == "no":
                page.text = final
                page.save(settings.editsumm)

    except Exception as e:
        continue

