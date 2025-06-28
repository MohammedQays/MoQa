import pywikibot
import re
import json

FOOTBALL_TEMPLATES = [
    'صندوق معلومات سيرة كرة قدم',
    'معلومات لاعب',
    'صندوق معلومات سيرة ذاتية للاعب كرة قدم',
    'Infobox Football biography',
    'Football player infobox',
    'صندوق معلومات سيرة ذاتية في كرة القدم',
    'Infobox Football biography 2',
    'Infobox football biography 2',
    'معلومات لاعب كرة قدم 2',
    'Infobox football biography',
    'معلومات لاعب كرة قدم',
    'صندوق معلومات سيرة كرة القدم',
    'صندوق معلومات لاعب كرة قدم',
    'صندوق معلومات سيرة لاعب كرة قدم',
    'معلومات شخصية كرة قدم',
    'صندوق معلومات لاعب كرة قدم أمريكية'
]

IMAGE_FIELDS = ['صورة', 'الصورة', 'image', 'image_name']


def find_infobox_start(text):
    for template in FOOTBALL_TEMPLATES:
        match = re.search(rf'(?i)\{{{{\s*{re.escape(template)}\b', text)
        if match:
            return match.start(), match.group(0)
    return None, None


def get_image_from_en_article(title):
    site_en = pywikibot.Site('en', 'wikipedia')
    page_en = pywikibot.Page(site_en, title)
    if not page_en.exists():
        return None

    text_en = page_en.text
    match = re.search(r'\|\s*image\s*=\s*(.+)', text_en, re.IGNORECASE)
    if match:
        image_name = match.group(1).strip()
        image_name = re.sub(r'\[\[|\]\]', '', image_name)
        image_name = image_name.split('|')[0].strip()
        if image_name.lower().endswith(('.jpg', '.jpeg', '.png', '.svg')):
            return image_name
    return None


def update_or_add_image(text, image_name):
    start, template_match = find_infobox_start(text)
    if start is None:
        return text

    lines = text.splitlines()
    updated = False
    found_image = False

    for idx, line in enumerate(lines):
        for field in IMAGE_FIELDS:
            match = re.match(rf'\|\s*{field}\s*=\s*(.+)', line)
            if match:
                found_image = True
                current = match.group(1).strip()
                current_clean = re.sub(r'\[\[|\]\]', '', current).split('|')[0].strip()
                if current_clean != image_name:
                    lines[idx] = f'| {field} = {image_name}'
                    updated = True
                break
        if found_image:
            break

    # لا تقم بإضافة صورة إذا لم تكن موجودة من قبل
    return '\n'.join(lines) if updated else text


def remove_nonempty_caption(text):
    def clean_caption(match):
        value = match.group(2).strip()
        return '' if not value else ''  
    return re.sub(r'^\|\s*(تعليق(?:\s*الصورة)?|caption|شرح)\s*=\s*.+$', clean_caption, text, flags=re.MULTILINE)


def process_article(title):
    site_ar = pywikibot.Site('ar', 'wikipedia')
    page_ar = pywikibot.Page(site_ar, title)

    if not page_ar.exists():
        return

    text_ar = page_ar.text

    if not any(template in text_ar for template in FOOTBALL_TEMPLATES):
        return

    item = pywikibot.ItemPage.fromPage(page_ar)
    item.get()
    sitelinks = item.sitelinks
    if 'enwiki' not in sitelinks:
        return

    en_title = sitelinks['enwiki'].title
    image_name = get_image_from_en_article(en_title)
    if not image_name:
        return

    commons_site = pywikibot.Site('commons', 'commons')
    image_page = pywikibot.FilePage(commons_site, 'File:' + image_name)
    if not image_page.exists():
        return

    new_text = update_or_add_image(text_ar, image_name)
    new_text = remove_nonempty_caption(new_text)

    if new_text != text_ar:
        page_ar.text = new_text
        page_ar.save(summary='بوت: تحديث صورة - تجريبي')


def load_titles_from_categories():
    site = pywikibot.Site('ar', 'wikipedia')
    user_page = pywikibot.Page(site, 'مستخدم:Mohammed Qays/photo.json')
    json_content = json.loads(user_page.text)

    titles = set()
    for category_name in json_content.get("categories", []):
        cat = pywikibot.Category(site, category_name)
        for page in cat.articles():
            titles.add(page.title())

    return list(titles)


if __name__ == '__main__':
    try:
        titles = load_titles_from_categories()
        for title in titles:
            try:
                process_article(title)
            except Exception:
                continue
    except Exception:
        pass
