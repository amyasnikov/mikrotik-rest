from typing import Tuple, Dict, Any, List
from librouteros.query import Key
from .connect import ConnectionManager


# GET - parameters in query
# POST, PATCH - parameters in body
# DELETE - parameters in query

class Node:

    def __init__(self, host, username='admin', password=''):
        self._host = host
        self._username = username
        self._password = password
        self.cm = ConnectionManager(host, username, password)

    def add(self, path: str, body: Dict[str, Any]) -> Tuple[Dict[str, str], int]:
        id = self.cm.add(path, body)
        return {'.id': id}, 201

    def set(self, path: str, ids: Tuple[str, ...], body: Dict[str, Any]):
        id = ','.join(ids)
        body['.id'] = id
        self.cm.update(path, body)
        return '', 204  # No Content

    def print(self, path: str, limit: int = 10 ** 10,
              fields=None, where=None) -> Tuple[Dict[str, str], int]:
        if where and not fields:
            fields = ('.id',)
        if where is None:
            where = {}
        res = self.cm.print(path, fields,
                            tuple(Key(k) == v for (k, v) in where.items()), limit)
        return res, 200

    def remove(self, path, id=None, ids=None):
        if id:
            self.cm.remove(path, (id,))
        if ids:
            self.cm.remove(path, ids)
        return '', 204  # No Content
