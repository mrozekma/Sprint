from json import dumps as toJS

from LoadValues import getLoadtime, getRevisionInfo, isDevMode, setDevMode
from Project import Project
from Settings import settings
from Sprint import Sprint
from relativeDates import timesince
from utils import *

from rorn.ResponseWriter import ResponseWriter

commands = {}

def command(syntax, mode = '', doc = None):
	def wrap(f):
		if mode not in commands:
			commands[mode] = []
		commands[mode].append((syntax.split(' '), f, doc))
		return f
	return wrap

def clr(text, fg = 'status', bg = None, bold = False, italic = False, underline = False, glow = False):
	return "[[%s%s%s%s;%s;%s]%s]" % ('g' if glow else '', 'u' if underline else '', 'i' if italic else '', 'b' if bold else '', HTML_COLORS.get(fg, fg or ''), HTML_COLORS.get(bg, bg or ''), text)

class CommandError(RuntimeError): pass
def fail(str):
	raise CommandError(str)

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

	parts = p_command.split(' ')
	testCommands = filterCommands(parts, p_mode)

	if len(testCommands) == 0:
		print toJS({'error': 'Unrecognized command'})
	elif len(testCommands) > 1:
		print toJS({'error': 'Ambiguous command'})
	else:
		syntax, fn, doc = testCommands[0]
		args = [y for (x, y) in zip(syntax, parts) if x == '_']
		w = ResponseWriter()
		try:
			mode = fn(handler.session['shell'], *args)
		except CommandError, e:
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

def filterCommands(parts, mode = ''):
	rtn = commands.get(mode, []) + commands.get('*', [])
	rtn = filter(lambda (syntax, fn, doc): len(syntax) == len(parts) and all(x.startswith(y) for (x, y) in zip(syntax, parts) if x != '_'), rtn)
	return rtn

def getUser(username):
	user = User.load(username = username)
	if not user:
		fail("No user named %s" % username)
	return user

def link(text, url = None):
	return "{{%s}{%s}}" % (text, url or text)

@command('help', mode = '*', doc = "Help using the shell")
def help(context):
	#TODO Need a better way to match command names
	names = set(syntax[0] for (syntax, fn, doc) in commands.get(context['mode'], []) + commands.get('*', []))
	print "%s: %s" % (clr("Available commands"), ', '.join(sorted(names)))

@command('help _', mode = '*')
def helpCommand(context, command):
	testCommands = filterCommands([command], context['mode'])
	sys.__stdout__.write("%s\n" % testCommands)
	if len(testCommands) == 0:
		fail("Unrecognized command")
	elif len(testCommands) > 1:
		fail("Ambiguous command")
	else:
		syntax, fn, doc = testCommands[0]
		if not doc:
			fail("No help available")
		print doc

@command('info')
def info(context):
	revisionHash, revisionDate, revisionRelative = getRevisionInfo()
	print "Sprint tool, revision %s" % link(revisionHash, settings.gitURL % {'hash': revisionHash})
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
	print "You are %s" % link(user.username, "/users/%s" % user.username)

@command('su')
def su(context):
	if not context['handler'].session['user'].hasPrivilege('Dev'):
		fail("You need the %s privilege" % clr('Dev'))
	return ('admin', '#')

@command('dev', mode = 'admin')
def devMode(context):
	setDevMode(True)
	print "Switched to %s mode" % clr('development', 'red')

@command('prod', mode = 'admin')
def prodMode(context):
	setDevMode(False)
	print "Switched to %s mode" % clr('production', 'green')
