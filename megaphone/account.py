import datetime
import math
import time
from collections import namedtuple
from dateutil import parser
from piston.steem import Post as PistonPost

import numpy as np
from megaphone.converter import Converter
from megaphone.helpers import parse_payout, time_diff
from megaphone.node import Node


class AccountError(RuntimeError):
    pass


class Account(object):
    """
    Social blockchain account.
    Currently supported: STEEM and GOLOS.
    """
    def __init__(self, account, chaind=None, blockchain_name="STEEM"):
        """
        Initialize Account object.

        :param account: STEEM/GOLOS account name
        :type account: str
        :param chaind: Blockchain node instance (steemd/golosd)
        :type chaind: :py:class:`Node`
        """
        self.blockchain_name = blockchain_name
        if not chaind:
            chaind = Node().default(blockchain_name=blockchain_name)
        self.rpc = chaind.rpc
        self.account = account
        self.converter = Converter(chaind)

        # caches
        self._blog = None
        self._props = None

    @property
    def reputation(self):
        """
        Account reputation score.

        :return: Reputation score
        :rtype: float
        """
        rep = int(self.get_props()["reputation"])
        if rep < 0:
            return -1
        if rep == 0:
            return 25

        score = (math.log10(abs(rep)) - 9) * 9 + 25
        return float("%.2f" % score)

    @property
    def power(self):
        """
        Account power in STEEM/GOLOS power.

        :return: power value
        :rtype
        """
        vests = int(parse_payout(self.get_props()["vesting_shares"]))
        return self.converter.vests_to_power(vests)

    @property
    def voting_power(self):
        """
        Account voting power.

        :return: voting power value
        :rtype: float
        """
        return self.get_props()['voting_power'] / 100

    @property
    def followers(self):
        return [x['follower'] for x in self._get_followers("follower")]

    @property
    def following(self):
        return [x['following'] for x in self._get_followers("following")]

    def _get_followers(self, direction="follower", last_user=""):
        """
        Return a full list of following/followers.

        :param direction: 'follower' for followers, 'fo
        :type direction: str
        :param last_user: account name to start from
        :type last_user: str

        :return: list of followers
        """
        allowed_directions = ["follower", "following"]
        if direction not in allowed_directions:
            raise AccountError("Allowed directions : %s" % allowed_directions)
        followers = self.rpc.get_followers(self.account, last_user,
                                           "blog", 100, api="follow")
        if len(followers) == 100:
            followers += self._get_followers(direction,
                                             followers[-1][direction])[1:]
        return followers

    @property
    def balances(self):
        """
        Return account's GOLOS, GBG ang GESTS balances.

        STEEM blockchain { "steem", "sbd", "vests" }
        GOLOS blockchain { "golos", "gbg", "gests" }

        :return: account's balances
        :rtype: dict
        """
        my_account_balances = self.rpc.get_balances(self.account)
        balances = {}
        if self.blockchain_name == "GOLOS":
            balances["golos"] = parse_payout(my_account_balances["balance"])
            balances["gbg"] = parse_payout(my_account_balances["sbd_balance"]),
            balances["gests"] = parse_payout(my_account_balances["vesting_shares"])
        elif self.blockchain_name == "STEEM":
            balances["steem"] = parse_payout(my_account_balances["balance"])
            balances["sbd"] = parse_payout(my_account_balances["sbd_balance"]),
            balances["vests"] = parse_payout(my_account_balances["vesting_shares"])
        return balances

    def get_props(self):
        """
        Get account properties.

        :return: Account properties.
        :rtype: dict
        """
        if self._props is None:
            self._props = self.rpc.get_account(self.account)
        return self._props

    def get_blog(self):
        """
        Get account blog in JSON format.

        :return:
        """
        if self._blog is None:
            def _get_blog(rpc, user):
                state = rpc.get_state("/@%s/blog" % user)
                posts = state["accounts"][user].get("blog", [])
                return [PistonPost(rpc, "@%s" % x) for x in posts if x]
            self._blog = _get_blog(self.rpc, self.account)
        return self._blog

    def number_of_winning_posts(self, skip=1, payout_requirement=300,
                                max_posts=10):
        """
        Get number of winning posts.

        :param skip:
        :param payout_requirement:
        :param max_posts:
        :return:
        """
        winning_posts = 0
        blog = self.get_blog()[skip:max_posts + skip]
        for post in blog:
            total_payout = parse_payout(post['total_payout_reward'])
            if total_payout >= payout_requirement:
                winning_posts += 1

        nt = namedtuple('WinningPosts', ['winners', 'blog_posts'])
        return nt(winning_posts, len(blog))

    def avg_payout_per_post(self, skip=1, max_posts=10):
        """
        Return average payout per post.

        :param skip:
        :param max_posts:

        :return:
        """
        total_payout = 0
        blog = self.get_blog()[skip:max_posts + skip]
        for post in blog:
            total_payout += parse_payout(post['total_payout_reward'])

        if len(blog) == 0:
            return 0

        return total_payout / len(blog)

    def time_to_whale(self, verbose=False, whale_power_threshold=1e5, skip=1,
                      max_posts=10, mean_of_recent=3):
        """
        Time elapsed between post creation and getting it noticed by a whale
        account. Whale can be defined by providing token power threshold.
        Currently default threshold is set to 100000 which means that a whale
        has an account with 100000 token power.

        :param verbose: verbosity of the output
        :type verbose: bool
        :param whale_power_threshold: amount of token power for a whale
        :type whale_power_threshold: float
        :param skip: how many posts to skip for get_blog() method
        :type skip: int
        :param max_posts: maximum number of posts to consider
        :type max_posts: int
        :param mean_of_recent: number of recent posts to take mean value from
        :type mean_of_recent: int
        :return:
        """
        blog = self.get_blog()[skip:max_posts + skip]

        max_rshares = self.converter.power_to_rshares(whale_power_threshold)
        time_to_whale = []

        for post in blog:
            votes = []
            rshares_sum = 0

            for vote in post['active_votes']:
                elapsed = int(time_diff(post['created'], vote['time']))
                vote['time_elapsed'] = elapsed
                votes.append(vote)

            # note: this function will already filter out posts without votes
            for vote in sorted(votes, key=lambda k: k['time_elapsed']):
                rshares_sum += int(vote['rshares'])
                if rshares_sum >= max_rshares:
                    ttw = time_diff(post['created'], vote['time'])
                    if verbose:
                        print('%s on %s' % (ttw, post['permlink']))
                    time_to_whale.append(ttw)
                    break

        if len(time_to_whale) == 0:
            return None
        return np.mean(time_to_whale[:mean_of_recent])

    def check_if_already_voted(self, post):
        """
        Check if current account already voted on a post.

        :param post: post
        :type post: py::class::`megaphone.Post`
        :return: True if already voted, False otherwise
        :rtype: bool
        """
        for v in self.history2(filter_by="vote"):
            vote = v['op']
            if vote['permlink'] == post['permlink']:
                return True

        return False

    def curation_stats(self):
        """
        Calculate curation statistics for last day, last week and daily
        average for the last week.

        :return: curation data
        :rtype: dict
        """
        day_ago = datetime.timedelta(hours=24).total_seconds()
        week_ago = datetime.timedelta(days=7).total_seconds()
        trailing_24hr_t = time.time() - day_ago
        trailing_7d_t = time.time() - week_ago

        reward_24h = 0.0
        reward_7d = 0.0

        for event in self.history2(filter_by="curation_reward", take=10000):
            event_utc = parser.parse(event['timestamp'] + "UTC").timestamp()
            if event_utc > trailing_7d_t:
                reward_7d += parse_payout(event['op']['reward'])

            if event_utc > trailing_24hr_t:
                reward_24h += parse_payout(event['op']['reward'])

        reward_7d = self.converter.vests_to_power(reward_7d)
        reward_24h = self.converter.vests_to_power(reward_24h)
        return {
            "24hr": reward_24h,
            "7d": reward_7d,
            "avg": reward_7d / 7,
        }

    def get_features(self, max_posts=10, payout_requirement=300):
        """
        Get common features of last posts.

        :param max_posts: maximum number of posts to consider
        :type max_posts: int
        :param payout_requirement: minimum payout threshold
        :type payout_requirement: int
        :return: common features dictionary
        :rtype: dict
        """
        num_winning_posts, post_count = \
            self.number_of_winning_posts(payout_requirement=payout_requirement,
                                         max_posts=max_posts)
        return {
            "name": self.account,
            "settings": {
                "max_posts": max_posts,
                "payout_requirement": payout_requirement,
            },
            "author": {
                "post_count": post_count,
                "winners": num_winning_posts,
                "sp": int(self.power),
                "rep": self.reputation,
                "followers": len(self.followers),
                "ttw": self.time_to_whale(max_posts=max_posts),
                "ppp": self.avg_payout_per_post(max_posts=max_posts),
            },
        }

    def virtual_op_count(self):
        """
        Return number of virtual operations for an account.

        :return: amount of virtual operations
        :rtype: int
        """
        try:
            last_item = self.rpc.get_account_history(self.account, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def history(self, filter_by=None, start=0):
        """
        All elements from start to last from history, oldest first.
        Generator.

        :param filter_by: filter by field
        :param start: start item

        :return: yield operations
        :rtype: dict
        """
        batch_size = 1000
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while True:
            if i == start_index:
                limit = batch_size
            else:
                limit = batch_size - 1
            history = self.rpc.get_account_history(self.account, i, limit)
            for item in history:
                index = item[0]
                if index >= max_index:
                    return

                op_type = item[1]['op'][0]
                op = item[1]['op'][1]
                timestamp = item[1]['timestamp']
                trx_id = item[1]['trx_id']

                def construct_op():
                    return {
                        "index": index,
                        "trx_id": trx_id,
                        "timestamp": timestamp,
                        "op_type": op_type,
                        "op": op,
                    }

                if filter_by is None:
                    yield construct_op()
                else:
                    if type(filter_by) is list:
                        if op_type in filter_by:
                            yield construct_op()

                    if type(filter_by) is str:
                        if op_type == filter_by:
                            yield construct_op()
            i += batch_size

    def history2(self, filter_by=None, take=1000):
        """
        Take X elements from most recent history, oldest first.

        :param filter_by: filter by field
        :param take: amount of elements to take

        :return: list of operations
        :rtype: dict
        """
        max_index = self.virtual_op_count()
        start_index = max_index - take
        if start_index < 0:
            start_index = 0

        return self.history(filter_by, start=start_index)

    def get_account_votes(self):
        """
        Get account votes. These are the votes for the witness.

        :return: account votes
        :rtype: dict
        """
        return self.rpc.get_account_votes(self.account)

    def get_withdraw_routes(self):
        """
        Get withdraw routes.

        :return: withdraw routes
        :rtype: dict
        """
        return self.rpc.get_withdraw_routes(self.account, 'all')

    def get_conversion_requests(self):
        """
        Get conversion requests from currency to power and vice-versa.

        :return: conversion requests
        :rtype: dict
        """
        return self.rpc.get_conversion_requests(self.account)
