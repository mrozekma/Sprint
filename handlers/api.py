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

	sprints = sorted(filter(lambda sprint: sprint.isActive(), project.getSprints()), lambda (x, y): cmp(x.start, y.start))
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

	print toJS({
			'id': sprint.id,
			'name': sprint.name,
			'start': sprint.start,
			'end': sprint.end
			})
