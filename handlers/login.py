from base64 import b32decode
import hashlib
from hmac import HMAC
import struct
from time import time

from rorn.Box import LoginBox, ErrorBox, WarningBox, SuccessBox

from User import User
from Button import Button
from LoadValues import isDevMode
from Event import Event
from utils import *

@get('login')
def login(handler, request, redir = '/'):
	handler.title('Login')
	if handler.session['user']:
		print WarningBox('Logged In', 'You are already logged in as %s' % handler.session['user'])
	else:
		print LoginBox(redir)

@post('login')
def loginPost(handler, request, p_username, p_password, p_verification, p_redir):
	def die(msg):
		print ErrorBox("Login Failed", msg)
		print LoginBox(p_redir)
		done()

	handler.title('Login')
	user = User.load(username = p_username, password = User.crypt(p_username, p_password))

	if not user:
		Event.login(handler, None, False, "Failed login for %s (bad password)" % p_username)
		die("Invalid username/password/code combination")

	if user.hotpKey != '' and (p_verification == '' or p_verification not in code(user.hotpKey)):
		Event.login(handler, None, False, "Failed login for %s (bad code)" % p_username)
		die("Invalid username/password/code combination")

	if not user.hasPrivilege('User'):
		Event.login(handler, user, False, "Account disabled")
		die("Your account has been disabled")

	if user.resetkey:
		user.resetkey = None
		user.save()

	handler.session['user'] = user
	Event.login(handler, user, True)
	redirect(p_redir)

@get('logout')
def logout(handler, request):
	print "<form method=\"post\" action=\"/logout\">"
	print Button('Logout', type = 'submit').negative()
	print "</form>"

@post('logout')
def logoutPost(handler, request):
	if handler.session['user']:
		del handler.session['user']
		if 'impersonator' in handler.session:
			del handler.session['impersonator']
		redirect('/')
	else:
		print ErrorBox("Logout Failed", "You are not logged in")

# Adapted from http://www.brool.com/index.php/using-google-authenticator-for-your-website
def code(key, window = 4):
	tm = int(time.time() / 30)
	key = b32decode(key)

	for ix in range(-window, window+1):
		b = struct.pack(">q", tm + ix)
		hm = HMAC(key, b, hashlib.sha1).digest()
		offset = ord(hm[-1]) & 0x0F
		truncatedHash = hm[offset:offset+4]
		code = struct.unpack(">L", truncatedHash)[0]
		code &= 0x7FFFFFFF;
		code %= 1000000;
		yield "%06d" % code
