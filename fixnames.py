import pywikibot
import toolforge
import re
import json
from pywikibot.exceptions import NoPageError, IsRedirectPageError

class Settings:
    lang = 'arwiki'
    json_page = "مستخدم:MoQabot/fixesname.json"
    editsumm = "[[وب:بوت|بوت]]: تصحيح."
    debug = "no"  # "yes" لمراجعة قبل الحفظ

# تحميل JSON من الصفحة
def load_json(site, page_title):
    page = pywikibot.Page(site, page_title)
    data = json.loads(page.text)
    return page, data

# تحديث العلم update = no في صفحة JSON
def disable_update_flag(json_page_obj, data):
    data['update'] = "no"
    json_page_obj.text = json.dumps(data, ensure_ascii=False, indent=2)
    json_page_obj.save(summary="[[وب:بوت|بوت]]: إيقاف التحديث.")

# تنفيذ الاستعلام في Toolforge
def execute_query(lang, namespace, terms):
    like_clauses = " OR ".join([f"page_title LIKE '%{term.replace(' ', '_')}%'" for term in terms])
    query = f"""
    /* {lang} */
    SELECT page_namespace, page_title
    FROM page
    WHERE page_is_redirect = 0
      AND page_namespace = {namespace}
      AND ({like_clauses})
    ORDER BY page_title;
    """
    conn = toolforge.connect(lang, 'analytics')
    with conn.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
    conn.close()
    return [(ns, title.decode('utf-8') if isinstance(title, bytes) else title) for ns, title in result]

def main():
    site = pywikibot.Site('ar', 'wikipedia')
    site.login()

    json_page_obj, data = load_json(site, Settings.json_page)

    if str(data.get("update", "no")).lower() != "yes":
        print("التحديث معطّل.")
        return

    namespace = int(data.get("namespace", 0))
    terms = data.get("terms", [])
    replacements = data.get("replacements", [])

    # بناء أنماط الاستبدال
    patterns = [(re.compile(item["old"]), item["new"]) for item in replacements]

    def fix_text(text: str) -> str:
        for pat, repl in patterns:
            text = pat.sub(repl, text)
        return text

    results = execute_query(Settings.lang, namespace, terms)

    CATEGORY_NS_NAME = site.namespace(14)
    TEMPLATE_NS_NAME = site.namespace(10)

    processed, edited, skipped = 0, 0, 0

    for ns, title in results:
        processed += 1

        if ns == 14:
            full_title = f"{CATEGORY_NS_NAME}:{title.replace('_', ' ')}"
        elif ns == 10:
            full_title = f"{TEMPLATE_NS_NAME}:{title.replace('_', ' ')}"
        else:
            full_title = title.replace("_", " ")

        page = pywikibot.Page(site, full_title)

        try:
            if page.isRedirectPage():
                skipped += 1
                continue

            text = page.get()
            new_text = fix_text(text)

            if new_text != text:
                if Settings.debug.lower() == "no":
                    page.text = new_text
                    page.save(Settings.editsumm, minor=True, quiet=True)
                else:
                    print(f"سيعدل: {full_title}\n---قبل---\n{text}\n---بعد---\n{new_text}\n")
                edited += 1
            else:
                skipped += 1

        except (NoPageError, IsRedirectPageError):
            skipped += 1
        except Exception as e:
            skipped += 1
            print(f"خطأ في {full_title}: {e}")

    print(f"تمت معالجة: {processed} | عُدّل: {edited} | تخطّي: {skipped}")

    # بعد الانتهاء: تعطيل العلم
    disable_update_flag(json_page_obj, data)

if __name__ == "__main__":
    main()
