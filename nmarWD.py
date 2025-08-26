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
    SELECT DISTINCT ?item ?LabelAR ?page_titleAR WHERE {
       ?item wdt:P31 wd:Q4167836 .
       ?article schema:about ?item ;
                schema:isPartOf <https://ar.wikipedia.org/> ;
                schema:name ?page_titleAR .
       ?item rdfs:label ?LabelAR filter (lang(?LabelAR) = "ar") .
       FILTER (?page_titleAR != ?LabelAR)
       BIND( REGEX(STR(?page_titleAR), "(\\))$") AS ?regexresult1 ) .
       FILTER( ?regexresult1 = false ) .
    }
    LIMIT 100
    """

    results = sparql.select(query, full_data=True)
    pywikibot.output(f"Fetched {len(results)} results from SPARQL")

    repo = site.data_repository()
    conflict_entries = []

    for row in results:
        qid = row['item'].getID()
        new_label = row['page_titleAR'].value  

        label_data = row.get('LabelAR')
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

    new_text = "\n".join(conflict_entries) + "\n"

    userpage = pywikibot.Page(site, "User:Mohammed Qays/MoQabot")
    userpage.text = new_text
    userpage.save(summary="bot: update")

if __name__ == '__main__':
    main()
