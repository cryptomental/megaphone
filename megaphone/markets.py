import time

import numpy as np
from megaphone.helpers import parse_payout
from megaphone.node import Node
from megaphone.ticker import Ticker


class Markets(Ticker):
    def __init__(self, cache_timeout=60, steem=None):
        if not steem:
            steem = Node().default()
        self.steem = steem

        self._cache_timeout = cache_timeout
        self._cache_timer = time.time()
        self._btc_usd = None
        self._steem_btc = None
        self._sbd_btc = None

    def _has_cache_expired(self):
        if self._cache_timer + self._cache_timeout < time.time():
            self._cache_timer = time.time()
            return True
        return False

    def btc_usd(self):
        if (self._btc_usd is None) or self._has_cache_expired():
            self._btc_usd = self.price("btc/usd")
        return self._btc_usd

    def steem_btc(self):
        if (self._steem_btc is None) or self._has_cache_expired():
            self._steem_btc = self.price("steem/btc")
        return self._steem_btc

    def sbd_btc(self):
        if (self._sbd_btc is None) or self._has_cache_expired():
            self._sbd_btc = self.price("sbd/btc")
        return self._sbd_btc

    def steem_sbd_implied(self):
        return self.steem_btc() / self.sbd_btc()

    def steem_usd_implied(self):
        return self.steem_btc() * self.btc_usd()

    def sbd_usd_implied(self):
        return self.sbd_btc() * self.btc_usd()

    def avg_witness_price(self, take=10):
        price_history = self.steem.rpc.get_feed_history()['price_history']
        return np.mean([parse_payout(x['base']) for x in price_history[-take:]])
