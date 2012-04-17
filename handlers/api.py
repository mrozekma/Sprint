from json import dumps as toJS

from Project import Project
from Sprint import Sprint
from utils import *

@get('api/projects/(?P<id>[0-9]+)/active/(?P<action>[^/]+)')
def apiProjectActive(handler, request, id, action):
	def die(msg):
		print toJS({'error': msg})
		done()

	id = int(id)
	request['wrappers'] = False

	project = Project.load(id)
	if not project:
		die("No project with ID %d" % id)

	sprints = sorted(filter(lambda sprint: sprint.isActive(), project.getSprints()), lambda x, y: cmp(x.start, y.start))
	if len(sprints):
		redirect("/api/sprints/%d/%s" % (sprints[-1].id, action))
	else:
		die('No active sprints found')

@get('api/sprints/(?P<id>[0-9]+)/info')
def apiSprintInfo(handler, request, id):
	def die(msg):
		print toJS({'error': msg})
		done()

	id = int(id)
	request['wrappers'] = False

	sprint = Sprint.load(id)
	if not sprint:
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
def apiSprintsList(handler, request, calendar = False, start = None, end = None, _ = None):
	def die(msg):
		print toJS({'error': msg})
		done()

	request['wrappers'] = False
	start = int(start) if start else None
	end = int(end) if end else None

	sprints = Sprint.loadAll()
	if start and end:
		sprints = filter(lambda sprint: (start <= sprint.start <= end) or (start <= sprint.end <= end), sprints)

	rtn = [{'id': sprint.id,
	        'title': sprint.name,
	        'start': tsToDate(sprint.start).strftime('%Y-%m-%d'),
	        'end': tsToDate(sprint.end).strftime('%Y-%m-%d'),
	        'active': sprint.isActive(),
	        'member': handler.session['user'] in sprint.members
	       } for sprint in sprints]
	if calendar:
		for entry in rtn:
			entry.update({'color': 'green' if entry['member'] and entry['active'] else '#36c;'})
	print toJS(rtn)

