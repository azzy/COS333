#!/usr/bin/python

from bottle import route, run, request
import bottle
import string
import json
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
def create_user():
    global users
    name = request.GET['name']
    lastname = request.GET.get('lastname', '')
    email = request.GET['email']
    password = request.GET['password']
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

@route('/get_friends')
def get_friends():
    global users
    userid = request.GET.get('userid', None)
    user = _get(users, userid)
    return json.dumps(user['friends'])

@route('/add_friend')
def add_friend():
    global users
    userid = request.GET.get('userid', None)
    friendid = request.GET.get('friendid', None)
    user = _add_friend(userid, friendid)
    friend = _add_friend(friendid, userid)
    users[userid] = user
    users[friendid] = friend
    _save(users, 'users.json')
    return json.dumps(user) # replace with true or false

@route('/remove_friend')
def remove_friend():
    global users
    userid = request.GET.get('userid', None)
    friendid = request.GET.get('friendid', None)
    user = _remove_friend(userid, friendid)
    friend = _remove_friend(friendid, userid)
    users[userid] = user
    users[friendid] = friend
    _save(users, 'users.json')
    return json.dumps(user) #replace with true or false

@route('/get_events')
def get_events():
    global events
    return json.dumps(events)

@route('/create_event')
def create_event():
    global events, users
    try: hostid = request.GET['hostid']
    except: return 'Hostid required'
    name = request.GET.get('name', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    starttime = request.GET.get('starttime', '')
    endtime = request.GET.get('endtime', '')
    description = request.GET.get('description', '')
    eventid = len(events) + 1
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

@route('/get_event')
def get_event():
    global events
    eventid = request.GET.get('eventid', None)
    event = _get(events, eventid)
    return json.dumps(event)

@route('/update_event')
def update_event():
    global events
    eventid = request.GET.get('eventid', None)
    name = request.GET.get('name', None)
    category = request.GET.get('category', None)
    location = request.GET.get('location', None)
    starttime = request.GET.get('starttime', None)
    endtime = request.GET.get('endtime', None)
    description = request.GET.get('description', None)
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

@route('/get_guests')
def get_guests():
    global events
    eventid = request.GET.get('eventid', None)
    event = _get(events, eventid)
    return json.dumps(event['guests'])

@route('/add_guest')
def add_guest():
    global users, events
    eventid = request.GET.get('eventid', None)
    guestid = request.GET.get('guestid', None)
    user = _add_invitation(eventid, guestid)
    event = _add_guest(eventid, guestid)
    users[guestid] = user
    events[eventid] = event
    _save(events, 'events.json')
    _save(users, 'users.json')
    return json.dumps(event) #replace with true or false

@route('/remove_guest')
def remove_guest():
    global users, events
    eventid = request.GET.get('eventid', None)
    guestid = request.GET.get('guestid', None)
    user = _remove_invitation(eventid, guestid)
    event = _remove_guest(eventid, guestid)
    users[guestid] = user
    events[eventid] = event
    _save(events, 'events.json')
    _save(users, 'users.json')
    return json.dumps(event) #replace with true or false

@route('/update_response')
def update_response():
    global users, events
    eventid = request.GET.get('eventid', None)
    guestid = request.GET.get('guestid', None)
    response = request.GET.get('response', 'no')
    event = _get(events, eventid)
    assert guestid in users, 'guest undefined'
    if guestid in event['guests']:
        event['guests'][guestid] = response
    else:
        return 'not on guestlist'
    events[eventid] = event
    _save(events, 'events.json')
    return json.dumps(event)

# ----------------------- SMART & SEARCH METHODS ---------------------------#

@route('/get_invited_events')
def get_invited_events():
    return None
    ''' takes userid and returns list of events to which user has been invited'''

@route('/get_hosted_events')
def get_hosted_events():
    return None
    ''' takes userid and returns list of events that user is hosting'''

run(host='ec2-50-17-119-54.compute-1.amazonaws.com',port=8080)
