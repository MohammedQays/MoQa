import toolforge
import pywikibot
import json

def get_portals_from_database():
    query = """
    SELECT DISTINCT
      SUBSTRING_INDEX(SUBSTRING_INDEX(p.page_title, '/', 1), 'بوابة_', -1) AS portal_name
    FROM page AS p
    JOIN categorylinks AS cl ON cl.cl_from = p.page_id
    WHERE p.page_namespace = 14
      AND p.page_title LIKE "بوابة_%/مقالات_متعلقة"
      AND cl.cl_to IN (
        "تصنيفات_لمقالات_متعلقة_ببوابات",
        "مقالات_جديدة_حسب_البوابة",
        "مقالات_متعلقة_ببوابات_الثقافة_والترفيه",
        "مقالات_متعلقة_ببوابات_العلوم",
        "مقالات_متعلقة_ببوابات_العلوم_الإنسانية",
        "مقالات_متعلقة_ببوابات_تقنية",
        "مقالات_متعلقة_ببوابات_جغرافية",
        "مقالات_متعلقة_ببوابات_حيوانات",
        "مقالات_متعلقة_ببوابات_ديانات_ومعتقدات",
        "مقالات_متعلقة_ببوابات_رياضية",
        "مقالات_متعلقة_ببوابات_عسكرية",
        "مقالات_متعلقة_ببوابات_مدن",
        "مقالات_متعلقة_ببوابات_آسيوية",
        "مقالات_متعلقة_ببوابات_أمريكية",
        "مقالات_متعلقة_ببوابات_أوروبية",
        "مقالات_متعلقة_ببوابات_أوقيانوسية",
        "مقالات_متعلقة_ببوابات_إفريقية",
        "مقالات_متعلقة_ببوابات_الشام",
        "مقالات_متعلقة_ببوابات_الوطن_العربي",
        "مقالات_متعلقة_ببوابات_عربية"
      )
    ORDER BY portal_name;
    """

    conn = toolforge.connect('arwiki')
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    portals = []
    for (portal_name,) in rows:
        if isinstance(portal_name, bytes):
            portal_name = portal_name.decode('utf-8')
        portals.append(portal_name)

    return portals

def upload_to_wiki_pywikibot(portals):
    site = pywikibot.Site('ar', 'wikipedia')
    site.login()  # تأكد من إعداد user-config.py بشكل صحيح

    page_title = 'مستخدم:Mohammed Qays/Portal.json'
    page = pywikibot.Page(site, page_title)

    text = json.dumps({"portals": portals}, ensure_ascii=False, indent=4)

    summary = 'تحديث قائمة البوابات بصيغة JSON'

    page.text = text
    page.save(summary=summary)

    print(f"تم رفع المحتوى إلى صفحة {page_title}")

if __name__ == "__main__":
    portals = get_portals_from_database()
    upload_to_wiki_pywikibot(portals)
