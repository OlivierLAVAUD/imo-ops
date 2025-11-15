import scrapy
import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from scrapy_playwright.page import PageMethod
from iad_scraper.items import IadItem
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class IadFranceSpider(scrapy.Spider):
    name = 'iad_france'
    allowed_domains = ['iadfrance.fr']
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 30000
        }
    }
    
    def __init__(self, localisation="Paris", max_biens=50, max_pages=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localisation = localisation
        self.max_biens = int(max_biens)
        self.max_pages = int(max_pages)
        self.config = self.load_config()
        self.scraped_count = 0
        self.current_page_number = 1
        
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON"""
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info("✅ Configuration chargée avec succès")
                return config
            else:
                self.logger.error("❌ Fichier config.json non trouvé")
                return {}
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement config: {e}")
            return {}

    async def start(self):
        """Démarrage asynchrone du spider"""
        site_config = self.config.get('site', {})
        base_url = site_config.get('base_url', 'https://www.iadfrance.fr')
        
        self.logger.info(f"🚀 Démarrage du scraping pour: {self.localisation}")
        self.logger.info(f"🏠 Nombre maximum de biens: {self.max_biens}")
        self.logger.info(f"📄 Pages maximum: {self.max_pages}")
        
        yield scrapy.Request(
            url=base_url,
            callback=self.parse_homepage,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_context': 'default',
                'playwright_page_methods': [
                    PageMethod('wait_for_timeout', site_config.get('navigation_delay', 2000)),
                ],
                'dont_retry': True
            }
        )

    async def parse_homepage(self, response):
        """Traite la page d'accueil et remplit le formulaire de recherche"""
        page = response.meta['playwright_page']
        
        try:
            # Gestion des cookies
            await self.handle_cookies(page)
            
            # Remplir le formulaire de recherche
            success = await self.fill_search_form(page)
            
            if success:
                # Attendre les résultats
                await self.wait_for_search_results(page)
                
                # Commencer le scraping des résultats
                yield scrapy.Request(
                    url=page.url,
                    callback=self.parse_results_page,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_number': 1,
                        'dont_retry': True
                    }
                )
            else:
                self.logger.error("❌ Échec du remplissage du formulaire")
                await page.close()
                
        except Exception as e:
            self.logger.error(f"❌ Erreur page d'accueil: {e}")
            await self.take_screenshot(page, "homepage_error")
            await page.close()

    async def handle_cookies(self, page: Page):
        """Gère la bannière de cookies"""
        try:
            # Attendre un peu pour que les cookies apparaissent
            await page.wait_for_timeout(3000)
            
            # Stratégies pour fermer les cookies
            refuse_selectors = [
                "button:has-text('Tout refuser')",
                "button:has-text('Refuser tout')",
                "button.ppms_cm_btn_reject_all",
                "button[data-consent-action='reject-all']",
                "[class*='reject-all']"
            ]
            
            for selector in refuse_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0 and await button.is_visible():
                        await button.click(force=True)
                        await page.wait_for_timeout(2000)
                        self.logger.info("✓ Cookies refusés")
                        return
                except Exception:
                    continue
                    
            self.logger.info("✓ Aucune fenêtre cookies détectée")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur gestion cookies: {e}")

    async def fill_search_form(self, page: Page) -> bool:
        """Remplit le formulaire de recherche complet"""
        try:
            search_config = self.config.get('search_form', {})
            
            # Sélectionner le type de transaction (Acheter)
            transaction_success = await self.select_transaction_type(page, search_config)
            if not transaction_success:
                return False
                
            # Sélectionner le type de bien (Ancien)
            property_type_success = await self.select_property_type(page, search_config)
            if not property_type_success:
                return False
                
            # Remplir la localisation
            location_success = await self.fill_location(page, search_config)
            if not location_success:
                return False
                
            self.logger.info("✅ Formulaire de recherche rempli avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur remplissage formulaire: {e}")
            return False

    async def select_transaction_type(self, page: Page, search_config: Dict) -> bool:
        """Sélectionne le type de transaction (Acheter)"""
        try:
            transaction_config = search_config.get('transaction_type', {})
            options = transaction_config.get('options', {})
            acheter_config = options.get('acheter', {})
            
            selectors = [
                acheter_config.get('css_selector'),
                acheter_config.get('input_css'),
                "label:has-text('Acheter')",
                "input[type='radio'][value*='buy']",
                "button:has-text('Acheter')"
            ]
            
            for selector in selectors:
                if not selector:
                    continue
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        if 'input' in selector:
                            # C'est un input radio, cliquer sur le label parent
                            label = page.locator(f"label:has({selector})")
                            if await label.count() > 0:
                                await label.first.click(force=True)
                            else:
                                await element.first.click(force=True)
                        else:
                            await element.first.click(force=True)
                            
                        await page.wait_for_timeout(1500)
                        self.logger.info("✓ Type de transaction 'Acheter' sélectionné")
                        return True
                except Exception:
                    continue
                    
            self.logger.warning("⚠️ Impossible de sélectionner 'Acheter'")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sélection transaction: {e}")
            return False

    async def select_property_type(self, page: Page, search_config: Dict) -> bool:
        """Sélectionne le type de bien (Ancien)"""
        try:
            type_bien_config = search_config.get('type_bien', {})
            options = type_bien_config.get('options', {})
            ancien_config = options.get('ancien', {})
            
            selectors = [
                ancien_config.get('css_selector'),
                ancien_config.get('input_css'),
                "label:has-text('Ancien')",
                "input[type='radio'][value*='old']",
                "button:has-text('Ancien')"
            ]
            
            for selector in selectors:
                if not selector:
                    continue
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        if 'input' in selector:
                            label = page.locator(f"label:has({selector})")
                            if await label.count() > 0:
                                await label.first.click(force=True)
                            else:
                                await element.first.click(force=True)
                        else:
                            await element.first.click(force=True)
                            
                        await page.wait_for_timeout(1500)
                        self.logger.info("✓ Type de bien 'Ancien' sélectionné")
                        return True
                except Exception:
                    continue
                    
            self.logger.warning("⚠️ Impossible de sélectionner 'Ancien'")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sélection type bien: {e}")
            return False

    async def fill_location(self, page: Page, search_config: Dict) -> bool:
        """Remplit le champ de localisation"""
        try:
            location_config = search_config.get('localisation', {})
            input_selector = location_config.get('input_css', "input[placeholder='Ville, code postal…']")
            
            # Vider et remplir le champ
            await page.fill(input_selector, '')
            await page.wait_for_timeout(200)
            await page.type(input_selector, self.localisation, delay=50)
            await page.wait_for_timeout(2000)
            
            # Attendre et sélectionner les suggestions
            suggestions_config = location_config.get('suggestions_container', {})
            suggestions_selector = suggestions_config.get('items_css', "div[role='option']")
            
            try:
                await page.wait_for_selector(suggestions_selector, timeout=5000)
                suggestions = page.locator(suggestions_selector)
                if await suggestions.count() > 0:
                    await suggestions.first.click(force=True)
                    self.logger.info(f"✓ Localisation '{self.localisation}' sélectionnée")
                else:
                    # Fallback: utiliser Enter
                    await page.keyboard.press('Enter')
                    self.logger.info(f"✓ Localisation '{self.localisation}' validée avec Enter")
            except PlaywrightTimeoutError:
                await page.keyboard.press('Enter')
                self.logger.info(f"✓ Localisation '{self.localisation}' validée avec Enter (timeout)")
            
            await page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur remplissage localisation: {e}")
            return False

    async def wait_for_search_results(self, page: Page):
        """Attend le chargement des résultats de recherche"""
        try:
            results_config = self.config.get('search_results', {})
            articles_config = results_config.get('articles', {})
            articles_selector = articles_config.get('css_selector', 'article.overflow-clip')
            
            # Attendre plus longtemps pour les résultats
            await page.wait_for_selector(articles_selector, timeout=15000, state='attached')
            
            # Vérifier qu'il y a bien des résultats
            articles = page.locator(articles_selector)
            article_count = await articles.count()
            
            if article_count > 0:
                self.logger.info(f"✅ {article_count} résultats de recherche chargés")
            else:
                self.logger.warning("⚠️ Aucun résultat trouvé après recherche")
                await self.take_screenshot(page, "no_results")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur attente résultats: {e}")
            await self.take_screenshot(page, "wait_results_error")
            raise

    async def parse_results_page(self, response):
        """Parse une page de résultats et extrait les liens des annonces"""
        page = response.meta['playwright_page']
        current_page = response.meta.get('playwright_page_number', 1)
        self.current_page_number = current_page
        
        self.logger.info(f"🔍 Traitement de la page {current_page}")
        
        try:
            # Récupérer les articles
            articles = await self.get_search_results(page)
            if not articles:
                self.logger.warning("⚠️ Aucun article trouvé sur cette page")
                await page.close()
                return
            
            self.logger.info(f"📄 {len(articles)} articles à traiter")
            
            # Traiter chaque article
            for i in range(min(len(articles), self.max_biens - self.scraped_count)):
                if self.scraped_count >= self.max_biens:
                    break
                    
                try:
                    article_data = await self.extract_article_list_data(articles[i])
                    
                    if article_data and article_data.get('lien'):
                        self.logger.info(f"📖 Article {i+1}: {article_data.get('titre', 'N/A')}")
                        
                        yield scrapy.Request(
                            url=article_data['lien'],
                            callback=self.parse_detail_page,
                            meta={
                                'playwright': True,
                                'playwright_include_page': True,
                                'list_data': article_data,
                                'dont_retry': True
                            }
                        )
                    else:
                        self.logger.warning(f"⚠️ Article {i+1} sans données valides")
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur article {i+1}: {e}")
            
            # Pagination
            if self.scraped_count < self.max_biens and current_page < self.max_pages:
                if await self.go_to_next_page(page):
                    yield scrapy.Request(
                        url=page.url,
                        callback=self.parse_results_page,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_number': current_page + 1,
                            'dont_retry': True
                        }
                    )
                else:
                    self.logger.info("✅ Dernière page atteinte")
                    await page.close()
            else:
                self.logger.info("✅ Limite atteinte (biens ou pages)")
                await page.close()
                
        except Exception as e:
            self.logger.error(f"❌ Erreur page résultats {current_page}: {e}")
            await self.take_screenshot(page, f"error_page_{current_page}")
            await page.close()

    async def get_search_results(self, page: Page) -> List[Locator]:
        """Récupère la liste des articles de résultats - CORRIGÉ"""
        try:
            results_config = self.config.get('search_results', {})
            articles_config = results_config.get('articles', {})
            articles_selector = articles_config.get('css_selector', 'article.overflow-clip')
            
            # Attendre que les articles soient chargés
            await page.wait_for_selector(articles_selector, timeout=10000)
            
            # Utiliser element_handles() au lieu de all()
            articles = await page.locator(articles_selector).element_handles()
            
            article_count = len(articles)
            self.logger.info(f"📄 Page {self.current_page_number} - {article_count} articles trouvés")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération résultats: {e}")
            return []

    async def extract_article_list_data(self, article_element) -> Dict[str, Any]:
        """Extrait les données d'un article de la liste - CORRIGÉ"""
        list_config = self.config.get('article_list_data', {})
        data = {}
        
        try:
            # Convertir l'element handle en Locator
            article_locator = article_element.as_locator()
            
            # Extraire les champs de base
            for field, config in list_config.items():
                if not isinstance(config, dict):
                    continue
                    
                value = await self.extract_field_value(article_locator, config)
                if value is not None:
                    data[field] = value

            # Date d'extraction
            data['date_extraction'] = datetime.now().isoformat()
            
            # Vérifier que les champs essentiels sont présents
            if not data.get('lien'):
                self.logger.warning("⚠️ Article sans lien - ignoré")
                return {}
                
            self.logger.debug(f"📊 Données extraites: {list(data.keys())}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur extraction données liste: {e}")
        
        return data

    async def extract_field_value(self, locator: Locator, config: Dict) -> Any:
        """Extrait la valeur d'un champ selon la configuration"""
        try:
            css_selector = config.get('css_selector')
            if not css_selector:
                return None
                
            element = locator.locator(css_selector).first
            if await element.count() == 0:
                return None
            
            # Récupérer la valeur selon le type
            if config.get('multiple'):
                # Champ multiple
                elements = locator.locator(css_selector)
                values = []
                for i in range(await elements.count()):
                    value = await self.get_element_value(elements.nth(i), config)
                    if value:
                        values.append(value)
                return values if values else None
            else:
                # Champ simple
                return await self.get_element_value(element, config)
                
        except Exception as e:
            self.logger.debug(f"⚠️ Erreur extraction champ {css_selector}: {e}")
            return None

    async def get_element_value(self, element: Locator, config: Dict) -> Optional[str]:
        """Récupère la valeur d'un élément"""
        try:
            if config.get('attribute'):
                value = await element.get_attribute(config['attribute'])
            else:
                value = await element.text_content()
            
            if value and config.get('regex'):
                match = re.search(config['regex'], value)
                if match:
                    value = match.group(1)
            
            return value.strip() if value else None
        except Exception:
            return None

    async def parse_detail_page(self, response):
        """Parse une page de détail et extrait toutes les données"""
        page = response.meta['playwright_page']
        list_data = response.meta['list_data']
        
        self.logger.info(f"🔍 Extraction détails: {list_data.get('titre', 'N/A')}")
        
        try:
            # Attendre le chargement de la page détail
            await self.wait_for_detail_page(page)
            
            # Extraire les données détaillées
            detail_data = await self.extract_detail_data(page, list_data)
            
            # Créer l'item Scrapy
            item = IadItem()
            for field, value in detail_data.items():
                if field in item.fields:
                    item[field] = value
            
            self.scraped_count += 1
            self.logger.info(f"✅ Article {self.scraped_count}/{self.max_biens} - Ref: {item.get('reference', 'N/A')}")
            
            yield item
            
        except Exception as e:
            self.logger.error(f"❌ Erreur extraction détails: {e}")
        finally:
            await page.close()

    async def wait_for_detail_page(self, page: Page):
        """Attend le chargement de la page détail"""
        try:
            detail_config = self.config.get('detail_page', {})
            wait_config = detail_config.get('wait_for', {})
            wait_selector = wait_config.get('css_selector', 'section.md\\:px-\\[4rem\\]')
            timeout = wait_config.get('timeout', 10000)
            
            await page.wait_for_selector(wait_selector, timeout=timeout)
            self.logger.info("✅ Page détail chargée")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement page détail: {e}")
            raise

    async def extract_detail_data(self, page: Page, list_data: Dict) -> Dict[str, Any]:
        """Extrait les données détaillées d'une annonce"""
        detail_config = self.config.get('detail_page', {}).get('data', {})
        data = {**list_data}
        
        try:
            # Extraire les champs directs
            for field, config in detail_config.items():
                if isinstance(config, dict) and 'css_selector' in config:
                    value = await self.extract_field_value(page, config)
                    if value is not None:
                        data[field] = value
            
            # Extraire les sections imbriquées
            nested_sections = ['copropriete', 'conseiller', 'dpe', 'ges']
            for section in nested_sections:
                if section in detail_config:
                    section_config = detail_config[section]
                    for subfield, subconfig in section_config.items():
                        if isinstance(subconfig, dict) and 'css_selector' in subconfig:
                            value = await self.extract_field_value(page, subconfig)
                            if value is not None:
                                field_name = f"{section}_{subfield}"
                                data[field_name] = value
                
        except Exception as e:
            self.logger.error(f"⚠️ Erreur extraction détails: {e}")
        
        return data

    async def go_to_next_page(self, page: Page) -> bool:
        """Passe à la page suivante"""
        try:
            pagination_config = self.config.get('search_results', {}).get('pagination', {})
            next_config = pagination_config.get('next_page', {})
            
            next_selectors = [
                next_config.get('css_selector'),
                "a.iad-btn[href*='page=']:has-text('Suivant')",
                "a[aria-label*='suivant']",
                "button[aria-label*='suivant']",
                "[class*='next']",
                "a:has-text('Suivant')",
                "button:has-text('Suivant')"
            ]
            
            for selector in next_selectors:
                if not selector:
                    continue
                    
                try:
                    next_buttons = page.locator(selector)
                    if await next_buttons.count() > 0:
                        for i in range(await next_buttons.count()):
                            if await next_buttons.nth(i).is_visible():
                                await next_buttons.nth(i).click(force=True)
                                await page.wait_for_timeout(3000)
                                
                                # Vérifier que la nouvelle page est chargée
                                await self.wait_for_search_results(page)
                                self.logger.info("✅ Navigation vers page suivante réussie")
                                return True
                except Exception:
                    continue
            
            self.logger.info("❌ Aucune page suivante trouvée")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur navigation page suivante: {e}")
            return False

    async def take_screenshot(self, page: Page, name: str):
        """Prend une capture d'écran pour debug"""
        try:
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = screenshots_dir / f"{name}_{timestamp}.png"
            
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"📸 Capture sauvegardée: {screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur capture écran: {e}")