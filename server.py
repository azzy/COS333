#!/usr/bin/python

from bottle import route, run, request
import bottle
import string
import json
import hmac
import hashlib
from itertools import izip, cycle
# import pdb; pdb.set_trace()
# put the above line at break points.
# ------------------------------- HELPERS -------------------------------- #
def _save(dictionary, file):
    json_string = json.dumps(dictionary)
    with open (file, 'w') as f:
        f.write(json_string)

def _get(dictionary, id):
    try:
        return dictionary[id]
    except:
        raise AssertionError('id out of bounds')

def make_first_digest(message):
    ''' return a digest for the message.'''
    return hmac.new('secret-shared-key', message, hashlib.sha1).hexdigest()

def make_digest(message):
    ''' return a digest for the message.'''
    return hmac.new('hashed-password-or-uid', message, hashlib.sha1).hexdigest()

def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(key)))

users = json.loads(open('users.json', 'r').read())
events = json.loads(open('events.json', 'r').read())

#add user to user's friends list
def _add_friend(userid, friendid):
    global users
    user = _get(users, userid)
    if friendid not in user['friends']:
        user['friends'].append(friendid)
    return user

#remove user from user's friends list
def _remove_friend(userid, friendid):
    global users
    user = _get(users, userid)
    if friendid in user['friends']:
        user['friends'].remove(friendid)
    return user

#add user to event's guests list
def _add_guest(eventid, guestid):
    global events
    event = _get(events, eventid)
    if guestid is event['hostid']: # this line doesn't work. make it work.
        raise AssertionError('cannot invite the host')
    if guestid not in event['guests']:
        event['guests'][guestid] = 'no'
    return event

#remove user from event's guests list
def _remove_guest(eventid, guestid):
    global events
    event = _get(events, eventid)
    if guestid in event['guests']:
        del event['guests'][guestid]
    return event

#add event to user's invitations list
def _add_invitation(eventid, guestid):
    global users
    user = _get(users, guestid)
    if eventid not in user['invitations']:
        user['invitations'].append(eventid)
    return user

#remove event from user's invitations list
def _remove_invitation(eventid, guestid):
    global users
    user = _get(users, guestid)
    if eventid in user['invitations']:
        user['invitations'].remove(eventid)
    return user

#add event to user's events list
def _add_event(eventid, hostid):
    global users
    user = _get(users, hostid)
    if eventid not in user['events']:
         user['events'].append(eventid)
    return user

# ------------------------------ INTERFACE ------------------------------- #
# note: still need to go through and proof everything my error proofing is so off.
@route('/get_users')
def get_users():
    global users
    return json.dumps(users)

@route('/get_user')
def get_user():
    global users
    userid = request.GET.get('userid', None)
    user = _get(users, userid)
    return json.dumps(users[userid])

@route('/create_user')
def create_user(name, lastname, email, password):
    userid = len(users) + 1
    user = {'userid': userid,
            'name': name,
            'lastname': lastname,
            'email': email,
            'password': password,
            'friends': [],
            'invitations': [],
            'events': []
            }
    users[userid] = user
    _save(users, 'users.json')
    return json.dumps(user)

@route('/update_user')
def update_user():
    global users
    userid = request.GET.get('userid', None)
    name = request.GET.get('name', None)
    lastname = request.GET.get('lastname', None)
    email = request.GET.get('email', None)
    password = request.GET.get('password', None)
    user = _get(users,userid)
    if name is not None:
        user['name'] = name
    if lastname is not None:
        user['lastname'] = lastname
    if email is not None:
        user['email'] = email
    if password is not None:
        user['password'] = password
    users[userid] = user
    _save(users, 'users.json')
    return json.dumps(user)


# ----------------------- ROUTING/AUTH & RUNNING ---------------------------#

key = "okXRDgXqnDfyYK11nARRIdUy5xmuGsJi00DQuyzaGYY"
xor_key = "37xjAjWSE5pr2x6gXEsxKJMwcR7L54hXBY2bjz1UnCQmOS8Nm84ePMDCjyr7Sgt2YvP8lQRHB2gQlKehCWUMW4dPm2flhdZSwCU0LGWZdydSLS1C3OUvNsfjQPcWnuAqcQiAPMgMQf5AhIAtRmhPxNX9Gg1tUXtfMix1jJCgLkCwLiBKBJFsxq4oCUaeyfkudkc9QljacqadsF2jv9u7V3A"

def is_authenticated(userid, token):
    return token == gen_token(userid)

def gen_token(userid):
    return hmac.new(key, userid, hashlib.sha1).hexdigest()

@route('/')
def main():
    # plain needs to be a json dump of a dictionary like:
    # don't bother encrypting?
'''
{'userid': userid,
'token': token,
'method': method,
'args': {'name': name,
         'lastname': lastname }
}
request in format data?=encrypted-data
'''
    data = request.GET.get('data')
    plain = json.loads(xor_crypt_string(data, xor_key))
    userid = plain['userid']
    token = plain['token']
    method = plain['method']
    args = plain['args']
    if is_authenticated(userid, token):
        request = method + '('
        for k, v in args.iteritems():
            request += k '=' v
            
            request = method + 
        ret = eval(method + '()')
        new_sig = make_digest(data)
        encrypted = xor_crypt_string(data, key=my_key)
        m = {'sig': new_sig, 'data': encrypted }
        return json.dumps(m)



def verify():
'''not using this anymore. uses signatures instead of tokens'''
    my_key = 'another-secret-key'
    method = request.GET.get('method')
    sig = request.GET.get('sig')
    actual_digest = make_digest(method)
    if sig != actual_digest:
        print 'WARNING: Data corruption'
        return None
    else: 
        data = eval(method + '()')
        new_sig = make_digest(data)
        encrypted = xor_crypt_string(data, key=my_key)
        m = {'sig': new_sig, 'data': encrypted }
        return json.dumps(m)

run(host='ec2-50-17-119-54.compute-1.amazonaws.com',port=9000)
