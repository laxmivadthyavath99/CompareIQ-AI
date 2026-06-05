import json
import time
import os
import sys

print("SCRAPER PYTHON =", sys.executable, file=sys.stderr)
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures


load_dotenv()
API_KEY = os.getenv("SCRAPERAPI_KEY")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

def init_driver(proxy=False):
    options = Options()

    # options.add_argument("--headless=new")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    if proxy and API_KEY:
        proxy_url = f"http://{API_KEY}:scraperapi.proxy:8001"
        options.add_argument(f"--proxy-server={proxy_url}")

    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                })
            """
        }
    )

    return driver

def scrape_myntra(keyword):
    driver = init_driver()
    try:
        #query = keyword.replace(" ", "%20")
        #url = f"https://www.myntra.com/{query}"
        query = keyword.replace(" ", "%20")
        url = f"https://www.myntra.com/{query}"

        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-base"))
        )

        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = []

        for product in soup.select("li.product-base")[:10]:
            brand = product.select_one("h3.product-brand")
            name = product.select_one("h4.product-product")
            price = (
                product.select_one("span.product-discountedPrice")
                or product.select_one("span.product-price")
            )
            link_tag = product.select_one("a[href]")

            if brand and name and price and link_tag:
                items.append({
                    "name": f"{brand.text.strip()} {name.text.strip()}",
                    "price": price.text.strip(),
                    "link": "https://www.myntra.com" + link_tag["href"]
                })

        return items

    except Exception as e:
        print(f"[MYNTRA] Error while scraping HTML: {e}", file=sys.stderr)
        driver.save_screenshot("myntra_error.png")
        return []

    finally:
        driver.quit()

def scrape_amazon(keyword):
    driver = init_driver()

    try:
        query = keyword.replace(" ", "+")
        url = f"https://www.amazon.in/s?k={query}"

        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
            )
        )

        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        items = []

        products = soup.select(
            "div[data-component-type='s-search-result']"
        )

        for product in products[:10]:

            title = product.select_one("h2 span")

            price = (
                product.select_one(".a-price-whole")
                or product.select_one(".a-offscreen")
            )

            link_tag = product.select_one("a[href]")

            if title and price and link_tag:

                href = link_tag.get("href", "")

                if href.startswith("/"):
                    href = "https://www.amazon.in" + href

                items.append({
                    "name": title.get_text(strip=True),
                    "price": f"₹{price.get_text(strip=True)}",
                    "link": href
                })

        return items

    except Exception as e:
        print(f"[AMAZON] Error: {e}", file=sys.stderr)

        with open("amazon_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        driver.save_screenshot("amazon_error.png")

        return []

    finally:
        driver.quit()

def scrape_ajio(keyword):
    driver = init_driver()

    try:
        query = keyword.replace(" ", "%20")
        url = f"https://www.ajio.com/search/?text={query}"

        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.item"))
        )

        time.sleep(5)

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        items = []

        for product in soup.select("div.item")[:10]:

            brand = product.select_one("div.brand")
            name = product.select_one("div.nameCls")
            price = product.select_one("span.price")
            link_tag = product.select_one("a[href]")

            if brand and name and price and link_tag:

                href = link_tag.get("href", "")

                if not href.startswith("http"):
                    href = "https://www.ajio.com" + href

                items.append({
                    "name": f"{brand.text.strip()} {name.text.strip()}",
                    "price": price.text.strip(),
                    "link": href
                })

        return items

    except Exception as e:
        print(f"[AJIO] Error: {e}", file=sys.stderr)

        with open("ajio.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        driver.save_screenshot("ajio_error.png")

        return []

    finally:
        driver.quit()

def scrape_nykaa(keyword):
    driver = init_driver()

    try:
        query = keyword.replace(" ", "%20")
        url = f"https://www.nykaa.com/search/result/?q={query}"

        driver.get(url)

        time.sleep(8)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        items = []

        products = [
            a for a in soup.find_all("a", href=True)
            if "/p/" in a["href"]
        ]

        for product in products[:10]:

            title = product.find("h2")

            price = product.find(
                lambda tag:
                tag.name == "span" and "₹" in tag.get_text()
            )

            if not title or not price:
                continue

            href = product["href"]

            if href.startswith("/"):
                href = "https://www.nykaa.com" + href

            items.append({
                "name": title.get_text(strip=True),
                "price": price.get_text(strip=True),
                "link": href
            })

        return items

    except Exception as e:
        print(f"[NYKAA] Error: {e}", file=sys.stderr)
        driver.save_screenshot("nykaa_error.png")
        return []

    finally:
        driver.quit()

def scrape_flipkart(keyword):
    driver = init_driver()

    try:
        query = keyword.replace(" ", "%20")
        url = f"https://www.flipkart.com/search?q={query}"

        driver.get(url)

        time.sleep(8)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        items = []

        links = [
            a for a in soup.find_all("a", href=True)
            if "/p/" in a["href"]
        ]

        seen = set()

        for link in links:

            href = link["href"]

            if href in seen:
                continue

            seen.add(href)

            title = link.get_text(" ", strip=True)

            if len(title) < 5:
                continue

            parent = link.parent

            price = None

            if parent:
                text = parent.get_text(" ", strip=True)

                import re

                match = re.search(r"₹[\d,]+", text)

                if match:
                    price = match.group()

            items.append({
                "name": title,
                "price": price or "N/A",
                "link": "https://www.flipkart.com" + href
            })

            if len(items) >= 10:
                break

        return items

    except Exception as e:
        print(f"[FLIPKART] Error: {e}", file=sys.stderr)

        driver.save_screenshot("flipkart_error.png")

        return []

    finally:
        driver.quit()
if __name__ == "__main__":

    keyword = sys.argv[1] if len(sys.argv) > 1 else "lipstick"

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = {
            "myntra": executor.submit(scrape_myntra, keyword),
            "amazon": executor.submit(scrape_amazon, keyword),
            "nykaa": executor.submit(scrape_nykaa, keyword),
            "flipkart": executor.submit(scrape_flipkart, keyword),
        }

        results = {}

        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as e:
                print(f"[{name.upper()}] Error: {e}", file=sys.stderr)
                results[name] = []

    print(json.dumps(results, indent=2))