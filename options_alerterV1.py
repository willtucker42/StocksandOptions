# This script scrapes finviz and yahoo finance using selenium
# It looks for low volatility stocks that are seeing an increase in price from market open
# It then looks for options for that stock that have not reacted to the price increase yet
# If it finds a stock that has good option prices it sends a push notification to my phone
# Stock criteria for finviz: Optionable, up 3% from open, average volume over 500k, ordered by lowest volatility
# Options criteria: Calls. Strike prices 10% above above underlying stock price with last price <= 0.05, nearest expiration date


from pushbullet import Pushbullet
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--headless")
PUSHBULLET_API_KEY = "o.sFSmq3qn2L7ZwD3acBTU2eRHGEmgXll3"


def getTickerSymbolsForRisingStocks():
    # CRITERIA: Optionable, up 3% from open, average volume over 500k, ordered by lowest volatility
    ticker_list = []
    get_url = "https://finviz.com/screener.ashx?v=141&f=sh_avgvol_o500,sh_opt_option,ta_changeopen_u3&ft=4&o=volatility4w"
    # req = Request(get_url)
    # html_page = urlopen(req)
    try:
        driver = webdriver.Chrome()
        driver.get(get_url)
    except Exception:
        print(traceback.format_exc())
        return 0
    links = driver.find_elements_by_xpath('//a')
    for link in links:
        class_ = link.get_attribute('class')
        if class_ is not None and class_ == "screener-link-primary":
            ticker_list.append(link.text)
            print(link.text)
    driver.close()
    return ticker_list


def getOptionDataForTickerSymbol(ticker):
    get_url = "https://finance.yahoo.com/quote/" + ticker + "/options"
    try:
        driver = webdriver.Chrome()
        driver.get(get_url)
    except Exception:
        print("\n\n ERROR IN getOptionDataForTickerSymbol \n\n")
        print(traceback.format_exc())
        driver.close()
        return 0
    try:
        rw_data = driver.find_elements_by_xpath("//table/tbody/tr")
        # print(rw_data)
        price_data = driver.find_elements_by_xpath("//fin-streamer")
        current_stock_price = 0
        for price in price_data:
            class_ = price.get_attribute('class')
            if class_ is not None and class_ == "Fw(b) Fz(36px) Mb(-4px) D(ib)":
                current_stock_price = float(price.text)
                print("Current price: " + str(current_stock_price))
        if current_stock_price == 0:
            print("\n\n UNABLE TO GET CURRENT STOCK PRICE \n\n")
            return
        upper_strike_limit = current_stock_price + (current_stock_price * 0.1)
        print("upper strike limit " + str(upper_strike_limit))
        last_strike = 0
        print("row data count: ")
        allows_non_multiples_of_five = False
        for row in rw_data:
            row_data = str(row.text).split(' ')
            if "P0" in row_data[0]:
                break
            # print(row_data)
            strike_price = float(row_data[4])
            last_price = float(row_data[5])
            bid = float(row_data[6])
            ask = float(row_data[7])
            if checkIfAllowsNonMultiplesOfFive(last_price, bid, ask):
                print(ticker + " supports nonMultiplesOfFive!")
                allows_non_multiples_of_five = True
            if current_stock_price < strike_price < upper_strike_limit:
                if last_price <= 0.05 and allows_non_multiples_of_five:  # potentially use multiples of 5 boolean here
                    print("SENDING NOTIF")
                    pb = Pushbullet(PUSHBULLET_API_KEY)
                    pb.push_note('$' + ticker + "(" + str(current_stock_price) + ")",
                                 "" + str(strike_price) + "C - Last price: " + str(last_price))

            # print("Strike: " + str(strike_price) + ", Last price: " + str(last_price))
            last_strike = float(strike_price)
    except Exception:
        print("\n\n ERROR AFTER GETTING PAGE DATA \n\n")
        print(traceback.format_exc())
        driver.close()
        getOptionDataForTickerSymbol(ticker)
    driver.close()


def checkIfAllowsNonMultiplesOfFive(last_price, bid, ask):
    last_price_last_digit = int(str(last_price)[-1])
    bid_last_digit = int(str(bid)[-1])
    ask_price_last_digit = int(str(ask)[-1])
    if ask_price_last_digit != 0 and ask_price_last_digit != 5:
        return True
    if bid_last_digit != 0 and bid_last_digit != 5:
        return True
    if last_price_last_digit != 0 and last_price_last_digit != 5:
        return True
    return False


# print(checkIfAllowsNonMultiplesOfFive(5.67, .10, 1.05))

t_list = getTickerSymbolsForRisingStocks()

getOptionDataForTickerSymbol("GOLD")
for t in t_list:
    getOptionDataForTickerSymbol(t)

