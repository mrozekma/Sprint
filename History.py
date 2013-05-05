from contextlib import contextmanager
from datetime import date

from rorn.ResponseWriter import ResponseWriter

from Task import Task
from LoadValues import isDevMode
from utils import *

colorMap = { # Maps status names to border colors
	'blocked': '#00008b',
	'canceled': '#000',
	'complete': '#008b00',
	'deferred': '#8b008b',
	'in progress': '#8b8b00',
	'not started': '#8b0000',
	'split': '#d7630b'
}

@contextmanager
def entry(rev, oldRev, describeTask, icon, color, text):
	useRev = oldRev or rev
	print "<div class=\"revision-entry\" style=\"border-color: %s\" assigned=\"%s\">" % (color, ' '.join(user.username for user in rev.assigned))
	print "<div class=\"type\"><img class=\"bullet\" src=\"/static/images/%s\">&nbsp;%s</div>" % (icon, text)
	print "<div class=\"timestamp\">%s by %s</div>" % (tsToDate(rev.timestamp).strftime('%H:%M:%S'), userStr(rev))
	print "<div class=\"body\">"
	if describeTask:
		print "<a href=\"/tasks/%d\">%s</a>, assigned to %s<br>" % (rev.id, useRev.safe.name, ', '.join(userStr(useRev, user) for user in sorted(useRev.assigned)))

	w = ResponseWriter()
	yield
	text = w.done().strip()

	# Show hours change
	if oldRev:
		hoursDiff = rev.hours - oldRev.hours
		if hoursDiff != 0:
			# Skip it if we moved to an end state and zeroed the hours
			if oldRev.status == rev.status or rev.status not in ('canceled', 'complete', 'deferred', 'split') or rev.hours != 0:
				if text != '':
					text += '. '
				text += "Hours %s by <span class=\"hours-%s\">%d</span> to %d" % ('increased' if hoursDiff > 0 else 'decreased', 'up' if hoursDiff > 0 else 'down', abs(hoursDiff), rev.hours)

	print text
	print "</div>"
	print "</div>"

def userStr(rev, arg = None):
	user = arg or rev.creator
	return user.str('scrummaster' if user == rev.sprint.owner else 'member')

def hoursChanged(rev, oldRev, describeTask):
	hoursDiff = rev.hours - oldRev.hours
	verb = 'increased' if hoursDiff > 0 else 'decreased'
	with entry(rev, oldRev, describeTask, "revision-hours-%s.svg" % verb, '#8b8b00', "Hours %s" % verb.capitalize()):
		pass # The entry() exit handler will output the text

def created(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-create.svg', '#008b00', 'Created'):
		print "%s. %s" % (rev.getStatus().text.capitalize(), pluralize(rev.hours, 'hour remains', 'hours remain'))

def deleted(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-deleted.svg', '#8b0000', 'Deleted'):
		pass

def undeleted(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-undeleted.svg', '#8b0000', 'Undeleted'):
		pass

def statusChanged(rev, oldRev, describeTask):
	status = rev.getStatus()
	verb = status.getRevisionVerb(oldRev.stillOpen())
	with entry(rev, oldRev, describeTask, "revision-%s.svg" % verb.lower().replace(' ', '-'), colorMap[status.name], verb):
		pass

def renamed(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-renamed.svg', '#0b88d7', 'Renamed'):
		print "Renamed to &quot;%s&quot;" % rev.safe.name

def reassigned(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-assigned.svg', '#8a2800', 'Reassigned'):
		print "Reassigned to %s" % ', '.join(userStr(rev, user) for user in sorted(rev.assigned))

def goalChanged(rev, oldRev, describeTask):
	with entry(rev, oldRev, describeTask, 'tag-blue.png', '#0bc6d7', 'Goal Changed'):
		if rev.goal is None:
			print "Cleared sprint goal"
		else:
			print "Set sprint goal to <img class=\"bumpdown\" src=\"/static/images/tag-%s.png\">&nbsp;<a href=\"/sprints/%d?search=goal:%s\">%s</a>" % (rev.goal.color, rev.sprint.id, rev.goal.color, rev.goal.safe.name)

def unrecognizedChange(rev, oldRev, field, describeTask):
	with entry(rev, oldRev, describeTask, 'revision-unknown.svg', '#000', "Field Changed"):
		print "Field '%s' changed: %s &#rarr; %s" % (field, stripTags(str(oldRev.__getattribute__(field))), stripTags(str(rev.__getattribute__(field))))

def showHistory(tasks, describeTask):
	if isinstance(tasks, Task):
		tasks = [tasks]

	revs = [task.getRevisions() for task in tasks]
	revs = [rev for l in revs for rev in l] # Flatten
	revs.sort(key = lambda rev: rev.timestamp) # Sort ascending by timestamp
	revMap = dict([((rev.id, rev.revision), rev) for rev in revs]) # Map (id, revision #) to the revision

	print "<div class=\"revision-history\">"
	fields = (set(Task.fields()) | set(['assigned'])) - set(['creatorid', 'timestamp', 'revision'])

	prevDay = None
	for rev in revs:
		day = date.fromtimestamp(rev.timestamp)
		if not prevDay or prevDay != day:
			print "<h2 class=\"daymarker\">%s</h2>" % day.strftime("%d %b %Y").lstrip('0')
		prevDay = day

		if rev.revision == 1:
			created(rev, None, describeTask)
			if rev.deleted:
				deleted(rev, None, describeTask)
			continue

		oldRev = revMap[(rev.id, rev.revision - 1)]
		changedFields = filter(lambda f: oldRev.__getattribute__(f) != rev.__getattribute__(f), fields)

		# If hours is the only changed field, output it. Otherwise it will be attached to the first change
		if 'hours' in changedFields:
			if changedFields == ['hours']:
				hoursChanged(rev, oldRev, describeTask)
			changedFields.remove('hours')

		for field in changedFields:
			if field == 'status':
				statusChanged(rev, oldRev, describeTask)
			elif field == 'name':
				renamed(rev, oldRev, describeTask)
			elif field == 'deleted':
				if rev.deleted:
					deleted(rev, oldRev, describeTask)
				else:
					undeleted(rev, oldRev, describeTask)
			elif field == 'assigned':
				reassigned(rev, oldRev, describeTask)
			elif field == 'goalid':
				goalChanged(rev, oldRev, describeTask)
			elif field == 'groupid':
				pass # Switching groups doesn't really matter
			else:
				unrecognizedChange(rev, oldRev, field, describeTask)
