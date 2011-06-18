from __future__ import with_statement
from utils import *
from Privilege import requirePriv
from Task import Task
from Box import TintedBox

@get('tasks')
def task(handler, request):
	for case in switch(len(request['path'])):
		if case(0):
			print ErrorBox("Tasks", "No task specified")
			done()
			break
		if case(1):
			showTask(handler, request, int(request['path'][0]))
			break


def showTask(handler, request, id):
	requirePriv(handler, 'User')
	task = Task.load(id)
	if not task:
		print ErrorBox('Tasks', "No task with ID <b>%d</b>" % id)

	handler.title(task.safe.name)

	# print "<script src=\"/static/tasks.js\" type=\"text/javascript\"></script>"
	print TintedBox('Unimplemented', scheme = 'blood')
	print "<br>"

	m = ['id', 'revision', 'sprintid', 'sprint', 'creatorid', 'creator', 'assignedid', 'assigned', 'name', 'status', 'hours', 'timestamp']
	revs = task.getRevisions()

	from Table import Table
	tbl = Table()
	tbl *= ['Field'] + [x for x in range(1, len(revs)+1)]
	for k in m:
		tbl += [k] + [str(x.__getattribute__(k)) for x in revs]
	print tbl

	# for rev in task.getRevisions():
		# print "<hr>"
		# print "<h2>%s</h2>" % rev.revision
		# tbl = LRTable()
		# for k in m:
			# tbl[k] = str(rev.__getattribute__(k))
		# print tbl
