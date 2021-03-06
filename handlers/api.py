from json import dumps as toJS

from LoadValues import getLoadtime
from Project import Project
from Sprint import Sprint
from utils import *

@get('api/uptime')
def apiUptime(handler):
	handler.wrappers = False
	delta = getNow() - getLoadtime()
	print delta.days * 60 * 60 * 24 + delta.seconds

@get('api/projects/(?P<id>[0-9]+)/active/(?P<action>[^/]+)')
def apiProjectActive(handler, id, action):
	def die(msg):
		print toJS({'error': msg})
		done()

	id = int(id)
	handler.wrappers = False

	project = Project.load(id)
	if not project:
		die("No project with ID %d" % id)

	sprints = sorted(filter(lambda sprint: sprint.isActive() and not sprint.isHidden(handler.session['user']), project.getSprints()), lambda x, y: cmp(x.start, y.start))
	if len(sprints):
		redirect("/api/sprints/%d/%s" % (sprints[-1].id, action))
	else:
		die('No active sprints found')

@get('api/sprints/(?P<id>[0-9]+)/info')
def apiSprintInfo(handler, id):
	def die(msg):
		print toJS({'error': msg})
		done()

	id = int(id)
	handler.wrappers = False

	sprint = Sprint.load(id)
	if not sprint or sprint.isHidden(handler.session['user']):
		die("No sprint with ID %d" % id)

	abbrName = sprint.name.strip()
	if abbrName.startswith(sprint.project.name):
		abbrName = abbrName[len(sprint.project.name):].strip()

	print toJS({
			'id': sprint.id,
			'name': sprint.name,
			'abbreviated name': abbrName,
			'start': sprint.start,
			'end': sprint.end
			})

@get('api/sprints/list')
def apiSprintsList(handler, calendar = False, start = None, end = None, _ = None):
	def die(msg):
		print toJS({'error': msg})
		done()

	handler.wrappers = False
	start = int(start) if start else None
	end = int(end) if end else None

	sprints = filter(lambda sprint: not sprint.isHidden(handler.session['user']), Sprint.loadAll())
	if start and end:
		sprints = filter(lambda sprint: (start <= sprint.start <= end) or (start <= sprint.end <= end), sprints)

	rtn = [{'id': sprint.id,
	        'title': "%s - %s" % (sprint.project.name, sprint.name) if calendar else sprint.name,
	        'start': tsToDate(sprint.start).strftime('%Y-%m-%d'),
	        'end': tsToDate(sprint.end).strftime('%Y-%m-%d'),
	        'active': sprint.isActive(),
	        'member': handler.session['user'] in sprint.members
	       } for sprint in sprints]
	if calendar:
		for entry in rtn:
			entry.update({'color': 'green' if entry['member'] and entry['active'] else '#36c;'})
	print toJS(rtn)
