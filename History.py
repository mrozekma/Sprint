from datetime import date

from rorn.ResponseWriter import ResponseWriter

from Task import Task
from LoadValues import isDevMode
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
	fields = set(Task.fields()) - set(['creatorid', 'timestamp', 'revision', 'hours'])
	prevDay = None
	strings = {
		'status': ("revision-%(status)s", "%(statusRevVerb)s by %(editor)s"),
		'name': ("revision-renamed", "Renamed <b>%(name)s</b> by %(editor)s"),
		'deleted': ("revision-%(deleted)s", "%(deleted)s by %(editor)s"),
		'assignedid': ("revision-assigned", "Assigned to %(assignee)s by %(editor)s"),
		'goalid': ("tag-blue", "Set sprint goal <b>%(goal)s</b> by %(editor)s"),
		'groupid': None
	}

	for rev in revs:
		entries = []
		if rev.revision == 1:
			entries.append(('revision-create', "<b>%s</b> created by %s. Assigned to %s, %s, %d %s remain" % (rev.safe.name, userStr(rev), userStr(rev, rev.assigned), rev.getStatus().text.lower(), rev.hours, 'hour' if rev.hours == 1 else 'hours')))
			if rev.deleted:
				entries.append(('revision-deleted', strings['deleted'][1] % {'deleted': 'Deleted', 'editor': userStr(rev)}))
		else:
			oldRev = revMap[(rev.id, rev.revision-1)]
			changedFields = filter(lambda f: oldRev.__getattribute__(f) != rev.__getattribute__(f), fields)
			stringData = {
				'status': rev.getStatus().name,
				'statusRevVerb': rev.getStatus().revisionVerb,
				'editor': userStr(rev),
				'assignee': userStr(rev, rev.assigned),
				'name': rev.safe.name,
				'deleted': 'Deleted' if rev.deleted else 'Undeleted',
				'goal': rev.goal.safe.name if rev.goal else None
			}

			# The hours change is attached to another field if possible
			hoursDiff = rev.hours - oldRev.hours

			for field in changedFields:
				if field in strings:
					if strings[field]:
						icon, text = strings[field]
						if hoursDiff:
							text += "&nbsp;(hours %s by <span class=\"hours-%s\">%d</span> to %d)" % ('increased' if hoursDiff > 0 else 'decreased', 'up' if hoursDiff > 0 else 'down', abs(hoursDiff), rev.hours)
							hoursDiff = 0
						entries.append(((icon % stringData).lower().replace(' ', '-'), text % stringData))
				else:
					entries.append(('revision-unknown', "Field '%s' changed: %s &#rarr; %s" % (field, stripTags(str(oldRev.__getattribute__(field))), stripTags(str(rev.__getattribute__(field))))))

			# If the hours change wasn't attached to another field, make a dedicated entry now
			if hoursDiff:
				entries.append(('revision-in-progress', "%s %s hours by <span class=\"hours-%s\">%d</span> to %d" % (userStr(rev), 'increased' if hoursDiff > 0 else 'decreased', 'up' if hoursDiff > 0 else 'down', abs(hoursDiff), rev.hours)))

		for icon, text in entries:
			if describeTask:
				day = date.fromtimestamp(rev.timestamp)
				if day != prevDay:
					print "<h2>%s</h2>" % day.strftime("%d %b %Y").lstrip('0')
				prevDay = day
			print "<img class=\"bullet\" src=\"/static/images/%s.png\">&nbsp;%s<span class=\"timestamp\">[%s]</span>%s%s<br>" % (icon, "<span class=\"debugtext\">[%d]</span>&nbsp;" % rev.revision if isDevMode() else '', tsToDate(rev.timestamp).strftime('%H:%M:%S' if describeTask else '%Y-%m-%d %H:%M:%S'), "<a href=\"/tasks/%d\">%s</a>:&nbsp;" % (rev.id, rev.safe.name) if describeTask else '', text)
	print "</div>"
