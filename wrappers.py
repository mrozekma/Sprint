from datetime import datetime
from json import dumps as toJS
from random import randint
import os

import HTTPHandler
import menu
from DB import db
from ChangeLog import getChanges
from Options import option
from LoadValues import getRevisionInfo, isDevMode
from Settings import settings
from User import User
from Message import Message
from utils import *

def header(handler, includes):
	print "<!DOCTYPE html>"
	print "<html>"
	print "<head>"
	print "<title>$title$</title>"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/syntax-highlighting.css\">"
	print "<link rel=\"shortcut icon\" href=\"/static/images/favicon.ico\">"

	print "<script src=\"/static/jquery.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery-migrate-1.1.1.min.js\" type=\"text/javascript\"></script>"
	print "<link rel=\"stylesheet\" href=\"/static/jquery-ui-1.10.1.custom.css\">"
	print "<script src=\"/static/jquery-ui-1.10.1.custom.min.js\" type=\"text/javascript\"></script>"
	print "<link href=\"/static/jquery.contextMenu.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.contextMenu.js\"></script>"
	print "<script src=\"/static/jquery.mousewheel-min.js\"></script>"
	print "<script src=\"/static/jquery.terminal-0.4.23.js\"></script>"
	print "<link href=\"/static/jquery.terminal.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.ba-bbq.js\"></script>"

	print "<script src=\"/static/bootstrap-dropdown.js\" type=\"text/javascript\"></script>"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/bootstrap.css\">"

	print "<link rel=\"stylesheet\" href=\"/static/chosen/chosen.css\" />"
	print "<script src=\"/static/chosen/chosen.jquery.js\" type=\"text/javascript\"></script>"

	print "<script src=\"/static/noty/jquery.noty.js\"></script>"
	print "<script src=\"/static/noty/layouts/bottomCenter.js\"></script>"
	print "<script src=\"/static/noty/themes/default.js\"></script>"
	print "<script src=\"/static/noty/themes/sprint.js\"></script>"

	print "<script src=\"/static/script.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/shell.js\" type=\"text/javascript\"></script>"

	print "<style type=\"text/css\">"
	if handler.session['user']:
		print ".username[username~=\"%s\"] {" % handler.session['user'].username
		print "    color: #C00;"
		print "    font-weight: bold;"
		print "}"
	print "</style>"

	for filename in includes['less']:
		print "<link rel=\"stylesheet/less\" type=\"text/css\" href=\"%s\" />" % filename
	# for filename in includes['css']:
		# print "<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\" />" % filename
	for filename in includes['js']:
		print "<script src=\"%s\" type=\"text/javascript\"></script>" % filename

	print "<link rel=\"stylesheet/less\" type=\"text/css\" href=\"/static/style.less\">"
	print "<script type=\"text/javascript\">"
	print "less = {"
	print "    env: '%s'," % ('development' if isDevMode(handler) else 'production')
	print "    async: false,"
	print "    dumpLineNumbers: 'comments'"
	print "};"
	print "</script>"
	print "<script src=\"/static/less.js\" type=\"text/javascript\"></script>"

	changes = list(getChanges(handler, handler.path))
	if changes:
		print "<script src=\"/static/changelog.js\"></script>"
		print "<script type=\"text/javascript\">"
		print "$(document).ready(function() {"
		fmt = "%%(message)s<div style=\"text-align: right; font-size: 6pt\"><a target=\"_blank\" href=\"%s\">%%(hash)s</a></div>" % settings.gitURL if 'gitURL' in settings else "%(message)s"
		for change in changes:
			print "    showChangelog(%s);" % toJS(fmt % {'hash': change.hash, 'message': change.message})
		print "});"
		print "</script>"

	print "</head>"
	print "<body>"
	print "<div id=\"shell\"></div>"
	print "<div id=\"frame\">"

	print "<div id=\"main_a\">"
	if handler.session['user']:
		print "<div class=\"avatar\">"
		print "<img class=\"avatar\" src=\"%s\">" % handler.session['user'].getAvatar()
		print "<div class=\"subavatar\">"
		if 'impersonator' in handler.session:
			print "<img class=\"subavatar\" src=\"%s\" onClick=\"unimpersonate();\" title=\"Unimpersonate\">" % handler.session['impersonator'].getAvatar()
		else:
			unreadMessages = Message.loadAll(userid = handler.session['user'].id, read = False)
			if len(unreadMessages) > 0:
				print "<a class=\"inbox\" href=\"/messages/inbox\">%d</a>" % len(unreadMessages)
		print "</div>"
		print "</div>"
	print "<div class=\"navigation\">"
	print "<div class=\"ident\">"
	if handler.session['user']:
		print "Logged in as %s" % handler.session['user']
	else:
		print "<a href=\"/login\">Not logged in</a>"
	print "</div>"

	if (option('dev') or isDevMode(handler)) and handler.session['user'] and handler.session['user'].hasPrivilege('Dev'):
		if isDevMode(handler):
			print "<div class=\"devwarning\" onClick=\"buildmode('production')\">"
			print "Development"
			print "</div>"
		else:
			print "<div class=\"prodwarning\" onClick=\"buildmode('development')\">"
			print "Production"
			print "</div>"

	print "<div class=\"topmenu\">"
	print menu.render(handler, handler.path)
	print "</div>"
	print "</div>"
	print "</div>"

	print "<div id=\"main_b\"></div>"

	print "<div id=\"main_c\">"

	if settings.systemMessage:
		print "<div class=\"sysmessage\">%s</div>" % settings.systemMessage

	print "<div id=\"main_d\">"

	print "<h1>$bodytitle$</h1>"

def footer(handler):
	print "</div>"
	print "<br style=\"clear:both\">"
	print "</div>"
	print "</div>"

	print "</div>"

	revisionHash, revisionDate, revisionRelative = getRevisionInfo()
	print "<div class=\"footer_timestamp\">"
	print "Current system time: %s<br>" % getNow()
	print "Current revision:",
	if isDevMode():
		print "<span style=\"color: #f00;\">Development build</span><br>"
		if isDevMode(handler):
			selects, updates = db().resetCount()
			print "Database (%s) requests: %d / %d<br>" % (settings.dbVersion, selects, updates)
	else:
		if 'gitURL' in settings:
			print "<a href=\"%s\">%s</a>" % (settings.gitURL % {'hash': revisionHash}, revisionHash),
		else:
			print revisionHash,
		print "(<span title=\"%s\">%s</span>)<br>" % (revisionDate, revisionRelative)
	print "</div>"

	print "</body>"
	print "</html>"
