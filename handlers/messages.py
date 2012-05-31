from rorn.Box import InfoBox, SuccessBox, ErrorBox
from rorn.Session import delay, undelay

from Privilege import requirePriv
from Message import Message
from User import User
from Tabs import Tabs
from Markdown import Markdown
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

	print "<div class=\"%s\">" % ' '.join(cls)
	print "<div class=\"avatar\"><img src=\"%s\"></div>" % (user.getAvatar() if user else '/static/images/user-system.png')
	print "<div class=\"title\">"
	print "%s %s %s" % (message.title, 'by' if inbox else 'to', user or 'system')
	print "<div class=\"timestamp\">%s</div>" % tsToDate(message.timestamp).replace(microsecond = 0)
	print "</div>"
	print "<div class=\"body markdown\">%s</div>" % message.render()
	print "</div>"


@post('messages/send')
def send(handler, request, p_userid, p_body):
	handler.title('Send message')
	requirePriv(handler, 'User')

	targetID = int(p_userid)
	target = User.load(targetID)
	if not target:
		ErrorBox.die("No user with ID %d" % targetID)

	Message(target.id, handler.session['user'].id, "Direct message", p_body, 'markdown').save()
	delay(handler, SuccessBox("Message dispatched to %s" % target, close = 3))
	redirect('/messages/sent')
