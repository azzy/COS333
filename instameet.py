#!/usr/local/bin/python

from MySQLdb import connect
from MySQLdb import cursors
from bottle import route, run, get, post, request, static_file, error, abort
from bottle import response, template
import bottle
import string

# import json
# use as: return json.dumps(dict)

# ------------------------------- HELPERS ------------------------------- #
def connect():
    # HOST = 'localhost'
    HOST = '10.210.138.52'
    PORT = '80'
    DATABASE = 'instameet'
    USER = 'web'
    PASSWORD = 'cos333'

    host = HOST
    connection = connect(host = host, port = PORT, user = USER,
                         passwd = PASSWORD, db = DATABASE)    
    cursor = connection.cursor(cursors.DictCursor)
    return cursor

# ------------------------------ INTERFACE ------------------------------- #
@route('/create_user')
def create_user():
    return None

@route('/add_friend')
def add_friend():
    return None

@route('/create_event')
def create_event():
    return None

# use this if we want users to search only by event name
@route('/get_events')
def get_event_by_name():
    event_name = request.query.get('event_name', '')
     q = 'SELECT eventid, hostid, name, category, location, starttime, endtime, description FROM events WHERE name LIKE "' + event_name + '"'
    cursor = connect()
    cursor.execute(q)
    
    events = {}
    event = cursor.fetchone()
    while event:
        events[event['eventid']] = {
            'eventid':event['eventid'],
            'hostid':event['hostid'],
            'name':  event['name'],
            'category': event['category'],
            'location': event['location'],
            'starttime': event['starttime'],
            'endtime': event['endtime'],
            'description': event['description']}
        event = cursor.fetchone()

@route('/get_events')
def get_events():
    q = 'SELECT eventid, hostid, name, category, location, starttime, endtime, description FROM events'
    ands = []
    if request.query.has_key('event_eventid'):
        q = q + ' WHERE eventid = "' + request.query['event_eventid'] + '"'
    else:
        if request.query.has_key('event_name'):
            ands.append('name LIKE "' + request.query['event_name'] + '"')
        if request.query.has_key('event_hostid'):
            ands.append('hostid = "' + request.query['event_hostid'] + '"')
        if request.query.has_key('event_category'):
            ands.append('category = "' + request.query['event_category'] + '"')
        if request.query.has_key('event_location'):
            ands.append('category = "' + request.query['event_location'] + '"')
            # note: find current location from phone and send in field
        if request.query.has_key('event_starttime'):
            ands.append('starttime >= "' + request.query['event_starttime'] + '"')
        if request.query.has_key('event_endtime'):
            ands.append('endtime <= "' + request.query['event_endtime'] + '"')
        if 
            
    event_starttime = request.query.get('event_starttime', '')
    event_endtime = request.query.get('event_endtime', '')
    event_keywords = request.query.get('event_keywords', '')
    
    cursor = connect()
    cursor.execute(q)
    
    events = {}
    event = cursor.fetchone()
    while event:
        events[event['eventid']] = {
            'eventid':event['eventid'],
            'hostid':event['hostid'],
            'name':  event['name'],
            'category': event['category'],
            'location': event['location'],
            'starttime': event['starttime'],
            'endtime': event['endtime'],
            'description': event['description']}
        event = cursor.fetchone()

    return events
