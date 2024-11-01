# البحث عن المقالات
def process_page(page):
    try:
        # تجاهل الصفحات التحويلية
        if page.isRedirectPage():
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة تحويلة)")
            return
        
        if re.match(r'#تحويل\s*\[\[.*?\]\]', page.text, re.IGNORECASE):
            print(f"تم تجاهل الصفحة: {page.title()} (صفحة تحويلة)")
            return
        # كود التحقق من صفحات التوضيح
        disambiguation_checker = Disambiguation(page, page.title(), page.text)

        # تجاهل صفحات التوضيح بناءً على النص أو العنوان أو التصنيفات
        if disambiguation_checker.check():
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
            print(f"تمت إضافة قالب بذرة إلى الصفحة: {page.title()}")
        else:
            print(f"الصفحة {page.title()} لا تحتاج إلى تعديل.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصفحة {page.title()}: {e}")
