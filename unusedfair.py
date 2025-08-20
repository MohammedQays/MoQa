import pywikibot
import toolforge
from datetime import date

# إعدادات البوت
class settings:
    lang = 'arwiki'
    editsumm = "[[وب:بوت|بوت]]: وسم صورة استعمال عادل يتيمة."
    debug = "no"  # اجعلها "yes" للتجربة دون نشر

# التاريخ الحالي
today = date.today().isoformat()

# استعلام الملفات غير الحرة اليتيمة
query = f"""
SELECT 
  page_title
FROM page AS p1
JOIN image 
  ON img_name = page_title
WHERE page_namespace = 6
  AND EXISTS (
    SELECT *
    FROM categorylinks AS cl1
    WHERE cl1.cl_from = page_id
      AND (
        cl1.cl_to IN ("جميع_الملفات_غير_الحرة", "جميع_الشعارات_غير_الحرة")
        OR EXISTS (
          SELECT *
          FROM page AS p2
          WHERE p2.page_namespace = 14
            AND p2.page_title = cl1.cl_to
            AND EXISTS (
              SELECT *
              FROM categorylinks AS cl2
              WHERE cl2.cl_from = p2.page_id
                AND (
                  cl2.cl_to IN ("جميع_الملفات_غير_الحرة", "جميع_الشعارات_غير_الحرة")
                  OR EXISTS (
                    SELECT *
                    FROM page AS p3
                    WHERE p3.page_namespace = 14
                      AND p3.page_title = cl2.cl_to
                      AND EXISTS (
                        SELECT *
                        FROM categorylinks AS cl3
                        WHERE cl3.cl_from = p3.page_id
                          AND cl3.cl_to IN ("جميع_الملفات_غير_الحرة", "جميع_الشعارات_غير_الحرة")
                      )
                  )
                )
            )
        )
      )
  )
  AND NOT EXISTS (
    SELECT *
    FROM imagelinks
    WHERE il_to = page_title
      AND il_from_namespace IN (0, 1, 2, 3, 4, 5, 10, 11, 12, 100, 118)
  )
  AND DATEDIFF(NOW(), img_timestamp) > 7
  AND page_id NOT IN (
    SELECT tl_from
    FROM templatelinks
    WHERE tl_target_id = (
      SELECT page_id
      FROM page
      WHERE page_namespace = 10
        AND page_title = 'صورة_استعمال_عادل_يتيمة'
    )
  )
  LIMIT 10;
"""

# الاتصال بقاعدة البيانات
site = pywikibot.Site()
conn = toolforge.connect(settings.lang, 'analytics')

# تنفيذ الاستعلام
with conn.cursor() as cursor:
    cursor.execute(query)
    results = cursor.fetchall()

# المعالجة
for row in results:
    title = row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]
    page = pywikibot.Page(site, f"ملف:{title.replace('_', ' ')}")

    try:
        text = page.get()
    except pywikibot.NoPage:
        continue  # تجاهل الصفحات غير الموجودة
    except pywikibot.IsRedirectPage:
        continue  # تجاهل التحويلات

    # التحقق من عدم وجود القالب مسبقاً
    if "صورة استعمال عادل يتيمة" in text:
        continue

    new_template = f"{{{{صورة استعمال عادل يتيمة|تاريخ={today}}}}}"

    # الإضافة في نهاية الصفحة (يمكن تعديل الموقع حسب السياق)
    new_text = text.strip() + "\n\n" + new_template

    if settings.debug == "no":
        page.text = new_text
        page.save(settings.editsumm)
    else:
        print(f"== Preview: {page.title()} ==\n{new_text}\n{'='*40}")
