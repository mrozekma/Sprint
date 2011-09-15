from datetime import date

from rorn.ResponseWriter import ResponseWriter

from Task import Task
from utils import *

def userStr(rev, arg = None):
	user = arg or rev.creator
	return user.str('scrummaster' if user == rev.sprint.project.owner else 'member')

def showHistory(tasks, describeTask):
	if isinstance(tasks, Task):
		tasks = [tasks]

	revs = [task.getRevisions() for task in tasks]
	revs = [rev for l in revs for rev in l] # Flatten
	revs.sort(key = lambda rev: rev.timestamp, reverse = True) # Sort descending by timestamp
	revMap = dict([((rev.id, rev.revision), rev) for rev in revs]) # Map (id, revision #) to the revision

	print "<div class=\"revision-history\">"
	fields = set(Task.fields()) - set(['creatorid', 'timestamp', 'revision'])
	lastDay = None
	for rev in revs:
		dayStr = ''
		day = date.fromtimestamp(rev.timestamp)
		if describeTask and day != lastDay:
			lastDay = day
			dayStr = "<h2>%s</h2>" % day.strftime("%d %b %Y").lstrip('0')

		w = ResponseWriter()
		if rev.revision == 1:
			icon = 'revision-create'
			print "Task created by %s." % userStr(rev),
			print "Assigned to %s," % userStr(rev, rev.assigned),
			print "%s," % rev.getStatus().text.lower(),
			print "%d %s remain" % (rev.hours, 'hour' if rev.hours == 1 else 'hours'),
		else:
			oldRev = revMap[(rev.id, rev.revision-1)]
			changedFields = filter(lambda f: oldRev.__getattribute__(f) != rev.__getattribute__(f), fields)
			for field in changedFields:
				old, new = oldRev.__getattribute__(field), rev.__getattribute__(field)
				for case in switch(field):
					if case('status'):
						icon = "revision-%s" % rev.getStatus().name.replace(' ', '-')
						print "%s by %s" % (rev.getStatus().revisionVerb, userStr(rev))
						if 'hours' in changedFields:
							print "(<span class=\"hours-%s\">%+d</span> to %d)" % ('up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
						break
					if case('hours'):
						if 'status' in changedFields:
							continue # Already showed the hours change in the status line
						icon = 'revision-in-progress'
						print "%s changed hours <span class=\"hours-%s\">%+d</span> to %d" % (userStr(rev), 'up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
						break
					if case('name'):
						icon = 'revision-renamed'
						print "Renamed <b>%s</b> by %s" % (rev.safe.name, userStr(rev))
						break
					if case('deleted'):
						icon = 'revision-deleted' if rev.deleted else 'revision-undeleted'
						print "%s by %s" % ('Deleted' if rev.deleted else 'Undeleted', userStr(rev))
						break
					if case('assignedid'):
						icon = 'revision-assigned'
						print "Assigned to %s by %s" % (userStr(rev, rev.assigned), userStr(rev))
						break
					if case('goalid'):
						icon = 'tag-blue'
						print "Set sprint goal <b>%s</b> by %s" % (rev.goal.safe.name, userStr(rev))
						break
					if case('groupid'):
						# Nobody cares
						break
					if case():
						icon = 'revision-unknown'
						print "Field '%s' changed: %s -> %s" % (field, stripTags(str(old)), stripTags(str(new)))
						break
		out = w.done()
		if out != '':
			print dayStr
			print "<img class=\"bullet\" src=\"/static/images/%s.png\">&nbsp;<span class=\"timestamp\">[%s]</span>" % (icon, tsToDate(rev.timestamp).strftime('%H:%M:%S' if describeTask else '%Y-%m-%d %H:%M:%S')),
			if describeTask:
				print "<a href=\"/tasks/%d\">%s</a>:&nbsp;" % (rev.id, rev.safe.name),
			print out
			print "<br>"
	print "</div>"
