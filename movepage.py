#!/usr/bin/env python3
import pywikibot
import toolforge

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: نقل حسب التوافق في [[ويكيبيديا:الميدان/لغويات#c-أحمد_ناجي-20250731110800-Mohanad-20250716030700|الميدان]]"
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
  LIMIT 3;
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

def move_articles():
    site = pywikibot.Site('ar', 'wikipedia')
    titles = execute_query()
    titles.sort()

    for title in titles:
        old_title = title
        new_title = title.replace("فيلم", "فلم")

        if old_title == new_title:
            continue

        try:
            page = pywikibot.Page(site, old_title)
            target = pywikibot.Page(site, new_title)

            if not page.exists():
                continue
            if target.exists():
                continue

            if settings.debug == "no":
                page.move(new_title, reason=settings.editsumm, movetalk=True)

        except Exception:
            continue

if __name__ == "__main__":
    move_articles()
