from selenium import webdriver
from bs4 import BeautifulSoup
import config 
from utils import text_cleaner
from datetime import datetime 
from utils.db_connect import db_connection
import time 
from selenium_stealth import stealth



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
  


def initiate_driver(url = config.URL):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")


    driver = webdriver.Chrome(options=options)
    
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

    driver.get(url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    print(f'[LOG] SOUP FETCH : {soup.title.string}')

    # Your parsing logic...
    india_gold_prices = fetch_india_gold_prices(soup)
    other_countries_gold_prices = fetch_major_countries_gold_prices(soup)
    print(f'[LOG] Successfully fetched gold prices from the soup.')
    print(f'[LOG] Successfully fetched data from {url}')

    print(f'[LOG] Dumping data to the database...')
    db_connection.dump_gold_prices(india_gold_prices)
    db_connection.dump_gold_prices(other_countries_gold_prices)
    print(f'[LOG] Data dumped successfully.')


    db_connection.close_connection()
    driver.quit()

if __name__ == "__main__":
    initiate_driver()