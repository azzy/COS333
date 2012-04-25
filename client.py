#!/usr/bin/python

from bottle import route, run, request
import bottle
import string
import json
import hmac
import hashlib
import urllib2
from itertools import izip, cycle

key = "okXRDgXqnDfyYK11nARRIdUy5xmuGsJi00DQuyzaGYY"
xor_key = "37xjAjWSE5pr2x6gXEsxKJMwcR7L54hXBY2bjz1UnCQmOS8Nm84ePMDCjyr7Sgt2YvP8lQRHB2gQlKehCWUMW4dPm2flhdZSwCU0LGWZdydSLS1C3OUvNsfjQPcWnuAqcQiAPMgMQf5AhIAtRmhPxNX9Gg1tUXtfMix1jJCgLkCwLiBKBJFsxq4oCUaeyfkudkc9QljacqadsF2jv9u7V3A"
my_key = 'another-secret-key'
host = 'http://ec2-50-17-119-54.compute-1.amazonaws.com'

def make_first_digest(message):
    ''' return a digest for the message.'''
    return hmac.new('secret-shared-key', message, hashlib.sha1).hexdigest()

def make_digest(message):
    ''' return a digest for the message.'''
    return hmac.new('hashed-password-or-uid', message, hashlib.sha1).hexdigest()

def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(key)))

@route('/get_users')
def get_users():
    method = "get_users"
    sig = make_digest(method)
    url = host + ':9000/?method=' + method + '&sig=' + sig
    f = urllib2.urlopen(url)
    m = json.loads(f.read())
    f.close()
    new_sig = m['sig']
    data = m['data']
    original = xor_crypt_string(data, key=my_key)
    actual_digest = make_digest(original)
    
    if new_sig != actual_digest:
        return 'WARNING: Data corruption'
    else:
        return original

@route('/create_user')
def create_user():
    name = request.GET['name']
    lastname = request.GET.get('lastname', '')
    email = request.GET['email']
    password = request.GET['password']
    p = hashlib.md5(password).hexdigest()
    method = "create_user"
    args = {'name': name,
            'lastname': lastname,
            'email':email,
            'password':p}
    sig = make_digest(method)
    url = host + ':9000/?method=' + method + '&args=' + args + '&sig=' + sig

run(host='ec2-50-17-119-54.compute-1.amazonaws.com',port=8085)
