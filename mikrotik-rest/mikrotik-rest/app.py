#!/usr/bin/env python3
import connexion
from misc import check_settings
from settings import SPEC_FILE

check_settings.check_all()
app = connexion.FlaskApp('mikrotik-rest')
app.add_api(SPEC_FILE,
            arguments={'title': 'Mikrotik RESTful API'})

if __name__ == '__main__':
    app.run()
