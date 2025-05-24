#!/usr/bin/python
# -*- coding: utf-8 -*-

import pywikibot
import math
import time
from SPARQLWrapper import SPARQLWrapper, JSON

CHUNK_SIZE = 100
INDEX_PAGE_TITLE = 'ويكيبيديا:مشروع تعريب خواص ويكي بيانات/الخواص'

def fetch_properties():
    all_props = []
    query = """
    SELECT ?property ?id WHERE {
      ?property a wikibase:Property .
      BIND(STRAFTER(STR(?property), "http://www.wikidata.org/entity/") AS ?id)
    }
    ORDER BY ?id
    """

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
    except Exception as e:
        print(f"خطأ في الاستعلام: {e}")
        return []

    bindings = results["results"]["bindings"]

    for result in bindings:
        all_props.append(result["id"]["value"])

    return all_props

def make_chunk_pages(props, site):
    total = len(props)
    num_chunks = math.ceil(total / CHUNK_SIZE)
    index_lines = []

    for i in range(num_chunks):
        start = i * CHUNK_SIZE + 1
        end = min((i + 1) * CHUNK_SIZE, total)
        chunk = props[start - 1:end]
        page_title = f"ويكيبيديا:مشروع تعريب خواص ويكي بيانات/الخواص/{start}-{end}"
        index_lines.append(f"# [[{page_title}|صفحة {i + 1}]]")

        text = f"{{{{تر. جد. خاصية}}}}\n"
        for prop_id in chunk:
            text += f"{{{{سط. جد. خاصية|{prop_id}|}}}}\n"
        text += "{{ذيل جدول}}"

        page = pywikibot.Page(site, page_title)
        page.text = text
        page.save(summary="بوت:تحديث خواص ويكي بيانات")

    return index_lines

def update_index_page(index_lines, site):
    page = pywikibot.Page(site, INDEX_PAGE_TITLE)
    text = "== فهرس الصفحات الفرعية ==\n" + "\n".join(index_lines)
    page.text = text
    page.save(summary="بوت:تحديث فهرس.")

def main():
    site = pywikibot.Site()
    pywikibot.Site().login()
    props = fetch_properties()
    index_lines = make_chunk_pages(props, site)
    update_index_page(index_lines, site)

if __name__ == '__main__':
    main()
