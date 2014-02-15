from os import rename
from os.path import isfile
import pickle
import sqlite3
from stasis.DiskMap import DiskMap
from utils import tsToDate, dateToTs
from datetime import timedelta

source = sqlite3.connect('db')
source.row_factory = sqlite3.Row
dest = DiskMap('db-new', create = True, cache = False)

# Some cleanup, because sqlite apparently doesn't cascade deletes
# This probably isn't comprehensive, but most databases shouldn't really need it anyway
queries = [
	"DELETE FROM availability WHERE NOT EXISTS (SELECT * FROM users WHERE availability.userid = users.id)",
	"DELETE FROM availability WHERE NOT EXISTS (SELECT * FROM sprints WHERE availability.sprintid = sprints.id)",
	"DELETE FROM grants WHERE NOT EXISTS (SELECT * FROM users WHERE grants.userid = users.id)",
	"DELETE FROM members WHERE NOT EXISTS (SELECT * FROM sprints WHERE members.sprintid = sprints.id)",
	"DELETE FROM tasks WHERE NOT EXISTS (SELECT * FROM sprints WHERE tasks.sprintid = sprints.id)",
	"DELETE FROM assigned WHERE NOT EXISTS (SELECT * FROM tasks WHERE assigned.taskid = tasks.id AND assigned.revision = tasks.revision)",
]
for query in queries:
	cur = source.cursor()
	cur.execute(query)
	cur.close()

# Some tables get converted directly:
for table in ['users', 'sprints', 'groups', 'goals', 'log', 'projects', 'notes', 'messages', 'searches', 'retrospective_categories', 'retrospective_entries', 'changelog_views']:
	cur = source.cursor()
	cur.execute("SELECT * FROM %s" % table)
	for row in cur:
		data = {k: row[k] for k in row.keys()}
		print "%-20s %d" % (table, data['id'])
		dest[table][data['id']] = data
	cur.close()

# Settings are converted to a straight key/value store; no IDs
cur = source.cursor()
cur.execute("SELECT * FROM settings WHERE name != 'gitURL'")
for row in cur:
	data = {k: row[k] for k in row.keys()}
	print "%-20s %d" % ('settings', row['id'])
	dest['settings'][row['name']] = row['value']
cur.close()

# Tasks have multiple revisions; they're stored as a list
cur = source.cursor()
cur.execute("SELECT * FROM tasks ORDER BY id, revision")
for row in cur:
	rev = {k: row[k] for k in row.keys()}
	print "%-20s %d (revision %d)" % ('tasks', row['id'], row['revision'])
	if int(rev['revision']) == 1:
		dest['tasks'][rev['id']] = [rev]
	else:
		with dest['tasks'].change(rev['id']) as data:
			assert len(data) + 1 == rev['revision']
			data.append(rev)
cur.close()

# Linking tables no longer exist
# Instead, add the lists directly to the appropriate parent class

# grants -> users.privileges
# (the privileges table is gone entirely)
for userid in dest['users']:
	with dest['users'].change(userid) as data:
		data['privileges'] = set()
cur = source.cursor()
cur.execute("SELECT g.userid, p.name FROM grants AS g, privileges AS p WHERE g.privid = p.id")
for row in cur:
	print "%-20s %d (%s)" % ('grants', row['userid'], row['name'])
	with dest['users'].change(int(row['userid'])) as data:
		data['privileges'].add(row['name'])
cur.close()

# members -> sprints.members
if 'sprints' in dest:
	for sprintid in dest['sprints']:
		with dest['sprints'].change(sprintid) as data:
			data['memberids'] = set()
	cur = source.cursor()
	cur.execute("SELECT * FROM members")
	for row in cur:
		print "%-20s %d (%d)" % ('members', row['sprintid'], row['userid'])
		with dest['sprints'].change(int(row['sprintid'])) as data:
			data['memberids'].add(row['userid'])
	cur.close()

# assigned -> tasks.assigned
if 'tasks' in dest:
	for taskid in dest['tasks']:
		with dest['tasks'].change(taskid) as data:
			for rev in data:
				rev['assignedids'] = set()
	cur = source.cursor()
	cur.execute("SELECT * FROM assigned")
	for row in cur:
		print "%-20s %d (revision %d) %s" % ('assigned', row['taskid'], row['revision'], row['userid'])
		with dest['tasks'].change(int(row['taskid'])) as data:
			data[int(row['revision']) - 1]['assignedids'].add(row['userid'])
	cur.close()

# search_uses -> searches.followers
if 'searches' in dest:
	for searchid in dest['searches']:
		with dest['searches'].change(searchid) as data:
			data['followerids'] = set()
	cur = source.cursor()
	cur.execute("SELECT * FROM search_uses")
	for row in cur:
		print "%-20s %d (%d)" % ('search_uses', row['searchid'], row['userid'])
		with dest['searches'].change(int(row['searchid'])) as data:
			data['followerids'].add(row['userid'])
	cur.close()

# prefs is converted normally, except the id is now set to the userid
# prefs_backlog_styles -> prefs.backlogStyles
# prefs_messages -> prefs.messages
cur = source.cursor()
cur.execute("SELECT * FROM prefs")
for row in cur:
	print "%-20s %d" % ('prefs', row['userid'])
	dest['prefs'][int(row['userid'])] = {}
	with dest['prefs'].change(int(row['userid'])) as data:
		data['id'] = int(row['userid'])
		data['defaultSprintTab'] = row['defaultSprintTab']
		data['backlogStyles'] = {}
		cur2 = source.cursor()
		cur2.execute("SELECT * FROM prefs_backlog_styles WHERE userid = %d" % int(row['userid']))
		for row2 in cur2:
			data['backlogStyles'][row2['status']] = row2['style']
		cur2.close()
		data['messages'] = {}
		cur2 = source.cursor()
		cur2.execute("SELECT * FROM prefs_messages WHERE userid = %d" % int(row['userid']))
		for row2 in cur2:
			data['messages'][row2['type']] = not not row2['enabled']
		cur2.close()
cur.close()

# Anyone who doesn't have prefs gets a default record
for userid in dest['users']:
	if userid not in dest['prefs']:
		dest['prefs'][userid] = {'id': userid, 'defaultSprintTab': 'backlog', 'backlogStyles': {status: 'show' for status in ['not started', 'in progress', 'complete', 'blocked', 'deferred', 'canceled', 'split']}, 'messages': {'sprintMembership': False, 'taskAssigned': False, 'noteRelated': True, 'noteMention': True, 'priv': True}}

# Availability is now stored by sprint id
# The contents are {user_id: {timestamp: hours}}
if 'sprints' in dest:
	oneday = timedelta(1)
	for sprintid, data in dest['sprints'].iteritems():
		m = {}
		for userid in data['memberids']:
			m[userid] = {}
			print "%-20s %d %d" % ('availability', sprintid, userid)
			cur = source.cursor()
			cur.execute("SELECT hours, timestamp FROM availability WHERE sprintid = %d AND userid = %d AND timestamp != 0" % (sprintid, userid))
			for row in cur:
				m[userid][int(row['timestamp'])] = int(row['hours'])
			cur.close()
		dest['availability'][sprintid] = m

# Make search.public a bool instead of an int
if 'searches' in dest:
	for searchid, data in dest['searches'].iteritems():
		with dest['searches'].change(searchid) as data:
			data['public'] = bool(data['public'])

# Bump the DB version
dest['settings']['dbVersion'] = 20

source.close()

# Rename
rename('db', 'db-old.sqlite')
rename('db-new', 'db')
