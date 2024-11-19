import pywikibot
import re
import wikitextparser as wtp
import json
from datetime import datetime

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# قراءة قائمة المقالات المحددة من ملف JSON
def load_target_pages():
    try:
        with open('target_pages.json', 'r', encoding='utf-8') as f:
            target_pages = json.load(f)
    except FileNotFoundError:
        target_pages = []
    return target_pages

# حفظ قائمة المقالات إلى ملف JSON
def save_target_pages(target_pages):
    with open('target_pages.json', 'w', encoding='utf-8') as f:
        json.dump(target_pages, f, ensure_ascii=False, indent=4)

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

# البحث عن المقالات
def process_page(page, target_pages):
    try:
        # إذا كانت المقالة ليست في قائمة المقالات المستهدفة، تجاهلها
        if page.title() not in target_pages:
            print(f"تم تجاهل الصفحة {page.title()} لأنها ليست في قائمة المقالات المستهدفة.")
            return

        # إذا كانت المقالة تحويلة
        if page.isRedirectPage():
            print(f"تم تجاهل الصفحة {page.title()} لأنها تحويلة.")
            return

        original_text = page.text

        # تجاهل المقالات التي تحتوي على تحويل في المتن
        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
            print(f"تجاهل الصفحة {page.title()} لأنها تحتوي على تحويل في المتن.")
            return

        disambiguation_checker = Disambiguation(page, page.title(), original_text)
        
        # تجاهل صفحات التوضيح بناءً على النص أو العنوان أو التصنيفات
        if disambiguation_checker.check():
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة توضيح)")
            return

        # تجاهل القوالب باستخدام تعبير منتظم
        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)

        # البحث عن التصنيفات ووضع قالب {{بذرة}} قبلها
        category_pattern = r'\[\[تصنيف:.*?\]\]'
        categories = re.findall(category_pattern, original_text)

        # إذا وُجدت التصنيفات، نضع قالب البذرة قبل التصنيفات
        if categories:
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories)
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            # إذا لم توجد تصنيفات، إضافة قالب البذرة في النهاية
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        # التحقق من حجم المقالة
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        # إذا كان حجم المقالة أقل من 3000 بايت ولم يتم إضافة قالب بذرة
        if size_in_bytes < 3000 and not re.search(r'{{بذرة\b', original_text):
            # إضافة قالب بذرة في نهاية المقالة
            page.text = new_text
            page.save(summary='بوت:إضافة قالب بذرة - تجريبي')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# تحميل المقالات المستهدفة من الملف
target_pages = load_target_pages()

# معالجة المقالات في قائمة المقالات المستهدفة
for page in site.allpages(namespace=0):
    process_page(page, target_pages)
