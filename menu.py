from urllib import quote_plus

menu = [
	('Login', '/login?redir=%(path)s', ['-User']),
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
	path = quote_plus(path)
	rtn = []
	for text, url, reqPrivs in menu:
		if all(hasPriv(handler.session['user'], priv) for priv in reqPrivs):
			rtn.append("<a href=\"%s\">%s</a>" % (url % {'path': path}, text))

			# Include the error count after the admin link
			if url == '/admin':
				from event_handlers.ErrorCounter import errorCounter
				if errorCounter.getCount() > 0:
					rtn[-1] += "<a class=\"error-count\" href=\"/admin/log?types[]=error\">%d</a>" % errorCounter.getCount()
	return '&nbsp;|&nbsp;'.join(rtn)
