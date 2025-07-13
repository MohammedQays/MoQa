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
        cleaned = clean_name(name_en)
        return cleaned.split()[-1] if cleaned else name_en.split()[-1]

    try:
        item = pywikibot.ItemPage.fromPage(page_en)
        item.get()
    except:
        cleaned = clean_name(name_en)
        return cleaned.split()[-1] if cleaned else name_en.split()[-1]

    if 'arwiki' in item.sitelinks:
        ar_title = item.sitelinks['arwiki'].title
        cleaned = clean_name(ar_title)
        label = cleaned.split()[-1] if cleaned else ar_title.split()[-1]
        return f'[[{ar_title}|{label}]]'
    return f'{{{{Ill-WD2|en=نعم|المعرف={item.id}}}}}'

def extract_players_and_manager(en_template_title):
    """يستخرج قائمة اللاعبين (بما فيهم من لا رقم لهم) واسم المدير"""
    if not en_template_title or not en_template_title.strip():
        return [], None

    site_en = pywikibot.Site('en', 'wikipedia')
    page = pywikibot.Page(site_en, f'Template:{en_template_title.strip()}')
    if not page.exists():
        return [], None

    text = page.text
    players = []

    # يلتقط اللاعب بكل حالاته: رقم موجود أو فارغ
    pattern_player = re.compile(
        r'\{\{\s*football squad2 player\s*\|\s*no\s*=\s*([^|}]*)\s*\|\s*name\s*=\s*(.*?)\s*\}\}',
        flags=re.IGNORECASE | re.DOTALL
    )
    for m in pattern_player.finditer(text):
        no = m.group(1).strip()
        name_raw = m.group(2).strip()
        players.append((no, name_raw))

    # يلتقط المدير مهما كان وجود title أو لا
    pattern_manager = re.compile(
        r'\{\{\s*football squad(?:2)? manager\s*(?:\|\s*title\s*=\s*[^|}]*\s*)?\|\s*name\s*=\s*(.*?)\s*\}\}',
        flags=re.IGNORECASE | re.DOTALL
    )
    m = pattern_manager.search(text)
    manager = m.group(1).strip() if m else None

    return players, manager

def handle_special_name(name):
    # أنماط القائد وتحويلها إلى {{ك}}
    name = re.sub(r'\(\s*\[\[\s*Captain \(association football\)\s*\|\s*c\s*\]\]\s*\)', '({{ك}})', name, flags=re.IGNORECASE)
    name = re.sub(r'\[\[\s*Captain \(association football\)\s*\|\s*c\s*\]\]', '({{ك}})', name, flags=re.IGNORECASE)
    name = re.sub(r'\(\s*\[\[\s*قائد الفريق \(كرة القدم\)\s*\|\s*الفريق\s*\]\]\s*\)', '({{ك}})', name)
    name = re.sub(r'\[\[\s*قائد الفريق \(كرة القدم\)\s*\|\s*الفريق\s*\]\]', '({{ك}})', name)

    # إزالة أقواس مكررة حول {{ك}}
    name = re.sub(r'\(\(\s*\{\{ك\}\}\s*\)\)', '({{ك}})', name)
    name = re.sub(r'\(\s*\{\{ك\}\}\s*\)', '({{ك}})', name)

    # تحويل Abbr إلى اختص وإغلاق القالب
    name = name.replace('{{Abbr|', '{{اختص|')
    open_count = name.count('{{اختص|')
    close_count = name.count('}}')
    if open_count > close_count:
        name += '}' * (2 * (open_count - close_count))

    # تحويل الوصلات إن وُجدت مقابل عربي
    def repl(m):
        inner = m.group(1).strip()
        parts = inner.split('|', 1)
        if len(parts) == 2:
            page, _ = parts
            return get_arabic_name(page.strip())
        return f'[[{inner}]]'
    name = re.sub(r'\[\[(.*?)\]\]', repl, name)

    return name

def build_arabic_template(team_name, players, manager):
    lines = [
        '{{شريط تصفح تشكيلة فريق كرة قدم',
        '|الاسم=',
        f'|اسم الفريق= {team_name}',
        '|القائمة='
    ]
    for no, raw in players:
        name = handle_special_name(raw)
        if no:
            lines.append(f'{{{{لاعب تشكيلة فريق كرة قدم|الرقم={no}|الاسم={name}}}}}')
        else:
            lines.append(f'{{{{لاعب تشكيلة فريق كرة قدم|الاسم={name}}}}}')
    if manager:
        mgr = handle_special_name(manager)
        lines.append(f'{{{{مدرب تشكيلة فريق كرة قدم|العنوان=مدرب|الاسم={mgr}}}}}')
    lines.append('}}')
    return '\n'.join(lines)

def update_arabic_template(ar_template_title, new_text):
    site_ar = pywikibot.Site('ar', 'wikipedia')
    page = pywikibot.Page(site_ar, f'Template:{ar_template_title}')
    cats = []
    if page.exists():
        cats = re.findall(r'\[\[تصنيف:[^\]]+\]\]', page.text)
    new = re.sub(r'<noinclude>.*?</noinclude>', '', new_text, flags=re.DOTALL)
    if cats:
        new += '\n<noinclude>\n' + '\n'.join(cats) + '\n</noinclude>'
    page.text = new
    page.save(summary='بوت: تحديث قالب تشكيلة من الإنجليزية')

def process_all_teams():
    site_ar = pywikibot.Site('ar', 'wikipedia')
    user_page = pywikibot.Page(site_ar, 'مستخدم:Mohammed Qays/teams.json')
    data = json.loads(user_page.text)

    for team in data.get('teams', []):
        ar_t = team.get('ar_template')
        en_t = team.get('en_template')
        name = team.get('name')
        if not (ar_t and en_t and name):
            continue
        players, manager = extract_players_and_manager(en_t)
        if not players:
            continue
        text = build_arabic_template(name, players, manager)
        update_arabic_template(ar_t, text)

if __name__ == '__main__':
    process_all_teams()
