import re
from .tree_builder import TreeBuilder
from .clinode import NodeType, CliNode
from .ssh import Ssh


def get_single_value(ssh_client: Ssh, cmd: str, regexp: str):
    _, stdout, _ = ssh_client.client.exec_command(cmd)
    output = stdout.read().decode('utf8')
    return re.search(regexp, output).group(0)