from __future__ import with_statement
from SilverCity import Python as SyntaxHighlighter
from StringIO import StringIO
import sys
from os.path import abspath, isabs, isfile

from ResponseWriter import ResponseWriter
from rorn.Box import Box, ErrorBox
from rorn.Lock import synchronized
from utils import *

def showCode(filename, line, around = None):
	parsedFilename = filename if isabs(filename) else abspath("%s/%s" % (basePath(), filename))
	if not any(parsedFilename.startswith(path) for path in [basePath()] + sys.path):
		print ErrorBox("Illegal filename", "File <b>%s</b> not part of codebase or standard library" % stripTags(filename))
		return
	elif not isfile(parsedFilename):
		print ErrorBox("Illegal filename", "Unknown file <b>%s</b>" % stripTags(filename))
		return

	with open(parsedFilename) as f:
		data = f.read()

	lines = highlightCode(data).split('<br/>')
	if line < 1:
		line = 1
	elif line > len(lines):
		line = len(lines)
	lines = ["<tr class=\"%s\"><td class=\"icon\">&nbsp;</td><td class=\"p_linum\"><a name=\"l%d\" href=\"#l%d\">%s</a></td><td class=\"code_line\">%s</td></tr>" % ('selected_line' if i == line else '', i, i, ("%3d" % i).replace(' ', '&nbsp;'), lines[i-1]) for i in range(1, len(lines)+1)]
	if around:
		lines = lines[line-around-1:line+around]

	lines = "<table class=\"code_default dark\">\n%s\n</table>" % '\n'.join(lines)
	print lines

@synchronized('silvercity')
def highlightCode(text):
	target = StringIO()
	SyntaxHighlighter.PythonHTMLGenerator().generate_html(target, text)
	return target.getvalue()
