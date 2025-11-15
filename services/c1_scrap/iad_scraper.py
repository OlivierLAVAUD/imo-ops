import asyncio
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Locator
import argparse


class CookieManager:
    """Gestionnaire spécialisé pour la bannière de cookies"""
    
    def __init__(self, page: Page):
        self.page = page
        self.cookie_selectors = [
            "#ppms_cm_consent_popup", ".ppms_cm_popup_overlay", 
            "#ppms_cm_popup_overlay", "div[data-root='true']", "[class*='ppms_cm']"
        ]
        self.refuse_selectors = [
            "button:has-text('Tout refuser')", "button:has-text('Refuser tout')",
            "button:has-text('Tout rejeter')", "button:has-text('Rejeter tout')",
            "button.ppms_cm_btn_reject_all", "button[data-consent-action='reject-all']",
            "[class*='reject-all']", "button:has-text('Refuser')"
        ]

    async def handle(self) -> bool:
        """Gère la bannière de cookies"""
        try:
            print("🍪 Traitement de la fenêtre cookies...")
            await self.page.wait_for_timeout(3000)

            if not await self._is_cookie_banner_present():
                print("✓ Aucune fenêtre cookies détectée")
                return True

            strategies = [
                self._strategy_refuse_buttons,
                self._strategy_javascript,
                self._strategy_escape_key
            ]

            for strategy in strategies:
                if await strategy():
                    return True

            print("❌ Impossible de fermer la fenêtre cookies")
            return False
            
        except Exception as e:
            print(f"⚠️ Erreur lors du traitement des cookies: {e}")
            return False

    async def _is_cookie_banner_present(self) -> bool:
        """Vérifie la présence de la bannière cookies"""
        for selector in self.cookie_selectors:
            banner = self.page.locator(selector)
            if await banner.count() > 0:
                return True
        return False

    async def _strategy_refuse_buttons(self) -> bool:
        """Stratégie principale: boutons 'Tout refuser'"""
        for selector in self.refuse_selectors:
            try:
                button = self.page.locator(selector)
                if await button.count() > 0 and await button.is_visible():
                    await button.click(force=True)
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue
        return False

    async def _strategy_javascript(self) -> bool:
        """Stratégie JavaScript pour les cas complexes"""
        js_scripts = [
            """() => { const btn = document.querySelector('button.ppms_cm_btn_reject_all'); if (btn) { btn.click(); return true; } return false; }""",
            """() => { const btn = document.querySelector('[data-consent-action="reject-all"]'); if (btn) { btn.click(); return true; } return false; }""",
            """() => { const buttons = Array.from(document.querySelectorAll('button')); const refuseBtn = buttons.find(btn => btn.textContent && (btn.textContent.includes('Tout refuser') || btn.textContent.includes('Refuser tout'))); if (refuseBtn) { refuseBtn.click(); return true; } return false; }"""
        ]
        
        for js_script in js_scripts:
            try:
                result = await self.page.evaluate(js_script)
                if result:
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue
        return False

    async def _strategy_escape_key(self) -> bool:
        """Dernier recours: touche Échap"""
        try:
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False


class DataExtractor:
    """Classe responsable de l'extraction des données"""
    
    def __init__(self, config: Dict[str, Any], context):
        self.config = config
        self.context = context

    async def extract_list_data(self, article_locator: Locator) -> Dict[str, Any]:
        """Extrait les données d'un article de la liste"""
        list_config = self.config['article_list_data']
        data = {'date_extraction': datetime.now().isoformat()}
        
        try:
            # Extraction des champs de base
            basic_fields = await self._extract_basic_fields(article_locator, list_config)
            data.update(basic_fields)
            
            # Extraction des caractéristiques seulement si on a un lien
            if data.get('lien'):
                features = await self._extract_features(article_locator, list_config)
                data.update(features)
                
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des données de liste: {e}")
        
        return data

    async def _extract_basic_fields(self, article_locator: Locator, config: Dict) -> Dict[str, Any]:
        """Extrait les champs de base d'un article"""
        fields = {}
        
        # Référence
        if 'reference' in config:
            ref_element = article_locator.locator(config['reference']['css_selector']).first
            if await ref_element.count() > 0:
                href = await ref_element.get_attribute('href')
                if href and 'regex' in config['reference']:
                    match = re.search(config['reference']['regex'], href)
                    if match:
                        fields['reference'] = match.group(1)

        # Titre et lien
        for field in ['titre', 'lien', 'prix']:
            if field in config:
                element = article_locator.locator(config[field]['css_selector']).first
                if await element.count() > 0:
                    if field == 'lien':
                        href = await element.get_attribute('href')
                        fields[field] = self._complete_url(href) if href else None
                    else:
                        text = await element.text_content()
                        fields[field] = text.strip() if text else None

        # Localisation extraite du titre
        if 'localisation' in config and fields.get('titre'):
            if 'regex' in config['localisation']:
                match = re.search(config['localisation']['regex'], fields['titre'])
                if match:
                    fields['localisation'] = match.group(1).strip()

        return {k: v for k, v in fields.items() if v is not None}

    async def _extract_features(self, article_locator: Locator, config: Dict) -> Dict[str, Any]:
        """Extrait les caractéristiques techniques"""
        features = {}
        
        # Caractéristiques complètes
        if 'caracteristiques' in config:
            elements = article_locator.locator(config['caracteristiques']['css_selector'])
            count = await elements.count()
            caracteristiques = []
            for i in range(count):
                text = await elements.nth(i).text_content()
                if text:
                    cleaned = text.replace('•', '').strip()
                    if cleaned:
                        caracteristiques.append(cleaned)
            if caracteristiques:
                features['caracteristiques'] = caracteristiques

        # Extraction pour surface, pièces, chambres
        for field in ['surface', 'pieces', 'chambres']:
            if field in config:
                value = await self._extract_feature(article_locator, config[field])
                if value:
                    features[field] = value

        # Badges
        if 'badges' in config:
            elements = article_locator.locator(config['badges']['css_selector'])
            count = await elements.count()
            badges = []
            for i in range(count):
                text = await elements.nth(i).text_content()
                if text and text.strip():
                    badges.append(text.strip())
            if badges:
                features['badges'] = badges

        # Image
        if 'image_url' in config:
            img_element = article_locator.locator(config['image_url']['css_selector']).first
            if await img_element.count() > 0:
                src = await img_element.get_attribute('src')
                if src:
                    features['image_url'] = src

        return features

    async def _extract_feature(self, article_locator: Locator, config: Dict) -> Optional[str]:
        """Extrait une caractéristique spécifique"""
        elements = article_locator.locator(config['css_selector'])
        count = await elements.count()
        
        for i in range(count):
            text = await elements.nth(i).text_content()
            if text:
                cleaned = text.replace('•', '').strip()
                # Vérifier les mots-clés si spécifiés
                keywords = config.get('keywords', [])
                if keywords and not any(keyword in text.lower() for keyword in keywords):
                    continue
                    
                if 'regex' in config:
                    match = re.search(config['regex'], cleaned)
                    if match:
                        suffix = config.get('suffix', '')
                        return match.group(1) + suffix
                else:
                    return cleaned
        return None

    def _complete_url(self, url: str) -> str:
        """Complète l'URL si nécessaire"""
        if url and not url.startswith('http'):
            base_url = self.config['site']['base_url']
            return base_url + url
        return url


class MediaExtractor:
    """Spécialisé dans l'extraction des médias"""
    
    @staticmethod
    async def extract_media_info(detail_page: Page) -> Dict[str, Any]:
        """Extrait les informations sur les médias"""
        media_data = {
            "nombre_photos": 0, "has_video": False, 
            "has_visite_virtuelle": False, "media_description": ""
        }
        
        try:
            media_button = detail_page.locator("button.iad-btn span.font-semibold")
            if await media_button.count() > 0:
                media_text = await media_button.text_content()
                if media_text:
                    media_data.update(MediaExtractor._parse_media_text(media_text))
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des infos médias: {e}")
        
        return media_data

    @staticmethod
    def _parse_media_text(media_text: str) -> Dict[str, Any]:
        """Parse le texte des médias pour en extraire les informations"""
        photos_match = re.search(r'(\d+)\s*photos?', media_text, re.IGNORECASE)
        return {
            "media_description": media_text.strip(),
            "nombre_photos": int(photos_match.group(1)) if photos_match else 0,
            "has_video": any(keyword in media_text.lower() for keyword in ['vidéo', 'video']),
            "has_visite_virtuelle": 'visite virtuelle' in media_text.lower()
        }


class IADFranceScraper:
    """Scraper principal pour IAD France"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self._load_config(config_file)
        self.results = []
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON"""
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def setup_browser(self):
        """Initialise le navigateur Playwright"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            slow_mo=100
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        self.cookie_manager = CookieManager(self.page)
        self.data_extractor = DataExtractor(self.config, self.context)
    
    async def navigate_to_site(self):
        """Navigation vers le site IAD France avec gestion des cookies"""
        try:
            print("🌐 Navigation vers le site...")
            await self.page.goto(self.config['site']['base_url'])
            await self.page.wait_for_timeout(self.config['site']['navigation_delay'])
            
            # Gérer la bannière cookies
            success = await self.cookie_manager.handle()
            if success:
                print("✓ Gestion des cookies réussie")
            else:
                print("⚠️ Problème avec les cookies, continuation...")
                
        except Exception as e:
            print(f"❌ Erreur lors de la navigation: {e}")
            raise
    
    async def fill_search_form(self, localisation: str = "Paris"):
        """Remplit le formulaire de recherche"""
        search_config = self.config['search_form']
        
        try:
            # Vérifier à nouveau les cookies avant de commencer
            await self.cookie_manager.handle()
            
            # Sélectionner le type de transaction
            transaction_config = search_config['transaction_type']['options']['acheter']
            await self.page.click(transaction_config['css_selector'], force=True)
            await self.page.wait_for_timeout(1000)
            print("✓ Type de transaction sélectionné: Acheter")
            
            # Sélectionner le type de bien
            type_bien_config = search_config['type_bien']['options']['ancien']
            await self.page.click(type_bien_config['css_selector'], force=True)
            await self.page.wait_for_timeout(1000)
            print("✓ Type de bien sélectionné: Ancien")
            
            # Remplir la localisation
            await self.page.fill(search_config['localisation']['input_css'], localisation)
            await self.page.wait_for_timeout(2000)
            
            # Sélectionner la première suggestion
            suggestions = self.page.locator(search_config['localisation']['suggestions_container']['items_css'])
            if await suggestions.count() > 0:
                await suggestions.first.click(force=True)
                await self.page.wait_for_timeout(1000)
            
            print("✓ Localisation remplie: " + localisation)
            
            # Soumettre le formulaire
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"❌ Erreur lors du remplissage du formulaire: {e}")
            raise

    async def scrape(self, localisation: str = "Paris", max_biens: int = None, max_pages: int = None):
        """Fonction principale de scraping"""
        max_pages = max_pages or self.config['scraping_strategy']['max_pages']
        max_biens = max_biens or self.config['scraping_strategy'].get('max_biens', float('inf'))
        
        try:
            await self.setup_browser()
            await self.navigate_to_site()
            await self.fill_search_form(localisation)
            
            all_data = await self._scrape_all_pages(max_pages, max_biens)
            await self.save_results_json(all_data)
            
            print(f"\n🎉 Scraping terminé! {len(all_data)} annonces extraites sur {max_biens} demandées")
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
        finally:
            await self.browser.close()
            await self.playwright.stop()

    async def _scrape_all_pages(self, max_pages: int, max_biens: int) -> List[Dict[str, Any]]:
        """Scrape toutes les pages"""
        all_data = []
        current_page = 1
        
        while current_page <= max_pages and len(all_data) < max_biens:
            print(f"\n🔍 Scraping de la page {current_page}...")
            
            page_data = await self._scrape_page(current_page, max_biens - len(all_data))
            
            if not page_data:
                print("ℹ️ Aucune donnée récupérée, arrêt du scraping.")
                break
            
            # Filtrer les données None
            valid_data = [data for data in page_data if data is not None]
            all_data.extend(valid_data)
            
            print(f"✓ Page {current_page} terminée - {len(valid_data)} articles extraits")
            print(f"📊 Total cumulé: {len(all_data)} biens sur {max_biens} demandés")
            
            if len(all_data) >= max_biens:
                print(f"🎯 Nombre maximum de biens ({max_biens}) atteint! Arrêt du scraping.")
                break
            
            if current_page < max_pages:
                if await self._go_to_next_page():
                    current_page += 1
                else:
                    print("ℹ️ Plus de pages disponibles, arrêt du scraping.")
                    break
            else:
                print("ℹ️ Nombre maximum de pages atteint, arrêt du scraping.")
                break
        
        return all_data

    async def _scrape_page(self, page_number: int, max_biens: int) -> List[Dict[str, Any]]:
        """Scrape une page de résultats"""
        page_data = []
        
        try:
            articles_config = self.config['search_results']['articles']
            await self.page.wait_for_selector(articles_config['css_selector'])
            
            articles = self.page.locator(articles_config['css_selector'])
            article_count = await articles.count()
            print(f"📄 Page {page_number} - {article_count} articles trouvés")
            
            # Limiter le nombre d'articles si nécessaire
            if max_biens is not None:
                article_count = min(article_count, max_biens)
                if article_count <= 0:
                    return page_data
            
            for i in range(article_count):
                try:
                    article_data = await self._process_single_article(articles.nth(i), i)
                    if article_data:  # Ne ajouter que si les données sont valides
                        page_data.append(article_data)
                    
                    # Délai entre les requêtes
                    delay = self.config['scraping_strategy']['delay_between_requests'] / 1000
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    print(f"❌ Erreur avec l'article {i+1}: {e}")
                    continue
                
        except Exception as e:
            print(f"❌ Erreur lors du scraping de la page {page_number}: {e}")
        
        return page_data

    async def _process_single_article(self, article_locator: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Traite un article individuel"""
        try:
            list_data = await self.data_extractor.extract_list_data(article_locator)
            
            if list_data and list_data.get('lien'):
                # Pour l'instant, on retourne seulement les données de liste
                # L'extraction des détails peut être ajoutée plus tard
                detail_data = await self._extract_detail_data(list_data['lien'])
                combined_data = {**list_data, **detail_data}
                
                print(f"✓ Article {index+1} traité - Ref: {combined_data.get('reference', 'N/A')}")
                return combined_data
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de l'article {index+1}: {e}")
            return None

    async def _extract_detail_data(self, url: str) -> Dict[str, Any]:
        """Extrait les données détaillées d'une annonce (version simplifiée)"""
        # Pour l'instant, retourner des données vides
        # Cette méthode peut être étendue pour extraire les détails complets
        return {
            "media_info": await MediaExtractor.extract_media_info(self.page)
        }

    async def _go_to_next_page(self) -> bool:
        """Passe à la page suivante"""
        pagination_config = self.config['search_results']['pagination']['next_page']
        
        try:
            next_buttons = self.page.locator(pagination_config['css_selector'])
            for i in range(await next_buttons.count()):
                button = next_buttons.nth(i)
                if await button.is_visible():
                    await button.click(force=True)
                    await self.page.wait_for_timeout(3000)
                    
                    # Vérifier que la navigation a fonctionné
                    await self.page.wait_for_selector(
                        self.config['search_results']['articles']['css_selector'], 
                        timeout=10000
                    )
                    print("✓ Navigation vers la page suivante réussie")
                    return True
            return False
            
        except Exception as e:
            print(f"❌ Erreur lors du passage à la page suivante: {e}")
            return False

    async def save_results_json(self, data: List[Dict[str, Any]]):
        """Sauvegarde les résultats dans un fichier JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iad_annonces_{timestamp}.json"
        
        # Créer le dossier results s'il n'existe pas
        os.makedirs('results', exist_ok=True)
        filepath = os.path.join('results', filename)
        
        # Filtrer les champs selon la configuration
        output_fields = self.config['output']['fields']
        filtered_data = [
            {field: item.get(field, "") for field in output_fields if field in item}
            for item in data
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON sauvegardé dans: {filepath}")


async def main():
    """Fonction principale d'exécution"""
    parser = argparse.ArgumentParser(description='Scraper IAD France')
    parser.add_argument('--localisation', type=str, default='Paris', 
                       help='Localisation pour la recherche')
    parser.add_argument('--max-biens', type=int, default=10, 
                       help='Nombre maximum de biens à scraper')
    parser.add_argument('--max-pages', type=int, default=10, 
                       help='Nombre maximum de pages à scraper')
    
    args = parser.parse_args()
    
    scraper = IADFranceScraper("config.json")
    
    print("🚀 Démarrage du scraping IAD France...")
    print(f"📍 Localisation: {args.localisation}")
    print(f"🏠 Nombre maximum de biens: {args.max_biens}")
    print(f"📄 Pages maximum: {args.max_pages}")
    
    await scraper.scrape(
        localisation=args.localisation, 
        max_biens=args.max_biens, 
        max_pages=args.max_pages
    )


if __name__ == "__main__":    
    asyncio.run(main())