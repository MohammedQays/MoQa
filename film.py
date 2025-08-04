#!/usr/bin/env python3
import pywikibot
import toolforge
import math

class settings:
    lang = 'arwiki'
    base_user_page = "مستخدم:Mohammed Qays/فلم"
    editsumm = "[[وب:بوت|بوت]]: تحديث."
    debug = "no"

query = '''
SELECT page.page_title
FROM page
LEFT JOIN categorylinks
  ON categorylinks.cl_from = page.page_id
  AND categorylinks.cl_to = 'تحويلات_عناوين_أفلام'
LEFT JOIN redirect
  ON redirect.rd_from = page.page_id
WHERE page.page_namespace = 0
  AND page.page_title LIKE '%فيلم%'
  AND categorylinks.cl_from IS NULL
  AND redirect.rd_from IS NULL
'''

def execute_query():
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return [row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0] for row in result]
    except Exception as e:
        raise SystemExit(f"Database query failed: {e}")

def format_table_section(start, end, articles):
    section = f"== {start} إلى {end} ==\n"
    section += "{| class=\"wikitable\"\n|-\n! عنوان المقالة !! الهدف !! الحالة !! المستخدم\n"
    for title in articles:
        alt_title = title.replace("فيلم", "فلم")
        section += f"|-\n| [[{title}]]|| [[{alt_title}]]|| {{{{لمذ}}}} || {{{{مس|؟؟}}}}\n"
    section += "|}\n"
    return section

def update_user_pages():
    site = pywikibot.Site('ar', 'wikipedia')
    titles = execute_query()
    titles.sort()

    big_batch_size = 2000   # كل صفحة 2000 مقال
    small_batch_size = 100  # كل قسم داخل الصفحة 100 مقال

    total_pages = math.ceil(len(titles) / big_batch_size)

    for page_index in range(total_pages):
        page_number = page_index + 1
        # بناء اسم الصفحة
        if page_number == 1:
            page_title = settings.base_user_page
        else:
            page_title = f"{settings.base_user_page} {page_number}"

        page = pywikibot.Page(site, page_title)

        content = ""

        start_idx = page_index * big_batch_size
        end_idx = min(start_idx + big_batch_size, len(titles))
        titles_in_page = titles[start_idx:end_idx]

        # تقسيم داخل الصفحة كل 100 مقال
        for i in range(0, len(titles_in_page), small_batch_size):
            sec_start = i + 1
            sec_end = min(i + small_batch_size, len(titles_in_page))
            section_articles = titles_in_page[i:sec_end]
            content += format_table_section(sec_start, sec_end, section_articles)

        if settings.debug == "no":
            page.put(content, summary=settings.editsumm)
        else:
            print(f"\n--- محتوى الصفحة: {page_title} ---\n")
            print(content)

if __name__ == "__main__":
    update_user_pages()


