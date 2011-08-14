from utils import andmap

menu = [
	('Home', '/', []),
	('Users', '/users', []),
	('Admin', '/admin', ['Dev']),
	('Logout', '/logout', ['User'])
]

def render(handler):
	return '&nbsp;|&nbsp;'.join(["<a href=\"%s\">%s</a>" % (url, text) for (text, url, reqPrivs) in menu if andmap(handler.session['user'].hasPrivilege if handler.session['user'] else lambda x: False, reqPrivs)])
