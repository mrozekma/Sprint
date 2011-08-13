from rorn.Session import Session

from Table import LRTable
from Project import Project

@get('dbg')
def index(handler, request):
	handler.title('Debugging Info')
	tbl = LRTable()
	tbl['Session'] = str(handler.session)
	tbl['Key'] = handler.session.key
	tbl['Cookie'] = handler.headers.getheader('Cookie') or 'None'
	tbl['User'] = handler.session['user']
	tbl['foo'] = Project.load(1).owner
	print tbl
