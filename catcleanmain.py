import pywikibot
import re
import sys

class Settings:
    lang = "ar"
    family = "wikipedia"
    edit_summary = "[[وب:بوت|بوت]]: صيانة تنظيف."
    debug = False
    limit = 50

PATTERNS_TO_REMOVE = [
    r"مقالات فيها معلومات ضبط استنادي",
    r"صفحات تستخدم خاصية P\d+",
    r".+ كما في ويكي بيانات",
    r"بوابة .+?/مقالات متعلقة",
]

LINE_REGEX = re.compile(
    r"^[ \t]*\[\[\s*(?:تصنيف|Category)\s*:\s*(?:" + "|".join(PATTERNS_TO_REMOVE) + r")\s*(?:\|[^\]]*)?\]\][ \t]*(?:\r?\n)?",
    re.IGNORECASE | re.MULTILINE
)

INLINE_REGEX = re.compile(
    r"\[\[\s*(?:تصنيف|Category)\s*:\s*(?:" + "|".join(PATTERNS_TO_REMOVE) + r")\s*(?:\|[^\]]*)?\]\]\s*",
    re.IGNORECASE
)

def remove_tracking_categories(text):
    """إزالة التصنيفات المستهدفة وحذف الأسطر الفارغة الناتجة عنها من جذورها."""
    cleaned_text = LINE_REGEX.sub("", text)
    cleaned_text = INLINE_REGEX.sub("", cleaned_text)
    cleaned_text = re.sub(r"^[ \t]+$", "", cleaned_text, flags=re.MULTILINE)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip() + "\n"

def get_target_pages(site):
    """مُولد (Generator) يجلب المقالات تدريجيًا لتجنب استنزاف الذاكرة."""
    seen_pages = set()

    cat_auth = pywikibot.Category(site, "تصنيف:مقالات فيها معلومات ضبط استنادي")
    for page in cat_auth.articles(namespaces=0):
        if page.title() not in seen_pages:
            seen_pages.add(page.title())
            yield page

    for cat_page in site.allpages(namespace=14, prefix="صفحات تستخدم خاصية P"):
        cat = pywikibot.Category(site, cat_page.title())
        for page in cat.articles(namespaces=0):
            if page.title() not in seen_pages:
                seen_pages.add(page.title())
                yield page

def main():
    site = pywikibot.Site(Settings.lang, Settings.family)

    try:
        site.login()
    except Exception:
        sys.exit(1)

    edits_count = 0

    for page in get_target_pages(site):
        if edits_count >= Settings.limit:
            break

        try:
            original_text = page.get()
            new_text = remove_tracking_categories(original_text)

            if original_text != new_text:
                if not Settings.debug:
                    page.text = new_text
                    page.save(summary=Settings.edit_summary, minor=True)

                edits_count += 1

        except (
            pywikibot.NoPageError,
            pywikibot.IsRedirectPageError,
            pywikibot.LockedPageError,
            pywikibot.OtherPageSaveError,
        ):
            continue
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
