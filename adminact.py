import requests
import pywikibot
from datetime import datetime, timedelta, timezone

# قاموس الإداريين مع تواريخ الحصول على الصلاحيات
admin_promotion_dates = {
    "Ajwaan": "2019-09-29",
    "Avicenno": "2015-08-24",
    "Dr-Taher": "2018-04-05",
    "Elph": "2012-07-07",
    "Ibrahim.ID": "2014-03-10",
    "Meno25": "2007-02-20",
    "Mervat": "2013-12-01",
    "Michel Bakni": "2020-07-07",
    "Mohamed Belgazem": "2022-09-15",
    "Mohammed Qays": "2024-01-23",
    "Nehaoua": "2020-12-06",
    "أبو هشام": "2023-04-02",
    "أحمد ناجي": "2023-01-04",
    "إسلام": "2018-02-10",
    "باسم": "2010-06-04",
    "علاء": "2016-08-14",
    "عمرو بن كلثوم": "2013-02-04",
    "فاطمة الزهراء": "2023-02-06",
    "فيصل": "2017-06-27",
    "كريم رائد": "2024-06-11",
    "لوقا": "2024-09-16",
    "محمد أحمد عبد الفتاح": "2008-09-03",
    "ولاء": "2013-01-20"
}

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

def count_admin_actions(username, days, namespaces=None):
    """
    حساب عدد الأفعال الإدارية للمستخدم خلال الفترة المحددة (يوم/أيام)
    من خلال سجلات الأحداث الإدارية (block, protect, delete, move, rights)
    """
    site = pywikibot.Site("ar", "wikipedia")
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    log_types = ["block", "protect", "delete", "move", "rights"]
    total_actions = 0
    for log_type in log_types:
        log_events = site.logevents(logtype=log_type, user=username, start=end_dt, end=start_dt)
        if namespaces is not None:
            log_events = [event for event in log_events if event.get('namespace') in namespaces]
        total_actions += len(list(log_events))
    return total_actions

def count_admin_edits_with_abuse_filter(username, days=180, filter_id=225, namespace=None):
    """
    حساب عدد التعديلات في نطاق ويكيبيديا خلال الفترة (days)
    باستخدام مرشح الإساءة (filter_id) والمجال (namespace).
    
    نقوم بطلب خاصيتي "timestamp" و "title" ثم نستخدم pywikibot لتحديد النطاق.
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
    إنشاء تقرير الإداريين بصيغة جدول ويكي وفق النموذج المطلوب.
    يتم حساب:
    - حالة النشاط خلال آخر 30 يوم (نشط إذا كان هناك أي فعل)
    - حالة النشاط خلال آخر 6 أشهر (نشط إذا تجاوزت الأفعال 65)
    - حالة النشاط المُنوَّع (نشط إذا تجاوزت الأفعال 2)
    - أفعال إدارية خلال آخر 6 أشهر
    - التعديلات في نطاق ويكيبيديا خلال آخر 180 يوم
    - تاريخ آخر تعديل
    """
    header = """{{نسخ:مستخدم:Mohammed Qays/ملعب6}}"""
    rows = ""
    for admin in admins:
        username = admin['name']
        if username == "مرشح الإساءة":
            continue
        # الحصول على تاريخ الصلاحيات
        reg_date = admin_promotion_dates.get(username, "غير معروف")
        formatted_reg_date = format_date(reg_date) if reg_date != "غير معروف" else "غير معروف"
        # حساب عدد الأفعال الإدارية
        actions_30 = count_admin_actions(username, 30)
        actions_180 = count_admin_actions(username, 180)
        # حالة النشاط:
        last_30_status = "{{Yes2}} نشط" if actions_30 > 0 else "{{No2}} غير نشط"
        last_6_status  = "{{Yes2}} نشط" if actions_180 > 65 else "{{No2}} غير نشط"
        diverse_status = "{{Yes2}} نشط" if actions_180 > 2 else "{{No2}} غير نشط"
        # الحصول على عدد أفعال إدارية (آخر 6 أشهر)
        admin_actions = actions_180
        # حساب التعديلات في نطاق ويكيبيديا خلال آخر 180 يوم (باستخدام مرشح الإساءة 225)
        ns_edits = count_admin_edits_with_abuse_filter(username, days=180, filter_id=225, namespace=4)
        # الحصول على تاريخ آخر تعديل
        last_edit = get_last_edit(username)
        formatted_last_edit = format_date(last_edit) if last_edit != "غير معروف" else "غير معروف"
        
        rows += f"""
|-
|{{{{إداري|{username}}}}}||{formatted_reg_date}||{last_30_status}||{last_6_status}||{diverse_status}||{{{{Formatnum:{admin_actions}}}}}||{{{{Formatnum:{ns_edits}}}}}||{formatted_last_edit}
"""
    footer = """|}
* "'''غَيرُ نَشط'''" تعني أن الإداري لم يقم بأي فعل إداري خلال الأيام الثلاثين الماضية.
* "'''غَيرُ نَشط خلال الأشهر الستة الماضية'''" تعني أن الإداري لم يقم بأكثر من خمس وستين (65) فعلًا إداريًّا خلال الأشهر الستة الماضية.
* "'''غَيرُ نَشط في حالة النشاط المُنوَّع'''" تعني أن الإداري لم يقم بأكثر من فعلين إداريين في أقسام مختلفة (حماية - حذف - منع - إخفاء - ...).
"""
    return header + rows + footer

def update_wiki_page(page_title, content):
    """تحديث الصفحة في ويكيبيديا باستخدام Pywikibot"""
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, page_title)
    page.text = content
    page.save(summary="تحديث قائمة الإداريين")

def main():
    admins = fetch_admins()
    content = generate_table(admins)
    update_wiki_page("مستخدم:Mohammed Qays/ملعب14", content)

if __name__ == "__main__":
    main()
