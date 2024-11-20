import pywikibot
import re
import wikitextparser as wtp
from datetime import datetime
from random import shuffle

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

class Disambiguation:
    def __init__(self, page, page_title, page_text):
        self.page = page
        self.page_title = str(page_title).lower()
        self.page_text = str(page_text).lower()
        self.list_of_templates = ["توضيح", "Disambig", "صفحة توضيح", "Disambiguation"]

    def check(self, logic="or"):
        return (self.check_text() or self.check_title()) or self.have_molecular_formula_set_index_articles()

    def check_text(self):
        parsed = wtp.parse(self.page_text)
        for needed_template in self.list_of_templates:
            for template in parsed.templates:
                if needed_template.lower() == template.normal_name().lower():
                    return True
        return False

    def have_molecular_formula_set_index_articles(self):
        categories = self.page.categories()
        list_category = ['صفحات مجموعات صيغ كيميائية مفهرسة']
        for cat in categories:
            for needed_cat in list_category:
                if needed_cat in cat.title():
                    return True
        return False

    def check_title(self):
        return bool(re.search(r"\(\s*(توضيح|disambiguation)\s*\)", self.page_title))


def process_page(page):
    try:
        if page.isRedirectPage():
            print(f"تم تجاهل الصفحة {page.title()} لأنها تحويلة.")
            return

        original_text = page.text

        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
            print(f"تجاهل الصفحة {page.title()} لأنها تحتوي على تحويل في المتن.")
            return

        categories = page.categories()
        for cat in categories:
            if "كواكب صغيرة مسماة" in cat.title():
                print(f"تم تجاهل الصفحة {page.title()} لأنها ضمن تصنيف كواكب صغيرة مسماة.")
                return

        disambiguation_checker = Disambiguation(page, page.title(), original_text)
        if disambiguation_checker.check():
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة توضيح)")
            return

        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)
        category_pattern = r'\[\[تصنيف:.*?\]\]'
        categories_in_text = re.findall(category_pattern, original_text)

        if categories_in_text:
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories_in_text)
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        threshold = 100
        if (word_count / 200 * 40) + (size_in_bytes / 3000 * 60) < threshold and not re.search(r'{{بذرة\b', original_text):
            page.text = new_text
            page.save(summary='بوت: إضافة قالب بذرة - تجريبي')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")


# جلب جميع المقالات في نطاق المقالات (النطاق الرئيسي)
pages = list(site.allpages(namespace=0))

# خلط المقالات عشوائيًا
shuffle(pages)

# معالجة المقالات بعد ترتيبها بشكل عشوائي
for page in pages:
    process_page(page)
