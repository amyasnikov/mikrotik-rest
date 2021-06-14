
from enum import Enum, auto
from anytree import Node


class NodeType(Enum):
    SUBTREE = auto()
    CMD = auto()
    PARAM = auto()


class CliNode(Node):
    def __init__(self, name, type: NodeType, description='', **kwargs):
        self.type = type
        self.description = description
        super().__init__(name, **kwargs)

    def full_name(self, separator='/'):
        path = [node.name for node in self.path]
        path[0] = path[0].replace(' ', separator)
        name = separator.join(path)
        if name[:2] == '//':
            name = name[1:]
        return name

    def __str__(self):
        return self.full_name(separator=' ')

    def __repr__(self):
        return str(self) if self.type is NodeType.SUBTREE else self.name