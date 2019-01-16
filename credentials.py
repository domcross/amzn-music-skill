#!/usr/bin/env python

import base64
import pickle
from getpass import getpass
try:
    input = raw_input
except NameError:
    pass

e = base64.b64encode(str(input('Login/Email: ')).encode('ascii'))
p = base64.b64encode(getpass('Password (input is hidden): ').encode('ascii'))

credentials = {'e': e, 'p': p}

with open('/opt/mycroft/skills/amzn-music-skill.domcross/credentials.store', 'wb') as f:
    pickle.dump(credentials, f, pickle.HIGHEST_PROTOCOL)
