#!/usr/bin/python

from bottle import route, run, request, server_names, ServerAdapter
import bottle
import string
import json
import hmac
import hashlib
# import pdb; pdb.set_trace()
# put the above line at break points.

# ---------------------------- AUTH HELPERS ------------------------------ #
secret_key = "okXRDgXqnDfyYK11nARRIdUy5xmuGsJi00DQuyzaGYY"

def perror():
    return "Intruder Alert!"

def is_benign(key):
    global secret_key
    if key is None: return False
    return key == secret_key

def is_authenticated(token):
    if token is None: return False
    return token['token'] == gen_token(token['userid'])
    
def gen_token(userid):
    return hmac.new(secret_key, userid, hashlib.sha1).hexdigest()

def make_digest(message):
    ''' return a digest for the message.'''
    return hmac.new(secret_key, message, hashlib.sha224).hexdigest()

def encode(dictionary):
    ret = ''
    for k, v in dictionary.iteritems():
        ret += str(k) + '+' + str(v) + '|'
    return ret[:-1]

def decode(s):
    try: 
        ret = {}
        pairs = s.split('|')
        print pairs
        for pair in pairs:
            (k,v) = pair.split(' ', 1)
            ret[k] = v
        return ret
    except:
        return None

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

def _load(filename):
    return json.loads(open(filename, 'r').read())
#users = json.loads(open('users.json', 'r').read())
#events = json.loads(open('events.json', 'r').read())
#auth = json.loads(open('auth.json', 'r').read())

def _update_auth(userid, email, password):
    auth = _load('auth.json')
    auth_entry = auth.get(userid, {})
    auth_entry['userid'] = userid
    if email is not None:
        auth_entry['email'] = email
    if password is not None:
        auth_entry['password'] = make_digest(password)
    auth[userid] = auth_entry
    _save(auth, 'auth.json')

def _update_user(userid, name, lastname, email):
    users = _load('users.json')
    if userid is None:
        userid = users['lastindex'] + 1
        users['lastindex'] += 1
    user = users.get(userid, {'friends':[], \
                                  'invitations':[], 'events':[]})
    user['userid'] = userid
    if name is not None:
        user['name'] = name
    if lastname is not None:
        user['lastname'] = lastname
    if email is not None:
        user['email'] = email
    users[userid] = user
    _save(users, 'users.json')
    return user

#add user to user's friends list
def _add_friend(userid, friendid):
    users = _load('users.json')
    user = _get(users, userid)
    if friendid not in user['friends']:
        user['friends'].append(friendid)
    return user

#remove user from user's friends list
def _remove_friend(userid, friendid):
    users = _load('users.json')
    user = _get(users, userid)
    if friendid in user['friends']:
        user['friends'].remove(friendid)
    return user

#add user to event's guests list
def _add_guest(eventid, guestid):
    events = _load('events.json')
    event = _get(events, eventid)
    if guestid is event['hostid']: # this line doesn't work. make it work.
        raise AssertionError('cannot invite the host')
    if guestid not in event['guests']:
        event['guests'][guestid] = 'no'
    return event

#remove user from event's guests list
def _remove_guest(eventid, guestid):
    events = _load('events.json')
    event = _get(events, eventid)
    if guestid in event['guests']:
        del event['guests'][guestid]
    return event

#add event to user's invitations list
def _add_invitation(eventid, guestid):
    users = _load('users.json')
    user = _get(users, guestid)
    if eventid not in user['invitations']:
        user['invitations'].append(eventid)
    return user

#remove event from user's invitations list
def _remove_invitation(eventid, guestid):
    users = _load('users.json')
    user = _get(users, guestid)
    if eventid in user['invitations']:
        user['invitations'].remove(eventid)
    return user

#add event to user's events list
def _add_event(eventid, hostid):
    users = _load('users.json')
    user = _get(users, hostid)
    if eventid not in user['events']:
         user['events'].append(eventid)
    return user

def _is_hosting(userid, eventid):
    events = _load('events.json')
    event = events[eventid]
    return userid == event['hostid']

def _is_invited(userid, eventid):
    users = _load('users.json')
    user = users[userid]
    return eventid in user['invitations']

# ------------------------------ INTERFACE ------------------------------- #
# note: still need to go through and proof everything my error proofing is so off.
@route('/login')
def login():
    auth = _load('auth.json')
    email = request.GET['email']
    password = make_digest(request.GET['password'])
    print password
    # assume that we connected through SSL
    for i, entry in auth.iteritems():
        print i, entry['password'], entry['email']
        if entry['email'] == email and entry['password'] == password:
            userid = entry['userid']
            return encode({'userid': userid, 'token':gen_token(str(userid))})
    return "Authentication Failed"

@route('/get_users')
def get_users():
    key = request.GET.get('key', None)
    if is_benign(key):
        users = _load('users.json')
        return json.dumps(users)
    else: return perror()

@route('/get_user')
def get_user():
    userid = request.GET['userid']
    key = request.GET.get('key', None)
    if is_benign(key):
        users = _load('users.json')
        user = _get(users, userid)
        return json.dumps(user)
    else: return perror()

@route('/get_auth')
def get_auth():
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        auth = _load('auth.json')
        entry = _get(auth, userid)
        return json.dumps(entry)
    else: return perror()

@route('/create_user')
def create_user():
    key = request.GET.get('key', None)
    name = request.GET['name']
    lastname = request.GET.get('lastname', '')
    email = request.GET['email']
    password = request.GET['password']
    if is_benign(key):
        user = _update_user(None, name, lastname, email)
        _update_auth(user['userid'], email, password) #function handles the sha
        return json.dumps(user)
    else: return perror()
    
@route('/update_user')
def update_user():
    name = request.GET.get('name', None)
    lastname = request.GET.get('lastname', None)
    email = request.GET.get('email', None)
    password = request.GET.get('password', None)
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        _update_auth(userid, email, password)
        user = _update_user(userid, name, lastname, email)
        return user
    else: return perror()

@route('/remove_user')
def remove_user():
    try:
        token = decode(request.GET['token'])
    except: return "no"
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        auth = _load('auth.json')
        del users[userid]
        del auth[userid]
        _save(users, 'users.json')
        _save(auth, 'auth.json')
        return "yes"
    else: return "no"

@route('/get_friends')
def get_friends():
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _get(users, userid)
        return json.dumps(user['friends'])
    else: return perror()

@route('/add_friend')
def add_friend():
    token = decode(request.GET['token'])
    friendid = request.GET['friendid']
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _add_friend(userid, friendid)
        #friend = _add_friend(friendid, userid) 
        # note that friend won't necessarily add you back.
        users[userid] = user
        #users[friendid] = friend
        _save(users, 'users.json')
        return "yes"
    else: return "no"

@route('/remove_friend')
def remove_friend():
    friendid = request.GET['friendid']
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _remove_friend(userid, friendid)
        #friend = _remove_friend(friendid, userid)
        users[userid] = user
        #users[friendid] = friend
        _save(users, 'users.json')
        return "yes"
    else: return "no"

@route('/get_events')
def get_events():
    key = request.GET.get('key', None)
    if is_benign(key):
        events = _load('events.json')
        return json.dumps(events)
    else: return perror()

@route('/get_event')
def get_event():
    token = decode(request.GET['token'])
    if not is_authenticated(token):
        return perror() + ' on token'
    eventid = request.GET.get('eventid', None)
    events = _load('events.json')
    event = _get(events, eventid)
    userid = token['userid']
    if _is_hosting(userid, eventid) or _is_invited(userid, eventid):
        return json.dumps(event)
    else: return perror() + ' on userid'

@route('/create_event')
def create_event():
    token = decode(request.GET['token']) 
    name = request.GET.get('name', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    starttime = request.GET.get('starttime', '')
    endtime = request.GET.get('endtime', '')
    description = request.GET.get('description', '')
    if is_authenticated(token):
        hostid = token['userid']
        events = _load('events.json')
        users = _load('users.json')
        eventid = events['lastindex'] + 1
        events['lastindex'] += 1
        event = {'eventid': eventid,
                 'hostid' : hostid,
                 'name': name,
                 'category': category,
                 'location': location,
                 'starttime': starttime,
                 'endtime': endtime,
                 'description': description,
                 'guests': {}
                 }
        user = _add_event(eventid, hostid)
        events[eventid] = event
        users[hostid] = user
        _save(events, 'events.json')
        _save(users, 'users.json')
        return json.dumps(event)
    else: return perror()

@route('/update_event')
def update_event():
    eventid = request.GET.get('eventid', None)
    token = decode(request.GET['token'])
    name = request.GET.get('name', None)
    category = request.GET.get('category', None)
    location = request.GET.get('location', None)
    starttime = request.GET.get('starttime', None)
    endtime = request.GET.get('endtime', None)
    description = request.GET.get('description', None)
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        events = _load('events.json')
        event = _get(events, eventid)
        if name is not None:
            event['name'] = name
        if category is not None:
            event['category'] = category
        if location is not None:
            event['location'] = location
        if starttime is not None:
            event['starttime'] = starttime
        if endtime is not None:
            event['endtime'] = endtime
        if description is not None:
            event['description'] = description
        events[eventid] = event
        _save(events, 'events.json')
        return json.dumps(event)
    else: return perror()

@route('/remove_event')
def remove_event():
    eventid = request.GET['eventid']
    try:
        token = decode(request.GET['token'])
    except: return "no"
    if not is_authenticated(token): return "no"
    userid = token['userid']
    events = _load('events.json')
    users = _load('users.json')
    if eventid not in events:
        return "event does not exist"
    if _is_hosting(userid, eventid):
        for guestid, response in events[eventid]['guests'].iteritems():
            _remove_invitation(eventid, guestid)
        del users[userid]['events'][eventid]
        del events[eventid]
        _save(users, 'users.json')
        _save(events, 'events.json')
        return "yes"
    else: return "no"

@route('/get_guests')
def get_guests():
    token = decode(request.GET['token'])
    eventid = request.GET['eventid']
    userid = token['userid']
    if is_authenticated(token) \
            and _is_hosting(userid, eventid) \
            or _is_invited(userid, eventid):
        events = _load('events.json')
        event = _get(events, eventid)
        return json.dumps(event['guests'])
    else: return perror()

@route('/add_guest')
def add_guest():
    eventid = request.GET['eventid']
    guestid = request.GET['guestid']
    token = decode(request.GET['token'])
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        users = _load('users.json')
        events = _load('events.json')
        user = _add_invitation(eventid, guestid)
        event = _add_guest(eventid, guestid)
        users[guestid] = user
        events[eventid] = event
        _save(events, 'events.json')
        _save(users, 'users.json')
        return "yes"
    else: return "no"

@route('/remove_guest')
def remove_guest():
    token = decode(request.GET['token'])
    eventid = request.GET['eventid']
    guestid = request.GET['guestid']
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        users = _load('users.json')
        events = _load('events.json')
        user = _remove_invitation(eventid, guestid)
        event = _remove_guest(eventid, guestid)
        users[guestid] = user
        events[eventid] = event
        _save(events, 'events.json')
        _save(users, 'users.json')
        return "yes"
    else: return "no"
@route('/update_response')
def update_response():
    eventid = request.GET['eventid']
    response = request.GET.get('response', 'no')
    token = decode(request.GET['token'])
    guestid = token['userid']
    if is_authenticated(token) and _is_invited(guestid, eventid):
        users = _load('users.json')
        events = _load('events.json')
        event = _get(events, eventid)
        event['guests'][guestid] = response
        events[eventid] = event
        _save(events, 'events.json')
        return "yes"
    else: return "no"

# ----------------------- ROUTING/AUTH & RUNNING ---------------------------#

class MySSLCherryPy(ServerAdapter):
    def run(self, handler):
        from cherrypy import wsgiserver
        server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler)
        cert = '/root/COS333/server.pem'
        ssl = wsgiserver.SSLAdapter(cert, cert)
        server.ssl_addapter = ssl
        try:
            server.start()
        finally:
            server.stop()

server_names['mysslcherrypy'] = MySSLCherryPy

# SSL connection:
# run(host='0.0.0.0', port=443, server='mysslcherrypy')

# non secure connection:
run(host='0.0.0.0', port=8080)

