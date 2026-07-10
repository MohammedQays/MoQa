import re
import sys
import pywikibot
import wikitextparser as wtp
from pywikibot import textlib


class Settings:
    lang = "ar"
    family = "wikipedia"
    edit_summary = "[[وب:بوت|بوت]]: صيانة تنظيف."
    debug = False
    limit = 50


SEARCH_QUERIES = [
    'insource:"[[تصنيف:مقالات فيها معلومات ضبط استنادي"',
    'insource:"[[تصنيف:جميع مقالات البذور"',
    'insource:"[[تصنيف:مقالات مشروع ويكي المغرب"',
    'insource:"[[تصنيف:مقالات تستعمل قوالب معلومات"',
    'insource:"[[تصنيف:مقالات أعلام بحاجة لصورة"',
    'insource:"[[تصنيف:صفحات تستخدم خاصية P"',
    'insource:" ليس على ويكي بيانات]]"',
    'insource:" ليست على ويكي بيانات]]"',
    'insource:" كما في ويكي بيانات]]"',
    'insource:"[[بوابة" insource:"/مقالات متعلقة"',
]


SPACE = r"[ _]+" 

PATTERNS_TO_REMOVE = [
    rf"مقالات{SPACE}فيها{SPACE}معلومات{SPACE}ضبط{SPACE}استنادي",
    rf"جميع{SPACE}مقالات{SPACE}البذور",
    rf"مقالات{SPACE}مشروع{SPACE}ويكي{SPACE}المغرب",
    rf"مقالات{SPACE}تستعمل{SPACE}قوالب{SPACE}معلومات",
    rf"مقالات{SPACE}أعلام{SPACE}بحاجة{SPACE}لصورة",
    rf"صفحات{SPACE}تستخدم{SPACE}خاصية{SPACE}P[1-9]\d*",
    rf"[^|\]\r\n]+{SPACE}(?:ليس|ليست){SPACE}على{SPACE}ويكي{SPACE}بيانات",
    rf"[^|\]\r\n]+{SPACE}كما{SPACE}في{SPACE}ويكي{SPACE}بيانات",
    rf"بوابة{SPACE}[^|\]\r\n]+/مقالات{SPACE}متعلقة",
]

COMBINED_PATTERN = re.compile(
    "|".join(PATTERNS_TO_REMOVE),
    re.IGNORECASE
)

PROTECTED_REGIONS = [
    "comment",
    "math",
    "nowiki",
    "pre",
    "syntaxhighlight",
]


def remove_categories_with_parser(text, site=None):
    """
    إزالة روابط التصنيف المستهدفة باستخدام wikitextparser مع احترام المناطق المحمية.
    """
    parsed = wtp.parse(text)

    protected_ranges = []
    for region_type in PROTECTED_REGIONS:
        elements = getattr(parsed, region_type + 's', [])
        for elem in elements:
            protected_ranges.append((elem.span[0], elem.span[1]))

    def is_protected(start, end):
        for ps, pe in protected_ranges:
            if not (end <= ps or start >= pe):  
                return True
        return False

    links_to_remove = []
    for link in parsed.wikilinks:
        title = link.title
        if not (title.startswith('تصنيف:') or title.startswith('Category:')):
            continue
        category_name = title.split(':', 1)[1]
        if COMBINED_PATTERN.search(category_name):
            start, end = link.span
            if not is_protected(start, end):
                links_to_remove.append((start, end, link.string))

    if not links_to_remove:
        return text

    links_to_remove.sort(key=lambda x: x[0], reverse=True)

    new_text = text
    for start, end, link_str in links_to_remove:
        new_text = new_text[:start] + new_text[end:]

    new_text = re.sub(r'\n\s*\n', '\n', new_text) 
    new_text = new_text.strip() + '\n'  

    return new_text


def get_pages_using_insource(site):
    """جلب الصفحات باستخدام insource (كما هو)"""
    seen_pages = set()
    for query in SEARCH_QUERIES:
        pywikibot.info(f"جاري البحث بالاستعلام: {query}")
        try:
            for page in site.search(query, total=Settings.limit * 5, namespaces=[0]):
                title = page.title()
                if title not in seen_pages:
                    seen_pages.add(title)
                    yield page
        except Exception as e:
            pywikibot.exception(f"فشل البحث عن الاستعلام: {query} - {e}")


def main():
    site = pywikibot.Site(Settings.lang, Settings.family)
    try:
        site.login()
    except Exception:
        pywikibot.exception("فشل تسجيل الدخول.")
        sys.exit(1)

    edits = 0
    for page in get_pages_using_insource(site):
        if edits >= Settings.limit:
            break
        try:
            original = page.get()
            cleaned = remove_categories_with_parser(original, site)
            if original == cleaned:
                continue
            if Settings.debug:
                pywikibot.showDiff(original, cleaned)
                pywikibot.info(f"[تجريبي] {page.title()}")
            else:
                page.text = cleaned
                page.save(
                    summary=Settings.edit_summary,
                    minor=True,
                    apply_cosmetic_changes=False,
                )
            edits += 1
        except KeyboardInterrupt:
            pywikibot.warning("أوقف المستخدم التشغيل.")
            break
        except (pywikibot.NoPageError, pywikibot.IsRedirectPageError) as error:
            pywikibot.error(f"{page.title()}: {error}")
        except pywikibot.LockedPageError:
            pywikibot.error(f"الصفحة محمية: {page.title()}")
        except pywikibot.OtherPageSaveError as error:
            pywikibot.error(f"فشل حفظ {page.title()}: {error}")
        except Exception:
            pywikibot.exception(f"خطأ غير متوقع أثناء معالجة {page.title()}.")

    pywikibot.info(f"انتهى التشغيل؛ عدد التعديلات: {edits}.")


if __name__ == "__main__":
    main()
