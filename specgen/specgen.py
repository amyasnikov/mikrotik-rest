#!/usr/bin/env python3
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from anytree import PreOrderIter
from jinja2 import Environment, FileSystemLoader

from cliparser import TreeBuilder, CliNode, NodeType, Ssh, get_single_value
from method import Method


def prepare_endpoints_for_template(root_node: CliNode) \
        -> Tuple[Dict[str, Dict[str, Set[str]]], Dict[str, Dict[str, str]]]:
    endpoints = {}
    params = defaultdict(dict)
    for node in PreOrderIter(root_node, filter_=lambda x: x.type == NodeType.SUBTREE):
        node_fullname = node.full_name()
        endpoints[node_fullname] = defaultdict(set)
        for command in filter(lambda n: n.type == NodeType.CMD
                                        and n.name in ('add', 'set', 'remove', 'print'),
                              node.children):
            endpoints[node_fullname]['commands'].add(
                str(Method[command.name].to_http()))
            if command.name == 'set':
                for param in command.children:
                    params[node_fullname][param.name] = {'description': param.description}
                    params[node_fullname][param.name]['type'] = param.param_type
        if not params[node_fullname]:
            endpoints[node_fullname]['commands'] -= \
                set(str(method) for method in Method.unsafe_methods())
    return endpoints, params


class SpecGenerator:

    def __init__(self, ssh_client: Ssh, template_filename: str, parse_root: str):
        dir, file = os.path.split(template_filename)
        self.jinja_env = Environment(loader=FileSystemLoader(searchpath=dir),
                                     trim_blocks=True, lstrip_blocks=True)
        self.template = self.jinja_env.get_template(file)
        self.parse_root = parse_root
        self.ssh_client = ssh_client
        self.tree_builder = TreeBuilder(ssh_client)

    def get_spec(self) -> str:
        root_node = self.tree_builder.get_syntax_tree(self.parse_root)
        version = get_single_value(ssh_client=ssh_client,
                                   cmd='/system resource print',
                                   regexp=r'(?<=version: )[0-9.]+')
        endpoints, params = prepare_endpoints_for_template(root_node)
        return self.template.render(endpoints=endpoints,
                                    mikrotik_version=version,
                                    params=params)


if __name__ == "__main__":
    host, username, password = '192.168.0.99', 'test', 'test'
    with Ssh(host, username, password) as ssh_client:
        sg = SpecGenerator(ssh_client, 'spec_template.yaml', '/')
        with open('spec.yaml', 'w') as spec_file:
            spec_file.write(sg.get_spec())



