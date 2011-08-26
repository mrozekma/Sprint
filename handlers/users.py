from User import User
from rorn.Box import ErrorBox
from utils import *

@get('users')
def users(handler, request):
	handler.title('Users')

	#TODO
	from Privilege import dev
	dev(handler)

	users = User.loadAll(orderby = 'username')
	for user in users:
		print "<div class=\"user-list-entry\"><a href=\"/users/%s\"><img src=\"%s\"></a><br>%s</div>" % (user.username, user.getAvatar(64), user.safe.username)

@get('users/(?P<username>[^/]+)')
def user(handler, request, username):
	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	handler.title(user.safe.username)

	#TODO
	from Privilege import dev
	dev(handler)

	print "<img src=\"%s\">" % user.getAvatar(128)
