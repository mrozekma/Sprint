from rorn.Box import WarningBox

from Search import Search

from utils import *

@get('help/search')
def helpSearch(handler, request):
	handler.title("Search")

	print "Searching is a combination of miscellaneous filters and a free-form task name fuzzy search. The search operators are:<br>"

	#TODO
	operators = [('assigned', "Comma-separated list of usernames the task is assigned to"), ('status', "Comma-separated list of the task's current status"), ('hours', "The tasks current hours (or a range of valid hours, e.g. <code>4-8</code>)"), ('goal', "Comma-separated list of goal colors"), ('created', "YYYYMMDD date (or range of dates) the task was created in"), ('modified', "YYYYMMDD date (or range of dates) the task was modified in")]

	print "<ul>"
	for (name, desc) in operators:
		print "<li><b>%s</b> &mdash; %s" % (name, desc)
	print "</ul>"

	print "Search operators are of the form <code>name:value</code>, e.g. <code>status:complete,deferred</code>. Fields can be quoted as necessary, e.g. <code>status:\"not started\"</code><br><br>"

	print "Any non-search operator is assumed to be part of the free-form task name search. For example, <code>foo hours:4 bar</code> shows all 4 hour tasks matching the string \"foo bar\". Task names must be at least %d%% similar to the free-form search to match<br><br>" % Search.minMatchPercent()

	print "The number of matching tasks is shown on the backlog dateline. The <img class=\"bumpdown\" src=\"/static/images/cross.png\"> icon cancels the search and shows all tasks"
