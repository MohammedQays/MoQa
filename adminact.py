# بوت احصائيات الإداريين محدث في 25 - 2- 2025
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

# دوال لتحديد حدود الفترات بناءً على تاريخ التحديث
def first_day_of_month(date):
    return date.replace(day=1)

def first_day_of_previous_month(date):
    if date.month == 1:
        return date.replace(year=date.year - 1, month=12, day=1)
    else:
        return date.replace(month=date.month - 1, day=1)

def first_day_next_month(date):
    if date.month == 12:
        return date.replace(year=date.year + 1, month=1, day=1)
    else:
        return date.replace(month=date.month + 1, day=1)

def first_day_six_months_ago(date):
    """
    للحصول على أول يوم للشهر الذي يكون 5 شهور قبل شهر التحديث،
    بحيث تغطي الفترة 6 شهور كاملة (مثلاً، إذا كان التحديث في فبراير 2025، 
    سيكون البداية 1 سبتمبر 2024).
    """
    month = date.month - 5
    year = date.year
    if month < 1:
        month += 12
        year -= 1
    return date.replace(year=year, month=month, day=1)

# دوال لحساب الأفعال بين تاريخين
def count_admin_actions_between(username, start_dt, end_dt, namespaces=None):
    """
    حساب عدد الأفعال الإدارية للمستخدم بين تاريخي البداية والنهاية
    """
    site = pywikibot.Site("ar", "wikipedia")
    log_types = ["block", "protect", "delete", "move", "merge", "rights"]
    total_actions = 0
    for log_type in log_types:
        log_events = site.logevents(logtype=log_type, user=username, start=end_dt, end=start_dt)
        if namespaces is not None:
            log_events = [event for event in log_events if event.get("namespace") in namespaces]
        total_actions += len(list(log_events))
    return total_actions

def count_admin_edits_between(username, start_dt, end_dt, filter_id=225, namespace=None):
    """
    حساب عدد التعديلات في نطاق ويكيبيديا خلال الفترة المحددة باستخدام مرشح الإساءة.
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
    log_entries = data.get("query", {}).get("abuselog", [])
    filtered_entries = [entry for entry in log_entries if start_dt.isoformat() <= entry["timestamp"] <= end_dt.isoformat()]
    if namespace is not None:
        site = pywikibot.Site("ar", "wikipedia")
        filtered_entries = [entry for entry in filtered_entries if pywikibot.Page(site, entry.get("title", "")).namespace() == namespace]
    return len(filtered_entries)

def get_last_edit(username):
    """جلب تاريخ آخر تعديل قام به المستخدم من مساهماته"""
    site = pywikibot.Site("ar", "wikipedia")
    user_contribs = site.usercontribs(user=username, total=1)
    for contrib in user_contribs:
        if "timestamp" in contrib:
            timestamp_obj = pywikibot.Timestamp.fromISOformat(contrib["timestamp"])
            return timestamp_obj.strftime("%Y-%m-%d")
    return "غير معروف"

def generate_table(admins):
    """
    إنشاء تقرير الإداريين بصيغة جدول ويكي وفق النموذج المطلوب.
    يتم حساب:
    - التفاعل الشهري: من أول يوم للشهر السابق حتى أول يوم للشهر الحالي.
    - الأفعال الإدارية خلال 6 أشهر: من أول يوم للشهر (6 أشهر كاملة) حتى أول يوم من الشهر التالي لتاريخ التحديث.
    - باقي الإحصائيات كما هو.
    """
    # تحديد تاريخ التحديث الحالي
    update_date = datetime.now(timezone.utc)
    
    # الفترة الخاصة بالتفاعل الشهري (آخر شهر كامل)
    monthly_end = first_day_of_month(update_date)            # أول يوم من شهر التحديث
    monthly_start = first_day_of_previous_month(update_date)   # أول يوم من الشهر السابق
    
    # الفترة الخاصة بالأفعال خلال 6 أشهر
    six_month_end = first_day_next_month(update_date)          # أول يوم من الشهر التالي لتاريخ التحديث
    six_month_start = first_day_six_months_ago(update_date)      # أول يوم للشهر الذي يكون 5 شهور قبل شهر التحديث
    
    header = """{{نسخ:مستخدم:Mohammed Qays/ملعب6}}"""
    rows = ""
    for admin in admins:
        username = admin["name"]
        if username == "مرشح الإساءة":
            continue
        reg_date = admin_promotion_dates.get(username, "غير معروف")
        formatted_reg_date = format_date(reg_date) if reg_date != "غير معروف" else "غير معروف"
        
        # حساب التفاعل الشهري من الشهر السابق (مثال: من 1 يناير 2025 إلى 1 فبراير 2025)
        actions_month = count_admin_actions_between(username, monthly_start, monthly_end)
        
        # حساب الأفعال الإدارية خلال 6 أشهر (مثال: من 1 سبتمبر 2024 إلى 1 مارس 2025)
        actions_six_month = count_admin_actions_between(username, six_month_start, six_month_end)
        
        last_month_status = "{{Yes2}} نشط" if actions_month > 0 else "{{No2}} غير نشط"
        last_six_status = "{{Yes2}} نشط" if actions_six_month > 119 else "{{No2}} غير نشط"
        diverse_status = "{{Yes2}} نشط" if actions_six_month > 2 else "{{No2}} غير نشط"
        
        ns_edits = count_admin_edits_between(username, six_month_start, six_month_end, filter_id=225, namespace=4)
        last_edit = get_last_edit(username)
        formatted_last_edit = format_date(last_edit) if last_edit != "غير معروف" else "غير معروف"
        
        rows += f"""\n|-\n|{{{{إداري|{username}}}}}||{formatted_reg_date}||{last_month_status}||{last_six_status}||{diverse_status}||{{{{Formatnum:{actions_six_month}}}}}||{{{{Formatnum:{ns_edits}}}}}||{formatted_last_edit}
"""
    
    footer = """
|}
* "'''غَيرُ نَشط'''" تعني أن الإداري لم يقم بأي فعل إداري خلال الأيام الثلاثين الماضية.
* "'''غَيرُ نَشط خلال الأشهر الستة الماضية'''" تعني أن الإداري لم يقم بأكثر من خمس وستين (120) فعلًا إداريًّا خلال الأشهر الستة الماضية.
* "'''غَيرُ نَشط في حالة النشاط المُنوَّع'''" تعني أن الإداري لم يقم بأكثر من فعلين إداريين في أقسام مختلفة (حماية - حذف - منع - إخفاء - ...).
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
    update_wiki_page("مستخدم:Mohammed Qays/قائمة الإداريين", content)

if __name__ == "__main__":
    main()
