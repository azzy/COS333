#!/usr/bin/python

from bottle import route, run, request
import bottle
import string
import json
import hmac
import hashlib
import urllib2, urllib

# ---------------------------- AUTH HELPERS ------------------------------ #
secret_key = "okXRDgXqnDfyYK11nARRIdUy5xmuGsJi00DQuyzaGYY"

def make_digest(message):
    ''' return a digest for the message.'''
    return hmac.new(secret_key, message, hashlib.sha224).hexdigest()

def encode(dictionary):
    ret = ''
    for k, v in dictionary.iteritems():
        ret += str(k) + '+' + str(v) + '|'
    return ret[:-1]

def decode(s):
    ret = {}
    kv = s.split('|')
    for pair in kv:
        key, value = pair.split(' ', 1)
        ret[key] = value
    return ret

# ------------------------------ INTERFACE ------------------------------- #

req_none = ['login']
req_key = ['get_users',
           'create_user',
           'find_users',
           'search_users',
           'get_events',
           'get_user',
           'rewrite_database'
           ]
req_tok = ['get_auth',
           'get_self',
           'update_user',
           'remove_user',
           'get_friends',
           'add_friend',
           'add_friends',
           'remove_friend',
           'remove_friends',
           'is_modified',
           'get_my_invitations',
           'get_my_events',
           'get_event',
           'remove_event',
           'create_event',
           'update_event',
           'get_guests',
           'add_guest',
           'add_guests',
           'remove_guest',
           'remove_guests',
           'update_response'
           ]
token = 'bullshit'
@route('/')
def app():
    global token
    method = request.GET['method']
    args = {}
    args['name'] = request.GET.get('name', '')
    args['lastname'] = request.GET.get('lastname', '')
    args['email'] = request.GET.get('email','')
    args['phone'] = request.GET.get('phone', '')
    args['password'] = request.GET.get('password','')
    args['eventid'] = request.GET.get('eventid', '')
    args['friendid'] = request.GET.get('friendid', '')
    args['friendids'] = request.GET.get('friendids', '')
    args['category'] = request.GET.get('category', '')
    args['location'] = request.GET.get('location', '')
    args['starttime'] = request.GET.get('starttime', '')
    args['endtime'] = request.GET.get('endtime', '')
    args['description'] = request.GET.get('description','')
    args['hostid'] = request.GET.get('hostid', '')
    args['guestid'] = request.GET.get('guestid', '')
    args['guestids'] = request.GET.get('guestids', '')
    args['userid'] = request.GET.get('userid', '')
    args['response'] = request.GET.get('response', '')
    args['which'] = request.GET.get('which', '')
    args['q'] = request.GET.get('q', '')
    
#    sig = encode({ 'method': method, 'sig': make_digest(method) })
    key = secret_key
    host = 'http://localhost:9000'
    url = host + '/' + method
    if method in req_tok:
        url += '?token=' + token
    elif method in req_key:
        url += '?key=' + key
    elif method in req_none:
        url += '?'
    else: return 'unsupported method'

    for param, val in args.iteritems():
        if len(val) > 0:
            url += '&' + param + '=' + urllib.quote_plus(val)    

    print url
    f = urllib2.urlopen(url)
    ret = f.read()
    f.close()
    if method == 'login' and ret is not 'Authentication Failed':
        token = ret
    return ret

run(host='0.0.0.0',port=8085)
