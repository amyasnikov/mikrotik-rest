from typing import Tuple, Dict, Any, List, Callable
from ssl import create_default_context, CERT_NONE, CERT_REQUIRED, SSLContext
import settings as setts
from librouteros.query import Key
from .connect import ConnectionManager


# GET - parameters in query
# POST, PATCH - parameters in body
# DELETE - parameters in query


def add_hostname_to_context(func, hostname):
    def wrapper(*args, **kwargs):
        return func(*args, server_hostname=hostname, **kwargs)
    return wrapper


class Node:

    @staticmethod
    def create_ssl_wrapper(hostname: str) -> Callable:
        check_cert, check_host = setts.SSL_CHECK_CERT, setts.SSL_CHECK_HOSTNAME
        ctx = create_default_context(cafile=setts.SSL_CAFILE)
        ctx.verify_mode = CERT_REQUIRED if check_cert else CERT_NONE
        ctx.check_hostname = check_host
        wrapper = ctx.wrap_socket
        if check_host:
            wrapper = add_hostname_to_context(wrapper, hostname)
        return wrapper

    def __init__(self, host, username='admin', password='', use_ssl=False):
        self.connection_args = {'host': host,
                                'username': username,
                                'password': password}
        if use_ssl:
            self.connection_args['ssl_wrapper'] = Node.create_ssl_wrapper(host)
            self.connection_args['port'] = 8729
        self.cm = ConnectionManager(**self.connection_args)

    def post(self, path: str, body: Dict[str, Any]) -> Tuple[Dict[str, str], int]:
        id = self.cm.add(path, body)
        return {'.id': id}, 201

    def patch(self, path: str, ids: Tuple[str, ...], body: Dict[str, Any]):
        id = ','.join(ids)
        body['.id'] = id
        self.cm.update(path, body)
        return '', 204  # No Content

    def get(self, path: str, limit: int = 10 ** 10,
              fields=None, where=None) -> Tuple[Dict[str, str], int]:
        if where and not fields:
            fields = ('.id',)
        if where is None:
            where = {}
        res = self.cm.print(path, fields,
                            tuple(Key(k) == v for (k, v) in where.items()), limit)
        return res, 200

    def delete(self, path, id=None, ids=None):
        if id:
            self.cm.remove(path, (id,))
        if ids:
            self.cm.remove(path, ids)
        return '', 204  # No Content
