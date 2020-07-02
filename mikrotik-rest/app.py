#!/usr/bin/env python3

import connexion

if __name__ == '__main__':
    app = connexion.FlaskApp('config-worker')
    app.add_api('spec.yaml',
                arguments={'title': 'MT-WAN config-worker'})
    app.run(port=8080)
