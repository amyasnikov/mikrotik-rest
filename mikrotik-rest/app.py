#!/usr/bin/env python3
import connexion

app = connexion.FlaskApp('config-worker')
app.add_api('spec.yaml',
            arguments={'title': 'MT-WAN config-worker'})
#app.run()
application = app.app
