#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot.data.sparql import SparqlQuery
import re

def main():
    pywikibot.handle_args()
    site = pywikibot.Site('wikidata', 'wikidata')
    site.login()

    sparql = SparqlQuery(repo=site)
    query = r"""
     SELECT ?item ?itemLabel ?sitelink WHERE {
      ?item rdfs:label ?itemLabel.
      FILTER(LANG(?itemLabel) = "ar").

      ?sitelink_schema schema:about ?item ;
                       schema:isPartOf <https://ar.wikipedia.org/> ;
                       schema:name ?sitelink .

      FILTER(?itemLabel != ?sitelink)
      FILTER(!CONTAINS(?sitelink, "("))
    }
    LIMIT 1000
    """

    results = sparql.select(query, full_data=True)
    pywikibot.output(f"Fetched {len(results)} results from SPARQL")

    repo = site.data_repository()
    conflict_entries = []

    for row in results:
        qid = row['item'].getID()
        new_label = row['sitelink'].value  # تغيير 'title' إلى 'sitelink'

        label_data = row.get('itemLabel')
        old_label = label_data.value if label_data is not None else None

        if old_label == new_label:
            pywikibot.output(f"Skipping {qid}: label already correct ({new_label})")
            continue

        item = pywikibot.ItemPage(repo, qid)
        try:
            item.get()
            item.editLabels(
                labels={'ar': new_label},
                summary='bot:Correct Arabic label'
            )
            pywikibot.output(f"Edited {qid}: “{old_label}” → “{new_label}”")
        except Exception as e:
            msg = str(e)
            if re.search(r'label.*already.*associated with language code ar', msg, re.IGNORECASE) or \
               re.search(r'label and description.*same value', msg, re.IGNORECASE):
                entry = f"# {{{{Q|{qid}}}}} (تعارض تسمية)"
                if entry not in conflict_entries:
                    conflict_entries.append(entry)
                pywikibot.output(f"Ignored {qid} due to label conflict")
            else:
                pywikibot.error(f"Failed to edit {qid}: {e}")

    # بناء نص جديد لصفحة المستخدم بالكامل مع العناصر الجديدة فقط
    new_text = "\n".join(conflict_entries) + "\n"

    userpage = pywikibot.Page(site, "User:Mohammed Qays/MoQabot")
    userpage.text = new_text
    userpage.save(summary="bot: update")

if __name__ == '__main__':
    main()
