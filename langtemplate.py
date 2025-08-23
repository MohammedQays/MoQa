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
  AND p.page_is_redirect = 0;
"""

conn = toolforge.connect(settings.lang, 'analytics')

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

titles = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in results]

site = pywikibot.Site()
site.login()

templates = ['أسامية', 'Lang-is', 'آيسلندية', 'لغة-آيسلندية', 'Lang-ab', 'أبخازية', 'لغة-أبخازية',
    'لغ-آت', 'لغة-أتشينيزية', 'أدي', 'أديغية', 'Lang-az', 'أذر', 'أذربيجانية', 'أذرية',
    'لغة-أذرية', 'Lang-an', 'أراغونية', 'لغة-أراغونية', 'Lang-ur', 'أرد', 'لغ-أر',
    'لغة-أردوية', 'Lang-hy', 'أرمنية', 'أرمينية', 'لغة-أرمنية', 'Lang-de', 'Lang-de-at',
    'ألم', 'ألمانية', 'لغ-ألم', 'Lang-uz', 'أوز', 'أوزبكية', 'لغة-أوز', 'لغة-أوزبكية',
    'Lang-uk', 'أوك', 'أوكرانية', 'لغ-أو', 'لغة-أو', 'Lang-ug', 'أويغورية', 'لغة-أويغورية',
    'Lang-ga', 'أير', 'أيرلندية', 'لغ-إر', 'لغة-أيرلندية', 'Lang-ay', 'لغة-أيمرية',
    'Lang-es', 'إسب', 'إسبا', 'إسبانية', 'اسب', 'Lang-sco', 'أسكتلندية', 'اسكتلندية',
    'لغة-اسكتلندية', 'لغة_إسكتلندية', 'Lang-id', 'أندونيسية', 'إندو', 'إندونيسية',
    'اندونيسية', 'إنغ', 'Lang-it', 'إيط', 'إيطالية', 'لغ-إط', 'لغة-إيطالية', 'Lang-pt',
    'Lang-pt-br', 'بر', 'برت', 'برتغالية', 'Lang-ps', 'بشتوية', 'لغة-بشتوية', 'Lang-eu',
    'باسكية', 'لغة-بشكنشية', 'Lang-ba', 'باشقير', 'Lang-bg', 'بلغ', 'بلغارية', 'لغة-بلغارية',
    'Lang-bn', 'بنغالية', 'لغ-بنق', 'لغة-بنغالية', 'Lang-my', 'بورمية', 'لغ-ميا',
    'لغة-بورمية', 'Lang-bs', 'اللغة-البوسنية', 'بوسنية', 'لغة-بوسنية', 'Lang-pl', 'بولندية',
    'لغ-بو', 'لغة-بولندية', 'Lang-be', 'بيل', 'بيلاروسية', 'لغة-بيلاروسية', 'Lang-ta',
    'لغة-تاميلية', 'Lang-th', 'Th_icon', 'تاي', 'تايلندية', 'لغة-تايلندية', 'Lang-bo',
    'تبتية', 'لغة-تبتية', 'Lang-crh', 'Lang-tt', 'تتارية', 'تترية', 'لغ-تت', 'Lang-tr',
    'تر', 'ترك', 'تركية', 'لغ-تر', 'Lang-cs', 'تشيكية', 'لغة-تشيكية', 'Lang-jv',
    'لغة-جاوية', 'لغة_جاوية', 'جرينلاندية', 'لغة-جغتائية', 'Lang-da', 'دنم', 'دنماركية',
    'لغة-دنماركية', 'IPA-ru', 'Lang-ru', 'Lang-rus', 'روس', 'روسي', 'Lang-ro', 'روم',
    'رومانية', 'لغة-روم', 'لغة-رومانية', 'Lang-syr', 'سر', 'سرن', 'سريانية', 'لغة-سريانية',
    'لغ-كن', 'Lang-sk', 'سلو', 'سلوفاكية', 'لغة-سلوفاكية', 'Lang-sl', 'سلوف', 'سلوفينية',
    'لغة-سلوفينية', 'Lang-mia', 'Lang-sv', 'سويدية', 'لغ-سوي', 'لغة-سويدية', 'Lang-sr',
    'صربية', 'لغة-صربية', 'Lang-zh', 'Lang-zh-hk', 'Zh', 'بالصينية', 'صينية', 'Lang-zh-hant',
    'Lang-zh-cn', 'Lang-zh-hans', 'عبر', 'عبري', 'عبرية', 'Lang-fa', 'بالفارسية', 'فار', 'فارسية', 'لغة-فا', 'Lang-fr', 'فر',
    'فرن', 'فرنسي', 'فرنسية', 'فريز', 'فلب', 'فلبينية', 'Lang-fi', 'فنلندية', 'لغ-فن',
    'لغة-فنلندية', 'Lang-vi', 'فيتنامية', 'لغة-فيتنامية', 'القبايلية', 'بالقبايلية',
    'قبايلية', 'Lang-krc', 'القراشاي_بلقار', 'Lang-ky', 'قرغيزية', 'قيرغيزية', 'Lang-kum',
    'قموقية', 'قوموقية', 'Lang-ca', 'كتالانية', 'كتالونية', 'Lang-ku', 'كرد', 'كردية',
    'لغة-كردية', 'Lang-co', 'اللغة-الكورسية', 'كورسية', 'لغة-كورسية', 'كور', 'لغة-كورية',
    'Lang-lv', 'لاتفية', 'لاتيفية', 'لغ-لات', 'لغة-لاتفية', 'Lang-la', 'Lang-lat',
    'بالاتينية', 'لات', 'لاتينية', 'ليتوانية', 'Lang-mt', 'لغة-مالطية', 'مالطية',
    'Lang-ml', 'لغة-ماليالامية', 'ماليالامية', 'Lang-mnc', 'Lang-hu', 'لغ-مج', 'لغة-مجرية',
    'مجر', 'مجرية', 'Lang-xmf', 'لغ-منغ', 'لغة-منغريلية', 'Lang-ms', 'لغة-ملايوية',
    'ملايو', 'Lang-mol', 'لغة-مولدوفية', 'مولدوفية', 'Lang-no', 'لغة-نر', 'لغة-نرويجية',
    'نرو', 'نرويجية', 'Lang-non', 'Lang-on', 'لغ-إق', 'لغة-إسكندنافية_قديمة', 'Lang-ne',
    'لغة-نيبالية', 'Lang-hi', 'لغ-هن', 'لغة-هندية', 'هند', 'هندية', 'Lang-nl',
    'لغة-هولندية', 'هول', 'هولندية', 'Lang-cy', 'Lang-yi', 'لغة-يديشية', 'يديشية',
    'Lang-el', 'اليونانية', 'لغة-يونانية', 'لغة_يونانية', 'يون']
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
