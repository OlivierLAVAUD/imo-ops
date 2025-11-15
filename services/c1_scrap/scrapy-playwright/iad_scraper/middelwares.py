from scrapy import signals
from scrapy.http import HtmlResponse
from itemadapter import is_item, ItemAdapter
from playwright.async_api import async_playwright
import asyncio

class PlaywrightMiddleware:
    def __init__(self):
        self.playwright = None
        self.browser = None
        
    async def process_request(self, request, spider):
        if not request.meta.get('playwright', False):
            return None
            
        page = request.meta.get('playwright_page')
        if not page:
            return None
            
        try:
            await page.goto(request.url)
            
            # Gestion des cookies si configurée
            if hasattr(spider, 'handle_cookies'):
                await spider.handle_cookies(page)
                
            # Attendre le chargement si spécifié
            wait_for = request.meta.get('playwright_wait_for')
            if wait_for:
                await page.wait_for_selector(wait_for)
                
            # Exécuter des actions si spécifiées
            page_function = request.meta.get('playwright_page_function')
            if page_function:
                await page_function(page, request)
                
            content = await page.content()
            return HtmlResponse(
                url=request.url,
                body=content.encode('utf-8'),
                request=request,
                encoding='utf-8'
            )
            
        except Exception as e:
            spider.logger.error(f"Playwright error: {e}")
            return HtmlResponse(url=request.url, status=500)