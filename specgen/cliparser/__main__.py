import sys

from anytree import RenderTree, AsciiStyle

from cliparser import Ssh, TreeBuilder


def get_tree(hostname='192.168.0.99',
             username='test',
             password='test',
             tree_root='/'):
    with Ssh(hostname, username, password) as ssh_client:
        tree_builder = TreeBuilder(ssh_client)
        tree = tree_builder.get_syntax_tree(tree_root)
        return RenderTree(tree, style=AsciiStyle)


if __name__ == "__main__":
    print(get_tree(*sys.argv[1:]))
