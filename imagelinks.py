import pywikibot
import toolforge
import re

class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: تصحيح استخدام الملفات."
    debug = "no"

# استعلام محسن لجلب جميع البيانات المطلوبة
query = """
SELECT
    p.page_title AS article_title,
    rd.rd_title AS target_file,
    il.il_to AS redirect_file,
    p.page_id AS page_id
FROM page p
JOIN imagelinks il ON il.il_from = p.page_id
JOIN page pf ON pf.page_title = il.il_to AND pf.page_namespace = 6
JOIN redirect rd ON rd.rd_from = pf.page_id
WHERE p.page_namespace = 0
AND rd.rd_namespace = 6  -- التأكد أن التحويلة في نطاق الملفات
LIMIT 1000;
"""

conn = toolforge.connect(settings.lang, 'analytics')

page_files = {}

with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()
    for row in results:
        article_title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
        target_file   = row[1].decode("utf-8") if isinstance(row[1], bytes) else row[1]
        redirect_file = row[2].decode("utf-8") if isinstance(row[2], bytes) else row[2]

        if article_title not in page_files:
            page_files[article_title] = []
        page_files[article_title].append((redirect_file, target_file))

site = pywikibot.Site()
site.login()

def make_file_regex(file_names):
    """إنشاء تعابير منتظمة لجميع الاحتمالات"""
    patterns = []
    
    for file_name in file_names:
        # جميع الاحتمالات الشائعة لكتابة الملفات
        file_variations = [
            file_name,
            file_name.replace(' ', '_'),
            file_name.replace('_', ' '),
            re.escape(file_name),
            re.escape(file_name.replace(' ', '_')),
            re.escape(file_name.replace('_', ' '))
        ]
        
        # إزالة التكرارات
        file_variations = list(set(file_variations))
        
        # نمط لـ [[ملف:...]]
        pattern_link = r'(\[\[\s*ملف\s*:\s*)(' + '|'.join(file_variations) + r')(\s*[\|\]]])'
        patterns.append(re.compile(pattern_link, re.IGNORECASE))
        
        # نمط لـ [[:ملف:...]] 
        pattern_colon = r'(\[\[\s*:\s*ملف\s*:\s*)(' + '|'.join(file_variations) + r')(\s*[\|\]]])'
        patterns.append(re.compile(pattern_colon, re.IGNORECASE))
        
        # نمط للاستخدام المباشر (بشكل أكثر دقة)
        pattern_direct = r'(?<![\[\]\w])(' + '|'.join(file_variations) + r')(?![\[\]\w])'
        patterns.append(re.compile(pattern_direct, re.IGNORECASE))
    
    return patterns

def normalize_filename(filename):
    """تطبيع اسم الملف للتعامل مع المسافات والشرطات"""
    return filename.replace(' ', '_').strip()

for article_title, files_list in page_files.items():
    try:
        page = pywikibot.Page(site, article_title.replace('_', ' '))
        
        # تخطي الصفحات غير الموجودة
        if not page.exists():
            continue
            
        original_text = page.text
        text = original_text

        # تجميع جميع الملفات التي تحتاج استبدال
        all_replacements = {}
        for redirect_file, target_file in files_list:
            # تطبيع الأسماء
            norm_redirect = normalize_filename(redirect_file)
            norm_target = normalize_filename(target_file)
            
            if norm_redirect != norm_target:
                all_replacements[norm_redirect] = norm_target
        
        if not all_replacements:
            continue
            
        # إنشاء التعابير المنتظمة لجميع الاستبدالات
        regex_patterns = make_file_regex(list(all_replacements.keys()))
        
        # تطبيق جميع الاستبدالات
        for pattern in regex_patterns:
            def replacer(match):
                matched_file = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                norm_matched = normalize_filename(matched_file)
                
                if norm_matched in all_replacements:
                    replacement = all_replacements[norm_matched]
                    # الحفاظ على التنسيق الأصلي
                    if len(match.groups()) >= 3:
                        return match.group(1) + replacement + match.group(3)
                    else:
                        return replacement
                return match.group(0)
            
            text = pattern.sub(replacer, text)

        # التحقق من وجود تغييرات فعلية والحفظ
        if text != original_text:
            changes_found = False
            for old_file, new_file in all_replacements.items():
                if old_file in original_text or old_file.replace('_', ' ') in original_text:
                    if new_file in text:
                        changes_found = True
                        break
            
            if changes_found and settings.debug == "no":
                page.text = text
                page.save(settings.editsumm, minor=False)

    except Exception:
        pass
