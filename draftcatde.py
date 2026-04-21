import pywikibot
import re

site = pywikibot.Site()
site.login()

run = True

edit_summary = 'بوت: إزالة قالب تصنيفات مسودة'

cat = pywikibot.Category(site, 'تصنيف:مقالات تستخدم تصنيفات مسودة')

regex_main = re.compile(r'\n\{\{(?:تصنيفات مسودة|Draft categories)\|(?:1\=)?(.*?)\n\}\}', re.DOTALL)
regex_cat = re.compile(r'\[\[:تصنيف:')
regex_blank = re.compile(r'^\s*?$')

def replace(text):
    match = regex_main.search(text)
    if match:
        text_cats = match.group(1)
        text_cats = regex_cat.sub('[[تصنيف:', text_cats)

        if regex_blank.search(text_cats):
            text_cats = '\n'

        text = regex_main.sub(text_cats, text)

    return text

def main():
    for page in cat.articles():
        try:
            text = page.text
            new_text = replace(text)

            if run and new_text != text:
                page.text = new_text
                page.save(summary=edit_summary)

        except Exception as e:
            print(f'خطأ في الصفحة {page.title()}: {e}')

main()
