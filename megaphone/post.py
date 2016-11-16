import json
import time
from contextlib import suppress
from dateutil import parser
from piston.steem import Post as PistonPost

from megaphone.helpers import parse_payout, time_diff
from megaphone.node import Node


class PostError(RuntimeError):
    pass


class Post(PistonPost):
    """
    Piston Post enhanced with metadata and a few utility methods.
    """
    def __init__(self, post, chaind=None):
        if not chaind:
            chaind = Node().default()
        self.blockchain_name = chaind.rpc.get_config()['BLOCKCHAIN_NAME']
        if isinstance(post, PistonPost):
            post = post.identifier
        super(Post, self).__init__(chaind, post)

    @property
    def meta(self):
        """
        JSON metadata of the post.

        :return: post metadata
        :rtype: json
        """
        with suppress(Exception):
            meta_str = self.get("json_metadata", "")
            meta = json.loads(meta_str)
        return meta

    @property
    def url(self):
        """
        Return post's url.

        :return: URL
        :rtype: str
        """
        url_prefix = {"STEEM": "https://steemit.com",
                      "GOLOS": "https://golos.io"}
        if self.blockchain_name not in url_prefix.keys():
            raise PostError("Trying to access post from not supported chain.")
        return "%s/%s/%s" % (url_prefix[self.blockchain_name], self.category,
                             self.identifier)

    def is_comment(self):
        """
        Return True if post is a comment. Post is a comment if it has an empty
        title, its depth is greater than zero or it does have a parent author.

        :return: True if post is a comment, false otherwise
        :rtype: bool
        """
        if len(self["title"]) == 0 or self["depth"] > 0 \
                or len(self["parent_author"]) > 0:
            return True
        else:
            return False

    def get_votes(self, from_account=None):
        """
        Get votes for an account.

        :param from_account:
        :return:
        """
        votes = []
        for vote in self['active_votes']:
            vote['time_elapsed'] = int(time_diff(self['created'], vote['time']))
            if from_account and vote['voter'] == from_account:
                return vote
            votes.append(vote)
        return votes

    def get_metadata(self):
        """
        Get metadata of the post: number of rshares, sum of weights
        and time elapsed since the post was created.

        :return: metadata
        :rtype: dict
        """
        rshares = int(self["vote_rshares"])
        weight = int(self["total_vote_weight"])

        if int(self["total_vote_weight"]) == 0 and self.time_elapsed() > 3600:
            weight = 0
            rshares = 0
            for vote in self['active_votes']:
                weight += int(vote['weight'])
                rshares += int(vote['rshares'])

        return {
            "rshares": rshares,
            "weight": weight,
            "time_elapsed": self.time_elapsed(),
        }

    def contains_tags(self, filter_by=('spam', 'test', 'nsfw')):
        """
        Check if a post contains certain tags.
        Default: spam, test, nsfw (Not Suitable For Work)

        :param filter_by: tags to filter the post with
        :type filter_by: tuple of str
        :return: True if post contains any of the tags, False otherwise
        :rtype: bool
        """
        for tag in filter_by:
            if tag in self['_tags']:
                return True

        return False

    def time_elapsed(self):
        """
        Return time elapsed since the post was created.

        :return: time elapsed in seconds since post creation
        :rtype int
        """
        created_at = parser.parse(self['created'] + "UTC").timestamp()
        now_adjusted = time.time()
        return now_adjusted - created_at

    def payout(self):
        """
        Return post payout.

        :return: post payout
        :rtype: float
        """
        return parse_payout(self['total_payout_reward'])

    def calc_reward_pct(self):
        """
        Calculate post reward percentage.

        :return: reward percent
        :rtype: int
        """
        reward = (self.time_elapsed() / 1800) * 100
        if reward > 100:
            reward = 100
        return reward
