import pywikibot
import toolforge
import re

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح استخدام الملفات."
    debug = "no"

# استعلام لجلب التحويلات والملفات الأصلية والمقالات
query = """
SELECT
    p.page_title AS article_title,
    rd.rd_title AS target_file,
    il.il_to AS redirect_file
FROM page p
JOIN imagelinks il ON il.il_from = p.page_id
JOIN page pf ON pf.page_title = il.il_to AND pf.page_namespace = 6
JOIN redirect rd ON rd.rd_from = pf.page_id
WHERE p.page_namespace = 0
LIMIT 1000;
"""

conn = toolforge.connect(settings.lang, 'analytics')

page_files = {}

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        article_title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
        target_file   = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
        redirect_file = row[2].decode("utf-8") if isinstance(row[2], bytes) else row[2]

        if article_title not in page_files:
            page_files[article_title] = []
        page_files[article_title].append((redirect_file, target_file))

site = pywikibot.Site()
site.login()

def make_file_regex(file_names):
    # نصوص الملفات داخل [[ملف:...]] أو كاسم عادي
    pattern_link = r'(\[\[\s*ملف\s*:\s*)(' + '|'.join(re.escape(f) for f in file_names) + r')(\s*[:\]\|])'
    pattern_text = r'(?<!\[\[ملف:])(' + '|'.join(re.escape(f) for f in file_names) + r')(?![\w\]])'
    return re.compile(pattern_link, re.IGNORECASE), re.compile(pattern_text)

for article_title, files_list in page_files.items():
    page = pywikibot.Page(site, article_title.replace('_', ' '))
    try:
        text = page.get()

        # لكل تحويلة في المقالة
        for redirect_file, target_file in files_list:
            regex_link, regex_text = make_file_regex([redirect_file])

            # استبدال داخل [[ملف:...]]
            def replacer_link(match):
                return match.group(1) + target_file + match.group(3)
            text = regex_link.sub(replacer_link, text)

            # استبدال النص العادي
            text = regex_text.sub(target_file, text)

        # حفظ إذا تغير النص
        if text != page.get():
            if settings.debug == "no":
                page.text = text
                page.save(settings.editsumm)

    except Exception:
        pass


