## Installation
```

pip install --user megaphone
```

## Documentation

Steemtools documentation for Steem blockchain by @furion is available on steemit.com:

[> Blockchain parsing, Posts and Accounts](https://steemit.com/steemtools/@furion/ann-steemtools-a-high-level-python-library-for-steem)  
[> Witness Fees and Markets](https://steemit.com/steem/@furion/witness-feed-publishing-with-automatic-sbd-usd-peg)  
[> Updating your Witness](https://steemit.com/witness-category/@furion/updating-you-witness-with-python)  
[> Fetching Market Prices](https://steemit.com/steemtools/@furion/steem-sbd-and-implied-market-prices-with-python)  

Golos specific docs will be added soon and published in readthedocs.io and/or golos.io.

## Examples
Please see [examples](https://github.com/cryptomental/megaphone/tree/master/examples).

## 3rd party
[> Automatic failover for witnesses by @jesta](https://steemit.com/witness-category/@jesta/steemtools-automatic-failover-for-witness-nodes)

## Known Issues
Megaphone depends on Piston, and Piston depends on scrypt.
If you get an error like this during installation:
```
fatal error: openssl/aes.h: No such file or directory

```

You can fix this by installing `libssl-dev`:
```
sudo apt-get install libssl-dev
```

------------

## Install a local node (optional)

By default megaphone connects to wss://node.golos.ws

>Having a local node is highly recommended for blockchain parsing, or applications that need low latency/high reliability.

```
/usr/local/bin/steemd --rpc-endpoint = 0.0.0.0:8090 --replay
```
