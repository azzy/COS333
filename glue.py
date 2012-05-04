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
# Note: consider rewriting save/load so they save and load specific entries.
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

def _mark_modified(user, which, friendid, status):
    if not user.has_key('modified'):
        user['modified'] = { 'invitations': [],
                             'events': [] }
    if status is "yes" and friendid not in user['modified'][which]:
        user['modified'][which].append(friendid)
        user['modified'][which].append('all')
    elif friendid in user['modified'][which]:
        user['modified'][which].remove(friendid)
    return user

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

def _update_user(userid, name, lastname, email, phone):
    users = _load('users.json')
    if userid is None:
        userid = users['lastindex'] + 1
        users['lastindex'] += 1
    user = users.get(userid, {'friends':[],\
                              'invitations':{},\
                              'events':[],\
                              'modified': { 'invitations': [],
                                            'events': [] } })
    user['userid'] = userid
    if name is not None:
        user['name'] = name
    if lastname is not None:
        user['lastname'] = lastname
    if email is not None:
        user['email'] = email
    if phone is not None:
        user['phone'] = phone
    users[userid] = user
    _save(users, 'users.json')
    return user

#add users to event's guests list and events to users' invitations lists
def _add_guests(eventid, guestids):
    events = _load('events.json')
    users = _load('users.json')
    event = _get(events, eventid)
    hostid = event['hostid']
    host = users[hostid]
    if guestid is event['hostid']: # this line doesn't work. make it work.
        raise AssertionError('cannot invite the host')
    for guestid in guestids:
        guest = users[guestid]
        #add guest from event's perspective, event from guest's
        event['guests'][guestid] = 'no'
        guest['invitations'][eventid] = 'no'
        # mark data as modified from guest's perspective
        guest = _mark_modified(guest, 'invitations', hostid, 'yes')
        # mark data as modified from host's perspective
        host = _mark_modified(host, 'events', guestid, 'yes')
        users[guestid] = guest
    users[hostid] = host
    events[eventid] = event
    _save(events, 'events.json')
    _save(users, 'users.json')

#remove users from event's guests list and events from users' invitation lists
def _remove_guests(eventid, guestids):
    events = _load('events.json')
    users = _load('users.json')
    event = _get(events, eventid)
    hostid = event['hostid']
    host = users[hostid]
    for guestid in guestids:
        if guestid in event['guests']:
            guest = users[guestid]
            # remove the guest from event's perspective, event from guest's
            del event['guests'][guestid]
            del guest['invitations'][eventid]
            # mark data as modified from guest's perspective
            guest = _mark_modified(guest, 'invitations', hostid, 'yes')
            host = _mark_modified(host, 'events', guestid, 'yes')
            users[guestid] = user
    users[hostid] = host
    events[eventid] = event
    _save(events, 'events.json')
    _save(users, 'users.json')

#add event to user's events list
def _add_event(eventid, hostid):
    users = _load('users.json')
    user = _get(users, hostid)
    if eventid not in user['events']:
         user['events'].append(str(eventid))
    return user

def _is_hosting(userid, eventid):
    events = _load('events.json')
    event = events[eventid]
    return userid == event['hostid']

def _is_invited(userid, eventid):
    users = _load('users.json')
    user = users[userid]
    return user['invitations'].has_key(eventid)

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

@route('/get_self')
def get_self():
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
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
    phone = request.GET.get('phone', '')
    password = request.GET['password']
    if is_benign(key):
        user = _update_user(None, name, lastname, email, phone)
        _update_auth(user['userid'], email, password) #function handles the sha
        return json.dumps(user)
    else: return perror()
    
@route('/update_user')
def update_user():
    name = request.GET.get('name', None)
    lastname = request.GET.get('lastname', None)
    email = request.GET.get('email', None)
    phone = request.GET.get('phone', '')
    password = request.GET.get('password', None)
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        _update_auth(userid, email, password)
        user = _update_user(userid, name, lastname, email, phone)
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
        user['friends'].append(friendid)
        users[userid] = user
        _save(users, 'users.json')
        return "yes"
    else: return "no"

@route('/add_friends')
def add_friends():
    token = decode(request.GET['token'])
    friendids = request.GET['friendids'].split(',')
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _get(users, userid)
        for friendid in friendids:
            user['friends'].append(friendid)
        users[userid] = user
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
        user['friends'].remove(friendid)
        users[userid] = user
        _save(users, 'users.json')
        return "yes"
    else: return "no"

@route('/remove_friends')
def remove_friends():
    token = decode(request.GET['token'])
    friendids = request.GET['friendids'].split(',')
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _get(users, userid)
        for friendid in friendids:
            user['friends'].remove(friendid)
        users[userid] = user
        _save(users, 'users.json')
        return "yes"
    else: return "no"
    
@route('/is_modified')
def is_modified():
    token = decode(request.GET['token'])
    which = request.GET['which'] # I know... this is an awful name.
    friendid = request.GET.get('friendid', 'all')
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        modified = friendid in users[userid]['modified'][which]
        if modified is True: return "yes"
        else: return 'no'
    else: return 'failed'

@route('/rewrite_database')
def rewrite_database():
    key = request.GET.get('key', None)
    if is_benign(key):
        events = _load('events.json')
        users = _load('users.json')
        for userid, user in users.iteritems():
            new_invitations = {}
            print userid, user
            if isinstance(user, int):
                continue
            if isinstance(user['invitations'], dict):
                continue
            for eventid in user['invitations']:
                if eventid not in events.keys():
                    continue
                if userid not in events[eventid]['guests'].keys():
                    continue
                print events[eventid]['guests']
                print events[eventid]['guests'][userid]
                new_invitations[eventid] = events[eventid]['guests'][userid]
            user['invitations'] = new_invitations
            users[userid] = user
        _save(users,'users.json')
        return json.dumps(events) + json.dumps(users)
    else: return perror()

@route('/get_events')
def get_events():
    key = request.GET.get('key', None)
    if is_benign(key):
        events = _load('events.json')
        return json.dumps(events)
    else: return perror()

@route('/get_my_invitations')
def get_my_invitations():
    token = decode(request.GET['token'])
    hostid = request.GET.get('hostid', 'all')
    ret = {}
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        events = _load('events.json')
        user = _get(users, userid)
        # get the events
        for eventid in user['invitations'].keys():
            event = events[eventid]
            if hostid is 'all' or hostid is event['hostid']:
                ret[eventid] = event
        
        # mark the data as modified
        user = _mark_modified(user, 'invitations', hostid, 'no')
        users[userid] = user
        _save(users, 'users.json')
    return ret

@route('/get_my_events')
def get_my_events():
    token = decode(request.GET['token'])
    guestid = request.GET.get('guestid', 'all')
    ret = {}
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        events = _load('events.json')
        user = _get(users, userid)
        # get my events
        for eventid in user['events']:
            event = events[str(eventid)]
            if guestid is 'all' or guestid in event['guests']:
                ret[eventid] = event

        #mark the data as modified and save it
        user = _mark_modified(user, 'events', guestid, "no")
        users[userid] = user
        _save(users, 'users.json')
    return ret

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
    try: guestids = request.GET['guestids'].split(',')
    except: guestids = None
    if is_authenticated(token):
        hostid = token['userid']
        events = _load('events.json')
        users = _load('users.json')
        eventid = events['lastindex'] + 1
        events['lastindex'] += 1
        if guestids is not None:
            for guestid in guestids:
                guests[guestid] = 'no'
        else: guests = {}
        event = {'eventid': str(eventid),
                 'hostid' : hostid,
                 'name': name,
                 'category': category,
                 'location': location,
                 'starttime': starttime,
                 'endtime': endtime,
                 'description': description,
                 'guests': guests
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
    if is_authenticated(token):
        userid = token['userid']
        if _is_hosting(userid, eventid):
            events = _load('events.json')
            users = _load('users.json')
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
            for guestid in event['guests'].keys():
                guest = users[guestid]
                guest = _mark_modified(guest, 'invitations', userid, 'yes')
                users[guestid] = guest
            events[eventid] = event
        _save(events, 'events.json')
        _save(users, 'users.json')
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
            guest = users[guestid]
            del guest['invitations'][eventid]
            guest = _mark_modified(guest, 'invitations', userid, 'yes')
            users[guestid] = guest
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
        _add_guests(eventid, [guestid])
        return "yes"
    else: return "no"

@route('/add_guests')
def add_guests():
    eventid = request.GET['eventid']
    guestids = request.GET['guestids'].split(',')
    token = decode(request.GET['token'])
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        _add_guests(eventid, guestids)
        return "yes"
    else: return "no"

@route('/remove_guest')
def remove_guest():
    token = decode(request.GET['token'])
    eventid = request.GET['eventid']
    guestid = request.GET['guestid']
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        _remove_guests(eventid, [guestid])
        return "yes"
    else: return "no"

@route('/remove_guests')
def remove_guests():
    token = decode(request.GET['token'])
    guestids = request.GET['guestids'].split(',')
    eventid = request.GET['eventid']
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        _remove_guests(eventid, guestids)
        return "yes"
    else: return "no"

@route('/update_response')
def update_response():
    eventid = request.GET['eventid']
    response = request.GET.get('response', 'no')
    token = decode(request.GET['token'])
    guestid = token['userid']
    if is_authenticated(token) and _is_invited(guestid, eventid):
        #get the event and users
        users = _load('users.json')
        events = _load('events.json')
        event = _get(events, eventid)
        user = _get(users, userid)
        guest = _get(users, guestid)

        # add update response info of guest and event
        event['guests'][guestid] = response
        guest['invitations'][eventid] = response
        # mark event as modified by guest
        user = _mark_modified(user, 'events', guestid, 'yes')
        # mark event as modified from guests' perspective
        guest = _mark_modified(guest, 'invitations', userid, 'yes')
        
        # save the event and users
        events[eventid] = event
        users[guestid] = guest
        users[userid] = user
        _save(events, 'events.json')
        _save(users, 'users.json')
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
run(host='0.0.0.0', port=9000)

