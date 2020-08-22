import re
from dataclasses import dataclass
from typing import List, Callable
from enum import Enum

from .ssh import Ssh
from .parser import Parser
from .clinode import CliNode, NodeType


class Parsers(Enum):
    SUBTREE = Parser(re.compile(r'(?<=\x1b\[m\x1b\[36m)[a-z \-0-9]+?(?=\x1b\[m\x1b\[35m)'),
                     Parser.find_leaves)

    CMD = Parser(re.compile(r'(?<=\x1b\[m\x1b\[35m).+?(?=\x1b\[)', flags=re.DOTALL),
                 Parser.find_leaves)

    PARAM = Parser(re.compile(r'([a-z.-0-9<>]+) +-- +([a-z.-0-9A-Z ]*)', flags=re.DOTALL),
                   Parser.find_params)

    PARAM_TYPE = Parser(re.compile(r'(?<=::=).+?(?=\r\n)'), Parser.find_param_type)

    def node_type(self) -> NodeType:
        try:
            return NodeType[self.name]
        except KeyError:
            raise KeyError(f'{str(self)} is not in NodeType enum')


@dataclass
class ParseRule:
    search_for: List[Parsers]
    ending: str = ' \t'
    create_new_node: bool = True
    do_recursion: Callable[[CliNode], bool] = lambda node: True


class TreeBuilder:
    rules = {
        NodeType.CMD: ParseRule([Parsers.PARAM], ' ?'),
        NodeType.SUBTREE: ParseRule([Parsers.SUBTREE, Parsers.CMD],
                                    do_recursion=lambda node: node.type == NodeType.SUBTREE
                                                              or node.name == 'set'),
        NodeType.PARAM: ParseRule([Parsers.PARAM_TYPE], '=?',
                                  create_new_node=False,
                                  do_recursion=lambda node: False)
    }

    def __init__(self, ssh: Ssh):
        self.ssh = ssh

    def get_syntax_tree(self, root='/') -> CliNode:
        root_node = CliNode(root, type=NodeType.SUBTREE)
        self.__build_tree(root_node)
        return root_node

    def __build_tree(self, current_node: CliNode):
        path = str(current_node)
        parse_rule = TreeBuilder.rules[current_node.type]
        self.ssh.send(path + parse_rule.ending)
        output = self.ssh.read_all()
        for parser in parse_rule.search_for:
            for node_fields in parser.value.finditer(output):
                if parse_rule.create_new_node:
                    new_node = CliNode(type=parser.node_type(),
                                       parent=current_node,
                                       **node_fields)
                else:
                    current_node.__dict__.update(node_fields)
                    new_node = current_node
                if parse_rule.do_recursion(new_node):
                    self.__build_tree(new_node)


