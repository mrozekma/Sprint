from datetime import datetime
from random import randint
import os

import HTTPHandler
import menu
from DB import db
from Options import option
from LoadValues import getRevisionInfo, isDevMode
from Settings import settings
from User import User
from Message import Message
from utils import *

def header(handler, path):
	print "<!DOCTYPE html>"
	print "<html>"
	print "<head>"
	print "<title>$title$</title>"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/style.css\">"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/bootstrap.css\">"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/syntax-highlighting.css\">"
	print "<link rel=\"shortcut icon\" href=\"/static/images/favicon.ico\">"
	print "<script src=\"/static/jquery.js\" type=\"text/javascript\"></script>"

	print "<link rel=\"stylesheet\" href=\"/static/jquery-ui-1.8.14.custom.css\">"
	print "<script src=\"/static/jquery-ui-1.8.14.custom.min.js\" type=\"text/javascript\"></script>"

	print "<link href=\"/static/jquery.contextMenu.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/jquery.contextMenu.js\"></script>"

	print "<link rel=\"stylesheet\" href=\"/static/chosen/chosen.css\" />"
	print "<script src=\"/static/chosen/chosen.jquery.js\" type=\"text/javascript\"></script>"

	print "<script src=\"/static/script.js\" type=\"text/javascript\"></script>"

	print "<style type=\"text/css\">"
	print "#main_a {"
	print "    background-color: $headerbg$;"
	print "}"
	if handler.session['user']:
		print ".username[username~=\"%s\"] {" % handler.session['user'].username
		print "    color: #C00;"
		print "    font-weight: bold;"
		print "}"
	print "</style>"

	print "</head>"
	print "<body>"
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
	print menu.render(handler, path)
	print "</div>"
	print "</div>"
	print "</div>"

	print "<div id=\"main_b\"></div>"

	print "<div id=\"main_c\">"

	if settings.systemMessage:
		print "<div class=\"sysmessage\">%s</div>" % settings.systemMessage

	print "<div id=\"main_d\">"

	print "<h1>$bodytitle$</h1>"

def footer(handler, path):
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
