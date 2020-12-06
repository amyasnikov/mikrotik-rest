import socket, time
from collections import defaultdict
from threading import RLock
from paramiko import SSHClient, AutoAddPolicy
from contextlib import contextmanager


class SafeModeError(Exception):
    """Raised when Mikrotik safe-mode entering failed"""
    pass


class AlreadyConnectedError(Exception):
    """Raised when there is another connection to the device"""
    pass


class Ssh:

    connected_hosts = defaultdict(RLock)

    def __init__(self, hostname: str, username: str, password: str, colored=True):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.colored = colored
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.shell = None

    def connect(self):
        if not Ssh.connected_hosts[self.hostname].acquire(timeout=10):
            raise AlreadyConnectedError(
                f'Device {self.hostname} is busy by another ssh conn'
            )
        transport = self.client.get_transport()
        if not (transport and transport.active):
            modificator = '+t300w' if self.colored else '+c300w'
            self.client.connect(
                hostname=self.hostname,
                username=self.username + modificator,
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
        self.shell.send(chr(3))  # Ctrl-C
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
        self.close()

    def close(self):
        self.client.close()
        Ssh.connected_hosts[self.hostname].release()
        del Ssh.connected_hosts[self.hostname]

    @contextmanager
    def safe_mode(self):
        try:
            time.sleep(3)
            self.send(chr(3))
            self.read_all()
            time.sleep(3)
            for _ in range(3):
                self.send(chr(0x18))  # Ctrl-X
                time.sleep(0.1)
                prompt = self.read_all()
                if '<SAFE>' in prompt:
                    break
            else:
                raise SafeModeError('Unable to get safe mode')
            yield
        finally:
            self.send(chr(0x18))
            self.read_all()
