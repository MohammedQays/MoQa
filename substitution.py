import pywikibot
import toolforge
import json

# خريطة أسماء النطاقات العربية إلى أرقام النطاق في ويكي عربية
NAMESPACE_MAP = {
    "مقال": 0,
    "": 0,  # إذا كان فارغ افتراضي مقالات
    "قالب": 10,
    "تصنيف": 14,
    "ملف": 6,
    "بوابة": 100,
    "ويكيبيديا": 4,
    "نقاش": 1,
    "نقاش_قالب": 11,
    "نقاش_تصنيف": 15,
    "نقاش_ملف": 7,
    "نقاش_بوابة": 101,
    "نقاش_ويكيبيديا": 5,
}

class Settings:
    lang = 'arwiki'
    json_page = "مستخدم:MoQabot/substitution.json"
    target_page = "مستخدم:Mohammed Qays/طلبات"
    editsumm = "[[وب:بوت|بوت]]: جلب قائمة."
    debug = "no"

def load_json(site, page_title):
    page = pywikibot.Page(site, page_title)
    try:
        text = page.text
        data = json.loads(text)
        return page, data
    except Exception as e:
        raise SystemExit(f"فشل تحميل أو تحليل ملف JSON من الصفحة {page_title}: {e}")

def get_namespace_number(ns):
    if isinstance(ns, int):
        return ns
    ns = ns.strip()
    if ns.endswith(":"):
        ns = ns[:-1]
    return NAMESPACE_MAP.get(ns, 0)

def execute_query(lang, search_word, namespace_num):
    # بناء بادئة العرض فقط (لا تؤثر على البحث)
    if namespace_num == 14:  # تصنيف
        display_prefix = "تصنيف:"
    elif namespace_num == 6:  # ملف
        display_prefix = "ملف:"
    elif namespace_num == 4:  # ويكيبيديا
        display_prefix = "ويكيبيديا:"
    elif namespace_num == 10:  # قالب
        display_prefix = "قالب:"
    elif namespace_num == 100:  # بوابة
        display_prefix = "بوابة:"
    else:
        display_prefix = ""

    like_pattern = f"%{search_word}%"

    # بناء شرط WHERE الأساسي
    where_clause = f"page.page_namespace = {namespace_num} AND page.page_title LIKE '{like_pattern}'"

    query = f'''
    SELECT page.page_title
    FROM page
    LEFT JOIN redirect
      ON redirect.rd_from = page.page_id
    WHERE {where_clause}
      AND redirect.rd_from IS NULL
    LIMIT 1000
    '''

    try:
        conn = toolforge.connect(lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()

        # إضافة البادئة المناسبة للعرض فقط
        return [f"{display_prefix}{row[0].decode('utf-8')}" if isinstance(row[0], bytes)
                else f"{display_prefix}{row[0]}" for row in result]
    except Exception as e:
        raise SystemExit(f"فشل تنفيذ الاستعلام: {e}")

def apply_replacements(titles, replacements):
    result = []
    for title in titles:
        new_title = title
        for old, new in replacements.items():
            new_title = new_title.replace(old, new)
        result.append((title, new_title))
    return result

def format_content(pairs):
    content = ""
    for original, replaced in pairs:
        # إزالة البادئة المكررة إذا كانت موجودة
        original = original.replace("قالب:قالب:", "قالب:")
        replaced = replaced.replace("قالب:قالب:", "قالب:")
        content += f"* [[:{original}]] &larr; [[:{replaced}]]\n"
    return content

def update_json_page_flag(site, json_page_obj, data):
    data['update'] = "no"
    new_text = json.dumps(data, ensure_ascii=False, indent=2)
    json_page_obj.text = new_text
    json_page_obj.save(summary="[[وب:بوت|بوت]]: ضبط التحديث.", minor=True)

def update_page():
    site = pywikibot.Site('ar', 'wikipedia')

    json_page_obj, data = load_json(site, Settings.json_page)

    update_flag = data.get("update", "no").lower()
    if update_flag != "yes":
        return

    search_word = data.get("search")
    replacements = data.get("replacements", {})
    namespace_input = data.get("namespace", 0)

    namespace_num = get_namespace_number(namespace_input)

    if Settings.debug == "yes":
        print(f"البحث في النطاق: {namespace_num} بكلمة البحث: {search_word}")

    if not search_word:
        raise SystemExit("لم يتم تحديد كلمة البحث (search) في ملف JSON")

    titles = execute_query(Settings.lang, search_word, namespace_num)
    titles.sort()

    if Settings.debug == "yes":
        print(f"النتائج الأولية: {titles}")

    replaced_pairs = apply_replacements(titles, replacements)
    content = format_content(replaced_pairs)

    target_page_obj = pywikibot.Page(site, Settings.target_page)

    if Settings.debug == "no":
        target_page_obj.put(content, summary=Settings.editsumm)
        update_json_page_flag(site, json_page_obj, data)
    else:
        print("محتوى التعديل:")
        print(content)

if __name__ == "__main__":
    update_page()
