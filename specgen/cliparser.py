import socket, re, time
from dataclasses import dataclass
from typing import Dict, Set, List, Callable
from anytree import Node, AsciiStyle, RenderTree
from paramiko import Channel, SSHClient, AutoAddPolicy


class CliNode(Node):
    def __init__(self, name, type='subtree', separator='/', **kwargs):
        self.type = type
        separator = separator
        super().__init__(name, **kwargs)

    def full_name(self, separator='/'):
        path = [node.name for node in self.path]
        path[0] = path[0].replace(' ', separator)
        return separator.join(path)

    def __str__(self):
        return self.full_name(' ')

    def __repr__(self):
        return str(self) if self.type == 'subtree' else self.name


@dataclass
class NodeFilter:
    match: Callable[[CliNode], bool]
    allow: Callable[[CliNode], bool]


class CliParser:

    menutypes = {
        'subtree': re.compile(r'(?<=\x1b\[m\x1b\[36m)[a-z -0-9]+?(?=\x1b\[m\x1b\[35m)'),
        'cmd': re.compile(r'(?<=\x1b\[m\x1b\[35m).+?(?=\x1b\[)', flags=re.DOTALL)
    }
    params = re.compile(r'(?<=value-name=).+?(?=\x1b\[9999B\[|\[\x1b\[m\x1b\[36m)', flags=re.DOTALL)
    expandable = re.compile(r'^.+?(?=\x1b)')

    @classmethod
    def trim_n_strip(cls, finds: List[str]) -> Set[str]:
        items = set()
        for entry in finds:
            entry = entry.replace('\x1b[m', '')
            entry = entry.replace('\r', '')
            entry = entry.replace('\n', ' ')
            items.update(entry.split(' '))
        try:
            items.remove('')
        except KeyError:
            pass
        return items

    @classmethod
    def find_leaves(cls, output_str: str) -> Dict[str, Set[str]]:
        leaves = {k: () for k in cls.menutypes}
        for t in cls.menutypes:
            search_res = cls.menutypes[t].findall(output_str)
            leaves[t] = cls.trim_n_strip(search_res)
        return leaves

    @classmethod
    def find_params(cls, output_str: str) -> Set[str]:
        search_res = cls.params.findall(output_str)
        return cls.trim_n_strip(search_res[0:1])

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

    def __read_all(self, timeout=1):
        if self.shell.gettimeout() != timeout:
            self.shell.settimeout(timeout)
        try:
            time.sleep(timeout/10)
            res = self.shell.recv(100000)
        except socket.timeout:
            res = b''
        return res.decode('utf-8')

    def get_syntax_tree(self, root='') -> CliNode:
        root_node = CliNode(root)
        self.__build_tree(root_node)
        return root_node

    def __get_tab_options(self, subtree, find_func, tab=' \t'):
        self.shell.send(chr(3))  # Ctrl-C
        self.__read_all()
        self.shell.send(subtree + tab)
        return find_func(self.__read_all())

    def __build_tree(self, current_node: CliNode):

        def get_params(path: str) -> List[str]:
            params = self.__get_tab_options(
                path + ' edit number=0 value-name=', CliParser.find_params)
            if params:
                params.add('.id')
            else:
                params = self.__get_tab_options(
                    path + ' edit value-name=', CliParser.find_params)
            expandables = tuple(filter(lambda x: '...' in x, params))
            for exp in expandables:
                params.remove(exp)
                exp_prefix = CliParser.expandable.findall(exp)[0]
                aux_params = self.__get_tab_options(
                    subtree=f'{path} edit value-name={exp_prefix}',
                    find_func=CliParser.find_params,
                    tab='\t\t')
                aux_params.remove(exp_prefix)
                params.update(aux_params)
            return sorted(params)

        path = str(current_node)
        items = self.__get_tab_options(path, CliParser.find_leaves)
        for subtree in sorted(items['subtree']):
            child = self.filter(CliNode(subtree, 'subtree', parent=current_node))
            if child:
                self.__build_tree(child)
        for cmd in sorted(items['cmd']):
            cmd_node = self.filter(CliNode(type='cmd', name=cmd, parent=current_node))
            if cmd_node and cmd == 'set':
                for param in get_params(path):
                    self.filter(CliNode(type='param', name=param, parent=cmd_node))

    def filter(self, node: CliNode):
        for nf in self.__node_filters:
            if nf.match(node):
                if nf.allow(node):
                    return node
                else:
                    node.parent = None
                    del node
                    return None
        return node

    def add_filter(self, match, allow):
        self.__node_filters.append(NodeFilter(match, allow))

    def clear_filters(self):
        self.__node_filters = []


if __name__ == '__main__':
    with CliParser('192.168.0.99', 'test', 'test') as cp:
#        cp.add_filter(match=lambda x: x.type == 'cmd',
#                      allow=lambda x: x.name != 'comment')
        tree = cp.get_syntax_tree('/interface bridge mdb')
        print(RenderTree(tree, style=AsciiStyle))
