import json
import os
from pathlib import Path
from playwright.sync_api import Page, TimeoutError
import time

class AuthManager:
    def __init__(self, storage_path="auth/session.json"):
        self.storage_path = storage_path
        Path("auth").mkdir(exist_ok=True)
    
    def is_session_valid(self):
        if not os.path.exists(self.storage_path):
            return False
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return len(data) > 0
        except Exception as e:
            print(f"Error checking session validity: {e}")
            return False
    
    def save_session_storage(self, page):
        try:
            session_data = page.evaluate("""() => {
                let data = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    let key = sessionStorage.key(i);
                    data[key] = sessionStorage.getItem(key);
                }
                return data;
            }""")
            
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(session_data, f, indent=4)
            
            print(f"SessionStorage saved ({len(session_data)} keys)")
            return True
        except Exception as e:
            print(f"Error saving session storage: {e}")
            return False
    
    def load_session_storage(self, page):
        try:
            with open(self.storage_path, 'r') as f:
                session_data = json.load(f)
            
            page.evaluate("() => sessionStorage.clear()")
            
            page.evaluate(
                """(data) => {
                    for (const key in data) {
                        sessionStorage.setItem(key, data[key]);
                    }
                }""",
                session_data
            )
            
            print(f"SessionStorage restored ({len(session_data)} keys)")
            return True
        except Exception as e:
            print(f"Error loading session storage: {e}")
            return False
    
    def authenticate(self, page: Page, username: str, password: str):
        try:
            page.evaluate("() => sessionStorage.clear()")
            
            email_field = page.wait_for_selector("#email", timeout=15000)
            email_field.fill(username)
            
            password_field = page.wait_for_selector("#password", timeout=15000)
            password_field.fill(password)
            
            submit_btn = page.wait_for_selector("button[type='submit']", timeout=15000)
            submit_btn.click()
            
            try:
                page.wait_for_selector("text=Instructions", timeout=30000)
                print("Redirected to instructions page after login")
            except TimeoutError:
                if "instructions" not in page.url and not self._is_logged_in(page):
                    raise Exception("Login failed")
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            page.screenshot(path="auth_error.png")
            return False
    
    def _is_logged_in(self, page):
        try:
            logged_in_indicators = [
                "button:has-text('Launch Challenge')",
                "a:has-text('Submit Solution')",
                "text=Instructions"
            ]
            for indicator in logged_in_indicators:
                if page.query_selector(indicator):
                    return True
            return False
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False
