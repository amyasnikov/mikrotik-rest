#!/usr/bin/env python3
import sys
from collections import defaultdict

from anytree import PreOrderIter
from jinja2 import Template, Environment, FileSystemLoader
from pprint import pprint

from cliparser import CliParser
from translator import Translate


if __name__ == "__main__":
    host, username, password = '192.168.0.99', 'test', 'test'
    with CliParser(host, username, password) as cp:
        cp.add_filter(match=lambda x: x.type == 'cmd',
                      allow=lambda x: x.name in ('add', 'set', 'remove', 'print'))
        root = cp.get_syntax_tree('/console')
        endpoints = {}
        for node in PreOrderIter(root, filter_=lambda x: x.type == 'subtree'):
            endpoints[node.full_name()] = defaultdict(list)
            for command in filter(lambda x: x.type == 'cmd', node.children):
                endpoints[node.full_name()]['commands'].append(
                    Translate.to_http(command.name))
                if command.name == 'set':
                    endpoints[node.full_name()]['params'].extend(x.name for x in command.children)
        env = Environment(loader=FileSystemLoader('.'), trim_blocks=True, lstrip_blocks=True)
        template = env.get_template('spec_template.yaml')
#        pprint(endpoints)
        with open('spec.yaml', 'w') as f:
            f.write(template.render(endpoints=endpoints))



