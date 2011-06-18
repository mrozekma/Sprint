from Box import LoginBox, ErrorBox
from User import User
from utils import *
from Session import delay

@get('login')
def login(handler, request):
	handler.title('Login')
	print LoginBox()

@post('login')
def loginPost(handler, request, p_username, p_password):
	handler.title('Login')
	user = User.load(username = p_username, password = md5(p_password))
	if user:
		handler.session['user'] = user
		delay(handler, PropBox("Login Complete", "Logged in as %s" % user))
		redirect('/')
	else:
		delay(handler, ErrorBox("Login Failed", "Invalid username/password combination"))
		redirect('/')

@get('logout')
def logout(handler, request):
	if handler.session['user']:
		del handler.session['user']
		redirect('/')
	else:
		print ErrorBox("Logout Failed", "You are not logged in")
