from __future__ import with_statement

from rorn.ResponseWriter import ResponseWriter
from rorn.Session import undelay
from rorn.Box import ErrorBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from LoadValues import isDevMode
from sprints import tabs as sprintTabs
from utils import *

@get('', statics = 'projects')
@get('projects', statics = 'projects')
@get('projects/list', statics = 'projects')
def projectsList(handler, request):
	undelay(handler)

	print "<div class=\"project-list\">"
	print "<div class=\"buttons\">"
	print Button('Calendar', '/projects/calendar')
	print "</div>"
	for project in Project.getAllSorted(handler.session['user']):
		sprints = project.getSprints()
		active, inactive = partition(lambda sprint: sprint.isActive() or sprint.isPlanning(), reversed(sprints))
		activeMembers = set(sum((sprint.members for sprint in active), []))
		isTest = project.id < 0

		classes = ['project-summary']
		if len(active) > 0:
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

		print "<div class=\"project-members %s\">" % ('short' if len(inactive) <= 6 or len(active) == 0 else 'long')
		members = set(project.getMembers())
		scrummasters = set(sprint.owner for sprint in active)
		for member in sorted(scrummasters):
			print "<div class=\"member scrummaster\">%s</div>" % member.str('scrummaster')
		for member in sorted(activeMembers - scrummasters):
			print "<div class=\"member active\">%s</div>" % member.str('member')
		for member in sorted(members - activeMembers - scrummasters):
			print "<div class=\"member inactive\">%s</div>" % member.str('member')
		print "</div>"

		if sprints:
			def printSprint(sprint):
				if sprint.isActive() or sprint.isPlanning():
					print "<div class=\"sprint-active\">"
					print "<div class=\"sprint-name\">%s</div>" % sprint.link(handler.session['user'], 'sprint-large')
					print "<div class=\"sprint-time\">"
					if sprint.isPlanning():
						print "<span class=\"label danger\">Planning</span>"
					elif sprint.isReview():
						print "<span class=\"label success\">Review</span>"
					else:
						day = Weekday.today().date()
						sprintDays = [i.date() for i in sprint.getDays()]
						print "<span class=\"label primary\">Day %d of %d</span>" % (sprintDays.index(day) + 1, len(sprintDays))
					print "</div><br>"
					for tab in sprintTabs().group('').values():
						print "<a href=\"%s\">%s</a>" % (tab.getPath(sprint.id), tab.getDisplayName().lower())
					print "</div>"
				else:
					print "<div class=\"sprint-summary\">%s <span class=\"sprint-time\">(%s - %s)</span></div>" % (sprint.link(handler.session['user']), sprint.getStartStr(), sprint.getEndStr())

			print "<div class=\"sprint-summaries\">"
			map(printSprint, active)
			if len(inactive) <= 6:
				map(printSprint, inactive)
			else:
				map(printSprint, inactive[:5])
				print "<div class=\"show-old-sprints\">(%d more)</div>" % (len(inactive) - 5)
				print "<div class=\"old-sprints\">"
				map(printSprint, inactive[5:])
				print "</div>"
			print "</div>"
		else:
			print "&nbsp;"

		print "<div class=\"clear\"></div>"
		print "</div>"
	print "</div>"

@get('projects/calendar')
def projectsCalendar(handler, request):
	undelay(handler)

	print "<link href=\"/static/fullcalendar.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/fullcalendar.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/projects-calendar.js\" type=\"text/javascript\"></script>"
	print "<div id=\"calendar\"></div>"
