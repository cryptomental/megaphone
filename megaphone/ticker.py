from decimal import Decimal
import grequests
import numpy as np


class TickerError(RuntimeError):
    pass


class Ticker(object):
    """
    Return ticker values.
    """
    URLS = {
        "btc-e": "https://btc-e.com/api/2/%s/ticker",
        "bitfinex": "https://api.bitfinex.com/v1/pubticker/%s",
        "bitstamp": "https://www.bitstamp.net/api/v2/ticker/%s",
        "coinbase": "https://api.exchange.coinbase.com/products/%s/ticker",
        "okcoin": "https://www.okcoin.com/api/v1/ticker.do?symbol=%s"
    }
    RESPONSES = {
        "price": {
            "btc-e": "avg",
            "bitfinex": "last_price",
            "bitstamp": "last",
            "coinbase": "price",
            "okcoin": "last"
        },
        "volume": {
            "btc-e": "vol_cur",
            "bitfinex": "volume",
            "bitstamp": "volume",
            "coinbase": "volume",
            "okcoin": "vol"
        }
    }

    @staticmethod
    def get_ticker_symbol(currency_pair, exchange_name):
        """
        Return ticker symbol used by an exchange.

        :param currency_pair: (Crypto)currency pair e.g. btc/usd
        :type currency_pair: str
        :param exchange_name: (Crypto)currency exchange name e.g. coinbase
        :type currency_pair: str

        :return: ticker symbol in format used by the exchange
        :rtype str
        """
        if exchange_name not in Ticker.URLS.keys():
            raise TickerError("Exchange %s not supported!")
        if "/" not in currency_pair:
            raise TickerError("Currency pair incorrect format."
                              "Use xxx/yyy e.g. btc/usd!")
        if exchange_name in ["btc-e", "okcoin"]:
            return currency_pair.replace("/", "_")
        elif exchange_name == "coinbase":
            return currency_pair.replace("/", "-")
        else:
            return currency_pair.replace("/", "")

    @staticmethod
    def price(pair):
        """
        Return VWAP price of a cryptocurrency pair.

        VWAP: Volume Weighted Average Price means the exchange with more volume
        has bigger influence on average price of the cryptocurrency pair.

        :param pair: Cryptocurrency pair. E.g. btcusd
        :type pair: str
        :return: VWAP price
        :rtype float
        """
        prices = {}
        urls = dict((k, v % Ticker.get_ticker_symbol(pair, k))
                    for k, v in Ticker.URLS.items())
        urls_rev = dict((v, k) for k, v in urls.items())
        rs = (grequests.get(u, timeout=2) for u in urls.values())
        responses = list(grequests.map(rs, exception_handler=lambda x, y: ""))

        valid_responses = [x for x in responses
                           if hasattr(x, "status_code")
                           and x.status_code == 200
                           and x.json()]

        for response in valid_responses:
            exchange = urls_rev[response.url]
            if exchange in ["okcoin", "btc-e"]:
                data = response.json()["ticker"]
            else:
                data = response.json()
            price = float(data[Ticker.RESPONSES["price"][exchange]])
            volume = float(data[Ticker.RESPONSES["volume"][exchange]])
            prices[exchange] = {"price": price,
                                "volume": volume}

        if len(prices) == 0:
            raise TickerError("Could not fetch any %s price." % pair)

        return np.average([x['price'] for x in prices.values()],
                          weights=[x['volume'] for x in prices.values()])

    @staticmethod
    def calc_spread(bid, ask):
        return (1 - (Decimal(bid) / Decimal(ask))) * 100
