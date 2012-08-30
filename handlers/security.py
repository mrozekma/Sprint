from base64 import b32encode
from random import randrange

from rorn.Box import ErrorBox, SuccessBox
from rorn.Session import delay

from Event import Event
from Privilege import requirePriv

from utils import *

@post('security/two-factor')
def twoFactorAuthentication(handler, request, p_action):
	handler.title('Two-Factor Authentication')
	requirePriv(handler, 'User')

	if p_action == 'enable':
		handler.session['user'].hotpKey = b32encode(''.join(chr(randrange(256)) for _ in range(10)))
		handler.session['user'].save()
		Event.tfa(handler, handler.session['user'])

		print SuccessBox("Two-factor authentication is <b>enabled</b>")
		print "Your HOTP key is <b>%s</b>:<br><br>" % handler.session['user'].hotpKey
		print "<div style=\"text-align: center\"><img src=\"https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=otpauth://totp/Sprint%%3Fsecret%%3D%s\"></div><br>" % handler.session['user'].hotpKey

		print "This key will not be displayed again &mdash; be sure to write it down, or add it to your Google Authenticator list now"
	elif p_action == 'disable':
		handler.session['user'].hotpKey = ''
		handler.session['user'].save()
		Event.tfa(handler, handler.session['user'])

		delay(handler, SuccessBox("Two-factor authentication is <b>disabled</b>"))
		redirect("/users/%s" % handler.session['user'].username)
	else:
		ErrorBox.die("Unexpected action: <b>%s</b>" % stripTags(p_action))
