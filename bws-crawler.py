import requests
import re
from bs4 import BeautifulSoup
from flask import Response, Flask
from flatten_json import flatten

def currency_parser(block_text):
    """
    Find the curreny value in the string
    """
    if not block_text:
        return False

    money = re.findall("(?:[\\$]{1}[,\\d]+.?\\d*)", block_text)

    if money:
        money = money[0]
    else:
        return None

    value = int(re.sub(r'[^\d.]', '', money))
    return value

def get_bws_long_short():
    # TARGET_URL = "http://localhost:5000/"
    # TARGET_URL = "http://localhost:8083/index-full.html"
    TARGET_URL = "https://blockchainwhispers.com/bitmex-position-calculator/"
    resp = requests.get(TARGET_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')

    currency_blocks = soup.find_all(class_='account-content')

    result = {}

    for currency_block in currency_blocks:

        # strip the block title
        if hasattr(currency_block.h2, 'string'):
            currency_name = currency_block.h2.string.split(' ')[0]
        else:
            continue
        
        exchanges_block = currency_block.find_all(class_='single-margin-platform')
        
        # print(exchanges_block)
        currency = {}
        for exchange_block in exchanges_block:
            sub_block = exchange_block.find_parent('div')
            # print(sub_block)

            exchange_title = sub_block.find('h3').get_text().split(' ')[0]
            # print(exchange_title)

            long_block = exchange_block.find(class_='value long')
            short_block = exchange_block.find(class_='value short')

            if hasattr(long_block, 'text'):
                long_value = currency_parser(long_block.text)
            else:
                long_value = 0

            if hasattr(short_block, 'text'):
                short_value = currency_parser(short_block.text)
            else:
                short_value = 0

            if not currency_name:
                continue

            
            positions = {}

            if long_value > 0:
                positions['long'] = long_value
            else:
                positions['long'] = None

            if short_value > 0:
                positions['short'] = short_value
            else:
                positions['short'] = None

            if positions:
                currency[exchange_title] = positions
            else:
                currency[exchange_title] = None
        

        if currency:
            result[currency_name] = currency
        else:
            result[currency_name] = None

    # print(result)
    return result

# Use the flask to ouput the data to a web server page,
# to be used in Prometheus
app = Flask("Blockchain Whispers Long Short Crawler")
@app.route("/metrics")
def output():
    output = flatten_output()
    return Response(output, mimetype="text/plain")

def flatten_output():

    output = ""
    data = get_bws_long_short()
    
    # flatten json, the format should be the key value in string
    flatten_data = flatten(data)

    for key, value in flatten_data.items():
        output += key + " " + str(value) + "\n"

    return output

def main():
    print(flatten_output())

if __name__ == '__main__':
    # main()
    try:
        app.run(host="0.0.0.0", port=8084)
    except KeyboardInterrupt:
        print("Quit!")
