import pywikibot
from pywikibot import pagegenerators
import re
import time
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# إعدادات أساسية
SITE = pywikibot.Site('ar', 'wikipedia')
SITE.login()
CATEGORY_NAME = "تصنيف:بذرة بحاجة لتعديل"
EXCLUDED_CATEGORIES = {
    'صفحات مجموعات صيغ كيميائية مفهرسة',
    'كواكب صغيرة مسماة',
    'تحويلات من لغات بديلة',
    'تحويلات علم الفلك'
}
CACHE_FILE = 'processed_articles.pkl'
MAX_WORKERS = 1  # عدد العمليات المتوازية

class ArticleProcessor:
    def __init__(self):
        self.processed = self.load_cache()
        self.session = requests.Session()

    @staticmethod
    def load_cache():
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return set()

    def save_cache(self):
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(self.processed, f)

    def fetch_articles(self):
        """جلب المقالات باستخدام API"""
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': CATEGORY_NAME,
            'cmnamespace': 0,
            'cmlimit': 'max',
            'format': 'json'
        }

        while True:
            response = self.session.get(
                'https://ar.wikipedia.org/w/api.php',
                params=params
            ).json()

            for page in response.get('query', {}).get('categorymembers', []):
                yield pywikibot.Page(SITE, page['title'])

            if 'continue' not in response:
                break
            params.update(response['continue'])

    def is_excluded(self, page):
        """التحقق من التصنيفات المستبعدة"""
        page_categories = {cat.title(with_ns=False) for cat in page.categories()}
        return any(ec in page_categories for ec in EXCLUDED_CATEGORIES)

    def process_article(self, page):
        """المعالجة الرئيسية للمقالة"""
        try:
            if page.title() in self.processed:
                return

            if self.is_excluded(page):
                print(f"تخطي: {page.title()} (تصنيف مستبعد)")
                self.processed.add(page.title())
                return

            text = page.get()
            if not re.search(r'\{\{\s*بذرة[^}]*\}\}', text):
                print(f"تخطي: {page.title()} (لا يوجد قالب بذرة)")
                self.processed.add(page.title())
                return

            text_without_stub = re.sub(r'\{\{\s*بذرة[^}]*\}\}', '', text)
            words = len(text_without_stub.split())
            size = len(text_without_stub.encode('utf-8'))

            if (words / 400 * 40) + (size / 5000 * 60) >= 100:
                new_text = text_without_stub.strip()
                if new_text != text:
                    page.text = new_text
                    page.save(summary="بوت:إزالة قالب بذرة")

            self.processed.add(page.title())

        except Exception:
            pass
        finally:
            time.sleep(1)

    def run(self):
        """تشغيل المعالجة مع التوازي"""
        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(self.process_article, page): page 
                    for page in self.fetch_articles()
                }

                for future in as_completed(futures):
                    page = futures[future]
                    try:
                        future.result()
                    except Exception:
                        pass

                    if len(self.processed) % 50 == 0:
                        time.sleep(10)
                        self.save_cache()

        finally:
            self.save_cache()

if __name__ == "__main__":
    processor = ArticleProcessor()
    processor.run()
