import sys
from megaphone.account import Account
from megaphone.node import Node

if len(sys.argv) == 2:
    account_name = sys.argv[1]
else:
    account_name = "cryptomental"


accounts = [Account(account_name, Node("steem").default()),
            Account(account_name, Node("golos").default())]

for account in accounts:
    print("-" * 80)
    print("Blockchain: %s" % account.blockchain_name)
    print("Account's power: %s" % account.power)
    print("Account's reputation: %s" % account.reputation)
    print("Three recent posts:")
    blog = account.get_blog()
    for post in blog[:3]:
        print(post['title'])
    print("Conversion requests: %s" % account.get_conversion_requests())
    print("Withdraw routes: %s" % account.get_withdraw_routes())

