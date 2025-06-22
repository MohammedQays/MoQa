#!/usr/bin/env python3
import pywikibot
import toolforge
import json
from datetime import datetime
from collections import defaultdict

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

year = datetime.now().year

query_template = '''
SELECT page.page_title, revision.rev_timestamp
FROM page
JOIN revision ON revision.rev_page = page.page_id
JOIN categorylinks ON categorylinks.cl_from = page.page_id
WHERE revision.rev_timestamp BETWEEN {start} AND {end}
  AND revision.rev_parent_id = 0
  AND page.page_namespace = 0
  AND page.page_is_redirect = 0
  AND categorylinks.cl_to = %s
ORDER BY revision.rev_timestamp DESC;
'''

def load_portals_from_json(site, title):
    """تحميل البوابات من صفحة JSON في ويكيبيديا."""
    page = pywikibot.Page(site, title)
    if not page.exists():
        return []
    try:
        content = page.get()
        return json.loads(content)
    except Exception as e:
        print(f"خطأ في تحميل أو تحليل JSON: {e}")
        return []

def execute_query(category):
    conn = toolforge.connect(settings.lang, 'analytics')
    with conn.cursor() as cursor:
        start = int(f"{year}0000000000")
        end = int(f"{year}1231235959")
        cursor.execute(query_template.format(start=start, end=end), (category,))
        return cursor.fetchall()

def generate_wikitext(portal, results):
    monthly_articles = defaultdict(list)

    for title, ts in results:
        ts = ts.decode('utf-8') if isinstance(ts, bytes) else str(ts)
        timestamp = datetime.strptime(ts, "%Y%m%d%H%M%S")
        month = timestamp.month
        title = title.decode('utf-8') if isinstance(title, bytes) else title
        title = title.replace("_", " ")
        monthly_articles[month].append(title)

    output = f"عدد المقالات المرتبطة ب[[بوابة:{portal}|بوابة {portal}]] والمستحدثة سنة [[{year}]] هو : '''{len(results)}'''.\n"
    output += "<div class=hlist>\n\n"
    for month in sorted(monthly_articles.keys(), reverse=True):
        articles = monthly_articles[month]
        output += f"=== {{{{اسم الشهر|{str(month).zfill(2)}}}}} ({len(articles)}) ===\n"
        for article in articles:
            output += f"* [[{article}]]\n"
    output += "</div>\n<noinclude>\n"
    output += f"[[تصنيف:بوابة_{portal}]]\n"
    output += f"[[تصنيف:مقالات جديدة حسب البوابة {year}|{portal}]]\n"
    output += "__NOTOC__ __NOEDITSECTION__\n</noinclude>"
    return output

def save_or_preview(page_title, content, site):
    page = pywikibot.Page(site, page_title)
    if settings.debug == "no":
        page.text = content
        page.save(summary=settings.editsumm)

def main():
    site = pywikibot.Site('ar', 'wikipedia')
    json_page = 'مستخدم:Mohammed Qays/Portal.json'
    portals = load_portals_from_json(site, json_page)

    for portal in portals:
        category = f'بوابة_{portal}/مقالات_متعلقة'
        results = execute_query(category)
        if not results:
            continue
        wikitext = generate_wikitext(portal, results)
        page_title = f"بوابة:{portal}/مقالات جديدة/{year}"
        save_or_preview(page_title, wikitext, site)

if __name__ == "__main__":
    main()
