import json
from pathlib import Path
from playwright.sync_api import Page
import re
import time

class DataExtractor:
    def __init__(self, output_path="data/products.json"):
        self.output_path = output_path
        Path("data").mkdir(exist_ok=True)
    
    def extract_products(self, page: Page):
        products = []
        
        try:
            # Wait for products to load
            page.wait_for_selector("div.flex.flex-col.sm\\:flex-row", timeout=15000)
            time.sleep(0.5)
            
            # Get total number of products from the page
            total_products = self._get_total_product_count(page)
            print(f"Total products to extract: {total_products}")
            
            # Calculate milestones only if we have a finite total
            milestones = {}
            if total_products != float('inf'):
                milestones = {
                    total_products // 4: "25% complete",
                    total_products // 2: "50% complete", 
                    (total_products * 3) // 4: "75% complete",
                    total_products: "100% complete"
                }
            
            scroll_attempts = 0
            max_scroll_attempts = 20  # Increased from 10
            last_product_count = 0
            no_change_counter = 0
            
            while scroll_attempts < max_scroll_attempts:
                # Get current product elements - use more specific selector
                product_elements = page.query_selector_all("div.p-4.border.rounded-md")
                
                # CRITICAL: Stop if we've reached the declared total (handle website bug)
                if total_products != float('inf') and len(products) >= total_products:
                    print(f"Reached declared total of {total_products} products, stopping extraction")
                    break
                
                # Extract only new products
                new_elements = product_elements[len(products):]
                new_products = []
                
                for element in new_elements:
                    try:
                        product_data = self._extract_product_data(element)
                        # Add all products, even those without valid IDs for now
                        new_products.append(product_data)
                        
                        # CRITICAL: Stop if we've hit the declared total (website bug protection)
                        if total_products != float('inf') and len(products) + len(new_products) >= total_products:
                            print(f"Limiting to declared total of {total_products} products")
                            new_products = new_products[:total_products - len(products)]
                            break
                            
                    except Exception as e:
                        print(f"Error extracting product: {e}")
                        continue
                
                if new_products:
                    products.extend(new_products)
                    scroll_attempts = 0
                    no_change_counter = 0
                    
                    # Show progress
                    current_count = len(products)
                    if total_products != float('inf'):
                        if current_count in milestones:
                            print(f"{milestones[current_count]}: {current_count}/{total_products} products")
                        elif current_count % 50 == 0:
                            print(f"Progress: {current_count}/{total_products} products")
                        
                        # CRITICAL: Stop if we've reached the declared total
                        if current_count >= total_products:
                            print(f"Reached declared total of {total_products} products")
                            break
                    else:
                        if current_count % 50 == 0:
                            print(f"Progress: {current_count} products extracted")
                else:
                    scroll_attempts += 1
                
                # Check if we're making progress
                if len(products) == last_product_count:
                    no_change_counter += 1
                    if no_change_counter >= 5:  # Increased threshold
                        print(f"No new products loaded after {no_change_counter} attempts")
                        # Check if there's a "load more" button or similar
                        load_more_btn = page.query_selector("button:has-text('Load'), button:has-text('More'), button:has-text('Show')")
                        if load_more_btn and load_more_btn.is_visible():
                            print("Clicking load more button")
                            load_more_btn.click()
                            time.sleep(2)
                            continue
                        else:
                            print("No load more button found, assuming all products loaded")
                            break
                else:
                    no_change_counter = 0
                
                last_product_count = len(products)
                
                # Enhanced scrolling strategy (but only if we haven't hit the limit)
                if total_products == float('inf') or len(products) < total_products:
                    # Multiple scroll approaches
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # Check if we've reached the end
                    scroll_height_before = page.evaluate("document.body.scrollHeight")
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(1)
                    scroll_height_after = page.evaluate("document.body.scrollHeight")
                    
                    if scroll_height_before == scroll_height_after and no_change_counter >= 3:
                        print("Reached end of page, no more content to load")
                        break
            
            print(f"Extraction completed: {len(products)}/{total_products} products")
            
        except Exception as e:
            print(f"Error during extraction: {e}")
        
        return products
    
    def _get_total_product_count(self, page: Page) -> int:
        """Get total product count from the page text - 'Showing 20 of 1475 products'"""
        try:
            # Look for the specific structure in your HTML
            count_element = page.query_selector("div.text-sm.text-muted-foreground")
            if count_element:
                count_text = count_element.text_content()
                print(f"Count text found: '{count_text}'")
                
                # Pattern for "Showing X of Y products"
                match = re.search(r"of\s+(\d+)\s+products", count_text, re.IGNORECASE)
                if match:
                    total = int(match.group(1))
                    print(f"Found total count: {total}")
                    return total
            
            # Fallback: look for "X remaining" at bottom
            remaining_element = page.query_selector("span:has-text('remaining')")
            if remaining_element:
                remaining_text = remaining_element.text_content()
                match = re.search(r"(\d+)\s+remaining", remaining_text)
                if match:
                    remaining = int(match.group(1))
                    # Add currently shown products (usually 20) + remaining
                    current_products = len(page.query_selector_all("div.flex.flex-col.sm\\:flex-row"))
                    total = current_products + remaining
                    print(f"Calculated total from remaining: {total}")
                    return total
            
            # If still no count found, scan what's actually available
            print("Could not find total product count, will extract all available products")
            return float('inf')  # Will extract until no more products load
            
        except Exception as e:
            print(f"Error getting product count: {e}")
            return float('inf')
    
    def _extract_product_data(self, element):
        try:
            # Extract name from h3.font-medium
            name_element = element.query_selector("h3.font-medium")
            name = name_element.text_content().strip() if name_element else "Unknown"
            
            # Extract ID and category from the specific structure
            id_category_element = element.query_selector("div.flex.items-center.text-sm.text-muted-foreground")
            id_category_text = id_category_element.text_content().strip() if id_category_element else ""
            
            product_id = self._extract_id(id_category_text)
            category = self._extract_category(id_category_text)
            
            # Extract details from the flex layout
            details = {}
            
            # Look for the details container
            details_container = element.query_selector("div.flex.flex-wrap.gap-4.text-sm")
            if details_container:
                detail_items = details_container.query_selector_all("div.flex.flex-col.items-center")
                
                for detail_item in detail_items:
                    label_el = detail_item.query_selector("span.text-muted-foreground")
                    value_el = detail_item.query_selector("span.font-medium")
                    
                    if label_el and value_el:
                        label = label_el.text_content().strip().lower().replace(" ", "_")
                        value = value_el.text_content().strip()
                        if label and value:
                            details[label] = value
            
            return {
                "id": product_id,
                "name": name,
                "category": category,
                "material": details.get("material", "Unknown"),
                "size": details.get("size", "Unknown"),
                "warranty": details.get("warranty", "Unknown"),
                "last_updated": details.get("updated", "Unknown")
            }
            
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return {
                "id": -1,
                "name": "Unknown",
                "category": "Unknown", 
                "material": "Unknown",
                "size": "Unknown",
                "warranty": "Unknown",
                "last_updated": "Unknown"
            }
    
    def _extract_id(self, text):
        try:
            # Try multiple ID patterns
            patterns = [
                r"ID:\s*(\d+)",
                r"id:\s*(\d+)",
                r"#(\d+)",
                r"\b(\d{3,})\b"  # 3+ digit numbers
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            return -1
        except:
            return -1
    
    def _extract_category(self, text):
        try:
            if '•' in text:
                category = text.split('•')[-1].strip()
                return category if category else "Unknown"
            elif '|' in text:
                category = text.split('|')[-1].strip()
                return category if category else "Unknown"
            else:
                # Try to extract category from the end of the text
                parts = text.split()
                if len(parts) > 2:
                    return " ".join(parts[-2:])
            return "Unknown"
        except:
            return "Unknown"
    
    def save_to_json(self, products):
        # Filter out products with invalid IDs (-1) BEFORE saving
        valid_products = [p for p in products if p["id"] != -1 and p["name"] != "Unknown"]
        
        print(f"Total products extracted: {len(products)}")
        print(f"Valid products (with IDs and names): {len(valid_products)}")
        print(f"Invalid products: {len(products) - len(valid_products)}")
        
        # Debug: Show first few invalid products
        invalid_products = [p for p in products if p["id"] == -1 or p["name"] == "Unknown"]
        if invalid_products:
            print("Sample invalid products:")
            for i, p in enumerate(invalid_products[:3]):
                print(f"  {i+1}: ID={p['id']}, Name='{p['name']}'")
        
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_products, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(valid_products)} valid products to {self.output_path}")
        
        return len(valid_products)