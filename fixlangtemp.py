#!/usr/bin/env python3
import pywikibot
import toolforge
import re

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: استبدال قوالب وصلة لغة بروابط ويكي."
    debug = "no"  # لتجربة بدون حفظ، اجعلها "yes"

# استعلام SQL لجلب المقالات ضمن تصنيف "صيانة قوالب لغة"
query = '''
SELECT page.page_title
FROM page
JOIN categorylinks ON categorylinks.cl_from = page.page_id
WHERE categorylinks.cl_to = 'صيانة_قوالب_لغة'
AND page.page_namespace = 0;
'''

# التعبيرات المنتظمة للقوالب المستهدفة
lang_templates = {
    r'\{\{\s*(?:وصلة\s*لغة|لغ)\s*\|\s*عربية\s*\}\}': r'[[اللغة العربية|العربية]]',
    r'\{\{\s*(?:وصلة\s*لغة|لغ)\s*\|\s*إنجليزية\s*\}\}': r'[[اللغة الإنجليزية|الإنجليزية]]'
}

# تجميع كل الأنماط في تعبير واحد
compiled_lang_templates = [(re.compile(pattern, re.IGNORECASE), replacement) 
                           for pattern, replacement in lang_templates.items()]

def execute_query():
    """تنفيذ الاستعلام لاسترداد عناوين المقالات."""
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print("خطأ في تنفيذ الاستعلام:", e)
        return []

def fix_lang_templates(text):
    """استبدال قوالب وصلة لغة بروابط ويكي."""
    new_text = text
    for regex, repl in compiled_lang_templates:
        new_text = regex.sub(repl, new_text)
    return new_text.strip()

def process_page(title, site):
    """تحديث صفحة واحدة إذا احتاجت تعديل."""
    page = pywikibot.Page(site, title)
    
    if not page.exists():
        return

    old_text = page.text
    new_text = fix_lang_templates(old_text)

    if old_text != new_text:
        if settings.debug == "no":
            page.text = new_text
            page.save(summary=settings.editsumm)
        else:
            print(f"تجربة فقط: {title}")

def main():
    site = pywikibot.Site('ar', 'wikipedia')
    results = execute_query()

    for row in results:
        title = row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]
        title = title.replace("_", " ")
        process_page(title, site)

if __name__ == "__main__":
    main()
