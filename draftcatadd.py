import pywikibot
from pywikibot import exceptions
import toolforge
import re

class settings:
    lang = 'arwiki'
    summary = "[[وب:بوت|بوت]]: إضافة قالب تصنيفات مسودة."
    debug = "no"

# --- الاستعلام ---
query = """
SELECT DISTINCT
  p.page_title
FROM
  page p
WHERE
  p.page_namespace = 2
  AND p.page_title LIKE '%/%'
  AND p.page_title NOT LIKE '%ويكيبيديون_حصلوا_على_جوائز%'
  AND p.page_title NOT LIKE '%أرشيف%'
  AND EXISTS (
    SELECT 1
    FROM categorylinks cl
    JOIN linktarget lt ON lt.lt_id = cl.cl_target_id
    JOIN page cpage 
      ON cpage.page_title = lt.lt_title
      AND cpage.page_namespace = lt.lt_namespace
    LEFT JOIN page_props pp 
      ON pp.pp_page = cpage.page_id
      AND pp.pp_propname = 'hiddencat'
    WHERE
      cl.cl_from = p.page_id
      AND cpage.page_namespace = 14
      AND pp.pp_page IS NULL
  );
  """

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [
    row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    for row in results
]

# --- الموقع ---
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# --- regex ---
cat_pattern = re.compile(r'\[\[\s*:?\s*تصنيف:[^\]]+\]\]', re.IGNORECASE)
nowiki_pattern = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL | re.IGNORECASE)

def process_text(text):
    if "{{تصنيفات مسودة" in text:
        return text, False

    categories = []

    def extract_nowiki(match):
        content = match.group(1)
        found = cat_pattern.findall(content)
        categories.extend(found)
        return ''  

    text = nowiki_pattern.sub(extract_nowiki, text)

    normal = cat_pattern.findall(text)
    categories.extend(normal)

    if not categories:
        return text, False

    text = cat_pattern.sub('', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    seen = set()
    unique = []
    for c in categories:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    template = "\n\n{{تصنيفات مسودة|\n" + "\n".join(unique) + "\n}}"
    final_text = text.rstrip() + template + "\n"

    return final_text, True
for raw_title in titles:
    try:
        clean_title = raw_title.replace('_', ' ').strip('"')
        page = pywikibot.Page(site, clean_title, ns=2)

        if not page.exists():
            continue

        if page.isRedirectPage():
            continue

        text = page.get()

        new_text, changed = process_text(text)

        if changed and new_text != text:
            if settings.debug == "no":
                page.text = new_text
                page.save(summary=settings.summary)

    except exceptions.NoPageError:
        continue
    except exceptions.IsRedirectPageError:
        continue
    except Exception as e:
        print(f"Error on {raw_title}: {e}")
