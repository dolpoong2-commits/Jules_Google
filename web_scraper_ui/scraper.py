import requests
from playwright.sync_api import sync_playwright
import urllib.parse

def scrape_github_repo(repo_url):
    """
    Fetches repository data from the GitHub API, including the zip download URL.
    e.g., repo_url = "https://github.com/espressif/esp-idf"
    """
    try:
        api_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # The archive URL needs to be formatted by replacing the placeholders
        archive_url = data.get('archive_url', '').replace('{archive_format}{/ref}', 'zipball/master')
        data['zipball_url'] = archive_url # Add a direct key for the zipball url

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub repo {repo_url}: {e}")
        return None

def scrape_website_headless(url, search_keyword=None):
    """
    Scrapes a website using a headless browser (Playwright).
    If a search_keyword is provided, it attempts to perform a search.
    """
    target_url = url
    if search_keyword:
        # A common, but not universal, search query format.
        target_url = f"{url}/search?q={urllib.parse.quote(search_keyword)}"

    print(f"Scraping: {target_url}")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
            page = browser.new_page()
            # Increase timeout to handle slower sites
            page.goto(target_url, timeout=90000, wait_until='domcontentloaded')
            content = page.content()
            browser.close()
            return content
        except Exception as e:
            print(f"Error scraping website {target_url}: {e}")
            return None

if __name__ == '__main__':
    # Example Usage (for testing)
    print("--- Testing GitHub Scraper ---")
    github_data = scrape_github_repo("https://github.com/lvgl/lvgl")
    if github_data:
        print(f"Successfully fetched {github_data.get('full_name')}")
        print(f"Stars: {github_data.get('stargazers_count')}")
        print(f"Description: {github_data.get('description')}")
        print(f"Zip URL: {github_data.get('zipball_url')}")

    print("\n--- Testing Headless Browser Scraper ---")
    website_content = scrape_website_headless("http://books.toscrape.com/")
    if website_content:
        print("Successfully scraped website content (first 200 chars):")
        print(website_content[:200])
    else:
        print("Failed to scrape website.")

    print("\n--- Testing Headless Browser Scraper with Keyword ---")
    website_content_search = scrape_website_headless("https://www.instructables.com", "esp32")
    if website_content_search:
        print("Successfully scraped search results page (first 200 chars):")
        print(website_content_search[:200])
    else:
        print("Failed to scrape website with search keyword.")