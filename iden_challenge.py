import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError
from utils.auth import AuthManager
from utils.navigation import NavigationManager
from utils.data_extraction import DataExtractor
import time

class IdenChallenge:
    def __init__(self):
        self.auth_manager = AuthManager()
        self.navigation_manager = NavigationManager()
        self.data_extractor = DataExtractor()
        self.base_url = "https://hiring.idenhq.com"
        self.credentials = {
            "username": "nandeesh.j.a@campusuvce.in",
            "password": "Ss2e38pf"
        }
    
    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(30000)
            
            try:
                if self.auth_manager.is_session_valid():
                    print("Trying to use stored session...")
                    try:
                        page.goto(self.base_url, wait_until="domcontentloaded")
                        self.auth_manager.load_session_storage(page)
                        page.reload(wait_until="networkidle")
                        time.sleep(2)
                        
                        if self._check_logged_in(page):
                            print("Logged in with stored session")
                            self._handle_post_login_flow(page)
                        else:
                            print("Stored session invalid, starting fresh authentication")
                            self._perform_full_authentication(page)
                    except Exception:
                        self._perform_full_authentication(page)
                else:
                    print("No stored session found, performing fresh authentication")
                    self._perform_full_authentication(page)
                
                self.navigation_manager.navigate_wizard(page)
                
                products = self.data_extractor.extract_products(page)
                self.data_extractor.save_to_json(products)
                
                print(f"Extracted {len(products)} products")
                
            except Exception as e:
                page.screenshot(path="error.png")
                raise
            finally:
                browser.close()
    
    def _perform_full_authentication(self, page):
        page.goto(self.base_url, wait_until="networkidle")
        time.sleep(2)
        
        success = self.auth_manager.authenticate(page, self.credentials["username"], self.credentials["password"])
        if success:
            print("Authentication successful")
            self.auth_manager.save_session_storage(page)
            self._handle_post_login_flow(page)
        else:
            raise Exception("Authentication failed")
    
    def _check_logged_in(self, page):  
        current_url = page.url
        if "/instructions" in current_url:
            return True
        
        login_indicators = ["/login", "/auth", "signin", "#email", "#password"]
        if not any(indicator in current_url for indicator in login_indicators):
             if not page.query_selector("#email, #password"):
                return True
    
        return False
    
    def _handle_post_login_flow(self, page):
        current_url = page.url
        
        if self._is_on_instructions_page(page):
            self._launch_challenge(page)
        elif self._is_in_challenge_wizard(page):
            pass
        elif self._is_on_dashboard(page):
            self._navigate_to_challenge_from_dashboard(page)
    
    def _is_on_instructions_page(self, page):
        try:
            instructions_heading = page.wait_for_selector("text=Instructions", timeout=3000)
            launch_button = page.wait_for_selector("button:has-text('Launch Challenge')", timeout=3000)
            return instructions_heading is not None and launch_button is not None
        except:
            return False
    
    def _is_in_challenge_wizard(self, page):
        try:
            wizard_elements = page.wait_for_selector(
                "button:has-text('Local Database'), "
                "button:has-text('Next'), "
                "button:has-text('All Products')", 
                timeout=3000
            )
            return wizard_elements is not None
        except:
            return False
    
    def _is_on_dashboard(self, page):
        try:
            dashboard_heading = page.wait_for_selector("h1:has-text('Dashboard')", timeout=3000)
            return dashboard_heading is not None
        except:
            return False
    
    def _navigate_to_challenge_from_dashboard(self, page):
        try:
            challenge_link = page.query_selector("a:has-text('Challenge'), button:has-text('Challenge')")
            if challenge_link:
                challenge_link.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                self._handle_post_login_flow(page)
            else:
                page.goto(f"{self.base_url}/challenge", wait_until="networkidle")
                time.sleep(2)
                self._handle_post_login_flow(page)
        except Exception as e:
            print(f"Error navigating from dashboard: {e}")
    
    def _launch_challenge(self, page):
        try:
            launch_btn = page.wait_for_selector("button:has-text('Launch Challenge')", timeout=10000)
            launch_btn.scroll_into_view_if_needed()
            time.sleep(1)
            launch_btn.click()
            page.wait_for_selector("button:has-text('Local Database'), button:has-text('Next')", timeout=15000)
            time.sleep(2)
        except Exception as e:
            page.screenshot(path="launch_error.png")
            raise

if __name__ == "__main__":
    challenge = IdenChallenge()
    challenge.run()
