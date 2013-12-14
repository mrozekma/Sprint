from base64 import b32decode
import hashlib
from hmac import HMAC
import struct
from time import time

from rorn.Box import LoginBox, ErrorBox, WarningBox, SuccessBox

from Settings import settings
from User import User
from Button import Button
from LoadValues import isDevMode
from Event import Event
from utils import *

@get('login')
def login(handler, redir = '/'):
	handler.title('Login')
	if handler.session['user']:
		redirect(redir)
	else:
		print LoginBox(redir)

@post('login')
def loginPost(handler, p_username, p_password, p_verification, p_redir):
	def die(msg):
		print ErrorBox("Login Failed", msg)
		print LoginBox(p_redir)
		done()

	def badCredentials():
		die("Invalid username/password/code combination")

	handler.title('Login')
	user = User.load(username = p_username)

	if not user:
		Event.login(handler, None, False, "Failed login for %s (bad username)" % p_username)
		badCredentials()

	if not checkPassword(user, p_password):
		Event.login(handler, None, False, "Failed login for %s (bad password)" % p_username)
		badCredentials()

	if user.hotpKey != '' and (p_verification == '' or p_verification not in code(user.hotpKey)):
		Event.login(handler, None, False, "Failed login for %s (bad code)" % p_username)
		badCredentials()

	if not user.hasPrivilege('User'):
		Event.login(handler, user, False, "Account disabled")
		die("Your account has been disabled")

	if user.resetkey:
		user.resetkey = None
		user.save()

	handler.session['user'] = user
	handler.session.remember('user')
	Event.login(handler, user, True)
	redirect(p_redir)

@get('logout')
def logout(handler):
	print "<form method=\"post\" action=\"/logout\">"
	print Button('Logout', type = 'submit').negative()
	print "</form>"

@post('logout')
def logoutPost(handler):
	if handler.session['user']:
		del handler.session['user']
		if 'impersonator' in handler.session:
			del handler.session['impersonator']
		redirect('/')
	else:
		print ErrorBox("Logout Failed", "You are not logged in")

def checkPassword(user, password):
	# First try their local password
	if user.password and user.password == User.crypt(user.username, password):
		return True

	# Then try Kerberos if possible
	if settings.kerberosRealm:
		try:
			import kerberos
			try:
				if kerberos.checkPassword(user.username, password, '', settings.kerberosRealm):
					return True
			except (kerberos.KrbError, kerberos.BasicAuthError):
				pass
		except ImportError:
			pass

	return False

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
