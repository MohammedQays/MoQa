import re
import sys

import pywikibot
from pywikibot import textlib


class Settings:
    lang = "ar"
    family = "wikipedia"
    edit_summary = "[[وب:بوت|بوت]]: صيانة تنظيف."
    debug = False
    limit = 50


# يدعم المسافات والشرطات السفلية في أسماء التصنيفات.
SPACE = r"[ _]+"

PATTERNS_TO_REMOVE = [
    rf"مقالات{SPACE}فيها{SPACE}معلومات{SPACE}ضبط{SPACE}استنادي",
    rf"صفحات{SPACE}تستخدم{SPACE}خاصية{SPACE}P[1-9]\d*",
    rf"[^|\]\r\n]+{SPACE}كما{SPACE}في{SPACE}ويكي{SPACE}بيانات",
    rf"بوابة{SPACE}[^|\]\r\n]+/مقالات{SPACE}متعلقة",
]

CATEGORY_LINK_PATTERN = (
    r"\[\["
    r"[ \t]*(?:تصنيف|Category)[ \t]*:[ \t]*"
    r"(?:"
    + "|".join(PATTERNS_TO_REMOVE)
    + r")"
    r"[ \t]*(?:\|[^\]\r\n]*)?"
    r"\]\]"
)

LINE_REGEX = re.compile(
    rf"^[ \t]*{CATEGORY_LINK_PATTERN}[ \t]*(?:\r?\n|$)",
    re.IGNORECASE | re.MULTILINE,
)

INLINE_REGEX = re.compile(
    CATEGORY_LINK_PATTERN + r"[ \t]*",
    re.IGNORECASE,
)

# استثناء التعليقات والوسوم المحمية من الاستبدال.
PROTECTED_REGIONS = [
    "comment",
    "math",
    "nowiki",
    "pre",
    "syntaxhighlight",
]


def remove_tracking_categories(text, site=None):
    """إزالة التصنيفات المستهدفة دون تعديل المحتوى المحمي."""
    cleaned = textlib.replaceExcept(
        text,
        LINE_REGEX,
        "",
        PROTECTED_REGIONS,
        site=site,
    )

    cleaned = textlib.replaceExcept(
        cleaned,
        INLINE_REGEX,
        "",
        PROTECTED_REGIONS,
        site=site,
    )

    return cleaned


def get_target_categories(site):
    """جلب التصنيفات المستهدفة دون مسح نطاق التصنيفات كاملًا."""
    seen_categories = set()

    fixed_category_names = [
        "تصنيف:مقالات فيها معلومات ضبط استنادي",
    ]

    for category_name in fixed_category_names:
        category = pywikibot.Category(site, category_name)
        title = category.title()

        if title not in seen_categories:
            seen_categories.add(title)
            yield category

    # جلب التصنيفات التي تبدأ بالعبارة المحددة.
    try:
        for category_page in site.allpages(
            namespace=14,
            prefix="صفحات تستخدم خاصية P",
        ):
            title = category_page.title()

            if title not in seen_categories:
                seen_categories.add(title)
                yield pywikibot.Category(site, title)

    except Exception:
        pywikibot.exception(
            "تعذر جلب التصنيفات البادئة بـ"
            " «صفحات تستخدم خاصية P»."
        )

    # البحث في عناوين التصنيفات والتحقق من التطابق النهائي.
    search_rules = [
        (
            '"كما في ويكي بيانات"',
            lambda title: title.endswith(" كما في ويكي بيانات"),
        ),
        (
            '"مقالات متعلقة"',
            lambda title: (
                title.startswith("بوابة ")
                and title.endswith("/مقالات متعلقة")
            ),
        ),
    ]

    for query, title_matches in search_rules:
        try:
            for category_page in site.search(
                query,
                namespaces=14,
                where="title",
            ):
                short_title = category_page.title(with_ns=False)

                if not title_matches(short_title):
                    continue

                full_title = category_page.title()

                if full_title not in seen_categories:
                    seen_categories.add(full_title)
                    yield pywikibot.Category(site, full_title)

        except Exception:
            pywikibot.exception(
                f"تعذر البحث عن التصنيفات بالاستعلام: {query}"
            )


def get_target_pages(site):
    """جلب المقالات الموجودة في التصنيفات المستهدفة دون تكرار."""
    seen_pages = set()

    for category in get_target_categories(site):
        try:
            for page in category.articles(namespaces=0):
                title = page.title()

                if title in seen_pages:
                    continue

                seen_pages.add(title)
                yield page

        except Exception:
            pywikibot.exception(
                f"تعذر قراءة أعضاء {category.title()}."
            )


def main():
    site = pywikibot.Site(Settings.lang, Settings.family)

    try:
        site.login()
    except Exception:
        pywikibot.exception("فشل تسجيل الدخول.")
        sys.exit(1)

    edits = 0

    for page in get_target_pages(site):
        if edits >= Settings.limit:
            break

        try:
            original = page.get()
            cleaned = remove_tracking_categories(original, site)

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
            pywikibot.warning("أوقف المستخدم تشغيل البوت.")
            break

        except (
            pywikibot.NoPageError,
            pywikibot.IsRedirectPageError,
        ) as error:
            pywikibot.error(f"{page.title()}: {error}")

        except pywikibot.LockedPageError:
            pywikibot.error(f"الصفحة محمية: {page.title()}")

        except pywikibot.OtherPageSaveError as error:
            pywikibot.error(
                f"فشل حفظ {page.title()}: {error}"
            )

        except Exception:
            pywikibot.exception(
                f"خطأ غير متوقع أثناء معالجة {page.title()}."
            )

    pywikibot.info(
        f"انتهى التشغيل؛ عدد التعديلات: {edits}."
    )


if __name__ == "__main__":
    main()
