menu = [
	('Login', '/login', ['-User']),
	('Home', '/', []),
	('Users', '/users', []),
	('Prefs', '/prefs', ['User']),
	('Admin', '/admin', ['Dev']),
	('Logout', '/logout', ['User'])
]

def hasPriv(user, priv):
	if priv[0] == '-':
		return not hasPriv(user, priv[1:])
	return user and user.hasPrivilege(priv)

def render(handler):
	return '&nbsp;|&nbsp;'.join("<a href=\"%s\">%s</a>" % (url, text) for (text, url, reqPrivs) in menu if all(hasPriv(handler.session['user'], priv) for priv in reqPrivs))
