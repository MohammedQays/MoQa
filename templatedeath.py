import pywikibot
from datetime import datetime, timedelta

def manage_recent_death_template():
    site = pywikibot.Site('ar', 'wikipedia')
    repo = site.data_repository()
    category = pywikibot.Category(site, 'تصنيف:وفيات حديثة')
    processed_pages = 0
    
    for page in category.articles():
        try:
            # الجزء 1: معالجة الصفحات الموجودة في التصنيف
            text = page.get()
            original_text = text  # حفظ نسخة من النص الأصلي للمقارنة
            template_added_time = None
            
            # البحث عن تاريخ إضافة القالب من سجل التعديلات
            for revision in page.revisions(total=10):
                if '{{وفاة حديثة' in revision['text']:
                    template_added_time = revision['timestamp']
                    break
            
            # الجزء 2: التحقق من ويكي بيانات
            wikidata_date = None
            last_edit_time = None
            try:
                item = pywikibot.ItemPage.fromPage(page)
                if item.exists():
                    item.get()
                    if 'P570' in item.claims:  # تاريخ الوفاة في ويكي بيانات
                        claim = item.claims['P570'][0]
                        wikidata_date = claim.getTarget().toTimestamp()
                        
                        # الحصول على وقت آخر تعديل على P570
                        for claim_rev in item.revisions(total=1):
                            last_edit_time = claim_rev['timestamp']
            except Exception as e:
                print(f"خطأ في ويكي بيانات لصفحة {page.title()}: {str(e)}")
                continue
            
            current_time = datetime.now()
            modified = False
            
            # الحالة 1: إذا كان هناك تاريخ وفاة في ويكي بيانات
            if wikidata_date:
                death_date = wikidata_date
                delta = current_time - death_date
                
                # إذا مرت أكثر من 15 يومًا من الوفاة
                if delta.days > 15:
                    # إزالة القالب بالكامل إذا كان موجودًا
                    if '{{وفاة حديثة' in text:
                        text, removed = remove_template_safely(text, 'وفاة حديثة')
                        if removed:
                            modified = True
                
                # إذا كان التعديل على P570 حديثًا (أقل من 3 ساعات)
                elif last_edit_time and (current_time - last_edit_time).total_seconds() < 10800:
                    if '{{وفاة حديثة' not in text:
                        # إضافة القالب إذا لم يكن موجودًا
                        text = '{{وفاة حديثة}}\n' + text
                        modified = True
            
            # الحالة 2: إذا لم يكن هناك ويكي بيانات، نعتمد على وقت إضافة القالب
            elif template_added_time:
                delta = current_time - template_added_time
                if delta.days > 15:
                    if '{{وفاة حديثة' in text:
                        text, removed = remove_template_safely(text, 'وفاة حديثة')
                        if removed:
                            modified = True
            
            # حفظ التغييرات إذا كانت هناك تعديلات
            if modified and text != original_text:
                page.put(text, summary='بوت: إزالة [[قالب:وفاة حديثة]] تجريبي')
                print(f"تمت معالجة الصفحة: {page.title()}")
                processed_pages += 1
        
        except Exception as e:
            print(f"حدث خطأ في معالجة {page.title()}: {str(e)}")
            continue
    
    return processed_pages

def remove_template_safely(text, template_name):
    """
    دالة لإزالة القالب بأمان مع الحفاظ على الفراغات الأخرى
    """
    start_tag = '{{' + template_name
    end_tag = '}}'
    start_pos = text.find(start_tag)
    
    if start_pos == -1:
        return text, False
    
    # البحث عن نهاية القالب مع مراعاة الأقواس المتداخلة
    depth = 0
    end_pos = start_pos
    for i in range(start_pos, len(text)):
        if text[i:i+2] == '{{':
            depth += 1
        elif text[i:i+2] == '}}':
            depth -= 1
            if depth == 0:
                end_pos = i + 2
                break
    
    # تحديد الفراغات حول القالب فقط
    before_template = text[:start_pos]
    after_template = text[end_pos:]
    
    # إزالة الفراغات المباشرة حول القالب فقط
    lines_before = before_template.split('\n')
    lines_after = after_template.split('\n')
    
    # الحفاظ على الفراغات قبل القالب ما عدا السطر الفارغ المباشر قبله
    if lines_before and not lines_before[-1].strip():
        before_template = '\n'.join(lines_before[:-1])
        if before_template and not before_template.endswith('\n'):
            before_template += '\n'
    
    # الحفاظ على الفراغات بعد القالب ما عدا السطر الفارغ المباشر بعده
    if lines_after and not lines_after[0].strip():
        after_template = '\n'.join(lines_after[1:])
        if after_template and not after_template.startswith('\n'):
            after_template = '\n' + after_template
    
    new_text = before_template + after_template
    return new_text, True

if __name__ == "__main__":
    print("بدء معالجة صفحات وفيات حديثة...")
    count = manage_recent_death_template()
    print(f"تم الانتهاء من معالجة {count} صفحة بنجاح")
