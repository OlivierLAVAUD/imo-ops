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
            "#ppms_cm_consent_popup",
            ".ppms_cm_popup_overlay", 
            "#ppms_cm_popup_overlay",
            "div[data-root='true']",
            "[class*='ppms_cm']",
        ]
        self.refuse_selectors = [
            "button:has-text('Tout refuser')",
            "button:has-text('Refuser tout')", 
            "button:has-text('Tout rejeter')",
            "button:has-text('Rejeter tout')",
            "button.ppms_cm_btn_reject_all",
            "button[data-consent-action='reject-all']",
            "[class*='reject-all']",
            "button:has-text('Refuser')",
        ]
        self.close_selectors = [
            "button.ppms_cm_btn_close",
            "button[aria-label*='close']",
            "button[class*='close']",
            "button:has-text('Fermer')",
        ]

    async def handle(self) -> bool:
        """Gère la bannière de cookies avec stratégies multiples"""
        try:
            print("🍪 Traitement de la fenêtre cookies...")
            await self.page.wait_for_timeout(3000)

            if not await self._is_cookie_banner_present():
                print("✓ Aucune fenêtre cookies détectée")
                return True

            # Stratégies successives
            strategies = [
                self._strategy_refuse_buttons,
                self._strategy_javascript,
                self._strategy_close_buttons,
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
                print(f"✓ Fenêtre cookies détectée: {selector}")
                return True
        return False

    async def _strategy_refuse_buttons(self) -> bool:
        """Stratégie principale: boutons 'Tout refuser'"""
        print("🔄 Recherche du bouton 'Tout refuser'...")
        for selector in self.refuse_selectors:
            try:
                button = self.page.locator(selector)
                if await button.count() > 0 and await button.is_visible():
                    print(f"✓ Bouton 'Tout refuser' trouvé: {selector}")
                    await button.click(force=True)
                    print("✓ Cookies refusés avec succès")
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue
        return False

    async def _strategy_javascript(self) -> bool:
        """Stratégie JavaScript pour les cas complexes"""
        print("🔄 Tentative via JavaScript...")
        js_scripts = [
            self._js_find_refuse_buttons(),
            self._js_find_reject_class(),
            self._js_find_consent_action()
        ]
        
        for js_script in js_scripts:
            try:
                result = await self.page.evaluate(js_script)
                if result:
                    print("✓ 'Tout refuser' cliqué via JavaScript")
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue
        return False

    async def _strategy_close_buttons(self) -> bool:
        """Stratégie de secours: boutons de fermeture"""
        print("🔄 Bouton 'Tout refuser' non trouvé, méthodes alternatives...")
        for selector in self.close_selectors:
            try:
                button = self.page.locator(selector)
                if await button.count() > 0 and await button.is_visible():
                    await button.click(force=True)
                    print("✓ Fenêtre fermée (méthode alternative)")
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue
        return False

    async def _strategy_escape_key(self) -> bool:
        """Dernier recours: touche Échap"""
        print("🔄 Dernières tentatives...")
        try:
            await self.page.keyboard.press('Escape')
            print("✓ Touche Échap pressée")
            await self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

    def _js_find_refuse_buttons(self) -> str:
        return """() => { 
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                if (btn.textContent.includes('Tout refuser') || btn.textContent.includes('Refuser tout')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }"""

    def _js_find_reject_class(self) -> str:
        return """() => { 
            const rejectBtn = document.querySelector('button.ppms_cm_btn_reject_all');
            if (rejectBtn) {
                rejectBtn.click();
                return true;
            }
            return false;
        }"""

    def _js_find_consent_action(self) -> str:
        return """() => {
            const rejectBtn = document.querySelector('[data-consent-action="reject-all"]');
            if (rejectBtn) {
                rejectBtn.click();
                return true;
            }
            return false;
        }"""


class DataExtractor:
    """Classe responsable de l'extraction des données"""
    
    def __init__(self, config: Dict[str, Any], context):
        self.config = config
        self.context = context

    def clean_css_selector_for_xpath(self, css_selector: str) -> str:
        """Convertit un sélecteur CSS en XPath simplifié"""
        if ':contains(' in css_selector:
            parts = css_selector.split(':contains')
            tag = parts[0].strip() or '*'
            text = parts[1].split('"')[1] if '"' in parts[1] else parts[1].split("'")[1]
            return f"//{tag}[contains(text(), '{text}')]"
        elif '.' in css_selector and ':contains' not in css_selector:
            tag = css_selector.split('.')[0] or '*'
            classes = css_selector.split('.')[1]
            return f"//{tag}[contains(@class, '{classes}')]"
        return css_selector

    async def extract_list_data(self, article_locator: Locator) -> Dict[str, Any]:
        """Extrait les données d'un article de la liste"""
        list_config = self.config['article_list_data']
        data = {}
        
        try:
            # Extraction des champs de base
            data.update(await self._extract_basic_fields(article_locator, list_config))
            
            # Extraction des caractéristiques
            data.update(await self._extract_features(article_locator, list_config))
            
            # Date d'extraction
            data['date_extraction'] = datetime.now().isoformat()
            
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
        if 'titre' in config:
            titre_element = article_locator.locator(config['titre']['css_selector']).first
            if await titre_element.count() > 0:
                fields['titre'] = await titre_element.text_content()

        if 'lien' in config:
            lien_element = article_locator.locator(config['lien']['css_selector']).first
            if await lien_element.count() > 0:
                fields['lien'] = await lien_element.get_attribute('href')
                if fields['lien'] and not fields['lien'].startswith('http'):
                    fields['lien'] = self.config['site']['base_url'] + fields['lien']

        # Prix
        if 'prix' in config:
            prix_element = article_locator.locator(config['prix']['css_selector']).first
            if await prix_element.count() > 0:
                fields['prix'] = await prix_element.text_content()

        # Localisation extraite du titre
        if 'localisation' in config and 'titre' in fields:
            if 'regex' in config['localisation']:
                match = re.search(config['localisation']['regex'], fields['titre'])
                if match:
                    fields['localisation'] = match.group(1).strip()

        return fields

    async def _extract_features(self, article_locator: Locator, config: Dict) -> Dict[str, Any]:
        """Extrait les caractéristiques techniques avec la nouvelle structure"""
        features = {}
        
        # Caractéristiques complètes
        if 'caracteristiques' in config:
            carac_elements = article_locator.locator(config['caracteristiques']['css_selector'])
            features['caracteristiques'] = []
            for i in range(await carac_elements.count()):
                text = await carac_elements.nth(i).text_content()
                if text:
                    # Nettoyer le texte (supprimer les •)
                    cleaned_text = text.replace('•', '').strip()
                    if cleaned_text:
                        features['caracteristiques'].append(cleaned_text)
        
        # Surface - nouvelle méthode
        if 'surface' in config:
            surface_elements = article_locator.locator(config['surface']['css_selector'])
            for i in range(await surface_elements.count()):
                text = await surface_elements.nth(i).text_content()
                if text and 'm²' in text:
                    cleaned_text = text.replace('•', '').strip()
                    if 'regex' in config['surface']:
                        match = re.search(config['surface']['regex'], cleaned_text)
                        if match:
                            features['surface'] = match.group(1) + " m²"
                            break
                    else:
                        features['surface'] = cleaned_text
        
        # Pièces - filtrer en Python
        if 'pieces' in config:
            pieces_elements = article_locator.locator(config['pieces']['css_selector'])
            for i in range(await pieces_elements.count()):
                text = await pieces_elements.nth(i).text_content()
                if text and 'pièces' in text:
                    cleaned_text = text.replace('•', '').strip()
                    if 'regex' in config['pieces']:
                        match = re.search(config['pieces']['regex'], cleaned_text)
                        if match:
                            features['pieces'] = match.group(1) + " pièces"
                            break
                    else:
                        features['pieces'] = cleaned_text
        
        # Chambres - filtrer en Python
        if 'chambres' in config:
            chambres_elements = article_locator.locator(config['chambres']['css_selector'])
            for i in range(await chambres_elements.count()):
                text = await chambres_elements.nth(i).text_content()
                if text and 'chambre' in text:
                    cleaned_text = text.replace('•', '').strip()
                    if 'regex' in config['chambres']:
                        match = re.search(config['chambres']['regex'], cleaned_text)
                        if match:
                            features['chambres'] = match.group(1) + " chambres"
                            break
                    else:
                        features['chambres'] = cleaned_text
                    
        # Badges
        if 'badges' in config:
            badges_elements = article_locator.locator(config['badges']['css_selector'])
            features['badges'] = []
            for i in range(await badges_elements.count()):
                text = await badges_elements.nth(i).text_content()
                if text and text.strip():
                    features['badges'].append(text.strip())
        
        # Image
        if 'image_url' in config:
            img_element = article_locator.locator(config['image_url']['css_selector']).first
            if await img_element.count() > 0:
                features['image_url'] = await img_element.get_attribute('src')

        return features

    async def _extract_feature_by_keyword(self, article_locator: Locator, keywords, config: Dict) -> Optional[str]:
        """Extrait une caractéristique basée sur des mots-clés"""
        if not isinstance(keywords, list):
            keywords = [keywords]
            
        elements = article_locator.locator('li')
        for i in range(await elements.count()):
            text = await elements.nth(i).text_content()
            if text and any(keyword in text.lower() for keyword in keywords):
                if 'regex' in config:
                    match = re.search(config['regex'], text)
                    if match:
                        return match.group(1) + " " + keywords[0].replace('s', '').strip()
                else:
                    return text.strip()
        return None

    async def _extract_copropriete_info(self, detail_page: Page) -> Dict[str, Any]:
        """Extrait les informations sur la copropriété"""
        copro_data = {
            "copropriete_nb_lots": "",
            "copropriete_charges_previsionnelles": "",
            "copropriete_procedures": ""
        }
        
        try:
            # Vérifier si la configuration existe pour la copropriété
            if 'copropriete' not in self.config['detail_page']['data']:
                return copro_data
                
            copro_config = self.config['detail_page']['data']['copropriete']
            
            # Extraire le nombre de lots
            if 'nb_lots' in copro_config:
                nb_lots = await self._extract_copro_field(detail_page, copro_config['nb_lots'])
                if nb_lots:
                    copro_data['copropriete_nb_lots'] = nb_lots
            
            # Extraire les charges prévisionnelles
            if 'charges_previsionnelles' in copro_config:
                charges = await self._extract_copro_field(detail_page, copro_config['charges_previsionnelles'])
                if charges:
                    copro_data['copropriete_charges_previsionnelles'] = charges
            
            # Extraire les procédures
            if 'procedures' in copro_config:
                procedures = await self._extract_copro_field(detail_page, copro_config['procedures'])
                if procedures:
                    copro_data['copropriete_procedures'] = procedures
            
            print(f"🏢 Copropriété: Lots={copro_data['copropriete_nb_lots'] or 'N/A'}, Charges={copro_data['copropriete_charges_previsionnelles'] or 'N/A'}")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des infos copropriété: {e}")
        
        return copro_data

    async def _extract_copro_field(self, detail_page: Page, config: Dict) -> Optional[str]:
        """Extrait un champ individuel pour la copropriété"""
        selector = config['css_selector']
        
        try:
            # Méthode 1: Essayer le sélecteur CSS directement (Playwright supporte :contains())
            elements = detail_page.locator(selector)
            
            if await elements.count() > 0:
                value = await self._get_copro_element_value(elements.first, config)
                return value if value else None
            
            # Méthode 2: Si CSS échoue, essayer XPath
            if 'xpath' in config:
                elements = detail_page.locator(f"xpath={config['xpath']}")
                if await elements.count() > 0:
                    value = await self._get_copro_element_value(elements.first, config)
                    return value if value else None
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur avec le sélecteur {selector}: {e}")
            # Dernière tentative avec XPath
            if 'xpath' in config:
                try:
                    elements = detail_page.locator(f"xpath={config['xpath']}")
                    if await elements.count() > 0:
                        value = await self._get_copro_element_value(elements.first, config)
                        return value if value else None
                except Exception as xpath_error:
                    print(f"⚠️ Erreur avec le XPath de fallback: {xpath_error}")
            return None

    async def _get_copro_element_value(self, element: Locator, config: Dict) -> Optional[str]:
        """Récupère la valeur d'un élément pour la copropriété"""
        if 'attribute' in config:
            value = await element.get_attribute(config['attribute'])
        else:
            value = await element.text_content()
        
        if value and 'regex' in config:
            match = re.search(config['regex'], value)
            if match:
                value = match.group(1)
        
        return value.strip() if value else None

    async def _extract_conseiller_info(self, detail_page: Page) -> Dict[str, Any]:
        """Extrait les informations détaillées du conseiller"""
        conseiller_data = {
            "conseiller_nom_complet": "",
            "conseiller_telephone": "",
            "conseiller_lien": "",
            "conseiller_photo": "",
            "conseiller_note": "",
            "conseiller_nombre_avis": ""
        }
        
        try:
            # Vérifier si la configuration existe pour le conseiller
            if 'conseiller' not in self.config['detail_page']['data']:
                return conseiller_data
                
            conseiller_config = self.config['detail_page']['data']['conseiller']
            
            # Extraire le nom complet
            if 'nom_conseiller' in conseiller_config:
                nom = await self._extract_copro_field(detail_page, conseiller_config['nom_conseiller'])
                if nom:
                    conseiller_data['conseiller_nom_complet'] = nom
            
            # Extraire le téléphone
            if 'telephone_conseiller' in conseiller_config:
                telephone = await self._extract_copro_field(detail_page, conseiller_config['telephone_conseiller'])
                if telephone:
                    conseiller_data['conseiller_telephone'] = telephone
            
            # Extraire le lien
            if 'lien_conseiller' in conseiller_config:
                lien = await self._extract_copro_field(detail_page, conseiller_config['lien_conseiller'])
                if lien:
                    conseiller_data['conseiller_lien'] = lien
                    # Compléter l'URL si nécessaire
                    if conseiller_data['conseiller_lien'] and not conseiller_data['conseiller_lien'].startswith('http'):
                        conseiller_data['conseiller_lien'] = self.config['site']['base_url'] + conseiller_data['conseiller_lien']
            
            # Extraire la photo
            if 'photo_conseiller' in conseiller_config:
                photo = await self._extract_copro_field(detail_page, conseiller_config['photo_conseiller'])
                if photo:
                    conseiller_data['conseiller_photo'] = photo
            
            # Extraire la note
            if 'note_conseiller' in conseiller_config:
                note = await self._extract_copro_field(detail_page, conseiller_config['note_conseiller'])
                if note:
                    conseiller_data['conseiller_note'] = note
            
            # Extraire le nombre d'avis
            if 'nombre_avis' in conseiller_config:
                avis = await self._extract_copro_field(detail_page, conseiller_config['nombre_avis'])
                if avis:
                    conseiller_data['conseiller_nombre_avis'] = avis
            
            print(f"👤 Conseiller: {conseiller_data['conseiller_nom_complet'] or 'N/A'}, Tél: {conseiller_data['conseiller_telephone'] or 'N/A'}")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des infos conseiller: {e}")
        
        return conseiller_data


class MediaExtractor:
    """Spécialisé dans l'extraction des médias"""
    
    @staticmethod
    async def extract_media_info(detail_page: Page) -> Dict[str, Any]:
        """Extrait les informations sur les médias"""
        media_data = {
            "nombre_photos": 0,
            "has_video": False,
            "has_visite_virtuelle": False,
            "media_description": ""
        }
        
        try:
            media_button = detail_page.locator("button.iad-btn span.font-semibold")
            
            if await media_button.count() > 0:
                media_text = await media_button.text_content()
                if media_text:
                    media_data.update(MediaExtractor._parse_media_text(media_text))
                    print(f"📊 Médias détectés: {media_text}")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des infos médias: {e}")
        
        return media_data

    @staticmethod
    def _parse_media_text(media_text: str) -> Dict[str, Any]:
        """Parse le texte des médias pour en extraire les informations"""
        result = {
            "media_description": media_text.strip(),
            "nombre_photos": 0,
            "has_video": False,
            "has_visite_virtuelle": False
        }
        
        # Extraire le nombre de photos
        photos_match = re.search(r'(\d+)\s*photos?', media_text, re.IGNORECASE)
        if photos_match:
            result["nombre_photos"] = int(photos_match.group(1))
        
        # Détecter vidéo et visite virtuelle
        result["has_video"] = any(keyword in media_text.lower() for keyword in ['vidéo', 'video'])
        result["has_visite_virtuelle"] = 'visite virtuelle' in media_text.lower()
        
        return result

    @staticmethod
    async def extract_all_photos(detail_page: Page) -> Dict[str, Any]:
        """Extrait toutes les photos en haute qualité"""
        photos_data = {
            "toutes_les_photos": [],
            "galerie_photos": [],
            "nombre_photos_reel": 0
        }
        
        try:
            photo_elements = detail_page.locator("ul.flex-col li img")
            count = await photo_elements.count()
            
            if count > 0:
                photos_data["nombre_photos_reel"] = count
                
                for i in range(count):
                    img_element = photo_elements.nth(i)
                    src = await img_element.get_attribute("src")
                    alt = await img_element.get_attribute("alt") or ""
                    
                    if src:
                        high_quality_url = MediaExtractor.clean_photo_url(src)
                        
                        photo_info = {
                            "url": high_quality_url,
                            "url_original": src,
                            "alt": alt,
                            "ordre": i + 1,
                            "description": f"Photo {i + 1}/{count}"
                        }
                        
                        photos_data["toutes_les_photos"].append(high_quality_url)
                        photos_data["galerie_photos"].append(photo_info)
                
                print(f"📸 {count} photos extraites depuis la galerie")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des photos: {e}")
        
        return photos_data

    @staticmethod
    def clean_photo_url(url: str) -> str:
        """Nettoie l'URL de la photo pour obtenir la meilleure qualité"""
        if not url:
            return url
        
        # Supprimer les paramètres de taille pour obtenir l'image originale
        if "?format=auto&width=" in url:
            url = url.split("?format=auto&width=")[0] + "?format=auto"
        
        # Remplacer par une qualité plus élevée
        if "width=390" in url:
            url = url.replace("width=390", "width=1200")
        elif "width=780" in url:
            url = url.replace("width=780", "width=1200")
        
        return url


class PerformanceEnergetiqueExtractor:
    """Spécialisé dans l'extraction des performances énergétiques"""
    
    @staticmethod
    async def extract_performances_energetiques(detail_page: Page) -> Dict[str, Any]:
        """Extraction complète des performances énergétiques basée sur l'analyse d'accessibilité"""
        perf_data = {
            "dpe_classe_active": "",
            "ges_classe_active": "",
            "dpe_consommation_energie_primaire": "",
            "dpe_consommation_energie_finale": "",
            "dpe_emissions": "",
            "ges_emissions": "",
            "depenses_energie_min": "",
            "depenses_energie_max": "",
            "legende_dpe": [],
            "legende_ges": [],
            "annee_reference": "2025"
        }
        
        try:
            # Section principale des performances énergétiques
            section_perf = detail_page.locator("section.flex")
            if await section_perf.count() > 0:
                print("📊 Extraction des performances énergétiques...")
                
                # Titre de la section
                titre_section = section_perf.locator("h3").first
                if await titre_section.count() > 0:
                    perf_data["titre_section"] = await titre_section.text_content()
                
                # DPE - Classe active (avec bordure blanche)
                dpe_section = detail_page.locator("div.group-\\[\\.is-prestige\\]\\:flex-col > div:nth-child(1)")
                if await dpe_section.count() > 0:
                    await PerformanceEnergetiqueExtractor._extract_dpe_data(dpe_section, perf_data)
                
                # GES - Classe active (avec bordure blanche)
                ges_section = detail_page.locator("div.group-\\[\\.is-prestige\\]\\:flex-col > div:nth-child(2)")
                if await ges_section.count() > 0:
                    await PerformanceEnergetiqueExtractor._extract_ges_data(ges_section, perf_data)
                
                # Détails DPE (consommations et émissions)
                await PerformanceEnergetiqueExtractor._extract_details_dpe(detail_page, perf_data)
                
                # Détails GES (émissions)
                await PerformanceEnergetiqueExtractor._extract_details_ges(detail_page, perf_data)
                
                # Dépenses énergétiques estimées
                await PerformanceEnergetiqueExtractor._extract_depenses_energie(detail_page, perf_data)
                
                # Légendes
                await PerformanceEnergetiqueExtractor._extract_legendes(detail_page, perf_data)
                
                print(f"✅ Performances énergétiques extraites - DPE: {perf_data.get('dpe_classe_active', 'N/A')}, GES: {perf_data.get('ges_classe_active', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des performances énergétiques: {e}")
        
        return perf_data

    @staticmethod
    async def _extract_dpe_data(dpe_section: Locator, perf_data: Dict[str, Any]):
        """Extrait les données DPE"""
        try:
            # Description DPE
            dpe_desc = dpe_section.locator("p").first
            if await dpe_desc.count() > 0:
                perf_data["dpe_description"] = await dpe_desc.text_content()
            
            # Classe DPE active (avec bordure blanche)
            dpe_classe_active = dpe_section.locator("li.border-white span").first
            if await dpe_classe_active.count() > 0:
                perf_data["dpe_classe_active"] = await dpe_classe_active.text_content()
            
        except Exception as e:
            print(f"⚠️ Erreur extraction DPE: {e}")

    @staticmethod
    async def _extract_ges_data(ges_section: Locator, perf_data: Dict[str, Any]):
        """Extrait les données GES"""
        try:
            # Description GES
            ges_desc = ges_section.locator("p").first
            if await ges_desc.count() > 0:
                perf_data["ges_description"] = await ges_desc.text_content()
            
            # Classe GES active (avec bordure blanche)
            ges_classe_active = ges_section.locator("li.border-white span").first
            if await ges_classe_active.count() > 0:
                perf_data["ges_classe_active"] = await ges_classe_active.text_content()
            
        except Exception as e:
            print(f"⚠️ Erreur extraction GES: {e}")

    @staticmethod
    async def _extract_details_dpe(detail_page: Page, perf_data: Dict[str, Any]):
        """Extrait les détails DPE (consommations et émissions)"""
        try:
            dpe_details = detail_page.locator(".border-epc-C")
            if await dpe_details.count() > 0:
                # Consommation énergie primaire
                energie_primaire = dpe_details.locator("p.flex span.text-base").first
                if await energie_primaire.count() > 0:
                    perf_data["dpe_consommation_energie_primaire"] = await energie_primaire.text_content()
                
                # Consommation énergie finale
                energie_finale = dpe_details.locator("span.text-base:nth-child(4)")
                if await energie_finale.count() > 0:
                    perf_data["dpe_consommation_energie_finale"] = await energie_finale.text_content()
                
                # Émissions
                emissions = dpe_details.locator("p.grid span.text-base")
                if await emissions.count() > 0:
                    perf_data["dpe_emissions"] = await emissions.text_content()
                
        except Exception as e:
            print(f"⚠️ Erreur extraction détails DPE: {e}")

    @staticmethod
    async def _extract_details_ges(detail_page: Page, perf_data: Dict[str, Any]):
        """Extrait les détails GES (émissions)"""
        try:
            ges_details = detail_page.locator(".border-ges-A")
            if await ges_details.count() > 0:
                # Émissions GES
                emissions_ges = ges_details.locator("p.grid span.text-base")
                if await emissions_ges.count() > 0:
                    perf_data["ges_emissions"] = await emissions_ges.text_content()
                
        except Exception as e:
            print(f"⚠️ Erreur extraction détails GES: {e}")

    @staticmethod
    async def _extract_depenses_energie(detail_page: Page, perf_data: Dict[str, Any]):
        """Extrait les dépenses énergétiques estimées"""
        try:
            # Dépenses minimum
            depenses_min = detail_page.locator("div.text-sm:nth-child(3) > p:nth-child(1)")
            if await depenses_min.count() > 0:
                text_min = await depenses_min.text_content()
                if text_min:
                    match = re.search(r'(\d+\s*€)', text_min)
                    if match:
                        perf_data["depenses_energie_min"] = match.group(1)
            
            # Dépenses maximum
            depenses_max = detail_page.locator("div.text-sm:nth-child(3) > p:nth-child(2)")
            if await depenses_max.count() > 0:
                text_max = await depenses_max.text_content()
                if text_max:
                    match = re.search(r'(\d+\s*€)', text_max)
                    if match:
                        perf_data["depenses_energie_max"] = match.group(1)
                        
        except Exception as e:
            print(f"⚠️ Erreur extraction dépenses énergie: {e}")

    @staticmethod
    async def _extract_legendes(detail_page: Page, perf_data: Dict[str, Any]):
        """Extrait les légendes DPE et GES"""
        try:
            # Légendes DPE
            legendes_dpe = detail_page.locator("div.gap-s:nth-child(1) em")
            perf_data["legende_dpe"] = []
            for i in range(await legendes_dpe.count()):
                legende = await legendes_dpe.nth(i).text_content()
                if legende:
                    perf_data["legende_dpe"].append(legende.strip())
            
            # Légendes GES
            legendes_ges = detail_page.locator(".xl\\:grid-cols-2 > div:nth-child(2) em")
            perf_data["legende_ges"] = []
            for i in range(await legendes_ges.count()):
                legende = await legendes_ges.nth(i).text_content()
                if legende:
                    perf_data["legende_ges"].append(legende.strip())
                    
        except Exception as e:
            print(f"⚠️ Erreur extraction légendes: {e}")


class IADFranceScraper:
    """Scraper principal pour IAD France"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.results = []
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
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
        
    async def close_browser(self):
        """Ferme le navigateur"""
        await self.browser.close()
        await self.playwright.stop()
    
    async def navigate_to_site(self):
        """Navigation vers le site IAD France avec gestion des cookies"""
        site_config = self.config['site']
        
        try:
            print("🌐 Navigation vers le site...")
            await self.page.goto(site_config['base_url'])
            await self.page.wait_for_timeout(site_config['navigation_delay'])
            
            # Gérer la bannière cookies
            success = await self.cookie_manager.handle()
            if success:
                print("✓ Gestion des cookies réussie")
            else:
                print("⚠️ Problème avec les cookies, continuation...")
            
            print("✓ Navigation vers le site réussie")
            
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
            await self._fill_localisation(localisation, search_config['localisation'])
            
            # Soumettre le formulaire
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"❌ Erreur lors du remplissage du formulaire: {e}")
            raise

    async def _fill_localisation(self, localisation: str, config: Dict):
        """Remplit le champ de localisation"""
        await self.page.fill(config['input_css'], localisation)
        await self.page.wait_for_timeout(2000)
        
        # Sélectionner la première suggestion
        suggestions = self.page.locator(config['suggestions_container']['items_css'])
        if await suggestions.count() > 0:
            await suggestions.first.click(force=True)
            await self.page.wait_for_timeout(1000)
        
        print("✓ Localisation remplie: " + localisation)

    async def extract_detail_data(self, url: str) -> Dict[str, Any]:
        """Extrait les données détaillées d'une annonce"""
        detail_config = self.config['detail_page']['data']
        data = {}
        
        print(f"🔍 Extraction des détails pour: {url}")
        
        try:
            # Créer une nouvelle page pour les détails
            detail_page = await self.context.new_page()
            await detail_page.goto(url)
            
            # Attendre le chargement de la page
            wait_config = self.config['detail_page']['wait_for']
            await detail_page.wait_for_selector(wait_config['css_selector'], timeout=wait_config['timeout'])
            
            # Extraire les informations sur les médias en premier
            print("📊 Extraction des informations médias...")
            media_data = await MediaExtractor.extract_media_info(detail_page)
            data.update(media_data)
            
            # Extraire les performances énergétiques
            print("📊 Extraction des performances énergétiques...")
            perf_data = await PerformanceEnergetiqueExtractor.extract_performances_energetiques(detail_page)
            data.update(perf_data)
            
            # Extraire TOUTES les photos
            print("📸 Extraction de toutes les photos...")
            photos_data = await MediaExtractor.extract_all_photos(detail_page)
            data.update(photos_data)
            
            # S'assurer que le nombre de photos est cohérent
            if data.get("nombre_photos_reel", 0) > 0 and data.get("nombre_photos", 0) == 0:
                data["nombre_photos"] = data["nombre_photos_reel"]
            
            # Extraire les autres données détaillées
            other_data = await self._extract_other_detail_fields(detail_page, detail_config)
            data.update(other_data)
            
            # Fermer la page de détail
            await detail_page.close()
            print(f"✓ Données détaillées extraites pour {url}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des données détaillées: {e}")
        
        return data

    async def _extract_other_detail_fields(self, detail_page: Page, detail_config: Dict) -> Dict[str, Any]:
        """Extrait les autres champs détaillés"""
        data = {}
        champs_extraits = 0
        champs_manquants = []
        
        for field, config in detail_config.items():
            try:
                if 'css_selector' not in config:
                    continue
                    
                # Ignorer les champs déjà extraits
                if field in data:
                    champs_extraits += 1
                    continue
                    
                # Gestion spéciale pour les honoraires
                if field == 'honoraires':
                    data[field] = ""
                    champs_extraits += 1
                    continue
                
                value = await self._extract_single_field(detail_page, config)
                if value is not None:
                    data[field] = value
                    champs_extraits += 1
                else:
                    champs_manquants.append(field)
                    data[field] = ""
                    
            except Exception as e:
                if field not in ['reference', 'titre_complet', 'prix_detaille']:
                    data[field] = ""
                    champs_manquants.append(field)
                else:
                    print(f"⚠️ Erreur pour le champ {field}: {e}")
                    champs_manquants.append(field)
                    data[field] = ""
        
        # Extraction des informations de copropriété
        print("🏢 Extraction des informations de copropriété...")
        copro_data = await self.data_extractor._extract_copropriete_info(detail_page)
        data.update(copro_data)
        champs_extraits += len(copro_data)
        
        # AJOUT: Extraction des informations du conseiller
        print("👤 Extraction des informations du conseiller...")
        conseiller_data = await self.data_extractor._extract_conseiller_info(detail_page)
        data.update(conseiller_data)
        champs_extraits += len(conseiller_data)
        
        print(f"✅ {champs_extraits} champs extraits, {len(champs_manquants)} manquants")
        return data

    async def _extract_single_field(self, detail_page: Page, config: Dict) -> Optional[str]:
        """Extrait un champ individuel"""
        selector = config['css_selector']
        
        if ':contains(' in selector:
            xpath_selector = self.data_extractor.clean_css_selector_for_xpath(selector)
            elements = detail_page.locator(f"xpath={xpath_selector}")
        else:
            elements = detail_page.locator(selector)
        
        if config.get('multiple', False):
            return await self._extract_multiple_values(elements, config)
        else:
            return await self._extract_single_value(elements, config)

    async def _extract_multiple_values(self, elements: Locator, config: Dict) -> List[str]:
        """Extrait plusieurs valeurs pour un champ"""
        values = []
        count = await elements.count()
        
        if count > 0:
            for i in range(count):
                value = await self._get_element_value(elements.nth(i), config)
                if value:
                    values.append(value)
        
        return values if values else None

    async def _extract_single_value(self, elements: Locator, config: Dict) -> Optional[str]:
        """Extrait une valeur unique pour un champ"""
        if await elements.count() > 0:
            value = await self._get_element_value(elements.first, config)
            return value if value else None
        return None

    async def _get_element_value(self, element: Locator, config: Dict) -> Optional[str]:
        """Récupère la valeur d'un élément selon la configuration"""
        if 'attribute' in config:
            value = await element.get_attribute(config['attribute'])
        else:
            value = await element.text_content()
        
        if value and 'regex' in config:
            match = re.search(config['regex'], value)
            if match:
                value = match.group(1)
        
        return value.strip() if value else None

    async def scrape_page(self, page_number: int = 1, max_biens: int = None) -> List[Dict[str, Any]]:
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
                article_count = min(article_count, max_biens - len(self.results))
                if article_count <= 0:
                    return page_data
            
            for i in range(article_count):
                try:
                    article_data = await self._process_single_article(articles.nth(i), i)
                    if article_data:
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
        list_data = await self.data_extractor.extract_list_data(article_locator)
        
        if list_data and 'lien' in list_data:
            detail_data = await self.extract_detail_data(list_data['lien'])
            combined_data = {**list_data, **detail_data}
            
            # Afficher un résumé
            media_info = f"Photos: {combined_data.get('nombre_photos', 0)}"
            if combined_data.get('has_video'):
                media_info += ", Vidéo"
            if combined_data.get('has_visite_virtuelle'):
                media_info += ", Visite virtuelle"
            
            print(f"✓ Article {index+1} traité - Ref: {combined_data.get('reference', 'N/A')} - {media_info}")
            
            return combined_data
        
        return None

    async def scrape(self, localisation: str = "Paris", max_biens: int = None, max_pages: int = None):
        """Fonction principale de scraping"""
        if max_pages is None:
            max_pages = self.config['scraping_strategy']['max_pages']
        
        if max_biens is None:
            max_biens = self.config['scraping_strategy'].get('max_biens', float('inf'))
        
        try:
            await self.setup_browser()
            await self.navigate_to_site()
            await self.fill_search_form(localisation)
            
            all_data = await self._scrape_all_pages(max_pages, max_biens)
            
            # Sauvegarder les résultats
            json_filename = await self.save_results_json(all_data)
            print(f"\n🎉 Scraping terminé! {len(all_data)} annonces extraites sur {max_biens} demandées")
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
        finally:
            await self.close_browser()

    async def _scrape_all_pages(self, max_pages: int, max_biens: int) -> List[Dict[str, Any]]:
        """Scrape toutes les pages avec gestion de la pagination"""
        all_data = []
        current_page = 1
        
        while current_page <= max_pages and len(all_data) < max_biens:
            print(f"\n🔍 Scraping de la page {current_page}...")
            
            biens_restants = max_biens - len(all_data)
            page_data = await self.scrape_page(current_page, max_biens=biens_restants)
            
            if not page_data:
                print("ℹ️ Aucune donnée récupérée, arrêt du scraping.")
                break
            
            all_data.extend(page_data)
            print(f"✓ Page {current_page} terminée - {len(page_data)} articles extraits")
            print(f"📊 Total cumulé: {len(all_data)} biens sur {max_biens} demandés")
            
            # Vérifier si on doit continuer
            if len(all_data) >= max_biens:
                print(f"🎯 Nombre maximum de biens ({max_biens}) atteint! Arrêt du scraping.")
                break
            
            # Vérifier s'il y a une page suivante
            if current_page < max_pages:
                has_next_page = await self.has_next_page()
                if has_next_page:
                    success = await self.go_to_next_page()
                    if success:
                        current_page += 1
                    else:
                        print("❌ Impossible d'accéder à la page suivante, arrêt du scraping.")
                        break
                else:
                    print("ℹ️ Plus de pages disponibles, arrêt du scraping.")
                    break
            else:
                print("ℹ️ Nombre maximum de pages atteint, arrêt du scraping.")
                break
        
        return all_data

    async def has_next_page(self) -> bool:
        """Vérifie s'il y a une page suivante"""
        pagination_config = self.config['search_results']['pagination']['next_page']
        try:
            # Eviter les problèmes de sélecteurs multiples
            next_buttons = self.page.locator(pagination_config['css_selector'])
            count = await next_buttons.count()
            
            if count == 0:
                return False
                
            # Vérifier si le bouton est actif et visible
            for i in range(count):
                button = next_buttons.nth(i)
                if await button.is_visible():
                    # Vérifier si c'est bien le bouton "suivant" et non "précédent"
                    text = await button.text_content() or ""
                    href = await button.get_attribute('href') or ""
                    
                    if 'next' in href or 'suivant' in text.lower() or ('page=' in href and str(int(re.search(r'page=(\d+)', href).group(1)) if re.search(r'page=(\d+)', href) else '0') > '1'):
                        return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la vérification de la page suivante: {e}")
            return False

    async def go_to_next_page(self) -> bool:
        """Passe à la page suivante avec gestion d'erreur améliorée"""
        pagination_config = self.config['search_results']['pagination']['next_page']
        
        try:
            # Attendre que la page soit stable
            await self.page.wait_for_timeout(2000)
            
            # Utiliser une approche plus spécifique pour éviter les clics sur mauvais éléments
            next_buttons = self.page.locator(pagination_config['css_selector'])
            count = await next_buttons.count()
            
            if count == 0:
                print("❌ Aucun bouton de pagination trouvé")
                return False
            
            # Trouver le bon bouton "suivant"
            target_button = None
            for i in range(count):
                button = next_buttons.nth(i)
                if await button.is_visible():
                    href = await button.get_attribute('href') or ""
                    text = await button.text_content() or ""
                    
                    # Identifier le vrai bouton "suivant"
                    if 'next' in href or 'suivant' in text.lower() or ('page=' in href and self._is_next_page_url(href)):
                        target_button = button
                        break
            
            if not target_button:
                print("❌ Bouton 'suivant' non trouvé parmi les éléments de pagination")
                return False
            
            # Cliquer sur le bon bouton
            await target_button.click(force=True)
            await self.page.wait_for_timeout(3000)
            
            # Vérifier que la navigation a fonctionné
            await self.page.wait_for_selector(self.config['search_results']['articles']['css_selector'], timeout=10000)
            print("✓ Navigation vers la page suivante réussie")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du passage à la page suivante: {e}")
            return False

    def _is_next_page_url(self, href: str) -> bool:
        """Détermine si une URL correspond à une page suivante"""
        try:
            if 'page=' in href:
                page_match = re.search(r'page=(\d+)', href)
                if page_match:
                    page_num = int(page_match.group(1))
                    
                    return page_num > 1
            return False
        except:
            return False

    async def save_results_json(self, data: List[Dict[str, Any]]) -> str:
        """Sauvegarde les résultats dans un fichier JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/results/iad_annonces_{timestamp}.json"
        
        # Créer le dossier results s'il n'existe pas
        os.makedirs('/app/results', exist_ok=True)
        
        # Filtrer les champs selon la configuration
        output_fields = self.config['output']['fields']
        filtered_data = [
            {field: item.get(field, "") for field in output_fields}
            for item in data
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON sauvegardé dans: {filename}")
        return filename


async def main():
    """Fonction principale d'exécution"""
    parser = argparse.ArgumentParser(description='Scraper IAD France')
    parser.add_argument('--localisation', type=str, default=os.getenv('LOCALISATION', 'Paris'), 
                       help='Localisation pour la recherche')
    parser.add_argument('--max-biens', type=int, default=os.getenv('MAX_BIENS', 10), 
                       help='Nombre maximum de biens à scraper')
    parser.add_argument('--max-pages', type=int, default=os.getenv('MAX_PAGES', 10), 
                       help='Nombre maximum de pages à scraper')
    
    args = parser.parse_args()
    
    scraper = IADFranceScraper("config.json")
    
    print("🚀 Démarrage du scraping IAD France...")
    print(f"📍 Localisation: {args.localisation}")
    print(f"🏠 Nombre maximum de biens: {args.max_biens}")
    print(f"📄 Pages maximum: {args.max_pages}")
    
    await scraper.scrape(localisation=args.localisation, max_biens=args.max_biens, max_pages=args.max_pages)


def install_dependencies():
    """Installe les dépendances si nécessaire"""
    try:
        import playwright
    except ImportError:
        print("❌ Playwright n'est pas installé. Installation...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "pandas"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])


if __name__ == "__main__":    
    asyncio.run(main())