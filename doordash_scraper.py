import asyncio
import json
import os
import re
from typing import List, Dict, Any

from scrapybara import Scrapybara
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def get_scrapybara_browser():
    """Creates a browser instance on a Scrapybara machine"""
    client = Scrapybara(api_key=os.getenv("SCRAPYBARA_API_KEY"))
    instance = client.start_browser()
    return instance

async def retrieve_menu_items(instance, start_url: str) -> List[Dict[str, Any]]:
    """
    Args
    instance: the scrapybara instance to use
    start_url: the initial url to navigate to

    Return value
    a list of menu items on the page, represented as dictionaries
    """
    cdp_url = instance.get_cdp_url().cdp_url
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        await stealth_async(page)
        
        menu_items_data = []
        
        async def handle_response(response):
            if "itemPage" in response.url:
                try:
                    json_data = await response.json()
                    if 'data' in json_data and 'itemPage' in json_data['data']:
                        item_data = json_data['data']['itemPage']
                        menu_items_data.append(item_data)
                except Exception as e:
                    print(f"Error parsing GraphQL response: {e}")
        
        page.on("response", handle_response)
        
        await page.goto(start_url, wait_until="domcontentloaded")
        
        html_content = await page.content()
        
        with open("doordash_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        menu_items_from_html = extract_menu_items_from_script(html_content)
        
        menu_items = await page.query_selector_all('[data-anchor-id="MenuItem"]')
        if not menu_items:
            menu_items = await page.query_selector_all('div[role="listitem"]')
        
        if menu_items:
            try:
                await menu_items[0].click()
                await page.wait_for_timeout(1000)
                close_button = await page.query_selector('button[aria-label="Close"]')
                if close_button:
                    await close_button.click()
                else:
                    await page.keyboard.press("Escape")
            except Exception as e:
                print(f"Error processing menu item: {e}")
        
        return menu_items_from_html

def extract_menu_items_from_script(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract menu items data from script tags in the HTML.
    """
    menu_items = []
    
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, html_content, re.DOTALL)
    
    menu_items_pattern = r'\{\\?"__typename\\?":\\?"MenuPageItem\\?".*?\}'
    
    for script in scripts:
        if '"MenuPageItem"' in script or r'\"MenuPageItem\"' in script:
            items_json = re.findall(menu_items_pattern, script)
            
            for item_json in items_json:
                try:
                    cleaned_json = item_json.replace('\\"', '"')
                    try:
                        item_data = json.loads(cleaned_json)
                    except json.JSONDecodeError:
                        item_data = extract_item_data_manually(cleaned_json)
                    
                    if item_data and 'name' in item_data:
                        menu_items.append(item_data)
                        
                except Exception as e:
                    print(f"Error parsing menu item JSON: {e}")
    
    unique_items = []
    seen_ids = set()
    
    for item in menu_items:
        if item.get('id') not in seen_ids:
            seen_ids.add(item.get('id'))
            unique_items.append(item)
    
    return unique_items

def extract_item_data_manually(json_string: str) -> Dict[str, Any]:
    """
    Extract item data manually using regex patterns. This is fallback when JSON parsing fails and any key/value unavailable.
    """
    item_data = {}
    
    id_match = re.search(r'"id"\s*:\s*"([^"]+)"', json_string)
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', json_string)
    desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', json_string)
    price_match = re.search(r'"displayPrice"\s*:\s*"([^"]*)"', json_string)
    image_match = re.search(r'"imageUrl"\s*:\s*"([^"]+)"', json_string)
    rating_match = re.search(r'"ratingDisplayString"\s*:\s*"([^"]*)"', json_string)
    
    if id_match:
        item_data['id'] = id_match.group(1)
    if name_match:
        item_data['name'] = name_match.group(1)
    if desc_match:
        item_data['description'] = desc_match.group(1)
    if price_match:
        item_data['price'] = price_match.group(1)
    if image_match:
        item_data['image_url'] = image_match.group(1)
    if rating_match and rating_match.group(1) != "null":
        item_data['rating'] = rating_match.group(1)
    
    return item_data

async def main():    
    instance = await get_scrapybara_browser()

    try:
        menu_items = await retrieve_menu_items(
            instance,
            "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false",
        )
        
        with open("menu_items.json", "w") as f:
            json.dump(menu_items, f, indent=2)
        
    finally:
        instance.stop()

if __name__ == "__main__":
    asyncio.run(main())
