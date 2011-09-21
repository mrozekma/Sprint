from __future__ import division
from datetime import datetime
from itertools import groupby

from rorn.Box import ErrorBox

from User import User
from Sprint import Sprint
from Availability import Availability
from Chart import Chart
from relativeDates import timesince
from utils import *

@get('users')
def users(handler, request):
	handler.title('Users')

	users = User.loadAll(orderby = 'username')
	for user in users:
		print "<div class=\"user-list-entry\"><a href=\"/users/%s\"><img src=\"%s\"></a><br>%s</div>" % (user.username, user.getAvatar(64), user.safe.username)

@get('users/(?P<username>[^/]+)')
def user(handler, request, username):
	user = User.load(username = username)
	if not user:
		ErrorBox.die('User', "No user named <b>%s</b>" % stripTags(username))

	Chart.include()

	handler.title(user.safe.username)
	handler.replace('$bodytitle$', '', 1)
	print "<img src=\"%s\" class=\"gravatar\">" % user.getAvatar(64)
	print "<h1>%s</h1>" % user.safe.username
	print "<div class=\"clear\"></div>"

	if user == handler.session['user']:
		print "<h3>Avatar</h3>"
		print "Your avatar can be changed at <a href=\"http://gravatar.com/\" target=\"_new\">http://gravatar.com/</a>. It must be associated with the e-mail <b>%s@microsemi-wl.com</b>, and be rated PG" % user.safe.username

		print "<h3>Authentication</h3>"
		print "Your password can be changed <a href=\"/resetpw\">here</a><br>"

	print "<h3>Last seen</h3>"
	if not user.lastseen:
		print "Never"
	elif dateToTs(datetime.now()) - user.lastseen < 60:
		print "Just now"
	else:
		print "%s ago" % timesince(tsToDate(user.lastseen))

	print "<h3>Project distribution</h3>"
	sprints = filter(lambda s: user in s.members, Sprint.loadAllActive())
	sprintHours = map(lambda s: (s, Availability(s).getAllForward(datetime.now(), user)), sprints)
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
