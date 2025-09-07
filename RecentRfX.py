# -*- coding: utf-8 -*-
import pywikibot
import re

site = pywikibot.Site("ar", "wikipedia")
template_page = "قالب:أحدث الترشيحات"

tpl_page = pywikibot.Page(site, template_page)
old_text = tpl_page.get()
tpl_text = old_text[:]

re_entry = re.compile(r"\{\{سط\. نتائج ترشيح\|.*?\}\}")
re_kind_user = re.compile(r"\{\{سط\. نتائج ترشيح\|([^|]*)\|([^|]*)")
re_status = re.compile(r"\|\s*حالة التصويت\s*=\s*(.+)")
re_date = re.compile(r"\|\s*تاريخ\s*=\s*([\d]{4})-([\d]{2})-([\d]{2})")
re_number = re.compile(r"\(\s*الترشيح\s+([^)]+)\s*\)")
re_result = re.compile(r"\|\s*نتيجة\s*=\s*(.+)")

def count_votes(text, word):
    return len(re.findall(r"\{\{\s*" + word + r"\s*\}\}", text))

# تحديد مسار الترشيح حسب النوع
def build_nomination_page(kind, username):
    if kind == "ب":
        return f"ويكيبيديا:بيروقراطيون/تصويت/{username}"
    elif kind == "و":
        return f"ويكيبيديا:إداريو الواجهة/تصويت/{username}"
    else:
        return f"ويكيبيديا:إداريون/تصويت/{username}"

# تفحص كل الأسطر في القالب
entries = re_entry.findall(old_text)
for entry in entries:
    m = re_kind_user.search(entry)
    if not m:
        continue
    kind = m.group(1).strip()
    username = m.group(2).strip()

    nomination_page = build_nomination_page(kind, username)
    page = pywikibot.Page(site, nomination_page)

    if not page.exists():
        continue

    try:
        text = page.get()
    except Exception:
        continue

    # حالة التصويت
    status_match = re_status.search(text)
    if not status_match:
        continue
    status = status_match.group(1).strip()

    # التاريخ
    date_match = re_date.search(text)
    if not date_match:
        continue
    year, month, day = date_match.groups()
    date_formatted = f"{day}-{month}-{year}"

    # الأصوات
    votes_for = count_votes(text, "مع")
    votes_against = count_votes(text, "ضد")
    votes_neutral = count_votes(text, "محايد")

    number_match = re_number.search(text)
    number = f"(الترشيح {number_match.group(1)})" if number_match else ""

    result_match = re_result.search(text)
    result = result_match.group(1).strip() if result_match else ""

    new_entry = f"{{{{سط. نتائج ترشيح|{kind}|{username}|{number}|{date_formatted}|{votes_for}|{votes_against}|{votes_neutral}|{result}}}}}"

    if entry != new_entry:
        tpl_text = tpl_text.replace(entry, new_entry)

if tpl_text != old_text:
    tpl_page.put(tpl_text, summary="بوت: تحديث أحدث الترشيحات")


