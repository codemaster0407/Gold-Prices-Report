from selenium import webdriver
from bs4 import BeautifulSoup
import config 
from utils import text_cleaner
from datetime import datetime 
from utils.db_connect import db_connection
from selenium_stealth import stealth
import tempfile 
import logging 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

def fetch_india_gold_prices(soup):   
    """
    Fetches the current gold prices in India from the specified URL.
    """ 
    gold_prices_sep_lit = None

    for div in soup.find_all('div', class_='gold-rate-container'):
        line_text = div.text.strip()
        if len(line_text) > 0:
            gold_prices_sep_lit = text_cleaner.split_clean_lines(line_text)


    current_gold_prices_dictionary = {}
    gold_types = []
    print(gold_prices_sep_lit)
    for idx, entry in enumerate(gold_prices_sep_lit):
        try:
            if idx % 3 == 0:
                gold_type = gold_prices_sep_lit[idx]
                gold_type = gold_type.replace(' ', '_')
                gold_type = gold_type.replace('/g', '')
                gold_types.append(gold_type)
                current_gold_prices_dictionary[gold_type] = {
                    'price': text_cleaner.clean_number_from_special_characters(gold_prices_sep_lit[idx + 1]), 
                }
        except IndexError:
            print(f'[ERROR] IndexError while processing entry: {entry}')
            break

    current_datetime_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #Fetch Country ID from the DB or hardcode it as it's to fetch only India gold prices
    country_id = 0
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_date = datetime.now().day

    mysql_entries = []
    
    for type in gold_types:
        entry = {
            'country_id': country_id,
            'gold_type': type,
            'price': float(current_gold_prices_dictionary[type]['price']),
            'year': current_year,
            'month': current_month,
            'date': current_date,
            'timestamp': current_datetime_stamp
        }
        mysql_entries.append(entry)
    if config.LOG:    
        print(f'[LOG] Current Gold Prices: {current_gold_prices_dictionary}')

    return mysql_entries
def fetch_major_countries_gold_prices(soup):

    
    div = soup.find('div', id='24k_major_countries')
    table = div.find_next('table', class_='table-conatiner')

    if not table:
        raise ValueError("No table found with class 'table-conatiner'")
    
    rows = table.find('tbody', class_ = 'tablebody').find_all('tr')
    gold_price_entries = []

    current_year = datetime.now().year
    current_month = datetime.now().month
    current_date = datetime.now().day
    current_datetime_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for row in rows:
        columns = row.find_all('td')
        country = columns[0].text.strip().lower().replace(' ', '')
        
        currency_name, local_curr_price = text_cleaner.extract_currency_and_amount(columns[1].text.strip())
        price_inr = text_cleaner.clean_number_from_special_characters(columns[2].text.strip())
        gold_price_entries.append({
            # 'price_local_curr': local_curr_price,
            'price': float(price_inr), 
            'country_id' : db_connection.fetch_country_id_from_string(country), 
            'gold_type': '24K_Gold_',
            'year': current_year,
            'month': current_month,
            'date': current_date,
            'timestamp': current_datetime_stamp
        })
    if config.LOG:
        print(f'[LOG] Major Countries Gold Prices: {gold_price_entries}')

    return gold_price_entries
  

def initiate_driver(url):
    logging.info("Starting ChromeDriver with headless Chrome on Linux VM...")
    
    options = Options()
    options.add_argument("--headless=new")  # Use '--headless' if your Chrome version does not support '--headless=new'
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.page_load_strategy = 'eager'
    options.add_argument("--disable-gpu")  # Sometimes helps in headless on Linux
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)

        # Apply stealth to mask Selenium fingerprint (update for Linux)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Linux x86_64",
                webgl_vendor="Intel Open Source Technology Center",
                renderer="Mesa DRI Intel(R) UHD Graphics 620 (Kabylake GT2)",
                fix_hairline=True)

        driver.set_page_load_timeout(480)    # increase if needed
        driver.set_script_timeout(120)
        driver.implicitly_wait(20)           # implicitly wait for elements before errors

        # driver.set_page_load_timeout(60)  # Timeout in seconds

        logging.info(f"Navigating to {url} ...")
        driver.get(url)

        # Explicitly wait until <title> element is present (or choose another element relevant to your page)
        WebDriverWait(driver, 480).until(EC.presence_of_element_located((By.TAG_NAME, "title")))

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        logging.info(f'[LOG] SOUP FETCH : {soup.title.string}')

        # Your custom scraping/parsing functions
        india_gold_prices = fetch_india_gold_prices(soup)
        other_countries_gold_prices = fetch_major_countries_gold_prices(soup)

        logging.info(f'[LOG] Successfully fetched gold prices from the soup.')
        logging.info(f'[LOG] Successfully fetched data from {url}')

        logging.info(f'[LOG] Dumping data to the database...')
        db_connection.dump_gold_prices(india_gold_prices)
        db_connection.dump_gold_prices(other_countries_gold_prices)
        logging.info(f'[LOG] Data dumped successfully.')

    except TimeoutException:
        logging.error("Timeout waiting for page to load or element to appear.")
    except WebDriverException as e:
        logging.error(f"WebDriver error: {e}")
    except Exception as e:
        import traceback 

        traceback.print_exc()
        logging.error(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
        db_connection.close_connection()
        logging.info("Driver and DB connection closed.")

if __name__ == "__main__":
    import config
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    initiate_driver(config.URL)