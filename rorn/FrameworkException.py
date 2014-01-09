from __future__ import with_statement
import traceback

from ResponseWriter import ResponseWriter
from code import highlightCode
from utils import *

class FrameworkException:
	def __init__(self, exc):
		self.exc = exc

	def __str__(self):
		writer = ResponseWriter()
		print "<style type=\"text/css\">"
		print """
div.error {
    background-color: #faa;
    border: 1px solid #f00;
    padding: 4px;
    -moz-border-radius: 3px;
    border-radius: 3px;
}

div.details {
    margin: 15px 0px 15px 30px;
}
"""

		#HACK
		with open('static/syntax-highlighting.css') as f:
			print ''.join(f.readlines())

		print "</style>"

		print "<div class=\"error\">"
		print "<b>Unexpected framework exception caught in rorn before action dispatching:</b><br>"
		print "<div class=\"details\">%s: %s</div>" % (self.exc[0].__name__, str(self.exc[1]).replace('\n', '<br>'))

		tb = self.exc[2]
		try:
			base = basePath()
			lpad = len(base) + 1
			print "<div class=\"code_default dark\" style=\"padding: 4px\">"
			for filename, line, fn, stmt in traceback.extract_tb(tb):
				print "<div class=\"code_header\">%s:%s(%d)</div>" % (filename[lpad:] if filename.startswith(base) else "<i>%s</i>" % filename.split('/')[-1], fn, line)
				print "<div style=\"padding: 0px 0px 10px 20px\">"
				print highlightCode(stmt)
				print "</div>"
			print "</div>"
		except:
			raise
			print "<pre>"
			traceback.print_tb(tb, None, writer)
			print "</pre>"
		print "</div>"

		return writer.done()
