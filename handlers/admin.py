from os.path import isfile
from shutil import move

from DB import db, dbReconnect
from Privilege import admin
from utils import *

@get('admin')
def adminIndex(handler, request):
	handler.title('Admin')
	admin(handler)

	# print "<a href=\"/admin/db/reset\">Reset database</a>"

# @get('admin/db/reset')
# def resetDB(handler, request):
	# handler.title('Reset database')
