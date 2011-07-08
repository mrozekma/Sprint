from datetime import datetime
from random import randint
import os
import HTTPHandler
import menu
from utils import *

class LeftMenu:
	def __init__(self):
		self.entries = []

	# text => url
	def __setitem__(self, k, v):
		self.entries.append((k, v))

	def clear(self):
		self.entries = []

	def __str__(self):
		if len(self.entries) == 0:
			return "&nbsp;"

		return "<br>\n".join(["<a href=\"%s\">%s</a>" % (url, text) for (text, url) in self.entries])

def header(handler, path):
	print "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">"
	print "<html>"
	print "<head>"
	print "<title>$title$</title>"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/style.css\">"
	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/syntax-highlighting.css\">"
	print "<script src=\"/static/jquery.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery-ui-1.8.2.custom.min.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/jquery.contextMenu.js\"></script>"
	print "<link href=\"/static/jquery.contextMenu.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/script.js?v=%d\" type=\"text/javascript\"></script>" % randint(0, 1000000) # TODO Remove

	if handler.session['user']:
		print "<style type=\"text/css\">"
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
		print "Not logged in"
	print "</div>"
	print menu.render(handler)
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

	revisionHash, revisionDate, revisionRelative = os.popen('git log -n 1 --format=format:"%H %ct %cr"').read().split(' ', 2)
	revisionDate = tsToDate(int(revisionDate)).strftime('%d %b %Y %H:%M:%S')
	print "<div class=\"footer_timestamp\">"
	print "Current system time: %s<br>" % datetime.now()
	print "Current revision: <a href=\"http://work.mrozekma.com:8080/?p=Sprint;a=commitdiff;h=%s\">%s</a> (<span title=\"%s\">%s</span>)" % (revisionHash, revisionHash, revisionDate, revisionRelative)
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
