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
    players = []

    player_matches = re.finditer(r'\{\{football squad2 player\|no=(\d+)\|name=(.*?)\}\}', text)
    for match in player_matches:
        number = match.group(1)
        name_raw = match.group(2).strip()
        players.append((number, name_raw))

    manager_match = re.search(r'\{\{football squad manager\|name=(.*?)\}\}', text)
    manager_name = manager_match.group(1).strip() if manager_match else None

    return players, manager_name

def handle_special_name(name):
    # استبدال أنماط القائد
    name = re.sub(r'\(\[\[\s*Captain \(association football\)\s*\|\s*c\s*\]\]\)', '({{ك}})', name, flags=re.IGNORECASE)
    name = re.sub(r'\[\[\s*Captain \(association football\)\s*\|\s*c\s*\]\]', '({{ك}})', name, flags=re.IGNORECASE)
    name = re.sub(r'\(\[\[\s*قائد الفريق \(كرة القدم\)\s*\|\s*الفريق\s*\]\]\)', '({{ك}})', name)
    name = re.sub(r'\[\[\s*قائد الفريق \(كرة القدم\)\s*\|\s*الفريق\s*\]\]', '({{ك}})', name)

    # إزالة الأقواس المكررة حول {{ك}}
    name = re.sub(r'\(\(\s*\{\{ك\}\}\s*\)\)', '({{ك}})', name)
    name = re.sub(r'\(\s*\{\{ك\}\}\s*\)', '({{ك}})', name)

    # تحويل Abbr إلى اختص
    name = name.replace('{{Abbr|', '{{اختص|')

    # التأكد من إغلاق قوالب اختص
    open_count = name.count('{{اختص|')
    close_count = name.count('}}')
    if open_count > close_count:
        name += '}' * (2 * (open_count - close_count))

    # تحويل الوصلات إلى العربية إن وجدت
    def replace_wikilink(match):
        full_link = match.group(1)
        parts = full_link.split('|')
        if len(parts) == 2:
            page, label = parts
            arabic = get_arabic_name(page)
            return arabic
        else:
            return f'[[{full_link}]]'

    name = re.sub(r'\[\[(.*?)\]\]', replace_wikilink, name)

    return name

def build_arabic_template(team_name, players, manager_name):
    result = ['{{شريط تصفح تشكيلة فريق كرة قدم', f'|الاسم=', f'|اسم الفريق= {team_name}', '|القائمة=']

    for number, name in players:
        name = handle_special_name(name)
        result.append(f'{{{{لاعب تشكيلة فريق كرة قدم|الرقم={number}|الاسم={name}}}}}')

    if manager_name:
        manager_name = handle_special_name(manager_name)
        result.append(f'{{{{مدرب تشكيلة فريق كرة قدم|العنوان=مدرب|الاسم={manager_name}}}}}')

    result.append('}}')

    return '\n'.join(result)

def update_arabic_template(ar_template_title, new_text):
    site_ar = pywikibot.Site('ar', 'wikipedia')
    template_page = pywikibot.Page(site_ar, f'Template:{ar_template_title}')

    existing_categories = []
    if template_page.exists():
        # استخراج التصنيفات القديمة
        existing_categories = re.findall(r'\[\[تصنيف:[^\]]+\]\]', template_page.text)

    # إزالة أي <noinclude> قديم
    new_text = re.sub(r'<noinclude>.*?</noinclude>', '', new_text, flags=re.DOTALL)

    # إعادة إدراج التصنيفات الموجودة
    if existing_categories:
        new_text += '\n<noinclude>\n' + '\n'.join(existing_categories) + '\n</noinclude>'

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
