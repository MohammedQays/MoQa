def process_page(page):
    try:
        # تجاهل الصفحة إذا لم تكن في النطاق الرئيسي (للتأكد من معالجة المقالات فقط)
        if page.namespace() != 0:
            return

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

        # التحقق من شروط الحجم والكلمات وغياب قالب بذرة
        word_count = len(text_without_templates.split())
        size_in_bytes = len(text_without_templates.encode('utf-8'))

        # حساب المعادلة لتحديد ما إذا كانت الصفحة تحتاج إلى قالب بذرة
        score = (word_count / 190 * 40) + (size_in_bytes / 2000 * 60)
        threshold = 100  # تحديد قيمة عتبة (threshold) المناسبة

        if score < threshold and not re.search(r'{{بذرة\b', original_text):
            # تحديث نص الصفحة
            page.text = new_text
            page.save(summary='بوت:إضافة قالب بذرة - تجريبي')
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")

# دالة لمعالجة جميع المقالات ضمن تصنيفات فرعية
def process_category(category_name):
    category = pywikibot.Category(site, category_name)
    for subcategory in category.subcategories():  # استعراض التصنيفات الفرعية
        for page in subcategory.articles():  # استعراض المقالات داخل التصنيف الفرعي
            process_page(page)

# استدعاء الدالة لمعالجة المقالات داخل التصنيفات الفرعية
process_category("تصنيف:مقالات_غير_مقيمة")
