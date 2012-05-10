#!/usr/bin/python

from meetme import _load_users, _save
import json
import sys

users = _load_users()
j = 0
for line in sys.stdin:
    j+=1
    words = line.split()
    name = words[0]
    try: lastname = words[1]
    except: lastname = 'Smith'
    if name[0:1] > 'p':
        email = name + '@gmail.com'
    else:
        email = name + '@hotmail.com'
    password = ''
    for i in range(0, len(name)):
        if i % 2 is 0:
            password += name[i:i+1]
        else:
            password += str(ord(name[i:i+1]))
    user = {'userid': j,
            'name': name,
            'lastname': lastname,
            'email': email,
            'password': password,
            'friends': [],
            'invitations': [],
            'events': []
            }
    users[j] = user
    _save(users, 'users.json')
    print user
    #sys.exit()
