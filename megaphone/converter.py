import math
from werkzeug.contrib.cache import SimpleCache

from megaphone.helpers import parse_payout, read_asset, simple_cache
from megaphone.node import Node


base_cache = SimpleCache()


class Converter(object):
    """
    Converter for social chain tokens, token powers and currencies.
    Currently supported:
        tokens: STEEM/GOLOS,
        token power: STEEM/GOLOS power,
        token currencies: SBD/GBG.
    """
    def __init__(self, chaind=None):
        if not chaind:
            chaind = Node().default()
        self.rpc = chaind.rpc
        self.CONTENT_CONSTANT = 2000000000000

    @simple_cache(base_cache, timeout=5 * 60)
    def currency_median_price(self):
        """
        Return median price of a token-based currency (SBD/GBG).

        :return: median price of a currency as reported by witnesses
        :rtype: float
        """
        asset = self.rpc.get_feed_history()['current_median_history']['base']
        return read_asset(asset)['value']

    @simple_cache(base_cache, timeout=5 * 60)
    def token_per_mvests(self):
        """
        Return amount of token per 1MV [Mega Vest] using Dynamic Global
        Property Object.

        :return: STEEM/GOLOS per mv
        :rtype: float
        """
        dgpo = self.rpc.get_dynamic_global_properties()
        return (
            parse_payout(dgpo["total_vesting_fund_steem"]) /
            (parse_payout(dgpo["total_vesting_shares"]) / 1e6)
        )

    def vests_to_power(self, vests):
        """
        Convert vests/gests to token power.

        :param vests: amount of vests

        :return: STEEM/GOLOS power
        :rtype: float
        """
        return vests * self.token_per_mvests() / 1e6

    def power_to_vests(self, power):
        """
        Convert token power to vests/gests.

        :param power: STEEM/GOLOS power
        :type power: float

        :return: amount of vests/gests
        :rtype: float
        """
        return power * 1e6 / self.token_per_mvests()

    def power_to_rshares(self, power, voting_power=10000, vote_pct=10000):
        """
        Convert STEEM/GOLOS power to number of rshares given current voting
        power and vote percentage.

        :param power: STEEM/GOLOS power
        :type power: float
        :param voting_power: current voting power multiplied by 100
        :type voting_power: int
        :param vote_pct: vote percentage multiplied by 100
        :type vote_pct: int

        :return: amount of rshares
        :rtype: float
        """
        # calculate our account voting shares (from vests)
        vesting_shares = int(self.power_to_vests(power) * 1e6)

        # calculate vote rshares
        vote_power = (((voting_power * vote_pct) / 10000) / 200) + 1
        rshares = (vote_power * vesting_shares) / 10000

        return rshares

    def token_to_currency(self, amount_token):
        """
        Convert token to token-based currency.

        :param amount_token: amount of STEEM/GOLOS tokens
        :type amount_token: float
        :return: amount of token-based currency
        :rtype: float
        """
        return self.currency_median_price() * amount_token

    def currency_to_token(self, amount_currency):
        """
        Convert token-based currency to tokens.

        :param amount_currency: amount of SBD/GBG to convert
        :type amount_currency: float

        :return: amount of tokens
        :rtype: float
        """
        return amount_currency / self.currency_median_price()

    def currency_to_rshares(self, currency_payout):
        """
        Convert token-based currency to reward shares.

        :param currency_payout: amount of SBD/GBG of the payout
        :type currency_payout: float

        :return: amount of reward shares
        :rtype: float
        """
        tokens_payout = self.currency_to_token(currency_payout)

        dgpo = self.rpc.get_dynamic_global_properties()
        asset = dgpo['total_reward_fund_steem']
        total_reward_fund_steem = read_asset(asset)['value']
        total_reward_shares2 = int(dgpo['total_reward_shares2'])
        tokens = (tokens_payout / total_reward_fund_steem)
        post_rshares2 = tokens * total_reward_shares2

        rshares = math.sqrt(self.CONTENT_CONSTANT ** 2 + post_rshares2)
        rshares -= self.CONTENT_CONSTANT
        return rshares

    def rshares_2_weight(self, rshares):
        """
        Convert rshares to weight.

        :param rshares: amount of rshares
        :type rshares: float

        :return: weight
        :rtype: float
        """
        _max = 2 ** 64 - 1
        return (_max * rshares) / (2 * self.CONTENT_CONSTANT + rshares)
