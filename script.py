import requests
import re
from bs4 import BeautifulSoup

import time
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server

def currency_parser(block_text):
    
    # Find the curreny value in the string
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

    currency_blocks = soup.find_all(class_='bcw-calculator-longs-shorts')

    result = {}

    for currency_block in currency_blocks:

        # strip the block title
        if hasattr(currency_block.h2, 'string'):
            currency_name = currency_block.h2.string.split(' ')[0]
        else:
            continue

        exchanges_block = currency_block.find_all(class_='bcw-calculator-card')

        # print(exchanges_block)
        currency = {}
        for exchange_block in exchanges_block:
            sub_block = exchange_block.find_parent('div')
            # print(sub_block)

            exchange_title = sub_block.find(class_='bcw-calculator-card-heading').get_text().split(' ')[0].lstrip()

            long_block = exchange_block.find(class_='btc-calculator-card-longs').find(class_='card-longs-value')           
            short_block = exchange_block.find(class_='btc-calculator-card-shorts').find(class_='card-shorts-value')

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

            positions['long']  = long_value  if long_value  > 0 else None
            positions['short'] = short_value if short_value > 0 else None
            
            if exchange_title == 'Total':
                diff  = long_value - short_value
                positions['diff'] = diff

            currency[exchange_title] = positions if positions else None

        if currency:
            result[currency_name] = currency
        else:
            result[currency_name] = None

    return result

class BWSPositionsCollector(object):

    def collect(self):

        data = get_bws_long_short()
        # print(data)
        """
        DATA STRUCTURE:

        data = {
            "BITCOIN": {
                "Bitfinex": {
                    "long": 286645401,
                    "short": 39771366
                },
                "BitMex": {
                    "long": 415450241,
                    "short": 302757624
                },
                "Binance": {
                    "long": 31076888,
                    "short": 33400311
                },
                "Total": {
                    "long": 733172530,
                    "short": 375929301
                }
            },
            "ETHEREUM": {
                "Bitfinex": {
                    "long": 157778327,
                    "short": 13177766
                },
                "BitMex": {
                    "long": 65297229,
                    "short": 22200073
                },
                "Total": {
                    "long": 238849969,
                    "short": 58014946
                }
            }
        }
        """

        coins = ['BITCOIN', 'ETHEREUM']

        metrics = {}

        for coin in coins:
            metrics[coin] = GaugeMetricFamily(
                'bws_position_{0}'.format(coin),
                'Blockchainwhispers ' + coin + ' position data',
                labels=['exchange', 'position'])

        for coin, exchanges in data.items():
            for exchange, position in exchanges.items():

                # skip if has no value
                if 'long' in position and position['long'] == None:
                    continue

                metrics[coin].add_metric(
                    [exchange, 'long'], position.get('long', None))
                metrics[coin].add_metric(
                    [exchange, 'short'], position.get('short', None))
                if exchange == 'Total':
                    metrics[coin].add_metric(
                    [exchange, 'diff'], position.get('diff', None))


        for m in metrics.values():
            yield m


if __name__ == "__main__":

    REGISTRY.register(BWSPositionsCollector())
    start_http_server(5000)
    while True:
        time.sleep(10)
