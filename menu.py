from urllib import urlencode

menu = [
	('Login', '/login', ['-User']),
	('Home', '/', []),
	('Users', '/users', []),
	('Prefs', '/prefs', ['User']),
	('Search', '#', ['User']),
	('Admin', '/admin', ['Dev']),
	('Logout', '/logout', ['User'])
]

def hasPriv(user, priv):
	if priv[0] == '-':
		return not hasPriv(user, priv[1:])
	return user and user.hasPrivilege(priv)

def render(handler, path):
	rtn = []
	for text, url, reqPrivs in menu:
		# Special case for /login that adds the current page URL
		if url == '/login':
			url += '?' + urlencode([('redir', path)])

		if all(hasPriv(handler.session['user'], priv) for priv in reqPrivs):
			rtn.append("<a href=\"%s\">%s</a>" % (url, text))
	return '&nbsp;|&nbsp;'.join(rtn)
