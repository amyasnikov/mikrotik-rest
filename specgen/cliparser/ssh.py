import socket, time

from paramiko import SSHClient, AutoAddPolicy


class Ssh:

    def __init__(self, hostname: str, username: str, password: str):
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
            self.read_all()

    def read_all(self, timeout=1) -> str:
        if self.shell.gettimeout() != timeout:
            self.shell.settimeout(timeout)
        try:
            time.sleep(timeout/10)
            res = self.shell.recv(1000000)
        except socket.timeout:
            res = b''
        return res.decode('utf-8', errors='replace')

    def send(self, string: str):
        self.shell.send(chr(3)) # Ctrl-C
        self.read_all()
        self.shell.send(string)

    def __enter__(self):
        self.connect()
        self.client.exec_command(
            '/system logging disable [find where action=echo disabled=no]')
        self.read_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.exec_command(
            '/system logging enable [find where action=echo disabled=yes]')
        self.client.close()