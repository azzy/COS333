#!/usr/bin/python

from bottle import route, run, request, server_names, ServerAdapter, static_file
import bottle
import string, re, time
import json
import hmac
import hashlib
# import pdb; pdb.set_trace()
# put the above line at break points.

# ---------------------------- AUTH HELPERS ------------------------------ #
secret_key = "okXRDgXqnDfyYK11nARRIdUy5xmuGsJi00DQuyzaGYY"

def perror(code):
    if code == 0:
        return "Authentication Failed"
    if code == 1:
        return "Event does not exist"
    if code == 2:
        return "User does not exist"

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
    if status is "yes" and friendid not in user['modified'][which]:
        user['modified'][which].append(friendid)
    if status is "yes" and 'all' not in user['modified'][which]:
        user['modified'][which].append('all')
    if status is "no" and friendid in user['modified'][which]:
        user['modified'][which].remove(friendid)
    print json.dumps(user)
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
        userid = str(users['lastindex'] + 1)
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
    #user['time'] = time.time()
    users[userid] = user
    _save(users, 'users.json')
    return user

#add users to event's guests list and events to users' invitations lists
def _add_guests(eventid, guestids):
    events = _load('events.json')
    users = _load('users.json')
    try: event = events[eventid]
    except: 
        print perror(1), eventid
        return
    hostid = event['hostid']
    try: host = users[hostid]
    except:
        print perror(2), hostid, "so removed event"
        _remove_event(eventid)
        return
    for guestid in guestids:
        if guestid == event['hostid']:
            raise AssertionError('cannot invite the host')
        try: guest = users[guestid]
        except:
            print perror(2), guestid
            continue
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
    try: event = events[eventid]
    except:
        print perror(1), eventid
        return
    hostid = event['hostid']
    try: host = users[hostid]
    except:
        print perror(2), hostid, "so removed event"
        _remove_event(eventid)
        return
    for guestid in guestids:
        if guestid in event['guests']:
            try: guest = users[guestid]
            except:
                print "user does not exist with id", guestid
                del event['guests'][guestid]
                host = _mark_modified(host, 'events', guestid, 'yes')
                events[eventid] = event
                _save(events, 'events.json')
                return
            # remove the guest from event's perspective, event from guest's
            del event['guests'][guestid]
            del guest['invitations'][eventid]
            # mark data as modified from guest's perspective
            guest = _mark_modified(guest, 'invitations', hostid, 'yes')
            host = _mark_modified(host, 'events', guestid, 'yes')
            users[guestid] = guest
    users[hostid] = host
    events[eventid] = event
    _save(events, 'events.json')
    _save(users, 'users.json')

#add event to user's events list
def _add_event(eventid, hostid):
    users = _load('users.json')
    user = users[hostid]
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
    return user['invitations'].has_key(eventid)

# --------------------------------- REGEX HELPERS----------------------------#

def _like(a, b):
    # returns True if string a is like substring b
    pattern = re.compile(b.lower() + ".*")
    return pattern.search(a.lower()) is not None

def _starts_with(a, b):
    # returns True if string a starts with substring b
    pattern = re.compile(b.lower() + ".*")
    return pattern.match(a.lower()) is not None

def _intersect(a, b):
    # returns True if at least half of list b is in list a
    match = 0
    if a is None or b is None: return True
    for item in a:
        if item in b:
            match += 1
    return (match / len(b)) > 0.5

# ------------------------------ INTERFACE ------------------------------- #
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

@route('/find_users')
def find_users():
    key = request.GET['key']
    try: 
        name = request.GET['name'].split()
        firstname = name[0]
        try: lastname = name[1]
        except: lastname = ''
    except: 
        firstname = ''
        lastname = ''
    #search snippet includes first and last
    email = request.GET.get('email', '') #search snippet is in email
    phone = request.GET.get('phone', '') #search snippet is part of phone number
    try: friendids = request.GET['friendids'].split(',') 
    except: friendids = None
    # list of some friends this friend is friends with
    # this should return in ranked order of number of friends matche
    if is_benign(key):
        ret = {}
        users = _load('users.json')
        for userid, user in users.iteritems():
            if isinstance(user, int): continue
            if _starts_with(user['name'], firstname)\
                    and _starts_with(user['lastname'], lastname)\
                    and _like(user['email'], email)\
                    and _starts_with(user['phone'], phone) \
                    and _intersect(user['friends'], friendids):
                ret[user['userid']] = user
#note I'm going to get errors here until I add in the phone
            else: continue
        return json.dumps(ret)
    else: return perror(0)

@route('/search_users')
def search_users():
    key = request.GET['key']
    name = request.GET['q'].split()
    firstname = name[0]
    try: lastname = name[1]
    except: lastname = ''
    q = request.GET['q']
    if is_benign(key):
        ret = {}
        users = _load('users.json')
        for userid, user in users.iteritems():
            if isinstance(user, int): continue
            if _starts_with(user['name'], firstname)\
                    and _starts_with(user['lastname'], lastname)\
                    or _like(user['email'], q)\
                    or _starts_with(user['phone'], q)\
                    or _starts_with(user['lastname'], q):
                ret[user['userid']] = user
            else: continue
        return json.dumps(ret)
    else: return perror(0)
        
@route('/get_users')
def get_users():
    key = request.GET.get('key', None)
    if is_benign(key):
        users = _load('users.json')
        return json.dumps(users)
    else: return perror(0)

@route('/get_user')
def get_user():
    userid = request.GET['userid']
    key = request.GET.get('key', None)
    if is_benign(key):
        users = _load('users.json')
        try: user = users[userid]
        except: return perror(2), userid
        return json.dumps(user)
    else: return perror(0)

@route('/get_self')
def get_self():
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        try: user = users[userid]
        except: return perror(2), userid
        return json.dumps(user)
    else: return perror(0)

@route('/get_auth')
def get_auth():
    token = decode(request.GET['token'])
    if is_authenticated(token):
        userid = token['userid']
        auth = _load('auth.json')
        try: entry = auth[userid]
        except: return perror(2), userid
        return json.dumps(entry)
    else: return perror(0)

@route('/create_user')
def create_user():
    key = request.GET.get('key', None)
    name = request.GET['name']
    lastname = request.GET.get('lastname', '')
    email = request.GET['email']
    phone = request.GET.get('phone', '')
    password = request.GET['password']
    if is_benign(key):
        auth = _load('auth.json')
        # check if a user exists with this email
        for userid, entry in auth.iteritems():
            if entry['email'] == email:
                return "User already exists"
        # add user if it doesn't already exist.
        user = _update_user(None, name, lastname, email, phone)
        _update_auth(user['userid'], email, password) #function handles the sha
        return "yes"
    else: return perror(0)
    
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
        users = _load('users.json')
        auth = _load('auth.json')
        try: user = users[userid]
        except: return perror(2)
        try: entry = auth[userid]
        except: return perror(2)
        _update_auth(userid, email, password) # rewrite this function
        user = _update_user(userid, name, lastname, email, phone)
        return user
    else: return perror(0)

@route('/remove_user')
def remove_user():
    try:
        token = decode(request.GET['token'])
    except: return "no"
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        auth = _load('auth.json')
        events = _load('events.json')
        #remove all traces
        for eventid, event in events.iteritems():
            if isinstance(event, int): continue
            if _is_hosting(userid, eventid):
                _remove_event(eventid)
            elif _is_invited(userid, eventid):
                _remove_guests(eventid, [userid])
        #remove the user
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
        ret = {}
        for friendid in user['friends']:
            try: ret[friendid] = users[friendid]
            except: 
                print "no user with id", friendid
                user['friends'].remove(friendid)
        users[userid] = user
        _save(users, 'users.json')
        return json.dumps(ret)
    else: return perror(0)

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

@route('/remove_friends')
def remove_friends():
    token = decode(request.GET['token'])
    friendids = request.GET['friendids'].split(',')
    if is_authenticated(token):
        userid = token['userid']
        users = _load('users.json')
        user = _get(users, userid)
        for friendid in friendids:
            try: user['friends'].remove(friendid)
            except: "no friends with id", friendid
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
    import random
    key = request.GET.get('key', None)
    if is_benign(key):
        events = _load('events.json')
        users = _load('users.json')
        auth = _load('auth.json')
        for userid, user in users.iteritems():
            print userid, user
        for userid, entry in auth.iteritems():
            if isinstance(entry, int): continue
        return json.dumps(counts), json.dumps(auth_counts), json.dumps(ids_to_delete)
    else: return perror(0)

@route('/get_events')
def get_events():
    key = request.GET.get('key', None)
    if is_benign(key):
        events = _load('events.json')
        return json.dumps(events)
    else: return perror(0)

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
            try: event = events[eventid]
            except: 
                print perror(1), eventid
                del user['invitations'][eventid]
            print hostid, event['hostid']
            print hostid == event['hostid']
            if hostid is 'all' or hostid == event['hostid']:
                ret[eventid] = event
        
        # mark the data as not modified
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
            try: event = events[eventid]
            except:
                print perror(1), eventid
                del event['events'][eventid]
            if guestid is 'all' or guestid in event['guests']:
                ret[eventid] = event

        #mark the data as not modified
        user = _mark_modified(user, 'events', guestid, "no")
        users[userid] = user
        _save(users, 'users.json')
    return ret

@route('/get_event')
def get_event():
    token = decode(request.GET['token'])
    if not is_authenticated(token):
        return perror(0) + ' on token'
    eventid = request.GET.get('eventid', None)
    events = _load('events.json')
    try: event = events[eventid]
    except:
        return perror(1), eventid
    userid = token['userid']
    if _is_hosting(userid, eventid) or _is_invited(userid, eventid):
        return json.dumps(event)
    else: return perror(0) + ' on userid'

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
        eventid = str(events['lastindex'] + 1)
        events['lastindex'] += 1
        guests = {}
        event = {'eventid': eventid,
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
        if guestids is not None:
            _add_guests(eventid, guestids)
        event = _load('events.json').get(eventid, '')
        return json.dumps(event)
    else: return perror(0)

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
            try: event = events[eventid]
            except: return perror(1)
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
                try: guest = users[guestid]
                except:
                    print perror(2), guestid
                    del event['guests'][guestid]
                guest = _mark_modified(guest, 'invitations', userid, 'yes')
                users[guestid] = guest
            events[eventid] = event
        _save(events, 'events.json')
        _save(users, 'users.json')
        return json.dumps(event)
    else: return perror(0)

def _remove_event(eventid):
    try:
        users = _load('users.json')
        events = _load('events.json')
        event = events[eventid]
        for guestid, response in event['guests'].iteritems():
            try: 
                guest = users[guestid]
                del guest['invitations'][eventid]
                guest = _mark_modified(guest, 'invitations', event['hostid'], 'yes')
                users[guestid] = guest
            except:
                print perror(2), guestid
        try: users[event['hostid']]['events'].remove(eventid)
        except: print perror(2), event['hostid']
        del events[eventid]
        _save(users, 'users.json')
        _save(events, 'events.json')
        return "yes"
    except: return "no"
        
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
        return _remove_event(eventid)
    else: return "no"

@route('/get_guests')
def get_guests():
    token = decode(request.GET['token'])
    eventid = request.GET['eventid']
    userid = token['userid']
    if is_authenticated(token) \
            and _is_hosting(userid, eventid) \
            or _is_invited(userid, eventid):
        users = _load('users.json')
        events = _load('events.json')
        event = _get(events, eventid)
        ret = {}
        for guestid in event['guests'].iterkeys():
            try: ret[guestid] = users[guestid]
            except: 
                print perror(2), guestid
                del event['guests'][guestid]
        return json.dumps(ret)
    else: return perror(0)

@route('/add_guests')
def add_guests():
    eventid = request.GET['eventid']
    guestids = request.GET['guestids'].split(',')
    token = decode(request.GET['token'])
    if is_authenticated(token) and _is_hosting(token['userid'], eventid):
        _add_guests(eventid, guestids)
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
        try: event = events[eventid]
        except: return perror(1)
        try: host = users[event['hostid']]
        except:
            print perror(2), event['hostid']
            _remove_event(eventid)
            return perror(2) + " on hostid, deleted the event"
        try: guest = _get(users, guestid)
        except: return perror(2) + " on token's userid"

        # add update response info of guest and event
        event['guests'][guestid] = response
        guest['invitations'][eventid] = response
        # mark event as modified by guest
        host = _mark_modified(host, 'events', guestid, 'yes')
        # mark event as modified from guests' perspective
        guest = _mark_modified(guest, 'invitations', event['hostid'], 'yes')
        
        # save the event and users
        events[eventid] = event
        users[guestid] = guest
        users[event['hostid']] = host
        _save(events, 'events.json')
        _save(users, 'users.json')
        return "yes"
    else: return "no"

# ----------------------- STATIC CONTENT/ABOUT INFO ---------------------------#
@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='/var/www/glue/static')

@route('/')
def home():
    html = open('../html/index.html', 'r').read()
    return html

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

