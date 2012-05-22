from rorn.Box import LoginBox, ErrorBox, WarningBox, SuccessBox
from rorn.Session import delay

from User import User
from Button import Button
from LoadValues import isDevMode
from Event import Event
from utils import *

@get('login')
def login(handler, request):
	handler.title('Login')
	if handler.session['user']:
		print WarningBox('Logged In', 'You are already logged in as %s' % handler.session['user'])
	else:
		print LoginBox()

@post('login')
def loginPost(handler, request, p_username, p_password):
	handler.title('Login')
	user = User.load(username = p_username, password = User.crypt(p_username, p_password))
	if user:
		if not user.hasPrivilege('User'):
			Event.login(handler, user, False, "Account disabled")
			delay(handler, ErrorBox("Login Failed", "Your account has been disabled"))
			redirect('/')
		elif isDevMode() and not user.hasPrivilege('Dev'):
			Event.login(handler, user, False, "Non-dev login blocked")
			delay(handler, ErrorBox("Login Failed", "This is a development build"))
			redirect('/')

		if user.resetkey:
			user.resetkey = None
			user.save()

		handler.session['user'] = user
		Event.login(handler, user, True)
		delay(handler, SuccessBox("Login Complete", "Logged in as %s" % user, close = True))
		redirect('/')
	else:
		Event.login(handler, None, False, "Failed login for %s" % p_username)
		delay(handler, ErrorBox("Login Failed", "Invalid username/password combination"))
		redirect('/')

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
