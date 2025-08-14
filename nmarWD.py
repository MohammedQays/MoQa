#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pywikibot
import re
from pywikibot import pagegenerators
from pywikibot.exceptions import NoPageError, IsRedirectPageError

BATCH_SIZE = 100

def main():
    site = pywikibot.Site('wikidata', 'wikidata')
    site.login()
    repo = site.data_repository()
    arwiki = pywikibot.Site('ar', 'wikipedia')

    conflict_entries = []
    batch_items = {}
    processed_count = 0

    # جلب كل صفحات ويكيبيديا العربية
    page_gen = pagegenerators.AllpagesPageGenerator(namespace=0, site=arwiki)

    for page in page_gen:
        title = page.title()
        if any(substr in title for substr in ["(", "قائمة", "،"]):
            continue

        try:
            item = pywikibot.ItemPage.fromPage(page)
            item.get()
            old_label = item.labels.get('ar', '')

            if old_label == title:
                continue

            batch_items[item] = title
            processed_count += 1

            if len(batch_items) >= BATCH_SIZE:
                update_batch(batch_items, conflict_entries)
                batch_items.clear()

        except (NoPageError, IsRedirectPageError):
            # الصفحة ما لها عنصر ويكي بيانات أو هي تحويلة
            continue
        except Exception as e:
            pywikibot.error(f"Failed processing {title}: {e}")

    if batch_items:
        update_batch(batch_items, conflict_entries)

    # حفظ التعارضات
    new_text = "\n".join(conflict_entries) + "\n"
    userpage = pywikibot.Page(site, "User:Mohammed Qays/MoQabot")
    userpage.text = new_text
    userpage.save(summary="bot: update")

    pywikibot.output(f"Processed {processed_count} pages.")

def update_batch(items_dict, conflict_entries):
    for item, new_label in items_dict.items():
        old_label = item.labels.get('ar', '')
        try:
            item.editLabels(labels={'ar': new_label}, summary='bot: Correct Arabic label')
            pywikibot.output(f"Edited {item.id}: “{old_label}” → “{new_label}”")
        except Exception as e:
            msg = str(e)
            if re.search(r'label.*already.*associated with language code ar', msg, re.IGNORECASE) or \
               re.search(r'label and description.*same value', msg, re.IGNORECASE):
                entry = f"# {{{{Q|{item.id}}}}} (تعارض تسمية)"
                if entry not in conflict_entries:
                    conflict_entries.append(entry)
                pywikibot.output(f"Ignored {item.id} due to label conflict")
            else:
                pywikibot.error(f"Failed to edit {item.id}: {e}")

if __name__ == '__main__':
    main()
