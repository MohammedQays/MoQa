import requests

# الحصول على أعلى 100 مقالة زيارة من ويكيبيديا الإنجليزية
url = "https://en.wikipedia.org/w/api.php?action=query&list=mostviewed&format=json&pvimlimit=100"
response = requests.get(url).json()

# قائمة المقالات الأعلى زيارة مع إحصاءات الزيارات
top_articles = [{"title": article["title"], "views": article["views"]} for article in response["query"]["mostviewed"]]

# التحقق من وجود كل مقالة في ويكيبيديا العربية
missing_in_arabic = []
for article in top_articles:
    title = article["title"]
    views = article["views"]
    
    # تحقق من وجود المقالة في ويكيبيديا العربية
    url = f"https://ar.wikipedia.org/w/api.php?action=query&titles={title}&format=json"
    response = requests.get(url).json()
    pages = response["query"]["pages"]
    
    # إذا كانت المقالة غير موجودة في النطاق الرئيسي في ويكيبيديا العربية
    if "-1" in pages:
        missing_in_arabic.append({"title": title, "views": views})

# إعداد التقرير بتنسيق ويكي
report = '{| class="wikitable"\n'
report += "! التسلسل !! عنوان المقالة !! عدد الزيارات\n"

for idx, article in enumerate(missing_in_arabic, start=1):
    title = article["title"]
    views = article["views"]
    # إضافة العنوان بتنسيق رابط للنسخة الإنجليزية
    report += f"|-\n| {idx} || [[:en:{title}|{title}]] || {views}\n"

report += "|}"

# طباعة التقرير لتتمكن من نسخه
print(report)
