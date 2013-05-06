from json import dumps as toJS
from shlex import split

from LoadValues import getLoadtime, getRevisionInfo, isDevMode, setDevMode
from Project import Project
from SavedSearch import SavedSearch
from Settings import settings
from Sprint import Sprint
from Task import Task
from User import User
from relativeDates import timesince
from utils import *

from rorn.ResponseWriter import ResponseWriter

commands = {}

def command(syntax, mode = '', doc = None):
	def wrap(f):
		if mode not in commands:
			commands[mode] = []
		commands[mode].append((split(syntax), f, doc))
		return f
	return wrap

def clr(text, fg = 'status', bg = None, bold = False, italic = False, underline = False, glow = False):
	return "[[%s%s%s%s;%s;%s]%s]" % ('g' if glow else '', 'u' if underline else '', 'i' if italic else '', 'b' if bold else '', HTML_COLORS.get(fg, fg or ''), HTML_COLORS.get(bg, bg or ''), text)

class CommandError(RuntimeError): pass
def fail(str):
	raise CommandError(str)

@post('shell/run')
def run(handler, request, p_command, p_path, p_mode = ''):
	request['wrappers'] = False

	if not handler.session['user']:
		print toJS({'error': 'You must be logged in to use the shell'})
		return

	# This is already checked in the "su" command, but could be spoofed by the user
	if p_mode == 'admin' and not handler.session['user'].hasPrivilege('Dev'):
		print toJS({'error': "You need the Dev privilege"})
		return

	if 'shell' not in handler.session: # Shell context
		handler.session['shell'] = {}
	handler.session['shell']['handler'] = handler;
	handler.session['shell']['path'] = p_path
	handler.session['shell']['mode'] = p_mode

	parts = split(p_command)
	testCommands = filterCommands(parts, p_mode)

	if len(testCommands) == 0:
		print toJS({'error': 'Unrecognized command'})
	elif len(testCommands) > 1:
		print toJS({'error': 'Ambiguous command'})
	else:
		syntax, fn, doc = testCommands[0]
		args = [y for (x, y) in zip(syntax, parts) if x == '_']
		w = ResponseWriter()
		mode = None
		rtn = {}

		try:
			mode = fn(handler.session['shell'], *args)
		except CommandError, e:
			w.done()
			print toJS({'error': str(e)})
			return
		except Redirect, e:
			rtn['redirect'] = e.target

		rtn['output'] = w.done()
		if mode is not None:
			if type(mode) == tuple:
				rtn['mode'], rtn['prompt'] = mode
			else:
				rtn['mode'] = rtn['prompt'] = mode
		if 'redirect' in rtn and rtn['output'] == '':
			rtn['output'] = clr('Redirecting...', 'yellow')
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

def nameLookup(cls, name, key = 'name', **attrs):
	rows = cls.loadAll(**attrs)
	rows = filter(lambda row: getattr(row, key).lower().startswith(name.lower()), rows)
	if len(rows) == 0:
		fail("Name %s not found" % name)
	elif len(rows) > 1:
		fail("Ambiguous name %s" % name)
	else:
		return rows[0]

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
	finger(context, context['handler'].session['user'].username)

@command('home')
def home(context):
	redirect('/')

@command('search _')
def search(context, name):
	if name.startswith('!'):
		search = nameLookup(SavedSearch, name[1:], userid = context['handler'].session['user'].id)
		if not search:
			fail("No search with name \"%s\"" % name[1:])
		redirect("/search/saved/%d/run" % search.id)
	else:
		redirect("/sprints/active?search=%s" % name)

@command('sprint')
def sprint(context):
	match = re.search('^/sprints/([0-9]+)/?', context['path'])
	if match:
		return sprintByID(context, int(match.group(1)))

	match = re.search('\\?sprint=([0-9]+)$', context['path'])
	if match:
		return sprintByID(context, int(match.group(1)))

	sprints = Sprint.loadAllActive(context['handler'].session['user'])
	for case in switch(len(sprints)):
		if case(0):
			fail("No active sprints")
			break
		if case(1):
			return sprintByID(context, sprints[0].id)
		if case():
			fail("%d active sprints" % len(sprints))
			break

@command('sprint _')
def sprintByID(context, id):
	id = to_int(id, 'id', fail)
	context['sprint'] = Sprint.load(id)
	if not context['sprint']:
		fail("No sprint with ID %d" % id)
	print context['sprint'].safe.name
	return ('sprint', "[sprint %d] $" % id)

@command('sprint _ _')
def sprintByName(context, projectName, sprintName):
	project = nameLookup(Project, projectName)
	if not project:
		fail("No project with name \"%s\"" % projectName)
	sprint = nameLookup(Sprint, sprintName, projectid = project.id)
	if not sprint:
		fail("No sprint with name \"%s\"" % sprintName)
	return sprintByID(context, sprint.id)

@command('info', mode = 'sprint')
def sprintInfo(context):
	redirect("/sprints/%d/info" % context['sprint'].id)

@command('backlog', mode = 'sprint')
def sprintBacklog(context):
	redirect("/sprints/%d" % context['sprint'].id)

@command('metrics', mode = 'sprint')
def sprintMetrics(context):
	redirect("/sprints/%d/metrics" % context['sprint'].id)

@command('checklist', mode = 'sprint')
def sprintChecklist(context):
	redirect("/sprints/%d/checklist" % context['sprint'].id)

@command('distribute', mode = 'sprint')
def sprintDistribute(context):
	redirect("/tasks/distribute?sprint=%d" % context['sprint'].id)

@command('results', mode = 'sprint')
def sprintResults(context):
	redirect("/sprints/%d/results" % context['sprint'].id)

@command('retrospective', mode = 'sprint')
def sprintRetrospective(context):
	redirect("/sprints/%d/retrospective" % context['sprint'].id)

@command('availability', mode = 'sprint')
def sprintAvailability(context):
	redirect("/sprints/%d/availability" % context['sprint'].id)

@command('search _', mode = 'sprint')
def sprintSearch(context, name):
	if name.startswith('!'):
		search = nameLookup(SavedSearch, name[1:], userid = context['handler'].session['user'].id)
		if not search:
			fail("No search with name \"%s\"" % name[1:])
		redirect("/search/saved/%d/run/%d" % (search.id, context['sprint'].id))
	else:
		redirect("/sprints/%d?search=%s" % (context['sprint'].id, name))

@command('task _')
def taskByID(context, id):
	id = to_int(id, 'id', fail)
	context['task'] = Task.load(id)
	if not context['task']:
		fail("No task with ID %d" % id)
	print context['task'].safe.name
	return ('task', "[task %d] $" % id)

@command('task _', mode = 'sprint')
def taskByName(context, name):
	tasks = context['sprint'].getTasks()
	tasks = filter(lambda task: task.name.lower().startswith(name.lower()), tasks)
	if len(tasks) == 0:
		fail("Name %s not found" % name)
	elif len(tasks) > 1:
		fail("Ambiguous name %s" % name)
	else:
		return taskByID(context, tasks[0].id)

@command('backlog', mode = 'task')
def taskBacklog(context):
	redirect("/sprints/%d?search=highlight:%d" % (context['task'].sprint.id, context['task'].id))

@command('history', mode = 'task')
def taskHistory(context):
	redirect("/tasks/%d" % context['task'].id)

@command('finger _')
def finger(context, username):
	user = nameLookup(User, username, key = 'username')
	if not user:
		fail("No user named %s" % username)
	print clr(user.username, bold = True)
	print "Last seen: %s" % clr(tsToDate(user.lastseen) if user.lastseen else 'Never')
	sprints = Sprint.loadAllActive(user)
	if sprints:
		print "Member of: %s" % ', '.join(link(sprint.name, "/sprints/%d" % sprint.id) for sprint in sprints)
	if context['handler'].session['user'].hasPrivilege('Dev'):
		if user.hotpKey:
			print "HOTP key: %s" % clr(user.hotpKey)
		if user.resetkey:
			print "Reset key: %s" % clr(user.resetkey)

@command('su')
def su(context):
	if not context['handler'].session['user'].hasPrivilege('Dev'):
		fail("You need the Dev privilege")
	return ('admin', '#')

@command('settings', mode = 'admin')
def adminSettings(context):
	redirect("/admin/settings")

@command('users', mode = 'admin')
def adminUsers(context):
	redirect("/admin/users")

@command('projects', mode = 'admin')
def adminProjects(context):
	redirect("/admin/projects")

@command('sessions', mode = 'admin')
def adminSessions(context):
	redirect("/admin/sessions")

@command('privileges', mode = 'admin')
def adminPrivileges(context):
	redirect("/admin/privileges")

@command('repl', mode = 'admin')
def adminRepl(context):
	redirect("/admin/repl")

@command('time', mode = 'admin')
def adminTime(context):
	redirect("/admin/time")

@command('cron', mode = 'admin')
def adminCron(context):
	redirect("/admin/cron")

@command('log', mode = 'admin')
def adminLog(context):
	redirect("/admin/log")

@command('dev', mode = 'admin')
def devMode(context):
	setDevMode(True)
	print "Switched to %s mode" % clr('development', 'red')

@command('prod', mode = 'admin')
def prodMode(context):
	setDevMode(False)
	print "Switched to %s mode" % clr('production', 'green')
