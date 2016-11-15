import ssl
import websocket
from piston.steem import Steem as Chain


class NodeError(RuntimeError):
    pass


class Node(object):
    # this allows us to override the steam instance for all instances of Node
    # and therefore all users of Node().default()
    _default = None

    def __init__(self, blockchain="steem"):
        supported_blockchains = ["steem", "golos"]
        if blockchain.lower() not in supported_blockchains:
            raise NodeError("Blockchain %s not supported!" % blockchain)

        public_nodes = {
            "golos": ["wss://node.golos.ws"],
            "steem": ["wss://node.steem.ws", "wss://this.piston.rocks"]}

        self._nodes = {
            "local": ["ws://127.0.0.1:8090"],
            "public": public_nodes[blockchain],
        }

        self._apis = [
            "database_api",
            "login_api",
            "network_broadcast_api",
            "follow_api",
            "market_history_api",
            "tag_api",
        ]

    def default(self, **kwargs):
        """
        Try local node first, and automatically fallback to public nodes.
        """
        if self._default:
            return self._default
        nodes = self.find_local_nodes() + self._nodes['public']
        return Chain(node=nodes, apis=self._apis, **kwargs)

    def public(self, **kwargs):
        return Chain(node=self._nodes['public'], apis=self._apis, **kwargs)

    def _prioritize(self, priority_node):
        return [priority_node].extend([x for x in self._nodes if x != priority_node])

    @staticmethod
    def find_local_nodes():
        local_nodes = []
        for node in ["ws://127.0.0.1:8090"]:
            if node[:3] == "wss":
                sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}
                ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
            else:
                ws = websocket.WebSocket()
            try:
                ws.connect(node)
                ws.close()
                local_nodes.append(node)
            except:
                ws.close()

        return local_nodes


# legacy method
def default():
    print("WARN: default() has been discontinued, please use Node().default() instead")
    return Node().default()
