from json import dumps as toJS

from Project import Project
from Sprint import Sprint
from utils import *

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
			'name': sprint.name,
			'start': sprint.start,
			'end': sprint.end
			})
