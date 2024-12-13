import pywikibot

# إنشاء موقع ويكيبيديا
site = pywikibot.Site("ar", "wikipedia")

# تصنيف القوالب
category = pywikibot.Category(site, "تصنيف:قوالب رسائل بذرة أفغانستان")

# البحث عن القوالب ضمن التصنيف
for page in category.articles():
    try:
        # تحميل محتوى الصفحة
        text = page.text

        # استبدال الصورة
        if "Flag of Syria.svg" in text:
            new_text = text.replace("Flag of Afghanistan (2013–2021).svg", "Flag of the Taliban.svg")

            # حفظ التعديلات
            page.text = new_text
            page.save(summary="استبدال صورة العلم")
            print(f"تم تعديل الصفحة: {page.title()}")
        else:
            print(f"لم يتم العثور على الصورة المستهدفة في الصفحة: {page.title()}")
    except Exception as e:
        print(f"حدث خطأ مع الصفحة {page.title()}: {e}")
