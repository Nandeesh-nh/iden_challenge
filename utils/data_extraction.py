import json
from pathlib import Path
from playwright.sync_api import Page
import re
import time
import sys

class DataExtractor:
    def __init__(self, output_path="data/products.json"):
        self.output_path = output_path
        Path("data").mkdir(exist_ok=True)
    
    def extract_products(self, page: Page):
        products = []
        page.wait_for_selector("div.p-4.border.rounded-md", timeout=15000)
        time.sleep(0.5)
        
        total_products = self._get_total_product_count(page)
        print(f"Total products to extract: {total_products}")
        
        last_product_count = 0
        no_change_counter = 0
        
        while True:
            product_elements = page.query_selector_all("div.p-4.border.rounded-md")
            current_count = len(product_elements)
            
            # Dynamic single-line loading progress
            bar_length = 50
            filled_length = int(bar_length * current_count // total_products)
            bar = '/' * filled_length
            percent = int((current_count / total_products) * 100)
            if(current_count>=total_products):
                current_count = total_products
            sys.stdout.write(f"\r{bar} {percent}% ({current_count}/{total_products})")
            sys.stdout.flush()
            
            if current_count >= total_products:
                product_elements = product_elements[:total_products]
                break
            
            if current_count == last_product_count:
                no_change_counter += 1
                if no_change_counter >= 3:
                    break
            else:
                no_change_counter = 0
            
            last_product_count = current_count
            
            if current_count < total_products:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.3)
        
        print("\nWait, till all products get extracted...")
        for element in product_elements:
            try:
                product_data = self._extract_product_data(element)
                products.append(product_data)
            except:
                continue
        
        print(f"Extraction completed: {len(products)} products")
        print("Wait, till the product is saving in json...")
        
        return products
    
    def _get_total_product_count(self, page: Page) -> int:
        try:
            count_elements = page.query_selector_all("div.text-sm.text-muted-foreground")
            for element in count_elements:
                text = element.text_content().strip()
                match = re.search(r"Showing\s+\d+\s+of\s+(\d+)\s+products", text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                match = re.search(r"of\s+(\d+)\s+products", text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            span_elements = page.query_selector_all("span.font-medium.text-foreground")
            for element in span_elements:
                text = element.text_content().strip()
                if text.isdigit() and int(text) > 100:
                    return int(text)
            
            full_text = page.text_content()
            match = re.search(r"of\s+<span[^>]*>(\d+)</span>\s+products", full_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
            if "1475" in full_text:
                return 1475
            
            return float('inf')
        except:
            return float('inf')
    
    def _extract_product_data(self, element):
        try:
            product_data = element.evaluate(r"""
                (el) => {
                    const name = el.querySelector('h3.font-medium')?.textContent?.trim() || 'Unknown';
                    const idCategoryEl = el.querySelector('div.flex.items-center.text-sm.text-muted-foreground');
                    const idCategoryText = idCategoryEl?.textContent?.trim() || '';
                    
                    let id = -1;
                    const patterns = [/ID:\s*(\d+)/i, /#(\d+)/, /id:\s*(\d+)/i];
                    for (let pat of patterns) {
                        const match = idCategoryText.match(pat);
                        if (match) { id = parseInt(match[1]); break; }
                    }
                    
                    const category = idCategoryText.includes('•') ? idCategoryText.split('•').pop().trim() : 'Unknown';
                    const details = {};
                    const detailItems = el.querySelectorAll('div.flex.flex-col.items-center');
                    detailItems.forEach(item => {
                        const label = item.querySelector('span.text-muted-foreground')?.textContent?.trim();
                        const value = item.querySelector('span.font-medium')?.textContent?.trim();
                        if (label && value) details[label.toLowerCase().replace(/\s+/g,'_')] = value;
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
        except:
            return {
                "id": -1,
                "name": "Unknown",
                "category": "Unknown",
                "material": "Unknown",
                "size": "Unknown",
                "warranty": "Unknown",
                "last_updated": "Unknown"
            }
    
    def save_to_json(self, products):
        valid_products = [p for p in products if p["id"] != -1 and p["name"] != "Unknown"]
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_products, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(valid_products)} valid products to {self.output_path}")
        return len(valid_products)
