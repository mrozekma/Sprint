from __future__ import with_statement

from rorn.ResponseWriter import ResponseWriter
from rorn.Session import undelay
from rorn.Box import ErrorBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from LoadValues import isDevMode
from utils import *

@get('', statics = 'projects')
@get('projects', statics = 'projects')
@get('projects/list', statics = 'projects')
def projectsList(handler, request):
	undelay(handler)

	boxes = {} # project -> {'str': box HTML, 'weight': ascending sort weight}
	for project in Project.getAllSorted(handler.session['user']):
		writer = ResponseWriter()
		sprints = project.getSprints()
		activeSprints = filter(lambda sprint: sprint.isActive(), sprints)
		activeMembers = set(sum((sprint.members for sprint in activeSprints), []))
		isTest = project.id < 0

		classes = ['project-summary']
		if len(activeSprints) > 0:
			classes.append('active')
		if isTest:
			classes.append('test')
		print "<div id=\"project-summary-%d\" class=\"%s\">" % (project.id, ' '.join(classes))
		print "<div class=\"project-name\">%s</div>" % project.name
		print "<div class=\"buttons\">"
		print Button("new sprint", "/sprints/new?project=%d" % project.id).mini()
		print Button("export", "/sprints/export?project=%d" % project.id).mini()
		print Button("active", "/sprints/active?project=%d" % project.id).mini()
		if handler.session['user'] and handler.session['user'].hasPrivilege('Dev'):
			print Button("manage", "/admin/projects/%d" % project.id).mini().negative()
		print "</div>"

		print "<div class=\"project-members\">"
		scrummasters = set(sprint.owner for sprint in sprints)
		for member in sorted(scrummasters):
			print "<div class=\"member scrummaster\">%s</div>" % member.str('scrummaster')
		for member in sorted(project.getMembers()):
			if member in scrummasters: continue
			print "<div class=\"member %s\">%s</div>" % ('active' if member in activeMembers or len(activeSprints) == 0 else 'inactive', member.str('member'))
		print "</div>"

		if sprints:
			print "<div class=\"sprint-summaries\">"
			for sprint in sprints:
				print "<div class=\"sprint-summary\">%s <span class=\"sprint-time\">(%s - %s)</span></div>" % (sprint.link(handler.session['user']), sprint.getStartStr(), sprint.getEndStr())
			print "</div>"
		else:
			print "&nbsp;"

		print "<div class=\"clear\"></div>"
		print "</div>"
		boxes[project] = {'str': writer.done(), 'weight': (2 if isTest else 0) + (0 if handler.session['user'] in activeMembers else 1)}

	print "<div class=\"project-list\">"
	print "<div class=\"buttons\">"
	print Button('Calendar', '/projects/calendar')
	print "</div>"
	# Show projects with active sprints this user is a member of first
	for project in sorted(boxes.keys(), key = lambda p: boxes[p]['weight']):
		print boxes[project]['str']
	print "</div>"

@get('projects/calendar')
def projectsCalendar(handler, request):
	undelay(handler)

	print "<link href=\"/static/fullcalendar.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/fullcalendar.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/projects-calendar.js\" type=\"text/javascript\"></script>"
	print "<div id=\"calendar\"></div>"
