import pywikibot
import toolforge
import json

class Settings:
    lang = 'enwiki'
    json_page = "مستخدم:MoQabot/articles.json"
    report_title = "مستخدم:Mohammed Qays/مقالات مشاريع"
    editsumm = "[[وب:بوت|بوت]]: تحديث التقرير."
    debug = "no"

def load_json(site, page_title):
    page = pywikibot.Page(site, page_title)
    try:
        data = json.loads(page.text)
        return page, data
    except Exception as e:
        raise SystemExit(f"خطأ في قراءة JSON: {e}")

def run_query(category, min_size, limit_value):
    query = f"""
    SELECT 
        article.page_title,
        article.page_len
    FROM page AS talk
    INNER JOIN categorylinks ON talk.page_id = cl_from
    INNER JOIN page AS article 
        ON article.page_namespace = 0 
        AND article.page_title = talk.page_title 
        AND article.page_namespace = talk.page_namespace - 1
    LEFT JOIN langlinks 
        ON article.page_id = langlinks.ll_from 
        AND langlinks.ll_lang = 'ar'
    WHERE talk.page_namespace = 1
        AND cl_to = '{category}'
        AND article.page_is_redirect = 0
        AND article.page_len > {min_size}
        AND langlinks.ll_from IS NULL
    GROUP BY article.page_id
    ORDER BY article.page_len ASC, article.page_title
    LIMIT {limit_value};
    """

    conn = toolforge.connect(Settings.lang, 'analytics')
    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def build_report(results):
    content = "{{تقدم تطوير مقالة مشروع ويكي|المصدر=نعم|المستخدم=نعم|العرض=90%|\n"

    row = 1
    for item in results:
        title = item[0].decode("utf-8") if isinstance(item[0], bytes) else item[0]
        clean_title = title.replace("_", " ")

        content += (
            "{{تقدم تطوير مقالة مشروع ويكي/صف"
            f"|م={row}"
            f"|المقالة={clean_title}"
            f"|المصدر=[[:en:{clean_title}]]"
            "|الهدف=2"
            "|المستخدم=؟؟"
            "}}\n"
        )
        row += 1

    content += "}}"
    return content

def update_json_flag(page_obj, data):
    data['update'] = "no"
    page_obj.text = json.dumps(data, ensure_ascii=False, indent=2)
    page_obj.save(summary="[[وب:بوت|بوت]]: تعطيل التحديث.", minor=True)

def update_page():
    site = pywikibot.Site('ar', 'wikipedia')

    # تحميل JSON
    json_page_obj, data = load_json(site, Settings.json_page)

    # هل يجب تشغيل البوت؟
    if data.get("update", "no").lower() != "yes":
        return

    category = data.get("category")
    size = int(data.get("size", 2000))
    limit_value = int(data.get("limit", 100))  # ← القيمة الافتراضية 100

    if not category:
        raise SystemExit("خطأ: لم يتم تحديد 'category' في JSON")

    # تنفيذ الاستعلام
    results = run_query(category, size, limit_value)

    # بناء التقرير
    report = build_report(results)

    # نشر التقرير
    target_page = pywikibot.Page(site, Settings.report_title)

    if Settings.debug == "no":
        target_page.put(report, summary=Settings.editsumm)
        update_json_flag(json_page_obj, data)
    else:
        print(report)

if __name__ == "__main__":
    update_page()
