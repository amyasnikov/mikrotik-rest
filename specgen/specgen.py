#!/usr/bin/env python3
import os
from collections import defaultdict
from typing import Dict, List
from pprint import pprint

from anytree import PreOrderIter
from jinja2 import Environment, FileSystemLoader

from cliparser import CliParser, CliNode
from translator import Translate


def prepare_endpoints_for_template(root_node: CliNode) -> Dict[str, Dict[str, List[str]]]:
    endpoints = {}
    for node in PreOrderIter(root_node, filter_=lambda x: x.type == 'subtree'):
        node_fullname = node.full_name()
        endpoints[node_fullname] = defaultdict(list)
        for command in filter(lambda x: x.type == 'cmd', node.children):
            endpoints[node_fullname]['commands'].append(
                Translate.to_http(command.name))
            if command.name == 'set':
                endpoints[node_fullname]['params'].extend(x.name for x in command.children)
            if not endpoints[node_fullname]['params']:
                endpoints[node_fullname]['commands'] = \
                    list(filter(lambda m: m not in ('post', 'patch', 'delete'),
                                endpoints[node_fullname]['commands']))
    pprint(endpoints)
    return endpoints


def parse_cli(parser: CliParser, parse_root: str) -> CliNode:
    with parser:
        parser.add_filter(match=lambda x: x.type == 'cmd',
                      allow=lambda x: x.name in ('add', 'set', 'remove', 'print'))
        return parser.get_syntax_tree(parse_root)


class SpecGenerator:

    def __init__(self, host, username, password, template_file: str, parse_root: str):
        dir, file = os.path.split(template_file)
        self.jinja_env = Environment(loader=FileSystemLoader(searchpath=dir),
                                     trim_blocks=True, lstrip_blocks=True)
        self.template = self.jinja_env.get_template(file)
        self.parse_root = parse_root
        self.parser = CliParser(host, username, password)

    def get_spec(self):
        with self.parser:
            self.parser.add_filter(match=lambda x: x.type == 'cmd',
                                   allow=lambda x: x.name in ('add', 'set', 'remove', 'print'))
            root_node = self.parser.get_syntax_tree(self.parse_root)
            version = self.parser.get_version()
        endpoints = prepare_endpoints_for_template(root_node)
        return self.template.render(endpoints=endpoints, mikrotik_version=version)


if __name__ == "__main__":
    host, username, password = '192.168.0.99', 'test', 'test'
    sg = SpecGenerator(host, username, password, 'spec_template.yaml', '/certificate')
    with open('spec.yaml', 'w') as f:
        f.write(sg.get_spec())



