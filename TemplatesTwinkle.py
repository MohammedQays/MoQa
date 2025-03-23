#!/usr/bin/env python3
import pywikibot
import toolforge

# إعدادات البوت
class settings:
    lang = 'enwiki'  # قاعدة البيانات المصدر (ويكيبيديا الإنجليزية)
    user_page = "مستخدم:Mohammed Qays/بوت"  # الصفحة الهدف للتحديث
    editsumm = "[[وب:بوت|بوت]]: تحديث تلقائي"  # ملخص التعديل
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
    
    # إزالة 'b' و '' من القيم إذا كانت من نوع str
    if isinstance(template_link, str):
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
    
    # تقسيم القوالب إلى قوالب تم إنشاؤها وغير منشأة
    created_templates = []
    uncreated_templates = []
    
    for row in templates_result:
        template_link = row[0]  # مثال: [[Template:اسم القالب]]
        
        # التحقق من نوع البيانات وإزالة 'b' و ''
        if isinstance(template_link, bytes):
            template_link = template_link.decode('utf-8')
        template_link = template_link.strip("b'")  # إزالة b' و '
        
        exists = check_template_exists(template_link, site)
        
        if exists:
            created_templates.append(template_link)
        else:
            uncreated_templates.append(template_link)
    
    # بناء المحتوى
    content = "== القوالب غير المنشأة ==\n"
    content += "{| class='wikitable sortable'\n"
    content += "|-\n! ت !! القالب !! الحالة\n"
    
    # إضافة تسلسل رقمي وحالة {{لمذ}} للقوالب غير المنشأة
    for index, template in enumerate(uncreated_templates, 1):
        content += "|-\n| {} || {} || {{لمذ}}\n".format(index, template)
    
    content += "|}\n"
    
    # ترتيب القوالب المنشأة حسب الحروف الأبجدية
    created_templates.sort()  # ترتيب القوالب أبجدياً
    
    # تقسيم القوالب المنشأة إلى مجموعات من 100 قالب
    total_templates = len(created_templates)
    for i in range(0, total_templates, 100):
        start = i + 1
        end = min(i + 100, total_templates)
        content += f"\n== القوالب من {start} إلى {end} ==\n"
        content += "{| class='wikitable sortable'\n"
        content += "|-\n! ت !! القالب !! الحالة\n"
        
        # إضافة تسلسل رقمي وحالة {{تم}} للقوالب المنشأة
        for index, template_link in enumerate(created_templates[i:end], 1):
            content += "|-\n| {} || {} || {{تم}}\n".format(index, template_link)
        
        content += "|}\n"
    
    if settings.debug == "no":
        page.put(content, summary=settings.editsumm)

if __name__ == "__main__":
    update_user_page()
