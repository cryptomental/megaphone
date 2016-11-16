from megaphone.blockchain import Blockchain
from megaphone.node import Node

blockchains = [Blockchain(Node("steem").default()),
               Blockchain(Node("golos").default())]

# give me just payments from specific day until now
for b in blockchains:
    print("-" * 80)
    print("Blockchain: %s" % b.blockchain_name)
    history = b.replay(
        start_block=b.get_block_from_time("2016-10-18T14:00:00"),
        end_block=b.get_block_from_time("2016-10-18T14:15:00"),
        filter_by=['transfer']
    )
    for event in history:
        payment = event['op']
        print("%s : @%s sent %s to @%s" % (event['timestamp'], payment['from'],
                                           payment['amount'], payment['to']))
