import sys
import stopwatch
from megaphone.node import Node
from megaphone.account import Account


if len(sys.argv) == 2:
    account_name = sys.argv[1]
else:
    account_name = "cryptomental"


chains = {"steem": Node("steem").default(),
          "golos": Node("golos").default()}


def benchmark_steem_vs_golos(max_repeats=10):
    sw = stopwatch.StopWatch()
    with sw.timer('blockchain-benchmark-public-nodes'):
        for i in range(1, max_repeats+1):
            print("Node reconnect #%d" % i)
            with sw.timer('reconnect-steem'):
                Node("steem").default()
            with sw.timer('reconnect-golos'):
                Node("golos").default()
        for i in range(max_repeats):
            with sw.timer('account-access-steem'):
                Account(account=account_name, chaind=chains["steem"])
            with sw.timer('account-access-golos'):
                Account(account=account_name, chaind=chains["golos"])

    print(stopwatch.format_report(sw.get_last_aggregated_report()))

benchmark_steem_vs_golos()
