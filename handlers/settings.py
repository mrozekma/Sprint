from json import dumps as toJS

from Settings import settings
from utils import *

@get('settings/sprints.js')
def sprintsJS(handler, request):
	request['wrappers'] = False
	request['log'] = False
	request['contentType'] = 'text/javascript'

	print "bugzilla_url = %s;" % toJS(settings.bugzillaURL or '')
