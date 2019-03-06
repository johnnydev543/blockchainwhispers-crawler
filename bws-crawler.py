import requests
import re
from bs4 import BeautifulSoup

def currency_parser(block_text):
    """
    Find the curreny value in the string
    """
    money = re.findall("(?:[\\$]{1}[,\\d]+.?\\d*)", block_text)[0]
    value = int(re.sub(r'[^\d.]', '', money))
    return value

def get_bws_long_short():
    TARGET_URL = "http://localhost:8083/D.A.R.T.%20Crypto%20Signals%20For%20BitMEX%20And%20Deribit.html"
    resp = requests.get(TARGET_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')

    titles = soup.find_all('h3', 'h-desc')

    result = {}

    for title in titles:

            block = title.find_parent(class_='col-md-3')
            long_block = block.find(class_='value long')
            short_block = block.find(class_='value short')

            # strip the block title
            exchange_title = title.text.split(' ')[0]

            long_value = currency_parser(long_block.text)
            short_value = currency_parser(short_block.text)

            if not exchange_title:
                continue

            exchange = {}

            if long_value > 0:
                exchange['long'] = long_value
                
            if short_value > 0:
                exchange['short'] = short_value

            if exchange:
                result[exchange_title] = exchange

    return result

def main():
    output = ""
    data = get_bws_long_short()
    for exchange, positions in data.items():
        long_key = exchange + "_long"
        short_key = exchange + "_short"
        long_value = positions['long']
        short_value = positions['short']
        output += long_key + " " + str(long_value) + "\n"
        output += short_key + " " + str(short_value) + "\n"

    print(output)

if __name__ == '__main__':
    main()
