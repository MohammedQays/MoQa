import pywikibot

# إنشاء موقع ويكيبيديا
site = pywikibot.Site("ar", "wikipedia")

# تصنيف القوالب
category = pywikibot.Category(site, "تصنيف:قوالب بذرة أعلام سوريا حسب المهنة")

# البحث عن القوالب ضمن التصنيف
for page in category.articles():
    try:
        # تحميل محتوى الصفحة
        text = page.text

        # استبدال الصورة
        if "Flag of Syria.svg" in text:
            new_text = text.replace("Flag of Syria.svg", "Flag of the Syrian revolution.svg")

            # حفظ التعديلات
            page.text = new_text
            page.save(summary="استبدال صورة العلم بعلم الثورة السورية")
            print(f"تم تعديل الصفحة: {page.title()}")
        else:
            print(f"لم يتم العثور على الصورة المستهدفة في الصفحة: {page.title()}")
    except Exception as e:
        print(f"حدث خطأ مع الصفحة {page.title()}: {e}")
