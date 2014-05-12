import cgi
import hashlib
from os.path import dirname
import sys
import traceback

def stripTags(value):
	return cgi.escape(value, True)

class DoneRendering(Exception): pass
def done():
	raise DoneRendering()

class Redirect(Exception):
	def __init__(self, target):
		self.target = target
def redirect(target):
	raise Redirect(target)

def md5(str):
	return hashlib.md5(str).hexdigest()

def ucfirst(str):
	if len(str) == 0:
		return str
	elif len(str) == 1:
		return str.upper()
	else:
		return str[0].upper() + str[1:]

def pluralize(num, singular, plural):
	return "%d %s" % (num, singular if num == 1 else plural)

def globalize(f):
	__builtins__[f.func_name] = f
	return f

def basePath():
	return dirname(__file__).replace('/rorn', '')

def formatException():
	type, e, tb = sys.exc_info()
	return "<b>%s: %s</b><br><br>%s" % (type.__name__, str(e).replace('\n', '<br>'), formatTrace(traceback.extract_tb(tb)))

def formatTrace(frames):
	from code import highlightCode
	from ResponseWriter import ResponseWriter
	writer = ResponseWriter()
	base = basePath()
	lpad = len(base) + 1
	print "<div class=\"code_default light\" style=\"padding: 4px\">"
	for filename, line, fn, stmt in frames:
		print "<div class=\"code_header\">%s:%s(%d)</div>" % (filename[lpad:] if filename.startswith(base) else "<i>%s</i>" % filename.split('/')[-1], fn, line)
		print "<div style=\"padding: 0px 0px 10px 20px\">"
		print highlightCode(stmt)
		print "</div>"
	print "</div>"
	return writer.done()
