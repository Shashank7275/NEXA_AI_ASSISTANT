if True:
    import requests
    from bs4 import BeautifulSoup
    import webbrowser
    from urllib.parse import quote_plus, urljoin
    from livekit.agents import function_tool
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver import ActionChains
    import os
    import time

class FlipkartScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_products(self, query, max_results=5):
        url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        try:
            resp = self.session.get(url, timeout=15)
            soup = BeautifulSoup(resp.content, 'html.parser')
            products = []
            anchors = soup.select('a')[:500]
            seen = set()
            for a in anchors:
                href = a.get('href', '')
                title = a.get('title') or a.text.strip()
                if not href or not title:
                    continue
                if '/p/' not in href:
                    continue
                link = urljoin("https://www.flipkart.com", href)
                key = (title, link)
                if key in seen:
                    continue
                seen.add(key)
                products.append({'name': title, 'url': link})
                if len(products) >= max_results:
                    break
            return products
        except Exception as e:
            return [{'error': str(e)}]

    def top_product_url(self, query):
        results = self.search_products(query, max_results=1)
        if results and 'url' in results[0]:
            return results[0]['url']
        return None

    def open_product(self, query):
        url = self.top_product_url(query)
        if not url:
            return "No product found"
        webbrowser.open(url)
        return url
    
    def buy_cod_auto(self, query, timeout=40):
        try:
            user = os.environ.get("USERNAME") or os.environ.get("USERPROFILE","user")
            user_data = os.path.join(os.environ.get("USERPROFILE",""), "AppData", "Local", "Google", "Chrome", "User Data")
            opts = Options()
            if os.path.isdir(user_data):
                opts.add_argument(f"--user-data-dir={user_data}")
                opts.add_argument("--profile-directory=Default")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
            driver.maximize_window()
            driver.get(f"https://www.flipkart.com/search?q={quote_plus(query)}")
            wait = WebDriverWait(driver, timeout)
            links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
            target = None
            for a in links:
                href = a.get_attribute("href") or ""
                if "/p/" in href:
                    target = href
                    break
            if not target:
                driver.quit()
                return "No product found"
            driver.get(target)
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            try:
                tabs = driver.window_handles
                if len(tabs) > 1:
                    driver.switch_to.window(tabs[-1])
            except Exception:
                pass
            size_token = None
            for tok in query.split():
                if tok.isdigit():
                    size_token = tok
            if size_token:
                try:
                    size_el = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[contains(normalize-space(.),'{size_token}') and (self::button or self::a or self::div or self::span)]"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", size_el)
                    driver.execute_script("arguments[0].click()", size_el)
                    time.sleep(1)
                except Exception:
                    pass
            try:
                btn = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUY NOW')]"))
                )
                btn.click()
            except Exception:
                try:
                    btn = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ADD TO CART')]"))
                    )
                    btn.click()
                    try:
                        place = WebDriverWait(driver, timeout).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PLACE ORDER')]/ancestor::button | //button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PLACE ORDER')]"))
                        )
                        place.click()
                    except Exception:
                        pass
                except Exception:
                    driver.quit()
                    return "Opened product but could not add/buy"
            time.sleep(4)
            try:
                deliver = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'DELIVER HERE') or contains(.,'Deliver here')]"))
                )
                deliver.click()
                time.sleep(2)
            except Exception:
                pass
            try:
                cont = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CONTINUE') or contains(.,'Continue')]"))
                )
                cont.click()
                time.sleep(2)
            except Exception:
                pass
            try:
                cod = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CASH ON DELIVERY') or contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PAY ON DELIVERY') or contains(.,'COD')]"))
                )
                cod.click()
                try:
                    confirm = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CONFIRM') or contains(.,'Confirm')]"))
                    )
                    confirm.click()
                except Exception:
                    pass
                return "COD selected or ready at payment"
            except Exception:
                try:
                    payment_tab = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PAYMENT OPTIONS') or contains(.,'Payment Options')]"))
                    )
                    payment_tab.click()
                    cod2 = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CASH ON DELIVERY') or contains(.,'COD')]"))
                    )
                    cod2.click()
                    return "COD selected"
                except Exception:
                    return "Proceed manually to payment and choose COD"
        except Exception as e:
            return f"Automation failed: {e}"

    def buy_auto(self, query, payment="cod", timeout=50):
        try:
            user_data = os.path.join(os.environ.get("USERPROFILE",""), "AppData", "Local", "Google", "Chrome", "User Data")
            opts = Options()
            if os.path.isdir(user_data):
                opts.add_argument(f"--user-data-dir={user_data}")
                opts.add_argument("--profile-directory=Default")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
            driver.maximize_window()
            driver.get(f"https://www.flipkart.com/search?q={quote_plus(query)}")
            wait = WebDriverWait(driver, timeout)
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            target = None
            for a in wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a"))):
                href = a.get_attribute("href") or ""
                if "/p/" in href:
                    target = href
                    break
            if not target:
                driver.quit()
                return "No product found"
            driver.get(target)
            try:
                tabs = driver.window_handles
                if len(tabs) > 1:
                    driver.switch_to.window(tabs[-1])
            except Exception:
                pass
            size_token = None
            for tok in query.split():
                if tok.isdigit():
                    size_token = tok
            if size_token:
                try:
                    size_el = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[contains(normalize-space(.),'{size_token}') and (self::button or self::a or self::div or self::span)]"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", size_el)
                    driver.execute_script("arguments[0].click()", size_el)
                    time.sleep(1)
                except Exception:
                    pass
            try:
                buy = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUY NOW')]"))
                )
                driver.execute_script("arguments[0].click()", buy)
            except Exception:
                add = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ADD TO CART')]"))
                )
                driver.execute_script("arguments[0].click()", add)
                try:
                    place = WebDriverWait(driver, 12).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PLACE ORDER')] | //span[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'PLACE ORDER')]/ancestor::button"))
                    )
                    driver.execute_script("arguments[0].click()", place)
                except Exception:
                    pass
            time.sleep(3)
            try:
                deliver = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'DELIVER HERE') or contains(.,'Deliver here')]"))
                )
                driver.execute_script("arguments[0].click()", deliver)
                time.sleep(1)
            except Exception:
                pass
            try:
                cont = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CONTINUE') or contains(.,'Continue')]"))
                )
                driver.execute_script("arguments[0].click()", cont)
                time.sleep(1)
            except Exception:
                pass
            if payment.lower() == "cod":
                return self.buy_cod_auto(query, timeout=timeout)
            else:
                try:
                    pay = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'UPI') or contains(.,'Net Banking') or contains(.,'Credit')]"))
                    )
                    driver.execute_script("arguments[0].click()", pay)
                    return "Online payment option selected"
                except Exception:
                    return "Proceed manually to select online method"
        except Exception as e:
            return f"Automation failed: {e}"

@function_tool
async def flipkart_buy_cod(query: str) -> str:
    scraper = FlipkartScraper()
    url = scraper.open_product(query)
    if url and url.startswith("http"):
        return f"Opened product page: {url}. Complete login and choose COD at checkout."
    return "Product not found"

@function_tool
async def flipkart_buy_cod_auto(query: str) -> str:
    scraper = FlipkartScraper()
    return scraper.buy_cod_auto(query)

@function_tool
async def flipkart_buy_auto(query: str, payment: str = "cod") -> str:
    scraper = FlipkartScraper()
    return scraper.buy_auto(query, payment)
