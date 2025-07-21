#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pywikibot
from pywikibot.data.sparql import SparqlQuery

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
       ?item rdfs:label ?LabelAR FILTER(lang(?LabelAR)="ar") .
       FILTER (?page_titleAR != ?LabelAR)
       BIND(REGEX(STR(?page_titleAR), "(\\))$") AS ?regexresult1) .
       FILTER (?regexresult1 = false) .
    }
    LIMIT 20
    """

    results = sparql.select(query, full_data=True)
    pywikibot.output(f"Fetched {len(results)} results from SPARQL")

    repo = site.data_repository()
    for row in results:
        qid = row['item'].getID()
        new_label = row['page_titleAR'].value  
        old_label = row['LabelAR'].value  

        if new_label == old_label:
            continue  

        item = pywikibot.ItemPage(repo, qid)
        try:
            item.get()
            item.editLabels(
                labels={'ar': new_label},
                summary='Correct Arabic label'
            )
            pywikibot.output(f"Edited {qid}: “{old_label}” → “{new_label}”")
        except Exception as e:
            pywikibot.error(f"Failed to edit {qid}: {e}")

if __name__ == '__main__':
    main()
