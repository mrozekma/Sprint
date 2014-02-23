from __future__ import division
from base64 import b64encode, b64decode
from datetime import datetime
from imghdr import what as imgtype
from itertools import groupby
from PIL import Image
from StringIO import StringIO

from rorn.Box import SuccessBox, ErrorBox
from rorn.Session import delay, undelay

from Settings import settings
from User import User, USERNAME_PATTERN, AVATAR_TYPES, AVATAR_MAX_SIZE
from Privilege import requirePriv
from Sprint import Sprint
from Task import Task
from Availability import Availability
from Button import Button
from Chart import Chart
from LoadValues import isDevMode
from Markdown import Markdown
from relativeDates import timesince
from utils import *

@get('users')
def users(handler):
	handler.title('Users')

	users = User.loadAll(orderby = 'username')
	print "<div class=\"user-list\">"
	for user in users:
		print "<div class=\"user-list-entry\"><a href=\"/users/%s\"><img src=\"%s\"></a><br>%s</div>" % (user.username, user.getAvatar(64), user.safe.username)
	print "</div>"
	print "<div class=\"clear\"></div>"

@get("users/(?P<username>%s)" % USERNAME_PATTERN, statics = 'user-profile')
def user(handler, username):
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
	if isDevMode(handler):
		print "<div class=\"debugtext\">User ID: %d</div>" % user.id
	print "<div class=\"clear\"></div>"

	if handler.session['user'] and handler.session['user'].hasPrivilege('Admin'):
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
		if user.hasLocalAvatar():
			print "Your avatar is currently <a href=\"/users/%s/avatar/set\">locally hosted</a>" % user.username
		else:
			print "Your avatar can be changed at <a href=\"http://gravatar.com/\" target=\"_new\">http://gravatar.com/</a>. It must be associated with the e-mail <b>%s</b>, and be rated PG. You can also host an avatar <a href=\"/users/%s/avatar/set\">locally</a>, if necessary" % (user.getEmail(), user.username)

		print "<h3>Authentication</h3>"
		print "Your sprint tool password can be changed <a href=\"/resetpw\">here</a>.",
		if settings.kerberosRealm:
			print "You can also use your %s kerberos password to login" % settings.kerberosRealm,
		print "<br><br>"
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

@get("users/(?P<username>%s)/tasks" % USERNAME_PATTERN)
def userTasks(handler, username):
	handler.title('User tasks')
	user = User.load(username = username)
	if not user:
		ErrorBox.die("User tasks", "No user named <b>%s</b>" % stripTags(username))

	tasks = [task.id for task in Task.loadAll() if user in task.assigned and task.stillOpen() and task.sprint.isActive()]
	if len(tasks) == 0:
		ErrorBox.die("User tasks", "%s has no open tasks in active sprints" % user)

	redirect("/tasks/%s" % ','.join(map(str, tasks)))

@get("users/(?P<username>%s)/avatar" % USERNAME_PATTERN)
def userAvatarShow(handler, username, size = 80):
	def die(msg):
		print msg
		done()

	handler.wrappers = False
	size = to_int(size, 'size', die)
	user = User.load(username = username)
	if not user:
		redirect(User.getBlankAvatar())
	if user.avatar is None:
		redirect(user.getAvatar())

	data = b64decode(user.avatar)
	image = Image.open(StringIO(data))
	image = image.resize((size, size), Image.ANTIALIAS)
	out = StringIO()
	image.save(out, 'png')
	print out.getvalue()
	handler.contentType = 'image/png'

@get("users/(?P<username>%s)/avatar/set" % USERNAME_PATTERN)
def userAvatarSet(handler, username):
	handler.title('Set avatar')
	requirePriv(handler, 'User')
	user = User.load(username = username)
	if not user:
		ErrorBox.die("Set avatar", "No user named <b>%s</b>" % stripTags(username))
	if user != handler.session['user']: #TODO Allow devs
		redirect("/users/%s/avatar/set" % handler.session['user'].username)

	print "Restrictions on a locally hosted avatar:"
	print "<ul>"
	print "<li>Type: %s</li>" % ", ".join(AVATAR_TYPES).upper()
	print "<li>Size: %s bytes</li>" % AVATAR_MAX_SIZE
	print "</ul>"

	print "<form method=\"post\" enctype=\"multipart/form-data\" action=\"/users/%s/avatar/set\">" % user.username
	print "<input type=\"file\" name=\"data\"><br>"
	# Using a plain button here because the file field isn't styled
	print "<button>Upload</button>"
	print "</form>"

	if user.hasLocalAvatar():
		print "<br>"
		print "You can also remove your existing local avatar. Your account will switch back to using your gravatar image<br>"
		print "<form method=\"post\" action=\"/users/%s/avatar/remove\">" % user.username
		print "<button>Remove avatar</button>"
		print "</form>"

@post("users/(?P<username>%s)/avatar/set" % USERNAME_PATTERN)
def userAvatarSet(handler, username, p_data):
	handler.title('Set avatar')
	requirePriv(handler, 'User')
	user = User.load(username = username)
	if not user:
		ErrorBox.die("Set avatar", "No user named <b>%s</b>" % stripTags(username))
	if user != handler.session['user']: #TODO Allow devs
		redirect("/users/%s/avatar/set" % handler.session['user'].username)

	if len(p_data) > AVATAR_MAX_SIZE:
		ErrorBox.die("Set avatar", "Avatar too large (%s)" % pluralize(len(p_data), 'byte', 'bytes'))
	type = imgtype(None, p_data)
	if type is None:
		ErrorBox.die("Set avatar", "Image type unrecognized")
	elif type not in AVATAR_TYPES:
		ErrorBox.die("Set avatar", "Unsupported image type %s" % type.upper())

	user.avatar = b64encode(p_data)
	user.save()
	delay(handler, SuccessBox("Avatar uploaded"))
	redirect("/users/%s" % user.username)

@post("users/(?P<username>%s)/avatar/remove" % USERNAME_PATTERN)
def userAvatarRemove(handler, username):
	handler.title('Remove avatar')
	requirePriv(handler, 'User')
	user = User.load(username = username)
	if not user:
		ErrorBox.die("Remove avatar", "No user named <b>%s</b>" % stripTags(username))
	if user != handler.session['user']: #TODO Allow devs
		redirect("/users/%s/avatar/set" % handler.session['user'].username)

	user.avatar = None
	user.save()
	delay(handler, SuccessBox("Avatar removed"))
	redirect("/users/%s" % user.username)
