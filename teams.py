import pywikibot
import re
import json

def clean_name(name):
    """إزالة النص بين الأقواس من الاسم"""
    return re.sub(r'\(.*?\)', '', name).strip()

def get_arabic_name(name_en):
    site_en = pywikibot.Site('en', 'wikipedia')
    page_en = pywikibot.Page(site_en, name_en)

    if not page_en.exists():
        # استخراج الاسم الأخير بعد إزالة النص بين الأقواس
        cleaned_name = clean_name(name_en)
        return cleaned_name.split()[-1] if cleaned_name else name_en.split()[-1]

    try:
        item = pywikibot.ItemPage.fromPage(page_en)
        item.get()
    except:
        cleaned_name = clean_name(name_en)
        return cleaned_name.split()[-1] if cleaned_name else name_en.split()[-1]

    if 'arwiki' in item.sitelinks:
        ar_title = item.sitelinks['arwiki'].title
        # استخراج الاسم الأخير بعد إزالة النص بين الأقواس
        cleaned_title = clean_name(ar_title)
        second_name = cleaned_title.split()[-1] if cleaned_title else ar_title.split()[-1]
        return f'[[{ar_title}|{second_name}]]'
    else:
        return f'{{{{Ill-WD2|en=نعم|المعرف={item.id}}}}}'


def extract_players_and_manager(en_template_title):
    site_en = pywikibot.Site('en', 'wikipedia')
    template_page = pywikibot.Page(site_en, f'Template:{en_template_title}')

    if not template_page.exists():
        return [], None

    text = template_page.text
    players = re.findall(r'\{\{football squad2 player\|no=(\d+)\|name=\[\[(.*?)\]\]\}\}', text)
    manager_match = re.search(r'\{\{football squad manager\|name=\[\[(.*?)\]\]\}\}', text)
    manager_name = manager_match.group(1) if manager_match else None

    return players, manager_name


def build_arabic_template(team_name, players, manager_name):
    result = ['{{شريط تصفح تشكيلة فريق كرة قدم', f'|الاسم=', f'|اسم الفريق= {team_name}', '|القائمة=']

    for number, name in players:
        arabic_name = get_arabic_name(name)
        result.append(f'{{{{لاعب تشكيلة فريق كرة قدم|الرقم={number}|الاسم={arabic_name}}}}}')

    if manager_name:
        arabic_manager = get_arabic_name(manager_name)
        result.append(f'{{{{مدرب تشكيلة فريق كرة قدم|العنوان=مدرب|الاسم={arabic_manager}}}}}')

    result.append('}}')
    result.append('<noinclude>')
    result.append('[[تصنيف:قوالب تشكيلات أندية كرة قدم]]')
    result.append('</noinclude>')

    return '\n'.join(result)


def update_arabic_template(ar_template_title, new_text):
    site_ar = pywikibot.Site('ar', 'wikipedia')
    template_page = pywikibot.Page(site_ar, f'Template:{ar_template_title}')

    if template_page.exists():
        template_page.text = new_text
        template_page.save(summary='بوت: تحديث قالب تشكيلة من الإنجليزية')


def process_all_teams():
    site = pywikibot.Site('ar', 'wikipedia')
    user_page = pywikibot.Page(site, 'مستخدم:Mohammed Qays/teams.json')
    teams_data = json.loads(user_page.text)

    for team in teams_data.get('teams', []):
        ar_template = team.get('ar_template')
        en_template = team.get('en_template')
        team_name = team.get('name')

        players, manager = extract_players_and_manager(en_template)
        if not players:
            continue

        new_template_text = build_arabic_template(team_name, players, manager)
        update_arabic_template(ar_template, new_template_text)


if __name__ == '__main__':
    process_all_teams()
