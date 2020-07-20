from typing import Dict
from .node import Node
from settings import USERNAME, PASSWORD, API_TRANSPORT
from librouteros.exceptions import ProtocolError, ConnectionClosed
from socket import timeout
from ssl import SSLError


class Endpoint:

    error_codes = {
        ProtocolError: 400,
        ConnectionClosed: 502,
        timeout: 503,
        ConnectionError: 502,
        SSLError: 502
    }

    def __init__(self, endpoint):
        self.path, self.method = Endpoint.parse(endpoint)

    def __call__(self, **kwargs):
        try:
            node = Resolver.nodes_cache.get(kwargs['hostname'])
            if not node:
                use_ssl = API_TRANSPORT == 'SSL'
                node = Node(kwargs['hostname'], USERNAME, PASSWORD, use_ssl)
                Resolver.nodes_cache[kwargs['hostname']] = node
            print(len(node.cm.connections), node.cm.connections)
            node_method = getattr(node, self.method)
            del kwargs['hostname']
            result = node_method(path=self.path, **kwargs)
            return result
        except tuple(Endpoint.error_codes) as err:
            err_type = type(err)
            for err_supertype in err_type.mro():
                if err_supertype in Endpoint.error_codes:
                    return {'type': '.'.join((err_type.__module__, err_type.__name__)),
                            'message': str(err)
                            }, Endpoint.error_codes[err_supertype]

    @staticmethod
    def parse(endpoint):
        ep = endpoint.split('.')[-1]
        fields = ep.split('_')
        method = fields.pop()
        path = '/' + '/'.join(fields)
        return path, method


class Resolver:

    nodes_cache: Dict[str, Node] = {}

    def __getattr__(self, name):
        return Endpoint(name)


cfg = Resolver()
