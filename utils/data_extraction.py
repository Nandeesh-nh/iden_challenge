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
            page.wait_for_selector("div.p-4.border.rounded-md", timeout=15000)
            time.sleep(0.5)
            
            # Get total number of products from the page
            total_products = self._get_total_product_count(page)
            print(f"Total products to extract: {total_products}")
            
            # SAFETY: Set absolute maximum to prevent infinite loops
            print(f"SAFETY: Will stop at exactly {total_products} products")
            
            last_product_count = 0
            no_change_counter = 0
            
            while True:
                
                # Get all product elements at once
                product_elements = page.query_selector_all("div.p-4.border.rounded-md")
                current_count = len(product_elements)
                
                print(f"Found {current_count} product elements on page")
                
                # CRITICAL: ABSOLUTE STOP at declared total
                if current_count >= total_products:
                    print(f"ABSOLUTE STOP: Reached maximum of {total_products} products")
                    product_elements = product_elements[:total_products]
                    break
                
                # Check if new products loaded
                if current_count == last_product_count:
                    no_change_counter += 1
                    print(f"No new products loaded (attempt {no_change_counter}/3)")
                    
                    if no_change_counter >= 3:
                        print("No more products loading, extraction complete")
                        break
                else:
                    no_change_counter = 0
                    print(f"Progress: {current_count} products found")
                
                last_product_count = current_count
                
                # CONTROLLED SCROLLING: Don't scroll if we're at or near the limit
                if current_count < total_products:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.3)
                else:
                    print(f"Reached target count {total_products}, stopping scroll")
                    break
            
            # FINAL SAFETY CHECK: Ensure we don't exceed the declared total
            if total_products != float('inf') and len(product_elements) > total_products:
                print(f"FINAL TRIM: Cutting {len(product_elements)} down to {total_products}")
                product_elements = product_elements[:total_products]
            
            # Extract data from all collected elements at once
            print(f"Extracting data from {len(product_elements)} products...")
            
            for i, element in enumerate(product_elements):
                try:
                    product_data = self._extract_product_data(element)
                    products.append(product_data)
                    
                    # Progress update every 100 products
                    if (i + 1) % 100 == 0:
                        print(f"Extracted {i + 1}/{len(product_elements)} products")
                        
                except Exception as e:
                    print(f"Error extracting product {i}: {e}")
                    continue
            
            print(f"Extraction completed: {len(products)} products")
            
        except Exception as e:
            print(f"Error during extraction: {e}")
        
        return products
    
    def _get_total_product_count(self, page: Page) -> int:
        """Get total product count from the page text"""
        try:
            # Method 1: Look for the exact text structure from your HTML
            count_elements = page.query_selector_all("div.text-sm.text-muted-foreground")
            for element in count_elements:
                text = element.text_content().strip()
                print(f"Checking element text: '{text}'")
                
                # Look for pattern "Showing X of Y products"
                match = re.search(r"Showing\s+\d+\s+of\s+(\d+)\s+products", text, re.IGNORECASE)
                if match:
                    total = int(match.group(1))
                    print(f"Found total count from 'Showing X of Y': {total}")
                    return total
                
                # Fallback pattern "of Y products"
                match = re.search(r"of\s+(\d+)\s+products", text, re.IGNORECASE)
                if match:
                    total = int(match.group(1))
                    print(f"Found total count from 'of Y products': {total}")
                    return total
            
            # Method 2: Look in spans with specific classes
            span_elements = page.query_selector_all("span.font-medium.text-foreground")
            for element in span_elements:
                text = element.text_content().strip()
                if text.isdigit() and int(text) > 100:  # Likely a total count
                    total = int(text)
                    print(f"Found potential total in span: {total}")
                    return total
            
            # Method 3: Search the entire page content
            full_text = page.text_content()
            print(f"Full page text snippet: {full_text[:500]}...")
            
            # Look for the exact pattern from your HTML
            match = re.search(r"of\s+<span[^>]*>(\d+)</span>\s+products", full_text, re.IGNORECASE)
            if match:
                total = int(match.group(1))
                print(f"Found total in HTML span: {total}")
                return total
            
            # Last resort: find "1475" specifically since you know it's there
            if "1475" in full_text:
                print("Found 1475 in page content")
                return 1475
            
            print("Could not find total product count - will extract until no more load")
            return float('inf')
            
        except Exception as e:
            print(f"Error getting product count: {e}")
            return float('inf')
    
    def _extract_product_data(self, element):
        """Extract product data using JavaScript for speed"""
        try:
            # Use JavaScript to extract data faster
            product_data = element.evaluate("""
                (el) => {
                    const name = el.querySelector('h3.font-medium')?.textContent?.trim() || 'Unknown';
                    const idCategoryEl = el.querySelector('div.flex.items-center.text-sm.text-muted-foreground');
                    const idCategoryText = idCategoryEl?.textContent?.trim() || '';
                    
                    // Extract ID
                    const idMatch = idCategoryText.match(/ID:\\s*(\\d+)/i);
                    const id = idMatch ? parseInt(idMatch[1]) : -1;
                    
                    // Extract category (after •)
                    const category = idCategoryText.includes('•') ? 
                        idCategoryText.split('•').pop().trim() : 'Unknown';
                    
                    // Extract details
                    const details = {};
                    const detailItems = el.querySelectorAll('div.flex.flex-col.items-center');
                    
                    detailItems.forEach(item => {
                        const label = item.querySelector('span.text-muted-foreground')?.textContent?.trim();
                        const value = item.querySelector('span.font-medium')?.textContent?.trim();
                        if (label && value) {
                            details[label.toLowerCase().replace(/\\s+/g, '_')] = value;
                        }
                    });
                    
                    return {
                        id: id,
                        name: name,
                        category: category,
                        material: details.material || 'Unknown',
                        size: details.size || 'Unknown',
                        warranty: details.warranty || 'Unknown',
                        last_updated: details.updated || 'Unknown'
                    };
                }
            """)
            
            return product_data
            
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
            match = re.search(r"ID:\s*(\d+)", text, re.IGNORECASE)
            return int(match.group(1)) if match else -1
        except:
            return -1
    
    def _extract_category(self, text):
        try:
            if '•' in text:
                category = text.split('•')[-1].strip()
                return category if category else "Unknown"
            return "Unknown"
        except:
            return "Unknown"
    
    def save_to_json(self, products):
        # Filter out products with invalid IDs
        valid_products = [p for p in products if p["id"] != -1 and p["name"] != "Unknown"]
        
        print(f"Total products extracted: {len(products)}")
        print(f"Valid products: {len(valid_products)}")
        print(f"Invalid products: {len(products) - len(valid_products)}")
        
        if len(products) != len(valid_products):
            print("Some products had missing data - check selectors if this number is high")
        
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_products, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(valid_products)} valid products to {self.output_path}")
        return len(valid_products)