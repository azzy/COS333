#!/usr/local/bin/python

from bottle import route, run, request
import bottle
import string
import json

#users = json.loads(open('users.json', 'r').read())
#events = json.loads(open('events.json', 'r').read())
users = {}
events = {}
# ------------------------------- HELPERS -------------------------------- #
def _save(dictionary, file):
    json_string = json.dumps(dictionary)
    with open (file, 'w') as f:
        f.write(json_string)

def _load(dictionary, id):
    if id is None:
        return 'id required'
    if int(id) <= len(dictionary):
        return dictionary[id]
    else:
        return 'entry for id not defined'

#add user to user's friends list
def _add_friend(userid, friendid):
    user = _load(users, userid)
    friends = user['friends']
    if friendid not in 
    #fid = len(friends) + 1
    #friends[fid] = friendid
    user['friends'] = friends
    users[userid] = user
    return user

#add user to event's guests list
def _add_guest(eventid, guestid):
    event = _load(events, eventid)
    guests = event['guests']
    gid = len(guests) + 1
    guests[gid] = guestid
    event['guests'] = guests
    events[eventid] = event
    return event

#add event to user's invitations list
def _add_invitation(eventid, guestid):
    user = _load(users, guestid)
    if eventid not in invitations:
        invitations.append(eventid)
    #invitations = user['invitations']
    #iid = len(invitations) + 1
    #invitations[iid] = eventid
    user['invitations'] = invitations
    users[guestid] = user
    return user

#add event to user's events list
def _add_event(eventid, hostid):
    user = _load(users, hostid)
    invitations = user['events']
    eid = len(events) + 1
    invitations[eid] = eventid
    user['events'] = events
    users[hostid] = user
    return user

# ------------------------------ INTERFACE ------------------------------- #
# note: still need to go through and proof everything my error proofing is so off.
@route('/get_users')
def get_users():
    return json.dumps(users)

@route('/get_user')
def get_user():
    userid = request.GET.get('userid', None)
    user = _load(users, userid)
    return json.dumps(users[userid])

@route('/create_user')
def create_user():
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
            'friends': {},
            'invitations': {},
            'events': {}
            }
    users[userid] = user
    _save(users, 'users.json')
    return json.dumps(user)

@route('/update_user')
def update_user():
    userid = request.GET.get('userid', None)
    if userid is None:
        return 'Userid required'
    name = request.GET.get('name', None)
    lastname = request.GET.get('lastname', None)
    email = request.GET.get('email', None)
    password = request.GET.get('password', None)
    user = _load(users, userid)
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
    userid = request.GET.get('userid', None)
    user = _load(users, userid)
    return json.dumps(user['friends'])

@route('/add_friend')
def add_friend():
    userid = request.GET.get('userid', None)
    friendid = request.GET.get('friendid', None)
    user = _add_friend(userid, friendid)
    friend = _add_friend(friendid, userid)
    _save(users, 'users.json')
    return json.dumps(user) # replace with true or false

@route('/get_events')
def get_events():
    return json.dumps(events)

@route('/create_event')
def create_event():
    hostid = request.GET.get('hostid', None)
    if hostid is None:
        return 'Hostid required'
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
    events[eventid] = event
    _add_event(eventid, hostid)
    _save(events, 'events.json')
    _save(users, 'users.json')
    return json.dumps(event)

@route('/get_event')
def get_event():
    eventid = request.GET.get('eventid', None)
    event = _load(events, eventid)
    return json.dumps(event)

@route('/update_event')
def update_event():
    eventid = request.GET.get('eventid', None)
    name = request.GET.get('name', None)
    category = request.GET.get('category', None)
    location = request.GET.get('location', None)
    starttime = request.GET.get('starttime', None)
    endtime = request.GET.get('endtime', None)
    description = request.GET.get('description', None)
    event = _load(events, eventid)
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

@route('/add_guest')
def add_guest():
    eventid = request.GET.get('eventid', None)
    guestid = request.GET.get('guestid', None)
    event = _add_guest(eventid, guestid)
    user = _add_invitation(eventid, guestid)
    _save(events, 'events.json')
    _save(users, 'users.json')
    return json.dumps(event) #replace with true or false



run(port=8080)
