import pywikibot
import toolforge
import json

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

def execute_query(lang, search_word):
    query = f'''
    SELECT page.page_title
    FROM page
    LEFT JOIN redirect
      ON redirect.rd_from = page.page_id
    WHERE page.page_namespace = 0
      AND page.page_title LIKE '%{search_word}%'
      AND redirect.rd_from IS NULL
    LIMIT 1000
    '''
    try:
        conn = toolforge.connect(lang, 'analytics')
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        conn.close()
        return [row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0] for row in result]
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

    if not search_word:
        raise SystemExit("لم يتم تحديد كلمة البحث (search) في ملف JSON")

    titles = execute_query(Settings.lang, search_word)
    titles.sort()

    replaced_pairs = apply_replacements(titles, replacements)
    content = format_content(replaced_pairs)

    target_page_obj = pywikibot.Page(site, Settings.target_page)

    if Settings.debug == "no":
        target_page_obj.put(content, summary=Settings.editsumm)
        update_json_page_flag(site, json_page_obj, data)
    else:
        # في وضع debug يمكن إضافة كود عرض لكن حسب طلبك تم الحذف
        pass

if __name__ == "__main__":
    update_page()
