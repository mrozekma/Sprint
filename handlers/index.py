from __future__ import with_statement

from rorn.Session import Session, undelay

from Privilege import requirePriv
from Project import Project
from handlers.projects import showProjects
from wrappers import *
from utils import *

@get('')
def index(handler, request):
	undelay(handler)

	requirePriv(handler, 'User')
	showProjects(handler)
