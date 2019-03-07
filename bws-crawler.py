import requests
import re
import prometheus_client
from bs4 import BeautifulSoup
from prometheus_client import Gauge
from flask import Response, Flask

def currency_parser(block_text):
    """
    Find the curreny value in the string
    """
    money = re.findall("(?:[\\$]{1}[,\\d]+.?\\d*)", block_text)[0]
    value = int(re.sub(r'[^\d.]', '', money))
    return value

def get_bws_long_short():
    # TARGET_URL = "http://localhost:8083/"
    TARGET_URL = "https://blockchainwhispers.com/cryptosignals/"
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


app = Flask("Blockchain Whispers Crawler")
@app.route("/metrics")
def output():
    output = expanded_output()
    return Response(output, mimetype="text/plain")

def export_metrics():
    output = ""
    data = get_bws_long_short()
    for exchange, positions in data.items():

        gauge_desc_long = exchange + " Long position"
        gauge_desc_short = exchange + " Short position"

        long_key = exchange + "_long"
        short_key = exchange + "_short"
        long_value = str(positions['long'])
        # print(long_value)
        short_value = str(positions['short'])
        # print(short_value)

        g_long = Gauge(long_key, gauge_desc_long)
        g_short = Gauge(short_key, gauge_desc_short)

        g_long.set(long_value)
        g_short.set(short_value)

        output += str(prometheus_client.generate_latest(g_long))
        output += str(prometheus_client.generate_latest(g_short))

        return Response(output, mimetype='text/plain')

def expanded_output():
    placeholder = 'blockchainwhispers'
    output = ""
    data = get_bws_long_short()
    for exchange, positions in data.items():
        long_key = placeholder + "_" + exchange + "_long"
        short_key = placeholder + "_" + exchange + "_short"
        long_value = positions['long']
        short_value = positions['short']
        output += long_key + " " + str(long_value) + "\n"
        output += short_key + " " + str(short_value) + "\n"

    return output

def main():
    print(expanded_output())

if __name__ == '__main__':
    # main()
    try:
        app.run(host="0.0.0.0", port=8084)
    except KeyboardInterrupt:
        print("Quit!")
