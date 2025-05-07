import pywikibot
import toolforge
import json
from datetime import datetime, timedelta, timezone

# إعداد الموقع
site = pywikibot.Site('ar', 'wikipedia')

# تحميل قائمة الإداريين وتواريخ ترشيحهم من صفحة JSON
admins_page = pywikibot.Page(site, "مستخدم:Mohammed Qays/admins.json")
admins_data = json.loads(admins_page.text)

# بناء قاموس لربط اسم الإداري بتاريخ الترقية
promo_dates = {entry["username"]: entry["promotion_date"] for entry in admins_data}

# الاتصال بقاعدة البيانات
conn = toolforge.connect('arwiki', 'analytics')
cursor = conn.cursor()

# تنفيذ الاستعلام
query = """
SELECT 
    a.actor_name AS user_name,

    COUNT(CASE WHEN log_type = 'delete' AND log_action = 'delete' THEN 1 END) AS delete_count,
    COUNT(CASE WHEN log_type = 'delete' AND log_action = 'revision' THEN 1 END) AS revision_delete_count,
    COUNT(CASE WHEN log_type = 'delete' AND log_action = 'restore' THEN 1 END) AS restore_count,

    COUNT(CASE WHEN log_type = 'block' AND log_action = 'block' THEN 1 END) AS block_count,
    COUNT(CASE WHEN log_type = 'block' AND log_action = 'unblock' THEN 1 END) AS unblock_count,
    COUNT(CASE WHEN log_type = 'block' AND log_action = 'reblock' THEN 1 END) AS reblock_count,

    COUNT(CASE WHEN log_type = 'protect' AND log_action = 'protect' THEN 1 END) AS protect_count,
    COUNT(CASE WHEN log_type = 'protect' AND log_action = 'modify' THEN 1 END) AS protect_modify_count,
    COUNT(CASE WHEN log_type = 'protect' AND log_action = 'unprotect' THEN 1 END) AS unprotect_count,

    COUNT(CASE WHEN log_type = 'rights' AND log_action = 'rights' THEN 1 END) AS rights_count,
    COUNT(*) AS total_admin_actions

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
ORDER BY total_admin_actions DESC;
"""
cursor.execute(query)
results = cursor.fetchall()

# رأس الجدول
header = """{| class="wikitable sortable" style="text-align:center; font-size:95%; width:100%"
|-
! الإداري !! تاريخ الحصول على الصلاحية !! حذف !! مراجعة حذف !! استرجاع !! منع !! رفع منع !! إعادة منع !! حماية !! تعديل حماية !! رفع حماية !! منح صلاحية !! مجموع الأفعال
"""

# تذييل الجدول
footer = """
|}
<noinclude>تحديث تلقائي بواسطة بوت</noinclude>
"""

# دالة تنسيق التاريخ إلى نص عربي
def format_date(date_str):
    months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
              "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{d.day} {months[d.month-1]} {d.year}"
    except:
        return "غير معروف"

# إنشاء الصفوف
rows = ""
for row in results:
    raw_name = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    promo = promo_dates.get(raw_name, "")
    promo_formatted = format_date(promo) if promo else "غير معروف"

    counts = row[1:]  # باقي القيم العدّية
    rows += "|-\n| %s || %s || %s\n" % (
        raw_name,
        promo_formatted,
        " || ".join(str(c) for c in counts)
    )

# دمج وحفظ المحتوى في الصفحة
content = header + rows + footer
page = pywikibot.Page(site, "مستخدم:MoQabot/جدول")
page.text = content
page.save(summary="بوت: تحديث")

cursor.close()
conn.close()
print("تم تحديث الصفحة بنجاح.")
