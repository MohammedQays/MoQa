import pywikibot
import re
import wikitextparser as wtp
import json
from datetime import datetime

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# تحميل المقالات من الملف JSON
def load_ignored_titles(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['title'] for item in data['query']['categorymembers']}
    except Exception as e:
        print(f"حدث خطأ أثناء قراءة الملف: {e}")
        return set()

# تحميل قائمة المقالات التي يجب تجاهلها
ignored_titles = load_ignored_titles("target_pages.json")

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
        list_category = [
            'صفحات مجموعات صيغ كيميائية مفهرسة',
            'كواكب صغيرة مسماة'
        ]
        for cat in categories:
            for needed_cat in list_category:
                if needed_cat in cat.title():
                    return True
        return False

    def check_title(self):
        return bool(re.search(r"\(\s*(توضيح|disambiguation)\s*\)", self.page_title))

# البحث عن المقالات
def process_page(page):
    try:
        # تجاهل الصفحة إذا كانت تحويلة
        if page.isRedirectPage():
            return

        # تجاهل المقالات المدرجة في قائمة التجاهل
        if page.title() in ignored_titles:
            print(f"تجاهل الصفحة {page.title()} لأنها مدرجة في قائمة التجاهل.")
            return

        original_text = page.text

        # تجاهل المقالات التي تحتوي على تحويل في المتن
        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
            print(f"تجاهل الصفحة {page.title()} لأنها تحتوي على تحويل في المتن.")
            return

        disambiguation_checker = Disambiguation(page, page.title(), original_text)

        # تجاهل صفحات التوضيح بناءً على النص أو العنوان أو التصنيفات
        if disambiguation_checker.check():
            return

        # تجاهل القوالب باستخدام تعبير منتظم
        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)

        # البحث عن التصنيفات ووضع قالب {{بذرة}} قبلها
        category_pattern = r'\[\[تصنيف:.*?\]\]'
        categories = re.findall(category_pattern, original_text)

        if categories:
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories)
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        # التحقق من شروط الحجم والكلمات وغياب قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))
        threshold = 40  # يمكن تعديل الحد الأدنى

        if (word_count / 300 * 40) + (size_in_bytes / 4000 * 60) < threshold and not re.search(r'{{بذرة\b', original_text):
            page.text = new_text
            page.save(summary='إضافة قالب بذرة - تجريبي')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# معالجة جميع المقالات في نطاق المقالات (النطاق الرئيسي)
for page in site.allpages(namespace=0):
    process_page(page)
