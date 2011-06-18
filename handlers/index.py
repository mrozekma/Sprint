from __future__ import with_statement
from wrappers import *
from Box import *
from Session import Session, undelay
from utils import *
from Privilege import requirePriv
from Project import Project
from handlers.projects import showProjects

@get('')
def index(handler, request):
	undelay(handler)

	requirePriv(handler, 'User')
	showProjects()

	# for t in [ErrorBox, WarningBox, SuccessBox]:
		# print t('Title', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer elementum placerat arcu, eu viverra velit auctor a. Morbi congue volutpat malesuada. Nullam elit velit, mollis ac pharetra ac, suscipit sed magna. Phasellus in leo a mi pretium tincidunt ac eget massa. Aenean posuere ipsum vel est lacinia nec blandit dui mattis. Vestibulum tortor mi, suscipit et varius in, sollicitudin sit amet neque. Praesent tempor dignissim molestie. Nam felis eros, posuere at tristique et, accumsan sed purus. Vestibulum porta aliquam tellus nec ultricies. Ut commodo, est sed fermentum adipiscing, ipsum dui ullamcorper ante, et gravida magna nulla quis massa. Aenean sagittis commodo tellus, ac malesuada massa posuere eget.')

	# for t in ['black', 'red', 'yellow', 'green', 'blue', 'blood']:
		# print TintedBox("This is a test tinted box", t)
