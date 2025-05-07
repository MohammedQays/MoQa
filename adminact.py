import requests
import json
import pywikibot
from datetime import datetime, timedelta, timezone

def get_admin_promotion_dates():
    """
    جلب قاموس الإداريين مع تواريخ الحصول على الصلاحيات من صفحة مستخدم:Mohammed Qays/admins.json
    يُتوقع أن تكون الصفحة بصيغة JSON على النحو التالي:
    [
        {
            "username": "Ajwaan",
            "promotion_date": "2019-09-29"
        },
        {
            "username": "Avicenno",
            "promotion_date": "2015-08-24"
        },
        ...
    ]
    """
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, "مستخدم:Mohammed Qays/admins.json")
    try:
        text = page.text.strip()
        # حذف وسوم <noinclude> إن وجدت
        if "<noinclude>" in text:
            text = text.split("<noinclude>")[0].strip()
        data = json.loads(text)
        # تحويل القائمة إلى قاموس بحيث يكون المفتاح هو username والقيمة promotion_date
        promotion_dates = {item["username"]: item["promotion_date"] for item in data}
        return promotion_dates
    except Exception as e:
        print(f"خطأ في جلب أو تحليل JSON: {e}")
        return {}

# قراءة قاموس الإداريين من القالب
admin_promotion_dates = get_admin_promotion_dates()

# تحديد الفترة الزمنية
end_date = datetime.now(timezone.utc)
start_date_30 = end_date - timedelta(days=30)
start_date_180 = end_date - timedelta(days=180)

def format_date(date_string):
    """
    تنسيق التاريخ الميلادي ليعرض الشهر بالأسم (مثلاً: 29 سبتمبر 2019)
    """
    month_names = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", 
                   "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    return f"{date_obj.day} {month_names[date_obj.month - 1]} {date_obj.year}"

def fetch_admins():
    """جلب قائمة الإداريين من ويكيبيديا العربية"""
    site = pywikibot.Site("ar", "wikipedia")
    return list(site.allusers(group="sysop"))

def count_specific_log_actions(username, days, log_type, action=None):
    """
    حساب عدد أفعال محددة في سجلات الأحداث خلال فترة زمنية معينة
    """
    site = pywikibot.Site("ar", "wikipedia")
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    log_events = site.logevents(logtype=log_type, user=username, start=end_dt, end=start_dt)
    
    if action:
        return len([event for event in log_events if event.get('action') == action])
    return len(list(log_events))

def count_admin_edits_with_abuse_filter(username, days=180, filter_id=225, namespace=None):
    """
    حساب عدد التعديلات في نطاق ويكيبيديا خلال الفترة (days)
    باستخدام مرشح الإساءة (filter_id) والمجال (namespace).
    """
    url = "https://ar.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "abuselog",
        "aflfilter": filter_id,
        "afluser": username,
        "afllimit": 500,
        "aflprop": "timestamp|title",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "query" in data and "abuselog" in data["query"]:
        log_entries = data["query"]["abuselog"]
        filtered_entries = [
            entry for entry in log_entries
            if start_date_180.isoformat() <= entry["timestamp"] <= end_date.isoformat()
        ]
        if namespace is not None:
            site = pywikibot.Site("ar", "wikipedia")
            new_filtered_entries = []
            for entry in filtered_entries:
                title = entry.get("title", "")
                if title:
                    page = pywikibot.Page(site, title)
                    if page.namespace() == namespace:
                        new_filtered_entries.append(entry)
            filtered_entries = new_filtered_entries
        return len(filtered_entries)
    return 0

def get_last_edit(username):
    """جلب تاريخ آخر تعديل قام به المستخدم من مساهماته"""
    site = pywikibot.Site("ar", "wikipedia")
    user_contribs = site.usercontribs(user=username, total=1)
    for contrib in user_contribs:
        if 'timestamp' in contrib:
            timestamp_obj = pywikibot.Timestamp.fromISOformat(contrib['timestamp'])
            return timestamp_obj.strftime("%Y-%m-%d")
    return "غير معروف"

def generate_table(admins):
    """
    إنشاء تقرير الإداريين بصيغة جدول ويكي مع الأعمدة المطلوبة
    """
    header = """{{نسخ:مستخدم:Mohammed Qays/ملعب6}}"""
    rows = ""
    for admin in admins:
        username = admin['name']
        if username == "مرشح الإساءة":
            continue
            
        # الحصول على تاريخ الصلاحيات من القاموس المُسترجع
        reg_date = admin_promotion_dates.get(username, "غير معروف")
        formatted_reg_date = format_date(reg_date) if reg_date != "غير معروف" else "غير معروف"
        
        # حساب عدد الأفعال الإدارية لكل نوع
        delete_count = count_specific_log_actions(username, 180, "delete", "delete")
        reblock_count = count_specific_log_actions(username, 180, "block", "reblock")
        reprotect_count = count_specific_log_actions(username, 180, "protect", "modify")
        revision_delete_count = count_specific_log_actions(username, 180, "delete", "revision")
        log_delete_count = count_specific_log_actions(username, 180, "delete", "event")
        restore_count = count_specific_log_actions(username, 180, "delete", "restore")
        unblock_count = count_specific_log_actions(username, 180, "block", "unblock")
        unprotect_count = count_specific_log_actions(username, 180, "protect", "unprotect")
        rights_count = count_specific_log_actions(username, 180, "rights")
        
        # حساب المجموع الكلي للأفعال الإدارية خلال 180 يوم
        total_actions = (delete_count + reblock_count + reprotect_count + 
                         revision_delete_count + log_delete_count + 
                         restore_count + unblock_count + 
                         unprotect_count + rights_count)
        
        # حساب أعمال مرشح الإساءة 225
        abuse_filter_actions = count_admin_edits_with_abuse_filter(username, 180, 225)
        
        # حساب الأفعال خلال 30 يوم فقط
        actions_30 = (count_specific_log_actions(username, 30, "delete") +
                      count_specific_log_actions(username, 30, "block") +
                      count_specific_log_actions(username, 30, "protect") +
                      count_specific_log_actions(username, 30, "rights"))
        
        # تحديد حالة النشاط خلال 30 يوم
        activity_30_status = "{{Yes2}} نشط" if actions_30 > 0 else "{{No2}} غير نشط"
        
        # تحديد حالة النشاط خلال 180 يوم (120 فعل)
        activity_180_status = "{{Yes2}} نشط" if total_actions >= 120 else "{{No2}} غير نشط"
        
        # تحديد حالة النشاط المتنوع (2 أنواع مختلفة على الأقل)
        diverse_categories = 0
        if delete_count + revision_delete_count + log_delete_count + restore_count > 0:
            diverse_categories += 1  # حذف/استعادة
        if reblock_count + unblock_count > 0:
            diverse_categories += 1  # منع/رفع منع
        if reprotect_count + unprotect_count > 0:
            diverse_categories += 1  # حماية/رفع حماية
        if rights_count > 0:
            diverse_categories += 1  # صلاحيات
        
        diverse_status = "{{Yes2}} نشط" if diverse_categories >= 2 else "{{No2}} غير نشط"
        
        # الحصول على تاريخ آخر تعديل
        last_edit = get_last_edit(username)
        formatted_last_edit = format_date(last_edit) if last_edit != "غير معروف" else "غير معروف"
        
        rows += f"""
|-
| {{{{إداري|{username}}}}} || {formatted_reg_date} || {{{{Formatnum:{total_actions}}}}} || {{{{Formatnum:{abuse_filter_actions}}}}} || {activity_30_status} || {activity_180_status} || {diverse_status} || {formatted_last_edit}
"""
    footer = """
|}
* "'''غَيرُ نَشط'''" تعني أن الإداري لم يقم بأي فعل إداري خلال الأيام الثلاثين الماضية.
* "'''غَيرُ نَشط خلال الأشهر الستة الماضية'''" تعني أن الإداري لم يقم بأكثر من (120) فعلًا إداريًّا خلال الأشهر الستة الماضية.
* "'''غَيرُ نشط في حالة النشاط المُنوَّع'''" تعني أن الإداري لم يقم بأكثر من فعلين إداريين في أقسام مختلفة (حماية - حذف - منع - إخفاء - ...).
<noinclude>
[[تصنيف:ويكيبيديون إداريون]]
[[تصنيف:تنظيم إدارة ويكيبيديا]]
</noinclude>
"""
    return header + rows + footer

def update_wiki_page(page_title, content):
    """تحديث الصفحة في ويكيبيديا باستخدام Pywikibot"""
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, page_title)
    page.text = content
    page.save(summary="بوت:تحديث قائمة الإداريين")

def main():
    admins = fetch_admins()
    content = generate_table(admins)
    update_wiki_page("قالب:قائمة الإداريين", content)

if __name__ == "__main__":
    main()
