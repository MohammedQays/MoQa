import pywikibot
import toolforge
import re

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح قوالب اللغة."
    debug = "no"

query = """
SELECT
  p.page_title
FROM
  page AS p
JOIN
  categorylinks AS cl
  ON cl.cl_from = p.page_id
WHERE
  cl.cl_to = 'أخطاء_قالب_لغة_واللغة'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  LIMIT 200;
"""

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]

site = pywikibot.Site()
site.login()

templates = ['إسبا', 'بولندية', 'لغة-إيطالية', 'لغ-سوي', 'لات', 'لغة-ألمانية', 'بنغالية', 'اللغة-الهولندية', 'تر', 'اللغة-التركية', 'اللغة-الفارسية', 'اللغة-الفرنسية', 'إسب', 'اللغة-الإسبانية', 'لغة-يونانية', 'إنج', 'فرن', 'خميرية', 'عبرية', 'lang-ca', 'أوكرانية', 'رمز لغة', 'هندية', 'برت', 'ألمانية', 'إيطالية', 'لغة-سلوفينية', 'لغة-صربية', 'برتغالية', 'لغة-أوكرانية', 'تركية', 'يون', 'لغة-فارسية', 'لغة-هولندية', 'إسبانية', 'هولندية', 'نرو']
template_pattern = re.compile(r'{{\s*(' + '|'.join(templates) + r')\s*\|\s*(.*?)\s*}}', re.DOTALL)
bold_italic_pattern = re.compile(r"[']{2,5}")

def clean_templates(text):
    def replacer(match):
        lang = match.group(1)
        content = match.group(2)
        clean_content = bold_italic_pattern.sub('', content).strip()
        return f"{{{{{lang}|{clean_content}}}}}"
    return template_pattern.sub(replacer, text)

for title in titles:
    page = pywikibot.Page(site, title.replace('_', ' '))
    try:
        text = page.get()
        new_text = clean_templates(text)
        if new_text != text:
            if settings.debug == "no":
                page.text = new_text
                page.save(settings.editsumm)
        else:
            pass
    except pywikibot.NoPageError:
        pass
    except pywikibot.IsRedirectPageError:
        pass
    except Exception:
        pass
