#!/usr/bin/env python3
import pywikibot
import toolforge

# إعدادات البوت
class settings:
    lang = 'enwiki'  # قاعدة البيانات المصدر (ويكيبيديا الإنجليزية)
    user_page = "مستخدم:Mohammed Qays/بوت"  # الصفحة الهدف للتحديث
    editsumm = "[[وب:بوت|بوت]]: تحديث تلقائي لقوالب لمح البصر."  # ملخص التعديل
    debug = "no"  # عند التعيين على "no"، يتم تحديث الصفحة فعليًا

# استعلام SQL لجلب القوالب من ويكيبيديا الإنجليزية
query = '''
SELECT CONCAT('[[Template:', page_title, ']]') AS Template_Link
FROM categorylinks 
JOIN page ON cl_from = page_id 
WHERE cl_to = 'Templates_used_by_Twinkle' 
AND page_namespace = 10;
'''

def execute_query():
    """تنفيذ الاستعلام لاسترداد قائمة القوالب."""
    try:
        conn = toolforge.connect(settings.lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()  # كل صف يحتوي على Template_Link
        conn.close()
        return result
    except Exception as e:
        raise SystemExit(e)

def check_template_exists(template_link, site):
    """التحقق مما إذا كان القالب موجودًا في ويكيبيديا العربية."""
    if isinstance(template_link, bytes):
        template_link = template_link.decode('utf-8')
    
    template_link = template_link.strip("b'")
    
    if template_link.startswith('[[Template:') and template_link.endswith(']]'):
        template_name = template_link[len('[[Template:'):-2]
        page = pywikibot.Page(site, f"Template:{template_name}")
        return page.exists()
    
    return False

def update_user_page():
    """تحديث صفحة المستخدم بقائمة القوالب وحالتها."""
    site = pywikibot.Site('ar', 'wikipedia')  # الاتصال بويكيبيديا العربية
    page = pywikibot.Page(site, settings.user_page)
    
    templates_result = execute_query()  # جلب القوالب من ويكيبيديا الإنجليزية
    
    # تقسيم القوالب إلى مجموعات من 100 قالب
    content = "== تحديث قائمة القوالب ==\n"
    total_templates = len(templates_result)
    
    for i in range(0, total_templates, 100):
        start = i + 1
        end = min(i + 100, total_templates)
        content += f"\n== القوالب من {start} إلى {end} ==\n"
        content += "{| class='wikitable sortable'\n"
        content += "|-\n! القالب !! الحالة\n"
        
        for row in templates_result[i:end]:
            template_link = row[0]  # مثال: [[Template:اسم القالب]]
            if isinstance(template_link, bytes):
                template_link = template_link.decode('utf-8')
            template_link = template_link.strip("b'")
            exists = check_template_exists(template_link, site)
            status = "{{تم}}" if exists else "{{لمذ}}"
            content += "|-\n| {} || {}\n".format(template_link, status)
        
        content += "|}\n"
    
    if settings.debug == "no":
        page.put(content, summary=settings.editsumm)

if __name__ == "__main__":
    update_user_page()
