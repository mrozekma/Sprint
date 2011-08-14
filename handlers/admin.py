from __future__ import with_statement
import re
import tokenize
from token import *

from Privilege import admin
from utils import *

@get('admin')
def adminIndex(handler, request):
	handler.title('Admin')
	admin(handler)

	# print "<a href=\"/admin/db/reset\">Reset database</a>"
	print "<a href=\"/admin/test\">Test pages</a>"

# @get('admin/db/reset')
# def resetDB(handler, request):
	# handler.title('Reset database')

@get('admin/test')
def adminTest(handler, request):
	handler.title('Test pages')
	admin(handler)

	with open('handlers/test.py') as f:
		found = 0
		for token, tokString, tokStart, tokEnd, line in tokenize.generate_tokens(f.readline):
			if token == OP and tokString == '@':
				found = 1
			elif token == NEWLINE:
				found = 0
			elif token == NAME and tokString == 'get' and found == 1:
				found = 2
			elif token == STRING and found == 2:
				tokString = tokString.replace("'", "")
				print "<a href=\"/%s\">%s</a><br>" % (tokString, stripTags(tokString))
				found = 0
