#!/usr/local/bin/python

from MySQLdb import connect
from MySQLdb import cursors
from bottle import route, run, get, post, request, static_file, error, abort
from bottle import response, template, Bottle
import bottle
import string
import json

# use as: return json.dumps(dict)

# ------------------------------- HELPERS ------------------------------- #
def connect():
    HOST = 'localhost'
    #HOST = '10.210.138.52'
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
@route('/forms')
def forms():
    return template('forms')

@route('/create_user')
def create_user():
    name = request.forms.get('name')
    lastname = request.forms.get('lastname')
    email = request.forms.get('email')
    password = request.forms.get('password')

    command = 'INSERT INTO users (name, lastname, email, password) VALUES('\
        + name + ',' + lastname + ',' + email + ',' + password + ');'
    cursor.execute(command)
    return command

@route('/update_user')
def update_user():
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
    name = request.query.get('name', '')
    q = 'SELECT eventid, hostid, name, category, location, starttime, endtime, description FROM events WHERE name LIKE "' + name + '"'
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
    # form query
    q = 'SELECT eventid, hostid, name, category, location, starttime, endtime, description FROM events'
    ands = []
    if request.query.has_key('eventid'):
        q = q + ' WHERE eventid = "' + request.query['eventid'] + '"'
    else:
        if request.query.has_key('name'):
            ands.append('name LIKE "' + request.query['name'] + '"')
        if request.query.has_key('hostid'):
            ands.append('hostid = "' + request.query['hostid'] + '"')
        if request.query.has_key('category'):
            ands.append('category = "' + request.query['category'] + '"')
        if request.query.has_key('location'):
            ands.append('category = "' + request.query['location'] + '"')
            # note: find current location from phone and send in field
        if request.query.has_key('starttime'):
            ands.append('starttime >= "' + request.query['starttime'] + '"')
        if request.query.has_key('endtime'):
            ands.append('endtime <= "' + request.query['endtime'] + '"')
    q = q + ' WHERE '
    for term in ands[:-1]:
        q = q + '"' + term + '"' + ' AND '
    q = q + ands[len(ands)]

    # execute query and pack results into events
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

bottle.debug(True)
run(host='localhost', port=8080)
