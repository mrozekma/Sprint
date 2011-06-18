from User import User
from Table import Table

@get('users')
def users(handler, request):
	handler.title('Users')
	tbl = Table()
	tbl *= ('ID', 'Username')
	for user in User.loadAll():
		tbl += (user.id, user)
	print tbl
