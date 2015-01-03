from __future__ import with_statement
from os.path import isfile, realpath
from utils import *

@get('static/(?P<path>.+)')
def static(handler, path, v = None):
	handler.wrappers = False
	handler.log = False

	filename = stripTags(path)
	types = {
		'css': 'text/css',
		'js': 'text/javascript',
		'png': 'image/png',
		'svg': 'image/svg+xml'
		}

	if not isfile("static/" + filename):
		return handler.error("Invalid static argument", "Static resource <b>%s</b> does not exist" % filename)
	if not realpath("static/" + filename).startswith(realpath("static")):
		return handler.error("Invalid static argument", "Static resource <b>%s</b> is not allowed" % filename)

	ext = filename[filename.rfind('.')+1:]
	if ext in types:
		handler.contentType = types[ext]

	with open("static/" + filename) as f:
		sys.stdout.write(f.read())
