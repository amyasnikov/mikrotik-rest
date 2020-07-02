from typing import Dict
from node import Node
from settings import USERNAME, PASSWORD
from librouteros.exceptions import ProtocolError, ConnectionClosed
from socket import timeout

error_codes = {
    ProtocolError: 400,
    ConnectionClosed: 502,
    ConnectionError: 502,
    timeout: 503
}

class Endpoint:

    mtranslate = {
        'get': 'print',
        'post': 'add',
        'patch': 'set',
        'delete': 'remove'
    }

    def __init__(self, endpoint):
        self.path, self.method = Endpoint.parse(endpoint)

    def __call__(self, **kwargs):
        try:
            node = Config.nodes.get(kwargs['hostname'])
            if not node:
                node = Node(kwargs['hostname'], USERNAME, PASSWORD)
            node_method = getattr(node, self.method)
            del kwargs['hostname']
            result = node_method(path=self.path, **kwargs)
            return result
        except (ProtocolError, ConnectionClosed, timeout, ConnectionError) as e:
            err_type = type(e)
            for err_supertype in err_type.mro():
                if err_supertype in error_codes:
                    return {'type': '.'.join((err_type.__module__, err_type.__name__)),
                            'message' : str(e)
                            }, error_codes[err_supertype]

    @staticmethod
    def parse(endpoint):
        ep = endpoint.split('.')[-1]
        fields = ep.split('_')
        method = Endpoint.mtranslate[fields.pop()]
        path = '/' + '/'.join(fields)
        return path, method


class Config:

    nodes: Dict[str, Node] = {}

    def __getattr__(self, name):
        return Endpoint(name)



config = Config()