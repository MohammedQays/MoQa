import requests
import pywikibot
import json
from datetime import datetime, timedelta, timezone

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

def get_admin_promotion_dates():
    """
    جلب قاموس الإداريين مع تواريخ الحصول على الصلاحيات من صفحة قالب:admins.json
    """
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, "مستخدم:Mohammed Qays/admins.json")
    try:
        text = page.text.strip()
        # حذف <noinclude> إن وجدت
        if "<noinclude>" in text:
            text = text.split("<noinclude>")[0].strip()
        data = json.loads(text)
        promotion_dates = {item["username"]: item["promotion_date"] for item in data}
        return promotion_dates
    except Exception as e:
        print(f"خطأ في جلب أو تحليل JSON: {e}")
        return {}

def generate_table(admins):
    """
    إنشاء تقرير الإداريين بصيغة جدول ويكي مع أعمدة لكل نوع من الأفعال الإدارية
    """
    admin_promotion_dates = get_admin_promotion_dates()

    header = """{|style=font-size:95%;text-align:center;width:100% class="prettytable sortable"
|-
! rowspan="2" | الإداري
! rowspan="2" | {{اختص| الصلاحية| تاريخ الحصول على الصلاحية}}
! colspan="9" | {{اختص|عدد الأفعال الإدارية| عدد الأفعال الإدارية التي قام بها الإداري خلال 6 أشهر}}
! rowspan="2" | {{اختص|المجموع| مجموع الأعمال الإدارية}}
! rowspan="2" | آخر تعديل
|-
! {{اختص| حذف| عمليات الحذف}}
! {{اختص|المنع| عمليات المنع}}
! {{اختص|الحماية| عمليات حماية الصفحات}}
! {{اختص|المراجعة| عمليات مراجعة الصفحات}}
! {{اختص|إخفاء| عمليات إخفاء السجلات}}
! {{اختص|استعادة| عمليات استرجاع الصفحات}}
! {{اختص|ر.منع| عمليات رفع المنع عن المستخدمين}}
! {{اختص|ر.الحماية| عمليات رفع الحماية عن الصفحات}}
! {{اختص|صلاحية| عمليات منح الصلاحيات للمستخدمين}}
"""
    rows = ""
    for admin in admins:
        username = admin['name']
        if username == "مرشح الإساءة":
            continue
            
        reg_date = admin_promotion_dates.get(username, "غير معروف")
        formatted_reg_date = format_date(reg_date) if reg_date != "غير معروف" else "غير معروف"
        
        delete_count = count_specific_log_actions(username, 180, "delete", "delete")
        reblock_count = count_specific_log_actions(username, 180, "block", "reblock")
        reprotect_count = count_specific_log_actions(username, 180, "protect", "modify")
        revision_delete_count = count_specific_log_actions(username, 180, "delete", "revision")
        log_delete_count = count_specific_log_actions(username, 180, "delete", "event")
        restore_count = count_specific_log_actions(username, 180, "delete", "restore")
        unblock_count = count_specific_log_actions(username, 180, "block", "unblock")
        unprotect_count = count_specific_log_actions(username, 180, "protect", "unprotect")
        rights_count = count_specific_log_actions(username, 180, "rights")
        
        total_actions = (delete_count + reblock_count + reprotect_count + 
                        revision_delete_count + log_delete_count + 
                        restore_count + unblock_count + 
                        unprotect_count + rights_count)
        
        last_edit = get_last_edit(username)
        formatted_last_edit = format_date(last_edit) if last_edit != "غير معروف" else "غير معروف"
        
        rows += f"""
|-
| {{{{إداري|{username}}}}} || {formatted_reg_date} || {delete_count} || {reblock_count} || {reprotect_count} || {revision_delete_count} || {log_delete_count} || {restore_count} || {unblock_count} || {unprotect_count} || {rights_count} || {total_actions} || {formatted_last_edit}
"""
    footer = """
|}
<noinclude>

</noinclude>
"""
    return header + rows + footer

def update_wiki_page(page_title, content):
    """تحديث الصفحة في ويكيبيديا باستخدام Pywikibot"""
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, page_title)
    page.text = content
    page.save(summary="بوت:تحديث")

def main():
    admins = fetch_admins()
    content = generate_table(admins)
    update_wiki_page("مستخدم:MoQabot/جدول", content)

if __name__ == "__main__":
    main()
