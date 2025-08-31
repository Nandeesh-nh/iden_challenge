from playwright.sync_api import Page
import time

class NavigationManager:
    def navigate_wizard(self, page: Page):
        steps = [
            ("Local Database", 2),
            ("All Products", 2), 
            ("Table View", 2),
            ("View Products", 3)
        ]
        
        for button_text, wait_time in steps:
            self._click_button(page, button_text)
            time.sleep(wait_time)
    
    def _click_button(self, page: Page, button_text: str):
        try:
            button = page.wait_for_selector(f"button:has-text('{button_text}')", timeout=10000)
            button.click()
        except:
            all_buttons = page.query_selector_all("button")
            for btn in all_buttons:
                if button_text.lower() in btn.text_content().lower():
                    btn.click()
                    break