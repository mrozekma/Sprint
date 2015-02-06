from Event import EventHandler
from Log import log
from utils import *

class DBLogger(EventHandler):
	def pageHandle(self, handler, fn):
		# Logged in HTTPHandler
		pass

	def error(self, handler, description):
		log(handler, 'error', description)

	def login(self, handler, user, success, text = None):
		log(handler, 'user.login', "Login %s for user %s%s" % ('succeeded' if success else 'failed', user.username if user else '(none)', (": %s" % text) if text else ''))

	def passwordReset(self, handler, user):
		log(handler, 'user.password.reset', "%s password reset" % user)

	def tfa(self, handler, user):
		if user.hotpKey == '':
			log(handler, 'user.tfa', "Two-factor authentication disabled")
		else:
			log(handler, 'user.tfa', "Two-factor authentication enabled: %s" % user.hotpKey)

	def prefs(self, handler):
		log(handler, 'user.prefs', handler.session['user'].getPrefs().getLogString())

	def newSprint(self, handler, sprint):
		lines = [
			sprint.link(None),
			"project: %s" % sprint.project,
			"name: %s" % sprint.safe.name,
			"owner: %s" % sprint.owner,
			"active: %s - %s" % (tsToDate(sprint.start), tsToDate(sprint.end)),
			"members: %s" % ', '.join(map(str, sprint.members))
		]

		log(handler, 'sprint.new', "\n".join(lines))

	def deleteSprint(self, handler, sprint):
		log(handler, 'sprint.delete', sprint.link(None))

	def undeleteSprint(self, handler, sprint):
		log(handler, 'sprint.undelete', sprint.link(None))

	def sprintInfoUpdate(self, handler, sprint, changes):
		lines = [sprint.link(None)]
		for k, v in changes.iteritems():
			if v:
				if isinstance(v, list):
					v = ', '.join(map(str, v))
				lines.append("%s: %s" % (k, stripTags(str(v))))

		log(handler, 'sprint.info.update', "\n".join(lines))

	def sprintAvailUpdate(self, handler, sprint):
		log(handler, 'sprint.availability.update', sprint.link(None))

	def newGroup(self, handler, group):
		lines = [
			group.safe.name,
			"sprint: %s" % group.sprint.link(None),
			"seq: %d" % group.seq,
			"deletable: %s" % group.deletable
		]

		log(handler, 'group.new', "\n".join(lines))

	def renameGroup(self, handler, group, oldName):
		log(handler, 'group.rename', "%s\nold name: %s\nsprint: %s" % (group.safe.name, stripTags(oldName), group.sprint.link(None)))

	def deleteGroup(self, handler, group):
		log(handler, 'group.delete', "%s\nsprint: %s" % (group.safe.name, group.sprint.link(None)))

	def newTask(self, handler, task):
		lines = [
			task.name,
			"sprint: %s" % task.sprint.link(None),
			"group: %s" % task.group.safe.name,
			"creator: %s" % task.creator,
			"assigned: %s" % ' '.join(map(str, task.assigned)),
			"status: %s" % task.getStatus().text,
			"hours: %d" % task.hours,
			"seq: %d" % task.seq
		]

		log(handler, 'task.new', "\n".join(lines))

	def taskUpdate(self, handler, task, field, value):
		if field == 'name':
			value = stripTags(str(value))
		elif field == 'assigned':
			value = ', '.join(map(str, value))
		log(handler, 'task.update', "Task %d\n%s: %s" % (task.id, field, value))

	def newNote(self, handler, note):
		lines = [
			"task: %s" % note.task.link(),
			"user: %s" % note.user,
			"body: %s" % note.safe.body
		]

		log(handler, 'note.new', "\n".join(lines))

	def deleteNote(self, handler, note):
		log(handler, 'note.delete', "%d\ntask: %s" % (note.id, note.task.link()))

	def adminSettings(self, handler, settings):
		log(handler, 'admin.settings', str(settings))

	def genResetKey(self, handler, user):
		log(handler, 'admin.user.resetkey.generate', "Generated reset key for %s" % user)

	def impersonate(self, handler, user):
		if user:
			log(handler, 'admin.user.impersonate', "Impersonating %s" % user)
		else:
			log(handler, 'admin.user.impersonate', "Stopped impersonating")

	def newUser(self, handler, user):
		log(handler, 'admin.user.new', str(user))

	def newProject(self, handler, project):
		log(handler, 'admin.project.new', project.name)

	def grantPrivilege(self, handler, user, priv, isNewUser):
		log(handler, 'admin.user.privilege.grant', "Granted %s to %s" % (priv, user))

	def revokePrivilege(self, handler, user, priv):
		log(handler, 'admin.user.privilege.revoke', "Revoked %s from %s" % (priv, user))

	def repl(self, handler, code):
		log(handler, 'admin.repl', code)

	def mockTime(self, handler, effectiveTime, delta):
		log(handler, 'admin.mocktime', "%s (%s)" % (effectiveTime, delta))

	def cron(self, handler, name):
		log(handler, 'admin.cron.run', "Ran cron job: %s" % name)

	def restart(self, handler):
		log(handler, 'admin.restart')
