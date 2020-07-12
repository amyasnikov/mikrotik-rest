from pathlib import Path
from settings import *

checks = []


def check_all():
    for check in checks:
        check()


class SettingsError(Exception):
    pass


def register(check_func):
    checks.append(check_func)
    return check_func


@register
def check_ssl():
    if API_TRANSPORT not in ('SSL', 'TCP'):
        raise SettingsError('API_TRANSPORT must be "SSL" or "TCP"')
    if SSL_CHECK_HOSTNAME and not SSL_CHECK_CERT:
        raise SettingsError('SSL_CHECK_CERT must be TRUE if SSL_CHECK_HOSTNAME is TRUE')
    ca_path = Path(SSL_CAFILE)
    if not ca_path.is_file():
        raise SettingsError(f'SSL_CAFILE: {ca_path.absolute()} does not exist')