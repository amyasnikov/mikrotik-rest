import os

# default username and password for login on routers
USERNAME = os.environ.get('MIKROTIK_USER','test')
PASSWORD = os.environ.get('MIKROTIK_PASSWD','test')

# openapi specification file
SPEC_FILE = 'api/spec.yaml'

# Maximum simultaneous connections stored per host (length of list)
# More than that will be dropped after the end of operation
MAX_CONN_PER_HOST = 10
# Idle open connection will be dropped after this timeout
CONN_TIMEOUT = 120

API_TRANSPORT = 'TCP'  # 'SSL' or 'TCP'
SSL_CHECK_CERT = True
SSL_CHECK_HOSTNAME = True
SSL_CAFILE = 'misc/rootCA.crt'
