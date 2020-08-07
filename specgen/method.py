from __future__ import annotations
from typing import Iterator
from enum import Enum, EnumMeta


class MethodEnumMeta(EnumMeta):
    def __getitem__(self, item):
        return super().__getitem__(item.upper())


class Method(Enum, metaclass=MethodEnumMeta):
    POST = 1
    GET = 2
    PATCH = 3
    DELETE = 4

    ADD = -1
    PRINT = -2
    SET = -3
    REMOVE = -4

    def __str__(self):
        return self.name.lower()

    def to_mikrotik(self) -> Method:
        return Method(-abs(self.value))

    def to_http(self) -> Method:
        return Method(abs(self.value))

    @classmethod
    def mikrotik_methods(cls) -> Iterator[Method]:
        return filter(lambda method: method.value < 0, iter(cls))

    @classmethod
    def http_methods(cls) -> Iterator[Method]:
        return filter(lambda method: method.value > 0, iter(cls))

    @classmethod
    def unsafe_methods(cls) -> Iterator[Method]:
        return filter(lambda method: abs(method.value) != 2, iter(cls))