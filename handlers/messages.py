from rorn.Box import InfoBox, SuccessBox, ErrorBox
from rorn.Session import delay, undelay

from Privilege import requirePriv
from Message import Message
from User import User
from Tabs import Tabs
from Markdown import Markdown
from Button import Button
from utils import *

tabs = Tabs()
tabs['inbox'] = '/messages/inbox'
tabs['sent'] = '/messages/sent'

@get('messages/inbox')
def inbox(handler, request):
	handler.title('Messages')
	requirePriv(handler, 'User')

	print InfoBox("Note", "You can control your automated message subscriptions from the <a href=\"/prefs\">preferences</a> page")

	print tabs << 'inbox'
	undelay(handler)

	Markdown.head('div.message .body pre code')

	messages = Message.loadAll(userid = handler.session['user'].id, orderby = 'timestamp DESC')
	for message in messages:
		printMessage(message, True)
		if not message.read:
			message.read = True
			message.save()

@get('messages/sent')
def sent(handler, request):
	handler.title('Messages')
	requirePriv(handler, 'User')

	print tabs << 'sent'
	undelay(handler)

	Markdown.head('div.message .body pre code')

	messages = Message.loadAll(senderid = handler.session['user'].id, orderby = 'timestamp DESC')
	for message in messages:
		printMessage(message, False)

def printMessage(message, inbox):
	cls = ['message']
	if not message.read:
		cls.append('unread')
	if not message.sender:
		cls.append('system')

	user = (message.sender if inbox else message.user) or None

	print "<form method=\"post\" action=\"/messages/%d/delete\">" % message.id
	print "<div class=\"%s\">" % ' '.join(cls)
	print "<div class=\"avatar\"><img src=\"%s\"></div>" % (user.getAvatar() if user else '/static/images/user-system.png')
	print "<div class=\"title\">"
	if inbox:
		print "<input type=\"image\" src=\"/static/images/cross.png\" title=\"Delete message\">"
	elif not message.read:
		print "<input type=\"image\" src=\"/static/images/message-retract.png\" title=\"Retract message\">"
	print "%s %s %s" % (message.title, 'by' if inbox else 'to', user or 'system')
	print "<div class=\"timestamp\">%s</div>" % tsToDate(message.timestamp).replace(microsecond = 0)
	print "</div>"
	print "<div class=\"body markdown\">%s</div>" % message.render()
	print "</div>"
	print "</form>"


@post('messages/send')
def send(handler, request, p_userid, p_body, dryrun = False):
	handler.title('Send message')
	if dryrun:
		request['wrappers'] = False
	requirePriv(handler, 'User')

	targetID = int(p_userid)
	target = User.load(targetID)
	if not target:
		ErrorBox.die("No user with ID %d" % targetID)

	message = Message(target.id, handler.session['user'].id, "Direct message", p_body, 'markdown')
	if dryrun:
		print message.render()
	else:
		if p_body == '':
			ErrorBox.die('Empty Body', "No message provided")
		message.save()
		delay(handler, SuccessBox("Message dispatched to %s" % target, close = 3))
		redirect('/messages/sent')

@post('messages/(?P<id>[0-9]+)/delete')
def deleteMessage(handler, request, id, p_x = None, p_y = None):
	handler.title('Delete message')
	requirePriv(handler, 'User')

	id = int(id)
	message = Message.load(id)
	if not message:
		ErrorBox.die("Message %d does not exist" % id)
	if message.user == handler.session['user']:
		verb = 'deleted'
		redir = '/messages/inbox'
	elif message.sender == handler.session['user']:
		verb = 'retracted'
		redir = '/messages/sent'
		if message.read:
			ErrorBox.die("Unable to retract read messages")
	else:
		ErrorBox.die("You don't have permission to delete this message")

	message.delete()
	delay(handler, SuccessBox("Message %s" % verb, close = 3))
	redirect(redir)
