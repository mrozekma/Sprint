from rorn.ResponseWriter import ResponseWriter

from Task import Task
from utils import *

def start(rev, icon):
	print "<img class=\"bullet\" src=\"/static/images/%s.png\">&nbsp;<span class=\"timestamp\">[%s]</span>" % (icon, tsToDate(rev.timestamp).strftime('%Y-%m-%d %H:%M:%S')),

def userStr(rev, arg = None):
	user = arg or rev.creator
	return user.str('scrummaster' if user == rev.sprint.project.owner else 'member')

def showHistory(tasks):
	if isinstance(tasks, Task):
		tasks = [tasks]

	print "<div class=\"revision-history\">"
	fields = set(Task.fields()) - set(['creatorid', 'timestamp', 'revision'])
	for task in tasks:
		revs = task.getRevisions()
		for rev in revs:
			w = ResponseWriter()
			if rev.revision == 1:
				start(rev, 'revision-create')
				print "Task created by %s." % userStr(rev),
				print "Assigned to %s," % userStr(rev, rev.assigned),
				print "%s," % rev.getStatus().text.lower(),
				print "%d %s remain" % (rev.hours, 'hour' if rev.hours == 1 else 'hours'),
			else:
				changedFields = filter(lambda f: oldRev.__getattribute__(f) != rev.__getattribute__(f), fields)
				for field in changedFields:
					old, new = oldRev.__getattribute__(field), rev.__getattribute__(field)
					for case in switch(field):
						if case('status'):
							start(rev, "revision-%s" % rev.getStatus().name.replace(' ', '-'))
							print "%s by %s" % (rev.getStatus().revisionVerb, userStr(rev))
							if 'hours' in changedFields:
								print "(<span class=\"hours-%s\">%+d</span> to %d)" % ('up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
							break
						if case('hours'):
							if 'status' in changedFields:
								continue # Already showed the hours change in the status line
							start(rev, 'revision-in-progress')
							print "%s changed hours <span class=\"hours-%s\">%+d</span> to %d" % (userStr(rev), 'up' if rev.hours > oldRev.hours else 'down', rev.hours - oldRev.hours, rev.hours)
							break
						if case('name'):
							start(rev, 'revision-renamed')
							print "Renamed <b>%s</b> by %s" % (rev.safe.name, userStr(rev))
							break
						if case('deleted'):
							start(rev, 'revision-deleted' if rev.deleted else 'revision-undeleted')
							print "%s by %s" % ('Deleted' if rev.deleted else 'Undeleted', userStr(rev))
							break
						if case('assignedid'):
							start(rev, 'revision-assigned')
							print "Assigned to %s by %s" % (userStr(rev, rev.assigned), userStr(rev))
							break
						if case('goalid'):
							start(rev, 'tag-blue')
							print "Set sprint goal <b>%s</b> by %s" % (rev.goal.safe.name, userStr(rev))
							break
						if case('groupid'):
							# Nobody cares
							break
						if case():
							start(rev, 'revision-unknown')
							print "Field '%s' changed: %s -> %s" % (field, stripTags(str(old)), stripTags(str(new)))
							break
			if w.data != '':
				print "<br>"
			print w.done()
			oldRev = rev
	print "</div>"
