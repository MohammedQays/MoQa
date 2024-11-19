import pywikibot
import re
import wikitextparser as wtp
from datetime import datetime

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
        # التحقق باستخدام المنطق المطلوب
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
def process_page(page):
    try:
        # تجاهل الصفحة إذا كانت تحويلة
        if page.isRedirectPage():
            print(f"تم تجاهل الصفحة {page.title()} لأنها تحويلة.")
            return

        original_text = page.text

        # تجاهل المقالات التي تحتوي على تحويل في المتن
        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
            print(f"تجاهل الصفحة {page.title()} لأنها تحتوي على تحويل في المتن.")
            return

        # التحقق من التصنيفات لتجاهل المقالات ضمن تصنيف "كواكب صغيرة مسماة"
        categories = page.categories()
        for cat in categories:
            if "كواكب صغيرة مسماة" in cat.title():
                print(f"تم تجاهل الصفحة {page.title()} لأنها ضمن تصنيف كواكب صغيرة مسماة.")
                return

        # التحقق من وجود القوالب أو التصنيفات أو العنوان الخاص بالتوضيح
        disambiguation_checker = Disambiguation(page, page.title(), original_text)
        
        # تجاهل صفحات التوضيح بناءً على النص أو العنوان أو التصنيفات
        if disambiguation_checker.check():
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة توضيح)")
            return

        # تجاهل القوالب باستخدام تعبير منتظم
        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)

        # البحث عن التصنيفات ووضع قالب {{بذرة}} قبلها
        category_pattern = r'\[\[تصنيف:.*?\]\]'
        categories_in_text = re.findall(category_pattern, original_text)

        # إذا وُجدت التصنيفات، نضع قالب البذرة قبل التصنيفات
        if categories_in_text:
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories_in_text)
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            # إذا لم توجد تصنيفات، إضافة قالب البذرة في النهاية
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        # التحقق من شروط الحجم والكلمات وغياب قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        threshold = 100  # يجب تحديد الحد الأدنى بناءً على متطلباتك
        if (word_count / 200 * 40) + (size_in_bytes / 3000 * 60) < threshold and not re.search(r'{{بذرة\b', original_text):
            # تحديث نص الصفحة
            page.text = new_text
            page.save(summary='بوت: إضافة قالب بذرة - تجريبي')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")


# معالجة جميع المقالات في نطاق المقالات (النطاق الرئيسي)
for page in site.allpages(namespace=0):
    # التحقق من أن العنوان يبدأ بحرف بين "أ" و "ي"
    if not re.match(r'^[أ-ي]', page.title()):
        continue  # تخطي الصفحات التي لا تبدأ بالحروف المطلوبة
    
    # معالجة الصفحة
    process_page(page)
