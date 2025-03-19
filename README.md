# doordash_scraper

So first, I was going through the [https://github.com/kaliiiiiiiiii/undetected-playwright-python/tree/main](undetected_playwright) codebase (that has read-only since Nov 2 and for which I could not find 'Malenia' docs for async bypassing) and realized there is a better and more popular CAPTCHA bypass alternative called [https://github.com/AtuboDad/playwright_stealth](stealth_playwright) (more stars, NOT read-only, and easier to use than patched or non-patched version of undetected_playwright).

Next, once stealth_playwright allowed me to quickly bypass cloudflare, there was minimal latency in pulling the HTML innerContent and subsequently parsing it for MenuContent matches as using just selector values did not work due to some sort of uuid system on their end.

To generalize this, as I found doordash took too much time to render the food item elements, I just pulled the DOM's innerContent and performed Regex on it if simple JSON field matching did not work (for example, Utensils or Napkins usually have no price or description).

This final result is stored as a list of menu item descriptions with primary key `id`.
