from json import dumps as toJS

from LoadValues import getLoadtime, getRevisionInfo, isDevMode, setDevMode
from Project import Project
from Settings import settings
from Sprint import Sprint
from relativeDates import timesince
from utils import *

from rorn.ResponseWriter import ResponseWriter

commands = {}

def command(pattern, mode = '', doc = None):
	def wrap(f):
		if mode not in commands:
			commands[mode] = []
		commands[mode].append((re.compile("^%s$" % pattern), f, doc))
		return f
	return wrap

def clr(text, fg = 'status', bg = None, bold = False, italic = False, underline = False, glow = False):
	return "[[%s%s%s%s;%s;%s]%s]" % ('g' if glow else '', 'u' if underline else '', 'i' if italic else '', 'b' if bold else '', HTML_COLORS.get(fg, fg or ''), HTML_COLORS.get(bg, bg or ''), text)

@post('shell/run')
def run(handler, request, p_command, p_mode = ''):
	request['wrappers'] = False

	if not handler.session['user']:
		print toJS({'error': 'You must be logged in to use the shell'})
		return

	if 'shell' not in handler.session: # Shell context
		handler.session['shell'] = {}
	handler.session['shell']['handler'] = handler;
	handler.session['shell']['mode'] = p_mode

	for pattern, fn, doc in commands.get(p_mode, []) + commands.get('*', []):
		match = pattern.match(p_command)
		if match:
			w = ResponseWriter()
			try:
				mode = fn(handler.session['shell'], *match.groups())
			except RuntimeError, e:
				w.done()
				print toJS({'error': str(e)})
				return

			rtn = {'output': w.done()}
			if mode is not None:
				if type(mode) == tuple:
					rtn['mode'], rtn['prompt'] = mode
				else:
					rtn['mode'] = rtn['prompt'] = mode
			print toJS(rtn)
			return
	print toJS({'error': 'Unrecognized command'})

def getUser(username):
	user = User.load(username = username)
	if not user:
		raise RuntimeError("No user named %s" % username)
	return user

@command('help', mode = '*', doc = "Help using the shell")
def help(context):
	#TODO Need a better way to match command names
	names = set()
	for pattern, fn, doc in commands.get(context['mode'], []) + commands.get('*', []):
		match = re.search('^([a-zA-Z0-9]+) ?', pattern.pattern[1:-1])
		if match:
			names.add(match.group(1))
	print "%s: %s" % (clr("Available commands"), ', '.join(sorted(names)))

@command('help (.+)', mode = '*')
def helpCommand(context, command):
	for pattern, fn, doc in commands.get(context['mode'], []) + commands.get('*', []):
		match = re.search('^([a-zA-Z0-9]+) ?', pattern.pattern[1:-1])
		if match and match.group(1) == command and doc:
			print "%s: %s" % (clr(match.group(1)), doc)
			return
	raise RuntimeError("No help available")

@command('info|about')
def info(context):
	revisionHash, revisionDate, revisionRelative = getRevisionInfo()
	print "Sprint tool, revision {{%s}{%s}}" % (revisionHash, settings.gitURL % {'hash': revisionHash})
	if isDevMode():
		print clr("Development mode", 'red')
	else:
		print clr("Production mode", 'green')
	loadTime = getLoadtime()
	print "Started %s" % clr(loadTime)
	print "Up for %s" % clr(timesince(loadTime))

@command('whoami')
def whoami(context):
	user = context['handler'].session['user']
	# print "You are {{%s}{/users/%s}}" % (clr(user.username), user.username)
	print "You are {{%s}{/users/%s}}" % (user.username, user.username)

@command('su')
def su(context):
	if not context['handler'].session['user'].hasPrivilege('Dev'):
		raise RuntimeError("You need the %s privilege" % clr('Dev'))
	return ('admin', '#')

@command('dev', mode = 'admin')
def devMode(context):
	setDevMode(True)
	print "Switched to %s mode" % clr('development', 'red')

@command('prod', mode = 'admin')
def prodMode(context):
	setDevMode(False)
	print "Switched to %s mode" % clr('production', 'green')
