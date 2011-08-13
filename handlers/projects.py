from __future__ import with_statement

from rorn.Session import undelay
from rorn.Box import ErrorBox

from Privilege import requirePriv
from Project import Project
from Sprint import Sprint
from Button import Button
from utils import *

@get('projects')
def projects(handler, request):
	requirePriv(handler, 'User')
	handler.title("Projects")
	showProjects(handler)

def showProjects(handler):
	undelay(handler)

	print "<div class=\"indented\">"
	for project in Project.loadAll():
		sprints = project.getSprints()

		classes = ['project-summary']
		if any(map(lambda sprint: sprint.isActive(), sprints)):
			classes.append('active')
		print "<div id=\"project-summary-%d\" class=\"%s\">" % (project.id, ' '.join(classes))
		print "<div class=\"project-name\">%s</div>" % project.name
		print "<div class=\"buttons\">"
		print Button("new sprint", "/sprints/new?project=%d" % project.id).mini()
		print Button("other", "#").mini()
		print "</div>"

		print "<div class=\"project-members\">"
		print "<div class=\"member scrummaster\">%s</div>" % project.owner.str('scrummaster')
		for member in sorted(project.getMembers()):
			if member == project.owner: continue
			print "<div class=\"member\">%s</div>" % member.str('member')
		print "</div>"

		if sprints:
			print "<div class=\"sprint-summaries\">"
			for sprint in sprints:
				print "<div class=\"sprint-summary\">%s <span class=\"sprint-time\">(%s - %s)</span></div>" % (sprint.link(), sprint.getStartStr(), sprint.getEndStr())
			print "</div>"
		else:
			print "&nbsp;"

		print "<div class=\"clear\"></div>"
		print "</div>"
	print "</div>"
