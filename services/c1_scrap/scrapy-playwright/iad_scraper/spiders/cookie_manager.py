from playwright.async_api import Page, Locator

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