from datetime import datetime
from random import randint
import sys
import os
import HTTPHandler
import menu
from DB import db
from LoadValues import getRevisionInfo, isDevMode
from Settings import settings
from utils import *

# class LeftMenu:
	# def __init__(self):
		# self.entries = []

	# # text => url
	# def __setitem__(self, k, v):
		# self.entries.append((k, v))

	# def clear(self):
		# self.entries = []

	# def __str__(self):
		# if len(self.entries) == 0:
			# return "&nbsp;"

		# return "<br>\n".join(["<a href=\"%s\">%s</a>" % (url, text) for (text, url) in self.entries])

def header(handler, path):
	# print "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">"
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

	print "<script src=\"/static/script.js?v=%d\" type=\"text/javascript\"></script>" % randint(0, 1000000) # TODO Remove

	print "<style type=\"text/css\">"
	print "#main_a {"
	print "    background-color: $headerbg$;"
	print "}"
	if handler.session['user']:
		print ".username[username=\"%s\"] {" % handler.session['user'].username
		print "    color: #C00;"
		print "    font-weight: bold;"
		print "}"
	print "</style>"

		# print "<script type=\"text/javascript\">"
		# print "$(document).ready(function () {"
		# print "    $(\".username:econtains('%s')\").addClass('me');" % handler.session['user'].username
		# print "});"
		# print "</script>"

	print "</head>"
	print "<body>"
	print "<div id=\"frame\">"

	print "<div id=\"main_a\">"
	if handler.session['user']:
		print "<img class=\"avatar\" src=\"%s\">" % handler.session['user'].getAvatar()
	print "<div class=\"navigation\">"
	print "<div class=\"ident\">"
	if handler.session['user']:
		print "Logged in as %s" % handler.session['user']
	else:
		print "<a href=\"/login\">Not logged in</a>"
	print "</div>"

	if ('--dev' in sys.argv or isDevMode(handler)) and handler.session['user'] and handler.session['user'].hasPrivilege('Dev'):
		if isDevMode(handler):
			print "<div class=\"devwarning\" onClick=\"buildmode('production')\">"
			print "Development"
			print "</div>"
		else:
			print "<div class=\"prodwarning\" onClick=\"buildmode('development')\">"
			print "Production"
			print "</div>"

	print "<div class=\"topmenu\">"
	print menu.render(handler)
	print "</div>"
	print "</div>"
	print "</div>"

	print "<div id=\"main_b\"></div>"

	print "<div id=\"main_c\">"
	print "<div id=\"main_d\">"

	# print "<div style=\"width: 200px; float: left\">"
	# print handler.leftMenu
	# print "</div>"

	# print "<div style=\"width: 700px; float: left\">"
	print "<h1>$bodytitle$</h1>"

def footer(handler, path):
	# print "</div>"
	print "</div>"
	print "<br style=\"clear:both\">"
	print "</div>"
	print "</div>"

	# print "<br style=\"clear:both\">"

	print "</div>"

	revisionHash, revisionDate, revisionRelative = getRevisionInfo()
	print "<div class=\"footer_timestamp\">"
	print "Current system time: %s<br>" % getNow()
	print "Current revision:",
	if isDevMode():
		print "<span style=\"color: #f00;\">Development build</span><br>"
		if isDevMode(handler):
			queries = db().resetCount()
			print "Database (%s) requests: %d<br>" % (settings.dbVersion, queries)
	else:
		if 'gitURL' in settings:
			print "<a href=\"%s\">%s</a>" % (settings.gitURL % {'hash': revisionHash}, revisionHash),
		else:
			print revisionHash,
		print "(<span title=\"%s\">%s</span>)<br>" % (revisionDate, revisionRelative)
	print "</div>"

	print "</body>"
	print "</html>"

# class Frame:
	# def __init__(self, handler, path, title = None):
		# self.handler = handler
		# self.path = path
		# self.title = title

	# def __enter__(self):
		# header(self.handler, self.path)
		# if self.title:
			# self.handler.title(self.title)

	# def __exit__(self, *args):
		# footer(self.handler, self.path)
