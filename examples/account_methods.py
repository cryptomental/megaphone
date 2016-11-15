import sys
from megaphone.account import Account

if len(sys.argv) == 2:
    account_name = sys.argv[1]
else:
    account_name = "cryptomental"

account = Account(account_name)

print("Account's power: %s" % account.power)

print("Account's reputation: %s" % account.reputation)

print("Three recent posts:")
blog = account.get_blog()
for post in blog[:3]:
    print(post['title'])

print("Conversion requests: %s" % account.get_conversion_requests())

print("Withdraw routes: %s" % account.get_withdraw_routes())
