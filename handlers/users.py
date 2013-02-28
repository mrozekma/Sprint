from __future__ import division
from datetime import datetime
from itertools import groupby

from rorn.Box import ErrorBox
from rorn.Session import undelay

from User import User
from Sprint import Sprint
from Task import Task
from Availability import Availability
from Button import Button
from Chart import Chart
from Markdown import Markdown
from relativeDates import timesince
from utils import *

@get('users')
def users(handler, request):
	handler.title('Users')

	users = User.loadAll(orderby = 'username')
	print "<div class=\"user-list\">"
	for user in users:
		print "<div class=\"user-list-entry\"><a href=\"/users/%s\"><img src=\"%s\"></a><br>%s</div>" % (user.username, user.getAvatar(64), user.safe.username)
	print "</div>"
	print "<div class=\"clear\"></div>"

@get('users/(?P<username>[^/]+)')
def user(handler, request, username):
	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	Markdown.head('form#message-form .body pre code')
	print "<script src=\"/static/jquery.typing-0.2.0.min.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/users.js\" type=\"text/javascript\"></script>"
	Chart.include()
	undelay(handler)

	handler.title(user.safe.username)
	handler.replace('$bodytitle$', '', 1)
	print "<img src=\"%s\" class=\"gravatar\">" % user.getAvatar(64)
	print "<h1>%s</h1>" % user.safe.username
	print "<div class=\"clear\"></div>"

	if handler.session['user'] and handler.session['user'].hasPrivilege('Dev'):
		print "<h3>Admin</h3>"
		print "<form method=\"post\" action=\"/admin/users\">"
		print "<input type=\"hidden\" name=\"username\" value=\"%s\">" % user.username
		print "<button type=\"submit\" class=\"btn\" name=\"action\" value=\"resetpw\">Reset password</button>"
		print "<button type=\"submit\" class=\"btn\" name=\"action\" value=\"impersonate\">Impersonate</button>"
		print "<button type=\"submit\" class=\"btn\" name=\"action\" value=\"sessions\">Manage sessions</button>"
		print "<button type=\"submit\" class=\"btn\" name=\"action\" value=\"privileges\">Manage privileges</button>"
		print "</form>"

	if user == handler.session['user']:
		print "<h3>Avatar</h3>"
		print "Your avatar can be changed at <a href=\"http://gravatar.com/\" target=\"_new\">http://gravatar.com/</a>. It must be associated with the e-mail <b>%s</b>, and be rated PG" % user.getEmail()

		print "<h3>Authentication</h3>"
		print "Your password can be changed <a href=\"/resetpw\">here</a><br><br>"
		if user.hotpKey == '':
			print "You also have the option to use two-factor authentication via <a href=\"http://en.wikipedia.org/wiki/HOTP\">HOTP</a>. You can use <a href=\"http://support.google.com/a/bin/answer.py?hl=en&answer=1037451\">Google Authenticator</a> to generate verification codes<br><br>"
			print "<form method=\"post\" action=\"/security/two-factor\">"
			print "<button type=\"submit\" class=\"btn danger\" name=\"action\" value=\"enable\">Enable two-factor authentication</button>"
			print "</form>"
		else:
			print "You are currently using two-factor authentication<br><br>"
			print "<form method=\"post\" action=\"/security/two-factor\">"
			print "<button type=\"submit\" class=\"btn danger\" name=\"action\" value=\"enable\">Reset HOTP key</button>"
			print "<button type=\"submit\" class=\"btn danger\" name=\"action\" value=\"disable\">Disable two-factor authentication</button>"
			print "</form>"

		print "<h3>Messages</h3>"
		print "Your inbox and sent messages can be viewed <a href=\"/messages/inbox\">here</a><br>"

	print "<h3>Last seen</h3>"
	if not user.lastseen:
		print "Never"
	elif dateToTs(getNow()) - user.lastseen < 60:
		print "Just now"
	else:
		print "%s ago" % timesince(tsToDate(user.lastseen))

	if handler.session['user'] and handler.session['user'] != user:
		print "<h3>Message</h3>"
		print "<small>(Messages are formatted in <a target=\"_blank\" href=\"/help/markdown\">markdown</a>)</small>"
		print "<form id=\"message-form\" method=\"post\" action=\"/messages/send\">"
		print "<input type=\"hidden\" name=\"userid\" value=\"%d\">" % user.id
		print "<textarea name=\"body\" class=\"large\"></textarea>"
		print "<div class=\"body markdown\"><div id=\"preview\"></div></div>"
		print Button('Send').post().positive()
		print "</form>"

	print "<h3>Project distribution</h3>"
	sprints = filter(lambda s: user in s.members, Sprint.loadAllActive())
	sprintHours = map(lambda s: (s, Availability(s).getAllForward(getNow(), user)), sprints)
	projectHours = map(lambda (p, g): (p, sum(hours for sprint, hours in g)), groupby(sprintHours, lambda (s, a): s.project))

	# For now at least, don't show projects with no hours
	projectHours = filter(lambda (p, h): h > 0, projectHours)
	if len(projectHours) > 0:
		chart = Chart('chart')
		chart.title.text = ''
		chart.tooltip.formatter = "function() {return '<b>' + this.point.name + '</b>: ' + this.point.y + '%';}"
		chart.plotOptions.pie.allowPointSelect = True
		chart.plotOptions.pie.cursor = 'pointer'
		chart.plotOptions.pie.dataLabels.enabled = False
		chart.plotOptions.pie.showInLegend = True
		chart.credits.enabled = False
		chart.series = seriesList = []

		series = {
			'type': 'pie',
			'name': '',
			'data': []
		}
		seriesList.append(series)

		total = sum(hours for project, hours in projectHours)
		for project, hours in projectHours:
			series['data'].append([project.name, float("%2.2f" % (100 * hours / total))])

		chart.js()
		chart.placeholder()
	else:
		print "Not a member of any active sprints"

@get('users/(?P<username>[^/]+)/tasks')
def userTasks(handler, request, username):
	handler.title('User tasks')
	user = User.load(username = username)
	if not user:
		ErrorBox.die("User tasks", "No user named <b>%s</b>" % stripTags(username))

	tasks = [task.id for task in Task.loadAll(assignedid = user.id) if task.stillOpen() and task.sprint.isActive()]
	if len(tasks) == 0:
		ErrorBox.die("User tasks", "%s has no open tasks in active sprints" % user)

	redirect("/tasks/%s" % ','.join(map(str, tasks)))
