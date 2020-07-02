from typing import Tuple, Generator, NewType, Iterable, Dict, Union, Any

import librouteros as ros
from threading import Lock
from expiringdict import ExpiringDict
from settings import MAX_CONN_PER_HOST, CONN_TIMEOUT


Where = NewType('Where', Generator[str, None, None])
MtEntry = NewType('MtEntry', Dict[str, Any])


def counter():
    i = 0
    while True:
        yield i
        i += 1


class Locked:
    def __init__(self):
        self.lock = Lock()

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, type, value, traceback):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

    def locked(self):
        return self.lock.locked()


class LockedApi(Locked, ros.Api):

    def __init__(self, api):
        self.__dict__ = dict(api.__dict__)
        Locked.__init__(self)

"""
class LockedDeque(Locked, deque):

    def __init__(self, iterable):
        super(Locked, self).__init__()
        super(deque, self).__init__(iterable)
"""


def connect(host, username, password, *args, **kwargs):
    api = ros.connect(host, username, password, *args, **kwargs)
    lapi = LockedApi(api)
    return lapi


class ConnectionManager:

    def __init__(self, host, user, password):
        self.user = user
        self.password = password
        self.host = host
        self._cnt = counter()
        api = connect(host, user, password)
        #TODO: move params to settings
        self.connections = ExpiringDict(max_len=MAX_CONN_PER_HOST,
                                        max_age_seconds=CONN_TIMEOUT,
                                        items={self._id: api})

    @property
    def _id(self) -> int:
        return next(self._cnt)

    def _acquire_api(self):
        with self.connections.lock:
            for api in self.connections.values():
                if not api.locked():
                    api.acquire()
                    free_api = api
                    break
            else:
                free_api = connect(self.host, self.user, self.password)
                free_api.acquire()
                self.connections[self._id] = free_api
            return free_api

    def _cur(self, op: str, path: str, *remove_params: Tuple[str, ...], **params: MtEntry):
        api = self._acquire_api()
        # TODO: add exceptions handling
        try:
            method = getattr(api.path(path), op)
            return method(*remove_params, **params)
        finally:
            api.release()

    def add(self, path: str, params: MtEntry) -> str:
        return self._cur('add', path, **params)

    def update(self, path: str, params: MtEntry):
        self._cur('update', path, **params)

    def remove(self, path: str, ids: Iterable[str]):
        self._cur('remove', path, *ids)

    def print(self, path: str, fields: Tuple[str, ...] = (),
              where_fields: Tuple[Where, ...] = (), limit: int = 10 ** 10) -> Tuple[MtEntry, ...]:
        api = self._acquire_api()
        try:
            query = api.path(path)
            if fields:
                query = query.select(*fields)
            if where_fields:
                query = query.where(*where_fields)
            c = counter()
            return tuple(i for i in query if next(c) < limit)
        finally:
            api.release()
