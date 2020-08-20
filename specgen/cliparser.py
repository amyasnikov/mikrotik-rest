import socket, re, time
from dataclasses import dataclass
from typing import Dict, Set, List, Callable, Iterator

from anytree import Node, AsciiStyle, RenderTree
from paramiko import SSHClient, AutoAddPolicy
from cliparser2 import TreeBuilder

class CliNode(Node):
    def __init__(self, name, type, description='', **kwargs):
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
        return self.full_name(' ')

    def __repr__(self):
        return str(self) if self.type == 'subtree' else self.name


@dataclass(frozen=True)
class NodeFilter:
    match: Callable[[CliNode], bool]
    allow: Callable[[CliNode], bool]


class CliParser:

    menutypes = {
        'subtree': re.compile(r'(?<=\x1b\[m\x1b\[36m)[a-z \-0-9]+?(?=\x1b\[m\x1b\[35m)'),
        'cmd': re.compile(r'(?<=\x1b\[m\x1b\[35m).+?(?=\x1b\[)', flags=re.DOTALL)
    }
    params = re.compile(r'([a-z.-0-9<>]+) +-- +([a-z.-0-9A-Z ]*)',
                        flags=re.DOTALL)

    @classmethod
    def find_leaves(cls, output_str: str) -> Iterator[CliNode]:
        def trim_n_strip(finds: List[str]) -> Set[str]:
            bad_chars = ('\x1b[m', '\r')
            items = set()
            for entry in finds:
                for bad_char in bad_chars:
                    entry = entry.replace(bad_char, '')
                entry = entry.replace('\n', ' ')

                items.update(entry.split(' '))
            try:
                items.remove('')
            except KeyError:
                pass
            return items

        for type_ in cls.menutypes:
            search_res = cls.menutypes[type_].findall(output_str)
            yield from map(lambda name: CliNode(name, type_),
                           trim_n_strip(search_res))

    @classmethod
    def find_params(cls, output_str: str) -> Iterator[CliNode]:
        def get_clinode(match: re.Match) -> CliNode:
            name = match.group(1)
            if name == '<numbers>':
                name = '.id'
            descr = match.group(2)
            description = {'description': descr} if descr else {}
            return CliNode(name=name, type='param', **description)

        bad_chars = ('\x1b[m\x1b[33m', '\x1b[m\x1b[32m', '\x1b[m')
        for char in bad_chars:
            output_str = output_str.replace(char, '')
        yield from map(get_clinode, cls.params.finditer(output_str))

    def __init__(self, hostname, username, password):
        self.__node_filters = []
        self.username = username
        self.password = password
        self.hostname = hostname
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.shell = None

    def connect(self):
        transport = self.client.get_transport()
        if not (transport and transport.active):
            self.client.connect(
                hostname=self.hostname,
                username=self.username + '+t300w',
                password=self.password,
                look_for_keys=False,
                allow_agent=False)
            self.shell = self.client.invoke_shell()
            self.__read_all()

    def __enter__(self):
        self.connect()
        self.shell.send(
            '/system logging disable [find where action=echo disabled=no]\n')
        self.__read_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shell.send(
            '/system logging enable [find where action=echo disabled=yes]\n')
        self.client.close()

    def __read_all(self, timeout=1) -> str:
        if self.shell.gettimeout() != timeout:
            self.shell.settimeout(timeout)
        try:
            time.sleep(timeout/10)
            res = self.shell.recv(100000)
        except socket.timeout:
            res = b''
        return res.decode('utf-8')

    def get_syntax_tree(self, root='/') -> CliNode:
        root_node = CliNode(root, type='subtree')
        self.__build_tree(root_node, CliParser.find_leaves)
        return root_node

    def __get_tab_options(self,
                          subtree: str,
                          find_func: Callable[[str], Iterator[CliNode]],
                          tab: str) -> Iterator[CliNode]:
        self.shell.send(chr(3))  # Ctrl-C
        self.__read_all()
        self.shell.send(subtree + tab)
        yield from find_func(self.__read_all())

    def __build_tree(self,
                     current_node: CliNode,
                     find_func: Callable[[str], Iterator[CliNode]],
                     tab: str = ' \t'):
        path = str(current_node)
        items_iter = self.__get_tab_options(path, find_func, tab=tab)
        items_iter = self.filter(items_iter)
        for item in items_iter:
            item.parent = current_node
            if item.type == 'subtree':
                self.__build_tree(item, CliParser.find_leaves)
            elif item.type == 'cmd' and item.name == 'set':
                self.__build_tree(item, CliParser.find_params, tab=' ?')
#            elif item.type == 'param':



    def filter(self, nodes: Iterator[CliNode]) -> Iterator[CliNode]:
        def allow(node: CliNode) -> bool:
            for filter_ in self.__node_filters:
                if filter_.match(node):
                    return filter_.allow(node)
            return True
        yield from filter(allow, nodes)

    def add_filter(self, match, allow):
        self.__node_filters.append(NodeFilter(match, allow))

    def clear_filters(self):
        self.__node_filters = []

    def get_version(self):
        _, stdout, _ = self.client.exec_command('/system resource print')
        output = stdout.read().decode('utf8')
        version = re.search(r'(?<=version: )[0-9.]+', output).group(0)
        return version


if __name__ == '__main__':
#    with CliParser('192.168.0.99', 'test', 'test') as cp:
#        cp.add_filter(match=lambda x: x.type == 'param',
#                      allow=lambda x: x.name != 'vlan-id')
    with TreeBuilder ('192.168.0.99', 'test', 'test') as cp:
        tree = cp.get_syntax_tree('/certificate')
    print(RenderTree(tree, style=AsciiStyle))
