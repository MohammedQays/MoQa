import pywikibot
import re
import wikitextparser as wtp

# تعريف الموقع (اللغة المختارة هي العربية ar)
site = pywikibot.Site('ar', 'wikipedia')
site.login()

# التصنيفات المستبعدة (إن وُجدت ضمن المقالات في التصنيف)
excluded_categories = [
    'صفحات مجموعات صيغ كيميائية مفهرسة',
    'كواكب صغيرة مسماة',
    'تحويلات من لغات بديلة',
    'تحويلات علم الفلك'
]

# ملف لحفظ المقالات المستبعدة (للتوثيق)
ignored_pages_file = "ignored_pages.txt"

def log_ignored_page(page_title):
    with open(ignored_pages_file, "a", encoding="utf-8") as file:
        file.write(f"{page_title}\n")
    print(f"تم إضافة {page_title} إلى ملف المقالات المستبعدة.")

def process_page(page):
    try:
        # التحقق من التصنيفات المستبعدة إن وُجدت
        page_categories = {cat.title(with_ns=False) for cat in page.categories()}
        if any(excluded_category in page_categories for excluded_category in excluded_categories):
            log_ignored_page(page.title())
            print(f"تم تخطي الصفحة {page.title()} لأنها تنتمي إلى تصنيف مستبعد.")
            return

        # بما أن التصنيف \"بذرة بحاجة لتعديل\" لا يحتوي على تحويلات أو صفحات توضيح، فلا حاجة لفحصها

        original_text = page.text

        # إزالة القوالب لحساب عدد الكلمات وحجم النص بدقة
        text_without_templates = re.sub(r'{{.*?}}', '', original_text, flags=re.DOTALL)
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        # حساب المعادلة لتحديد مستوى المقالة
        score = (word_count / 400 * 40) + (size_in_bytes / 5000 * 60)
        threshold = 100  # قيمة العتبة المناسبة

        # إذا كانت المقالة تحقق المعايير الأعلى وتحتوي على قالب {{بذرة}}، نقوم بإزالته
        if score >= threshold and re.search(r'{{بذرة\b', original_text):
            new_text = re.sub(r'{{بذرة}}\s*', '', original_text, flags=re.IGNORECASE).strip()
            page.text = new_text
            page.save(summary='بوت: إزالة قالب بذرة')
            print(f"تمت إزالة قالب بذرة من الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# معالجة جميع المقالات في تصنيف "بذرة بحاجة لتعديل"
category = pywikibot.Category(site, 'تصنيف:بذرة بحاجة لتعديل')
for page in category.articles():
    process_page(page)
