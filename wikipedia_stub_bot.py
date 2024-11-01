import pywikibot
import re
import wikitextparser as wtp
from core.utils.helpers import prepare_str
from datetime import datetime

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# قائمة لتسجيل التعديلات لتقرير البوت
report = []

class Disambiguation:
    def __init__(self, page, page_title, page_text):
        self.page = page
        self.page_title = str(page_title).lower()
        self.page_text = str(page_text).lower()
        self.list_of_templates = ["توضيح", "Disambig", "صفحة توضيح", "Disambiguation"]

    def check(self, logic="and"):
        if logic.lower() == "and".lower():
            return (self.check_text() and self.check_title()) or self.have_molecular_formula_set_index_articles()
        elif logic.lower() == "or".lower():
            return (self.check_text() or self.check_title()) or self.have_molecular_formula_set_index_articles()

    def check_text(self):
        parsed = wtp.parse(self.page_text)
        template_found = False
        for needed_template in self.list_of_templates:
            for template in parsed.templates:
                if needed_template.lower() == template.normal_name().lower():
                    template_found = True
                    break
        return template_found

    def have_molecular_formula_set_index_articles(self):
        categories = self.page.categories()
        found = 0
        list_category = ['صفحات مجموعات صيغ كيميائية مفهرسة']
        for cat in categories:
            for needed_cat in list_category:
                if prepare_str(needed_cat) == prepare_str(cat.title(with_ns=False)):
                    found = 1
                    break
        return found

    def check_title(self):
        if re.search(r"\(\s*(توضيح|disambiguation)\s*\)", self.page_title) is not None:
            return True
        return False

# البحث عن المقالات
def process_page(page):
    try:
        disambiguation_checker = Disambiguation(page, page.title(), page.text)
        
        # تجاهل صفحات التوضيح بناءً على النص أو العنوان أو التصنيفات
        if disambiguation_checker.check("or"):
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة توضيح)")
            return

        original_text = page.text

        # تجاهل القوالب باستخدام تعبير منتظم
        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)

        # البحث عن التصنيفات ووضع قالب {{بذرة}} قبلها
        category_pattern = r'\[\[تصنيف:.*?\]\]'
        categories = re.findall(category_pattern, original_text)

        # إذا وُجدت التصنيفات، نضع قالب البذرة قبل التصنيفات
        if categories:
            # فصل النص إلى جزئين: قبل التصنيفات وبعدها
            text_before_categories = re.split(category_pattern, original_text, maxsplit=1)[0]
            text_with_categories = "\n".join(categories)

            # إضافة قالب بذرة قبل التصنيفات
            new_text = text_before_categories.strip() + '\n\n{{بذرة}}\n\n' + text_with_categories
        else:
            # إذا لم توجد تصنيفات، إضافة قالب البذرة في النهاية
            new_text = original_text.strip() + '\n\n{{بذرة}}'

        # التحقق من شروط الحجم والكلمات وغياب قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        if word_count < 300 and size_in_bytes < 4000 and not re.search(r'{{بذرة\b', original_text):
            # تحديث نص الصفحة
            page.text = new_text
            page.save(summary='إضافة قالب بذرة - تجريبي')
            # إضافة التعديل إلى التقرير مع التاريخ والوقت
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.append(f"* {now} - [[{page.title()}]] - تمت إضافة قالب بذرة")
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# تحديث تقرير البوت في صفحة "مستخدم:Mohammed Qays/بوت"
def update_report():
    report_page = pywikibot.Page(site, 'مستخدم:Mohammed Qays/بوت')
    
    # جلب محتوى التقرير الحالي
    try:
        current_report = report_page.text
    except pywikibot.NoPage:
        current_report = "== تقرير تعديلات البوت ==\n\n"  # إذا لم تكن الصفحة موجودة، نبدأ تقريرًا جديدًا
    
    # محتوى التقرير الجديد (إضافة إلى التقرير القديم)
    report_content = "\n".join(report)
    
    if report:
        # إضافة التعديلات الجديدة إلى التقرير الحالي مع ترتيبها بالأعلى
        new_report_text = f"== تقرير تعديلات البوت ==\n\n{report_content}\n\n" + current_report
    else:
        new_report_text = current_report  # إذا لم يتم إجراء أي تعديلات، لا نغير التقرير
    
    # حفظ التقرير المحدث
    report_page.text = new_report_text
    report_page.save(summary="تحديث تقرير تعديلات البوت")

# المقالات المحددة للعمل عليها
article_titles = [
    'آلان غواميني',
    'آرت ديفي',
    'آرني إليبي',
    'آقا ميراك',
    'آرثر بوجين'
]

# معالجة المقالات المحددة
for title in article_titles:
    page = pywikibot.Page(site, title)
    process_page(page)

# تحديث تقرير البوت
update_report()
