import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class PageParser:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        self.playwright = None
        self.browser = None

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def stop_browser(self):
        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()

    def fetch_page(self, url, use_playwright=False):
        try:
            if use_playwright:
                return self._fetch_with_playwright(url)
            try:
                return self._fetch_with_requests(url)
            
            except requests.HTTPError as error:
                status_code = error.response.status_code

                if status_code == 403:
                    print("\033[33m[WARNING] 403 Forbidden. Повторяю попытку через Playwright.\033[0m")
                    return self._fetch_with_playwright(url)

                raise

        except Exception as error:
            print(f"\033[31m[ERROR] Ошибка загрузки {url}: {error}\033[0m")
            return None, None

    def _fetch_with_requests(self, url):
        response = requests.get(url, headers=self.headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        final_url = response.url
        return response.text, final_url

    def _fetch_with_playwright(self, url):
        page = self.browser.new_page()

        try:
            page.set_default_timeout(30000)

            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass

            page.wait_for_timeout(2000)

            html = page.content()
            final_url = page.url

            return html, final_url

        finally:
            page.close()

    def extract_text(self, html):
        soup = BeautifulSoup(html, "lxml")

        canonical = soup.find("link", rel="canonical")
        canonical_url = None

        if canonical and canonical.get("href"):
            canonical_url = canonical["href"]

        for tag in soup([
            "script", "style", "noscript", "svg",
            "footer", "nav", "iframe","form",
            "button", "img", "blockquote", 
            "title", "video", "aside"          
        ]):
            tag.decompose()

        tag_selectors = [
            #region replit - самый доставучий
            {"id": "sidebar-content"},
            {"id": "navbar"},
            {"id": "content-side-layout"},
            {"id": "pagination"},
            {"id": "page-context-menu"},
            {"class": "feedback-toolbar pb-16 w-full flex flex-col gap-y-8"},
            {"class": "eyebrow h-5 text-primary"},
            {"class": "mt-2 text-lg prose prose-gray"},
            #endregion 
            #region lovable
            {"class": "text-muted-foreground text-sm"},
            {"class": "hidden h-full lg:block"},
            #endregion
            #region figma
            {"class": "fig-1smnc27"},
            {"class": "fig-sa8fot"},
            {"class": "fig-82uc28"},
            {"class": "fig-19ciivj"},
            {"class": "fig-20t2nh"},
            {"class": "fig-1w2p18d"},
            {"class": "fig-7wpver"},
            {"class": "fig-qpu3wz"},
            #endregion
            #region VercelBlog
            {"class": "author-module__OTTSya__authors"},
            {"data-testid": "geistcn/skip-nav-link"},
            {"class": "text-heading-24 md:text-heading-32"},
            {"id": "header-wrapper"},
            #endregion
            #region V0 changelog
            {"id": "fides-overlay"},
            {"class": "text-heading-40 md:text-heading-48 font-semibold"},
            {"class": "flex items-center gap-4 mb-8"},
            {"id": "nd-nav"}
            #endregion
        ]
                
        for selector in tag_selectors:
            for element in soup.find_all(**selector):
                element.decompose()
                
        # В lovable удаляем span внутри класса, чтобы осталась даита, но удалился автор "поста"
        div = soup.find("div", class_="text-muted-foreground mt-2 flex items-center gap-2 text-sm")
        if div:
            for span in div.find_all("span"):
                span.decompose()
                
        # Ради vercel catalog пишем отдельный цикл, иначе новости раздвоятся, может потом рефакторну код, чтоб был компактнее
        for element in soup.find_all("ul", class_="grid-module__AMTIxG__grid", aria_live=None):
            if not element.get("aria-live"):
                element.decompose()
        
        text = soup.get_text(separator="\n")
        
        ignored_phrases = { #топ фраз сайтов-токсиков по отношению к парсеру
            "skip to main content",
            "allow all cookies",
            "do not allow cookies",
            "cookie settings",
            "cookies settings",
            "essential cookies",
            "marketing",
            "analytics",
            "functional",
            "privacy",
            "log in",
            "sign in",
            "sign up",
            "get started",
            "search...",
            "ctrl",
            "home page",
            "navigation",
            "menu",
            "loading",
        }

        lines = []
        seen = set()

        for line in text.splitlines():
            line = line.strip()
            
            if not line or len(line) < 3:
                continue

            lower_line = line.lower()
            
            if lower_line in ignored_phrases:
                continue
            
            if line in seen:
                continue

            seen.add(line)
            lines.append(line)

        cleaned_text = "\n".join(lines)

        cloudflare_signs = [
            "attention required",
            "cloudflare",
            "sorry, you have been blocked",
            "please enable cookies"
        ]

        text_lower = cleaned_text.lower()

        # обработка на случай защиты от использования Cloudflare
        for sign in cloudflare_signs:
            if sign in text_lower:
                print("\033[31m[WARNING] Cloudflare block.\033[0m") #видимо защита срабатывает, это её текст был
                return None, None

        return cleaned_text, canonical_url