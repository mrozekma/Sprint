from json import dumps as toJS

from rorn.Box import InfoBox, SuccessBox, ErrorBox
from rorn.Session import delay, undelay

from Button import Button
from Privilege import requirePriv
from SavedSearch import SavedSearch
from Tabs import Tabs
from utils import *

tabs = Tabs()
tabs['yours'] = '/search/saved'
tabs['others'] = '/search/saved/others'

@get('search/saved')
def searchSaved(handler):
	handler.title('Saved Searches')
	requirePriv(handler, 'User')
	print tabs.where('yours')
	undelay(handler)

	searches = SavedSearch.loadAll(userid = handler.session['user'].id)
	if searches != []:
		print "<table border=0 cellspacing=4>"
		print "<tr><th>Name</th><th>Query</th><th>Shared</th><th>&nbsp;</th></tr>"
		for search in searches:
			print "<form method=\"post\" action=\"/search/saved/%d/update\">" % search.id
			print "<tr>"
			print "<td><input type=\"text\" name=\"name\" value=\"%s\"></td>" % search.name.replace('"', '&quot;')
			print "<td style=\"width: 100%%\"><input type=\"text\" name=\"query\" value=\"%s\" style=\"width: 100%%\"></td>" % search.query.replace('"', '&quot;')
			print "<td style=\"text-align: center\"><input type=\"checkbox\" name=\"share\"%s></td>" % (' checked' if search.public else '')
			print "<td nowrap>"
			print "<button onClick=\"document.location = '/search/saved/%d/run'; return false;\" class=\"fancy\">run</button>" % search.id
			print "<button type=\"submit\" class=\"fancy\" name=\"action\" value=\"update\">update</button>"
			print "<button type=\"submit\" class=\"fancy danger\" name=\"action\" value=\"delete\">delete</button>"
			print "</td>"
			print "</tr>"
			print "</form>"
		print "</table>"

	print "<h3>New Search</h3>"
	newSearchForm()

@get('search/saved/others')
def searchSavedOthers(handler):
	handler.title('Saved Searches')
	requirePriv(handler, 'User')
	print tabs.where('others')
	undelay(handler)

	print "<style type=\"text/css\">"
	print ".other-search {padding-bottom: 4px; border-bottom: 1px dashed #000;}"
	print ".other-search h2 {margin-bottom: 4px;}"
	print ".other-search small {float: right; font-weight: normal; font-size: 12pt;}"
	print ".other-search code {font-size: 14pt;}"
	print "</style>"

	searches = filter(lambda search: search.user != handler.session['user'] and search.public, SavedSearch.loadAll(orderby = 'name'))
	if searches == []:
		print "No shared searches available"
	else:
		for search in searches:
			print "<div class=\"other-search\">"
			print "<h2>%s<small><img class=\"bumpdown\" src=\"%s\">&nbsp;%s</small></h2>" % (search.safe.name, search.user.getAvatar(16), search.user.username)
			print "<code>%s</code><br><br>" % search.safe.query

			following = handler.session['user'] in search.followers
			print "<form method=\"post\" action=\"/search/saved/%d/%s\">" % (search.id, 'unfollow' if following else 'follow')
			print Button('Run', url = "/search/saved/%d/run" % search.id)
			btn = Button('Unfollow' if following else 'Follow', type = 'submit')
			if following:
				btn.negative()
			else:
				btn.positive()
			print btn
			print "</form>"
			print "</div>"

@get('search/saved/new')
def newSavedSearch(handler, sprintid = None, name = '', query = ''):
	handler.title('New Search')
	requirePriv(handler, 'User')
	newSearchForm(sprintid, name, query)

def newSearchForm(sprintid = None, name = '', query = ''):
	print """
<style type="text/css">
table.list td.right input[type=text] {width: 400px;}
table.list td.right button {width: 200px;}
</style>

<script type="text/javascript">
$(document).ready(function() {
    $('#save-button').savebutton($('#post-status'), '');
    $('#cancel-button').cancelbutton('%s');
});
</script>
""" % ("/sprints/%d" % int(sprintid) if sprintid else "/search/saved")

	print InfoBox('', id = 'post-status')

	print "<form method=\"post\" action=\"/search/saved/new\">"
	if sprintid:
		print "<input type=\"hidden\" name=\"sprintid\" value=\"%d\">" % int(sprintid)
	print "<table class=\"list\">"
	print "<tr><td class=\"left\">Name:</td><td class=\"right\"><input type=\"text\" name=\"name\" class=\"defaultfocus\" value=\"%s\"></td></tr>" % stripTags(name.replace('"', '&quot;'))
	print "<tr><td class=\"left\">Query:</td><td class=\"right\"><input type=\"text\" name=\"query\" value=\"%s\"></td></tr>" % query
	print "<tr><td class=\"left\">Share:</td><td class=\"right\"><input type=\"checkbox\" name=\"public\" id=\"public_chk\" checked><label for=\"public_chk\">&nbsp;Share this search with other users</label></td></tr>"
	print "<tr><td class=\"left\">&nbsp;</td><td class=\"right\">"
	print Button('Save', id = 'save-button', type = 'button').positive()
	print Button('Cancel', id = 'cancel-button', type = 'button').negative()
	print "</td></tr>"
	print "</table>"
	print "</form>"

@post('search/saved/new')
def newSavedSearchPost(handler, p_name, p_query, p_public = False, p_sprintid = None):
	# def die(msg):
		# print msg
		# done()

	handler.title('New Search')
	requirePriv(handler, 'User')
	handler.wrappers = False

	search = SavedSearch(handler.session['user'].id, p_name, p_query, bool(p_public))
	search.save()

	handler.responseCode = 299
	delay(handler, SuccessBox("Saved search <b>%s</b>" % search.safe.name, close = 3, fixed = True))
	if p_sprintid:
		print "/search/saved/%d/run/%s" % (search.id, p_sprintid)
	else:
		print "/search/saved"

@post('search/saved/(?P<id>[0-9]+)/update')
def updateSavedSearch(handler, id, p_action, p_name, p_query, p_share = False):
	handler.title('Update Search')
	requirePriv(handler, 'User')

	search = SavedSearch.load(int(id))
	if not search:
		ErrorBox.die('Invalid Search', "No search with ID <b>%d</b>" % int(id))
	elif search.user != handler.session['user']:
		ErrorBox.die('Permission Denied', "You cannot modify another user's search")

	if p_action == 'update':
		search.name = p_name
		search.query = p_query
		search.public = p_share
		search.save()
		if not search.public:
			search.unfollow()
		delay(handler, SuccessBox("Updated search <b>%s</b>" % search.safe.name))
	elif p_action == 'delete':
		search.delete()
		delay(handler, SuccessBox("Deleted search <b>%s</b>" % search.safe.name))
	else:
		ErrorBox.die('Invalid Action', "Unknown action %s" % stripTags(p_action))

	redirect('/search/saved')

@post('search/saved/(?P<id>[0-9]+)/(?P<action>(?:un)?follow)')
def updateSavedSearch(handler, id, action):
	handler.title('Update Search')
	requirePriv(handler, 'User')

	search = SavedSearch.load(int(id))
	if not search:
		ErrorBox.die('Invalid Search', "No search with ID <b>%d</b>" % int(id))
	elif search.user == handler.session['user']:
		ErrorBox.die('Permission Denied', "You cannot follow your own search")
	elif action == 'follow' and search.following(handler.session['user']):
		ErrorBox.die('Invalid State', "Already following this search")
	elif action == 'unfollow' and not search.following(handler.session['user']):
		ErrorBox.die('Invalid State', "Not following this search")

	if action == 'follow':
		search.follow(handler.session['user'])
		delay(handler, SuccessBox("Search followed"))
	elif action == 'unfollow':
		search.unfollow(handler.session['user'])
		delay(handler, SuccessBox("Search unfollowed"))
	else:
		ErrorBox.die('Invalid Action', "Unknown action %s" % stripTags(action))

	redirect('/search/saved/others')

@get('search/saved/(?P<id>[0-9]+)/run')
def searchRunActive(handler, id):
	searchRunSprint(handler, id, 'active')

@get('search/saved/(?P<id>[0-9]+)/run/(?P<sprintid>[0-9]+)')
def searchRunSprint(handler, id, sprintid):
	handler.title('Run Search')
	requirePriv(handler, 'User')
	id = int(id)

	search = SavedSearch.load(id)
	if not search:
		ErrorBox.die('Invalid Search', "Search <b>%d</b> does not exist" % int(id))
	elif search.user != handler.session['user'] and not search.public:
		ErrorBox.die('Invalid Search', "You cannot run search <b>%d</b>" % int(id))

	redirect("/sprints/%s?search=%s" % (sprintid, search.query))

@get('search/saved/menubox')
def searchSavedMenubox(handler):
	handler.wrappers = False
	handler.log = False
	if not handler.session['user']: return

	yours = [{'name': search.name, 'id': search.id, 'query': search.query} for search in SavedSearch.loadAll(userid = handler.session['user'].id)]
	others = [{'name': search.name, 'id': search.id, 'query': search.query, 'username': search.user.username, 'gravatar': search.user.getAvatar(16)} for search in SavedSearch.loadAll(public = True) if handler.session['user'] in search.followers]
	otherTotal = len(filter(lambda search: search.user != handler.session['user'], SavedSearch.loadAll(public = True)))

	print toJS({'yours': yours, 'others': others, 'otherTotal': otherTotal})
