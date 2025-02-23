import pywikibot
from datetime import datetime, timedelta, timezone

# 🟢 قاموس ثابت يحتوي على تاريخ حصول الإداريين على الصلاحيات
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

def fetch_admins():
    """جلب قائمة الإداريين في ويكيبيديا العربية"""
    site = pywikibot.Site("ar", "wikipedia")
    return list(site.allusers(group="sysop"))

def count_admin_actions(username, days, namespaces=None):
    """حساب عدد الأفعال الإدارية خلال مدة محددة"""
    site = pywikibot.Site("ar", "wikipedia")
    # التاريخ الأحدث: الآن
    end_date = datetime.now(timezone.utc)
    # التاريخ الأقدم: الآن - الأيام المطلوبة
    start_date = end_date - timedelta(days=days)
    
    log_types = ["block", "protect", "delete", "move", "rights"]
    total_actions = 0
    
    # بالنسبة لدالة logevents، نمرر start=end_date (الأحدث) وend=start_date (الأقدم)
    for log_type in log_types:
        log_events = site.logevents(logtype=log_type, user=username, start=end_date, end=start_date)
        if namespaces is not None:
            log_events = [event for event in log_events if event.get('namespace') in namespaces]
        total_actions += len(list(log_events))
    
    return total_actions

def count_admin_recent_changes_with_tag(username, days=30, tag="أعمال إدارية (رفض طلب)"):
    """
    حساب عدد التعديلات خلال الفترة الأخيرة (days) التي تحمل الوسم المحدد.
    يتم جلب التغييرات من النطاقات: المقالات (0)، ويكيبيديا (4)، طلبات صلاحيات (5)، وإخطار الإداريين (6).
    """
    site = pywikibot.Site("ar", "wikipedia")
    rc_start = datetime.now(timezone.utc)
    rc_end = rc_start - timedelta(days=days)
    count = 0
    for change in site.recentchanges(start=rc_start, end=rc_end, user=username, namespaces=[0, 4, 5, 6]):
        if tag in change.get("tags", []):
            count += 1
    return count

def get_last_edit(username):
    """جلب تاريخ آخر تعديل قام به الإداري (من مساهماته)"""
    site = pywikibot.Site("ar", "wikipedia")
    user_contribs = site.usercontribs(user=username, total=1)
    for contrib in user_contribs:
        if 'timestamp' in contrib:
            timestamp_obj = pywikibot.Timestamp.fromISOformat(contrib['timestamp'])
            return timestamp_obj.strftime("%Y-%m-%d")
    return "غير معروف"

def generate_table(admins):
    """إنشاء جدول الإداريين مع حالة النشاط وفق المعايير المطلوبة"""
    table_header = """== قائمة الإداريين ==
:انظر أيضا: [[خاص:عرض المستخدمين/sysop|عرض قائمة كاملة لكل الإداريين]]{{•}} [[xtools:adminstats/ar.wikipedia.org|إحصائيات الإداريين في آخر شهر]] {{•}} [[xtools:adminstats/ar.wikipedia.org/{{#time: Y-m-01|-6 month}}/{{#time: Y-m-t|-1 month}}|إحصائيات الإداريين في آخر ستة أشهر]] {{•}} [[xtools:adminstats/ar.wikipedia.org/{{#time: Y-m-01|-1 year}}/{{#time: Y-m-t|-1 month}}|إحصائيات الإداريين في آخر سنة]]

{|style=font-size:95%;text-align:center;width:100% class="prettytable sortable"
|-
!style="width:40%" rowspan=2| اسم المستخدم
! rowspan=2|تاريخ الحصول على الصلاحيات
! colspan=3|حالة النشاط
! colspan=2|تعداد المساهمات
! rowspan=2|تاريخ آخر تعديل
|-
! آخر 30 يوم
! آخر 6 أشهر
! المنوّع
! أفعال إدارية (آخر 6 أشهر)
! في نطاق ويكيبيديا (آخر 30 يوم)
"""
    table_rows = ""
    for admin in admins:
        username = admin['name']
        
        # استبعاد "مستخدم:مرشح الإساءة"
        if username == "مرشح الإساءة":
            continue
        
        registration_date = admin_promotion_dates.get(username, "غير معروف")
        
        # حساب عدد الأفعال الإدارية العامة خلال 30 يوم و6 أشهر
        actions_30_days = count_admin_actions(username, 30)
        actions_6_months = count_admin_actions(username, 180)
        
        # حساب عدد التعديلات في نطاق ويكيبيديا (بواسطة متابعة الوسم) خلال آخر 30 يوم
        actions_wikipedia = count_admin_recent_changes_with_tag(username, days=30, tag="أعمال إدارية (رفض طلب)")
        
        last_30_status = "{{Yes2}} نشط" if actions_30_days > 0 else "{{No2}} غير نشط"
        last_6_status = "{{Yes2}} نشط" if actions_6_months > 65 else "{{No2}} غير نشط"
        diverse_status = "{{Yes2}} نشط" if actions_6_months > 2 else "{{No2}} غير نشط"
        
        last_edit_date = get_last_edit(username)
        
        table_rows += f"""|-\n|{{{{إداري|{username}}}}}||{registration_date}||{last_30_status}||{last_6_status}||{diverse_status}||{{{{Formatnum:{actions_6_months}}}}}||{{{{Formatnum:{actions_wikipedia}}}}}||{last_edit_date}\n"""
        
    table_footer = """|}
* "'''غَيرُ نَشط'''" تعني أن الإداري لم يقم بأي فعل إداري خلال الأيام الثلاثين الماضية.
* "'''غَيرُ نَشط خلال الأشهر الستة الماضية'''" تعني أن الإداري لم يقم بأكثر من خمس وستين (65) فعلًا إداريًّا خلال الأشهر الستة الماضية.
* "'''غَيرُ نَشط في حالة النشاط المُنوَّع'''" تعني أن الإداري لم يقم بأكثر من فعلين إداريين في أقسام مختلفة (حماية - حذف - منع - إخفاء - ...)."""
    
    return table_header + table_rows + table_footer

def update_wiki_page(page_title, content):
    """تحديث صفحة الإداريين في ويكيبيديا"""
    site = pywikibot.Site("ar", "wikipedia")
    page = pywikibot.Page(site, page_title)
    page.text = content
    page.save(summary="تحديث قائمة الإداريين")

def main():
    admins = fetch_admins()
    content = generate_table(admins)
    update_wiki_page("User:Mohammed Qays/قائمة الإداريين", content)

if __name__ == "__main__":
    main()
