import pywikibot
import re
import wikitextparser as wtp
from datetime import datetime

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# التصنيفات المستبعدة
excluded_categories = [
    'صفحات مجموعات صيغ كيميائية مفهرسة',
    'كواكب صغيرة مسماة',
    'تحويلات من لغات بديلة',
    'تحويلات علم الفلك'
]

# ملف لحفظ المقالات المستبعدة
ignored_pages_file = "ignored_pages.txt"

# فتح الملف لتسجيل المقالات المستبعدة
def log_ignored_page(page_title):
    with open(ignored_pages_file, "a", encoding="utf-8") as file:
        file.write(f"{page_title}\n")
        print(f"تم إضافة {page_title} إلى ملف المقالات المستبعدة.")

class Disambiguation:
    def __init__(self, page, page_title, page_text):
        self.page = page
        self.page_title = str(page_title).lower()
        self.page_text = str(page_text).lower()
        self.list_of_templates = ["توضيح", "Disambig", "صفحة توضيح", "Disambiguation"]

    def check(self):
        return self.check_text() or self.check_title()

    def check_text(self):
        parsed = wtp.parse(self.page_text)
        for needed_template in self.list_of_templates:
            for template in parsed.templates:
                if needed_template.lower() == template.normal_name().lower():
                    return True
        return False

    def check_title(self):
        return bool(re.search(r"\(\s*(توضيح|disambiguation)\s*\)", self.page_title))

# البحث عن المقالات
def process_page(page):
    try:
        # التحقق من التصنيفات المستبعدة
        page_categories = {cat.title(with_ns=False) for cat in page.categories()}
        if any(excluded_category in page_categories for excluded_category in excluded_categories):
            log_ignored_page(page.title())  # إضافة المقالة إلى الملف المستبعد
            print(f"تم تخطي الصفحة {page.title()} لأنها تنتمي إلى تصنيف مستبعد.")
            return

        # تجاهل الصفحة إذا كانت تحويلة
        if page.isRedirectPage():
            log_ignored_page(page.title())  # إضافة المقالة إلى الملف المستبعد
            print(f"تم تجاهل الصفحة {page.title()} لأنها تحويلة.")
            return

        original_text = page.text

        # تجاهل المقالات التي تحتوي على تحويل في المتن
        if re.match(r'#تحويل\s*\[\[.*?\]\]', original_text, re.IGNORECASE):
            log_ignored_page(page.title())  # إضافة المقالة إلى الملف المستبعد
            return

        disambiguation_checker = Disambiguation(page, page.title(), original_text)

        # تجاهل صفحات التوضيح
        if disambiguation_checker.check():
            log_ignored_page(page.title())  # إضافة المقالة إلى الملف المستبعد
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

        # التحقق من شروط الحجم والكلمات وغياب قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        # حساب المعادلة لتحديد ما إذا كانت الصفحة تحتاج إلى قالب بذرة
        score = (word_count / 300 * 40) + (size_in_bytes / 4000 * 60)
        threshold = 100  # تحديد قيمة عتبة (threshold) المناسبة

        if score < threshold and not re.search(r'{{بذرة\b', original_text):
            # تحديث نص الصفحة
            page.text = new_text
            page.save(summary='بوت:إضافة قالب بذرة')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# معالجة جميع المقالات في نطاق المقالات (النطاق الرئيسي) مع تخطي المقالات المستبعدة مسبقًا
for page in site.allpages(namespace=0):
    process_page(page)
