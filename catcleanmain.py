import re
import sys
import pywikibot

class Settings:
    lang = "ar"
    family = "wikipedia"
    edit_summary = "[[وب:بوت|بوت]]: صيانة تنظيف."
    debug = False
    limit = 50

PATTERNS_TO_REMOVE = [
    r"مقالات فيها معلومات ضبط استنادي",
    r"صفحات تستخدم خاصية P\d+",
    r"[^|\]\r\n]+ كما في ويكي بيانات",
    r"بوابة [^|\]\r\n]+/مقالات متعلقة",
]

LINE_REGEX = re.compile(
    r"^[ \t]*\[\[\s*(?:تصنيف|Category)\s*:\s*(?:"
    + "|".join(PATTERNS_TO_REMOVE)
    + r")\s*(?:\|[^\]]*)?\]\][ \t]*(?:\r?\n)?",
    re.IGNORECASE | re.MULTILINE,
)

INLINE_REGEX = re.compile(
    r"\[\[\s*(?:تصنيف|Category)\s*:\s*(?:"
    + "|".join(PATTERNS_TO_REMOVE)
    + r")\s*(?:\|[^\]]*)?\]\][ \t]*",
    re.IGNORECASE,
)


def remove_tracking_categories(text):
    """إزالة التصنيفات المستهدفة فقط دون أي تغييرات تنسيقية أخرى."""
    text = LINE_REGEX.sub("", text)
    text = INLINE_REGEX.sub("", text)
    return text


def get_target_pages(site):
    """يجلب الصفحات المطلوب تنظيفها دون تكرار."""
    seen = set()

    category_names = [
        "تصنيف:مقالات فيها معلومات ضبط استنادي",
    ]

    for cat_name in category_names:
        cat = pywikibot.Category(site, cat_name)
        try:
            for page in cat.articles(namespaces=0):
                title = page.title()
                if title not in seen:
                    seen.add(title)
                    yield page
        except Exception:
            pywikibot.error(f"تعذر قراءة {cat_name}")

    for cat_page in site.allpages(namespace=14, prefix="صفحات تستخدم خاصية P"):
        cat = pywikibot.Category(site, cat_page.title())
        try:
            for page in cat.articles(namespaces=0):
                title = page.title()
                if title not in seen:
                    seen.add(title)
                    yield page
        except Exception:
            pywikibot.error(f"تعذر قراءة {cat_page.title()}")

    for cat_page in site.allpages(namespace=14):
        title = cat_page.title(with_ns=False)

        if (
            title.endswith(" كما في ويكي بيانات")
            or (
                title.startswith("بوابة ")
                and title.endswith("/مقالات متعلقة")
            )
        ):
            cat = pywikibot.Category(site, cat_page.title())
            try:
                for page in cat.articles(namespaces=0):
                    page_title = page.title()
                    if page_title not in seen:
                        seen.add(page_title)
                        yield page
            except Exception:
                pywikibot.error(f"تعذر قراءة {cat_page.title()}")


def main():
    site = pywikibot.Site(Settings.lang, Settings.family)

    try:
        site.login()
    except Exception as e:
        pywikibot.error(f"فشل تسجيل الدخول: {e}")
        sys.exit(1)

    edits = 0

    for page in get_target_pages(site):
        if edits >= Settings.limit:
            break

        try:
            original = page.get()
            cleaned = remove_tracking_categories(original)

            if original == cleaned:
                continue

            if Settings.debug:
                pywikibot.showDiff(original, cleaned)
                pywikibot.output(f"[تجريبي] {page.title()}")
            else:
                page.text = cleaned
                page.save(
                    summary=Settings.edit_summary,
                    minor=True
                )

            edits += 1

        except (
            pywikibot.NoPageError,
            pywikibot.IsRedirectPageError,
        ) as e:
            pywikibot.error(f"{page.title()}: {e}")

        except pywikibot.LockedPageError:
            pywikibot.error(f"الصفحة محمية: {page.title()}")

        except pywikibot.OtherPageSaveError as e:
            pywikibot.error(f"فشل حفظ {page.title()}: {e}")

        except Exception as e:
            pywikibot.exception(exc_info=e)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
