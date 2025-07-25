#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from pathlib import Path
import re
from typing import Any

import pywikibot
from pywikibot.data import api

SITE = pywikibot.Site('ar', 'wikipedia')
REPO = pywikibot.Site('wikidata', 'wikidata').data_repository()

CNT_ADDED_LIMIT = 1000
TIMESTAMP_FILENAME = Path('arwiki-deleted_time.dat')

def load_timestamp_from_logfile() -> str:
    with open(TIMESTAMP_FILENAME, 'r', encoding='utf8') as file:
        return file.read().strip()


def save_timestamp_to_logfile(timestamp: str) -> None:
    with open(TIMESTAMP_FILENAME, 'w', encoding='utf8') as file:
        file.write(re.sub(r'[:\-Z|T]', '', timestamp))


def save_to_wiki(page: pywikibot.Page, wikitext: str) -> None:
    page.text = wikitext
    page.save(summary='بوت: تحديث صفحات محذوفة', minor=False)


def parse_revision(revision: dict[str, Any]) -> tuple[dict[str, Any], str]:
    timestamp = revision.get('timestamp')
    comment = revision.get('comment')
    title = revision.get('title')

    if not timestamp or not comment:
        return {}, timestamp

    # تحليل التعليق لتحديد إزالة وصلة ويكيبيديا العربية
    match = re.search(r'clientsitelink-remove:1\|\|arwiki \*/ (.+)', comment)
    if not match:
        return {}, timestamp

    item = pywikibot.ItemPage(REPO, title)
    if not item.exists() or item.isRedirectPage():
        return {}, timestamp

    dct = item.get()
    if 'sitelinks' in dct and 'arwiki' in dct['sitelinks']:
        return {}, timestamp  # لا تزال مرتبطة بمقال عربي

    if 'claims' not in dct:
        return {}, timestamp

    cnt_statements = len(dct['claims'])
    cnt_sources = sum(
        len(source.keys()) - list(source.keys()).count('P143')
        for pid in dct['claims']
        for claim in dct['claims'][pid]
        for source in claim.getSources()
    )
    cnt_backlinks = sum(1 for _ in item.backlinks(namespaces=0))
    cnt_externalids = sum(1 for pid in dct['claims']
                          if dct['claims'][pid][0].type == 'external-id')

    return {
        'title': title,
        'cnt_statements': cnt_statements,
        'cnt_sources': cnt_sources,
        'cnt_backlinks': cnt_backlinks,
        'cnt_externalids': cnt_externalids,
        'deleted_sitelink': match.group(1),
        'timestamp': timestamp,
    }, timestamp


def query_new_revisions(old_time: str, rccontinue: str) -> tuple[list[dict[str, Any]], str, str]:
    timestamp = old_time
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rcprop': 'title|comment|timestamp',
        'rcstart': old_time,
        'rcdir': 'newer',
        'rctype': 'edit',
        'rcnamespace': '0',
        'rccontinue': rccontinue,
        'rclimit': '500',
        'format': 'json',
    }
    req = api.Request(site=REPO, parameters=params)
    data = req.submit()

    revisions = []
    for rev in data.get('query', {}).get('recentchanges', []):
        try:
            parsed, timestamp = parse_revision(rev)
            if parsed:
                revisions.append(parsed)
        except Exception:
            continue

    rccontinue = data.get('continue', {}).get('rccontinue', '')

    return revisions, timestamp, rccontinue


def update_report_text(wikitext: str, old_time: str) -> tuple[str, str]:
    rccontinue = f'{old_time}|0'
    all_revisions = []

    while True:
        revisions, timestamp, rccontinue = query_new_revisions(old_time, rccontinue)
        all_revisions.extend(revisions)

        if rccontinue == '' or len(all_revisions) >= CNT_ADDED_LIMIT:
            break

    for entry in all_revisions:
        wikitext += (
            f'\n|-\n'
            f'| {{{{Q|{entry["title"]}}}}} '
            f'|| {entry["cnt_statements"]} '
            f'|| <small>({entry["cnt_sources"]})</small> '
            f'|| {entry["cnt_backlinks"]} '
            f'|| {entry["cnt_externalids"]} '
            f'|| {entry["deleted_sitelink"]} '
            f'|| {entry["timestamp"]}'
        )

    wikitext += '\n|}'

    return wikitext, timestamp


def main():
    page = pywikibot.Page(SITE, 'مستخدم:Mohammed Qays/ملعب 21')
    wikitext = page.get()
    wikitext = wikitext.replace('\n|}', '')  # إزالة نهاية الجدول القديمة

    old_time = load_timestamp_from_logfile()
    new_wikitext, new_time = update_report_text(wikitext, old_time)

    save_to_wiki(page, new_wikitext)
    save_timestamp_to_logfile(new_time)


if __name__ == '__main__':
    main()
