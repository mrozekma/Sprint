from rorn.Box import LoginBox, ErrorBox, WarningBox, SuccessBox
from rorn.Session import delay

from User import User
from Button import Button
from LoadValues import isDevBuild
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
		if isDevBuild() and not user.hasPrivilege('Dev'):
			delay(handler, ErrorBox("Login Failed", "This is a development build"))
			redirect('/')

		if user.resetkey:
			user.resetkey = None
			user.save()

		handler.session['user'] = user
		delay(handler, SuccessBox("Login Complete", "Logged in as %s" % user, close = True))
		redirect('/')
	else:
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
		redirect('/')
	else:
		print ErrorBox("Logout Failed", "You are not logged in")
