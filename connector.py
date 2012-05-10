#!/usr/local/bin/python

from MySQLdb import connect
from MySQLdb import cursors
import string

def add_quotes(s):
	s = '\'' + s + '\''
	return s 

def get_connection():
	HOST = 'localhost'
	PORT = 80
	DATABASE = 'instameet'
	USER = 'web'
	PASSWORD = 'cos333'

	host = HOST
	connection = connect(host = host, port = PORT, user = USER, passwd = PASSWORD, db = DATABASE)    
	return connection

def add_event(hostid, name, category, location, starttime, endtime, descrip):
	hostid = str(hostid)
	name = add_quotes(name)
	category = add_quotes(category)
	location = add_quotes(location)
	starttime = add_quotes(starttime)
	endtime = add_quotes(endtime)
	descrip = add_quotes(descrip)

	connection = get_connection()
        cursor = connection.cursor(cursors.DictCursor)
        q1 = 'INSERT INTO events (hostid, name, category, location, starttime, endtime, descrip) '
        q2  =  'VALUES (' + hostid + ', ' + name + ', ' + category + ', ' + location + ', ' + starttime + ', ' + endtime+ ', ' + descrip + ');'
	cursor.execute(q1+q2)
        cursor.close()
        connection.close()

def add_user(name, lastname, email, password):
	name = add_quotes(name)
	lastname = add_quotes(lastname)
	email = add_quotes(email)
	password = add_quotes(password)

	connection = get_connection()
	cursor = connection.cursor(cursors.DictCursor)
	q1 = 'INSERT INTO users (name, lastname, email, password)'
	q2  =  'VALUES (' + name + ', ' + lastname + ', ' + email + ', ' + password + ');'
	cursor.execute(q1+q2)
	cursor.close()
	connection.close()

def add_friend(userid, friendid):
	connection = get_connection()
        cursor = connection.cursor(cursors.DictCursor)
	q = 'INSERT INTO friends (userid, friendid) VALUES (' + str(userid) + ', ' +  str(friendid) + ');'
	cursor.execute(q)
        cursor.close()
        connection.close()	

def add_invitation(eventid, guestid, response):
	connection = get_connection()
        cursor = connection.cursor(cursors.DictCursor)
	q = 'INSERT INTO invitations (eventid, guestid, response) VALUES (' + str(eventid) + ', ' +  str(guestid) + ', ' + str(response) + ');'
        cursor.execute(q)
        cursor.close()
        connection.close()

