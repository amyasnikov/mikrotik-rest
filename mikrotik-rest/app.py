#!/usr/bin/env python3
import connexion
from misc import check_settings
from settings import  SPEC_FILE

check_settings.check_all()
app = connexion.FlaskApp('config-worker')
app.add_api(SPEC_FILE,
            arguments={'title': 'MT-WAN config-worker'})
# start werkzeug server instead of "$ uwsgi uwsgi.ini"
#app.run() 
