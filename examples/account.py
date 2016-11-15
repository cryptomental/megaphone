import sys

from megaphone.account import Account
from megaphone.helpers import parse_payout, is_comment, filter_by_date


if len(sys.argv) == 2:
    account_name = sys.argv[1]
else:
    account_name = "cryptomental"

account = Account(account_name)

# get all posts and comments from October
START_DATE = "2016-10-01T00:00:00"
END_DATE = "2016-11-01T00:00:00"

posts = filter_by_date(account.history(filter_by="comment"), START_DATE, END_DATE)

# print titles of top level posts from October 2016
titles = [x["op"]["title"] for x in posts if not is_comment(x["op"])]
print(titles)

# get transfers to "null" account
for event in Account(account_name).history(filter_by=["transfer"]):
    transfer = event["op"]
    if transfer["to"] == "null":
        print("$%.1f :: %s" % (parse_payout(transfer["amount"]),
                               transfer["memo"]))
