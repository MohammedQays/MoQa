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
            return

        original_text = page.text

        # تجاهل المقالات التي تحتوي على تحويل في المتن
        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
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

        # إذا وُجدت التصنيفات، نضع قالب البذرة قبل التصنيفات
        if categories:
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories)
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            # إذا لم توجد تصنيفات، إضافة قالب البذرة في النهاية
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        # التحقق من شروط الحجم والكلمات وغياب أو وجود قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        # حساب المعادلة لتحديد ما إذا كانت الصفحة تحتاج إلى قالب بذرة
        word_score = (word_count / 200) * 40
        size_score = (size_in_bytes / 3000) * 60
        score = word_score + size_score
        threshold = 100  # القيمة الحدية للقرار

        # إذا كانت المقالة أعلى من الحد الأدنى وتحتوي على قالب بذرة، قم بإزالة القالب
        if score >= threshold and re.search(r'{{بذرة\b', original_text):
            # إزالة قالب البذرة
            new_text = re.sub(r'{{بذرة}}\n*', '', original_text, flags=re.IGNORECASE).strip()
            page.text = new_text
            try:
                page.save(summary='بوت: إزالة قالب بذرة')
                print(f"تمت إزالة قالب بذرة من الصفحة: {page.title()}")
            except Exception as e:
                print(f"حدث خطأ أثناء حفظ الصفحة {page.title()}: {e}")

        # إذا كانت المقالة أقل من الحد الأدنى ولا تحتوي على قالب بذرة، قم بإضافته
        elif score < threshold and not re.search(r'{{بذرة\b', original_text):
            # تحديث نص الصفحة بإضافة قالب بذرة
            page.text = new_text
            try:
                page.save(summary='بوت: إضافة قالب بذرة - تجريبي')
                print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
            except Exception as e:
                print(f"حدث خطأ أثناء حفظ الصفحة {page.title()}: {e}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# معالجة جميع المقالات في نطاق المقالات (النطاق الرئيسي)
for page in site.allpages(namespace=0):
    process_page(page)
