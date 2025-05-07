import pywikibot
import toolforge
import json
from datetime import datetime, timedelta
import requests

# إعداد الموقع
site = pywikibot.Site('ar', 'wikipedia')

# تحميل بيانات الإداريين من صفحة JSON
admins_page = pywikibot.Page(site, "مستخدم:Mohammed Qays/admins.json")
admins_data = json.loads(admins_page.text)
promo_dates = {entry["username"]: entry["promotion_date"] for entry in admins_data}

# الاتصال بقاعدة البيانات
conn = toolforge.connect('arwiki', 'analytics')
cursor = conn.cursor()

# استعلام قاعدة البيانات
query = """
SELECT 
    a.actor_name AS user_name,
    COUNT(*) AS total_admin_actions_6_months,
    CASE 
        WHEN COUNT(*) >= 120 THEN 'نشط'
        ELSE 'غير نشط'
    END AS status_6_months,
    DATE_FORMAT(MAX(l.log_timestamp), '%Y-%m-%d') AS last_edit_date,
    COUNT(CASE 
        WHEN l.log_timestamp >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 30 DAY), '%Y%m%d%H%i%S')
        THEN 1 END) AS actions_last_30_days,
    CASE 
        WHEN COUNT(DISTINCT CASE 
            WHEN log_type IN ('delete', 'block', 'protect', 'rights') THEN log_type 
        END) >= 2 THEN 'نشط'
        ELSE 'غير نشط'
    END AS status_varied_actions
FROM logging l
JOIN actor a ON l.log_actor = a.actor_id
JOIN user_groups ug ON ug.ug_user = a.actor_user
WHERE ug.ug_group = 'sysop'
  AND a.actor_name != 'مرشح الإساءة'
  AND l.log_timestamp >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 6 MONTH), '%Y%m%d%H%i%S')
  AND (
      (log_type = 'delete' AND log_action IN ('delete', 'restore', 'revision', 'log')) OR
      (log_type = 'block' AND log_action IN ('block', 'unblock', 'reblock')) OR
      (log_type = 'protect' AND log_action IN ('protect', 'modify', 'unprotect')) OR
      (log_type = 'rights' AND log_action = 'rights')
  )
GROUP BY a.actor_name
ORDER BY total_admin_actions_6_months DESC;
"""

cursor.execute(query)
results = cursor.fetchall()

# ترويسة الجدول
header = """{{نسخ:مستخدم:Mohammed Qays/ملعب6}}
"""

# تذييل الجدول
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

# تحويل التاريخ إلى تنسيق عربي
def format_ar_date(date_str):
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
              "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{d.day} {months[d.month-1]} {d.year}"
    except:
        return "غير معروف"

# رمز الحالة
def yes_no_template(status):
    return "{{Yes2}} نشط" if status == "نشط" else "{{No2}} غير نشط"

# دالة لحساب عدد التعديلات التي استوقفتها مرشحات الإساءة في نطاق ويكيبيديا (namespace 4) خلال آخر 30 يومًا فقط
def count_abusefilter_namespace_wikipedia(username, filter_id=225):
    url = "https://ar.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "abuselog",
        "afluser": username,
        "aflfilter": filter_id,
        "afllimit": "500",
        "aflprop": "title|timestamp",
        "format": "json"
    }
    count = 0
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "query" in data and "abuselog" in data["query"]:
            site = pywikibot.Site("ar", "wikipedia")
            thirty_days_ago = datetime.now() - timedelta(days=30)
            for entry in data["query"]["abuselog"]:
                timestamp = entry.get("timestamp", "")
                if timestamp:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                    if timestamp >= thirty_days_ago:
                        title = entry.get("title", "")
                        if title:
                            page = pywikibot.Page(site, title)
                            if page.namespace() == 4:  # نطاق ويكيبيديا
                                count += 1
    except Exception as e:
        print(f"خطأ في جلب بيانات مرشح الإساءة للمستخدم {username}: {e}")
    return count

# بناء صفوف الجدول
rows = ""
for row in results:
    name = row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0]
    total_actions = row[1]
    status_6_months = row[2]
    last_edit_raw = row[3]
    actions_30_days = row[4]
    status_varied = row[5]

    # حساب التعديلات في نطاق ويكيبيديا بواسطة مرشح الإساءة في آخر 30 يومًا فقط
    abuse_filter_wp_edits = count_abusefilter_namespace_wikipedia(name)

    promo_date = format_ar_date(promo_dates.get(name, ""))
    last_edit_date = format_ar_date(last_edit_raw)

    # إضافة عدد التعديلات من مرشح الإساءة في نطاق ويكيبيديا
    rows += f"""|-
| {{{{إداري|{name}}}}} || {promo_date} || {{{{Formatnum:{total_actions}}}}} || {{{{Formatnum:{abuse_filter_wp_edits}}}}} || {yes_no_template('نشط' if actions_30_days >= 1 else 'غير نشط')} || {yes_no_template(status_6_months)} || {yes_no_template(status_varied)} || {last_edit_date}
"""

# دمج المحتوى
content = header + rows + footer

# حفظ الصفحة
page = pywikibot.Page(site, "مستخدم:Mohammed Qays/ملعب 18")
page.text = content
page.save(summary="بوت: تحديث")

# إغلاق الاتصال
cursor.close()
conn.close()

print("تم التحديث")
