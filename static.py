from __future__ import with_statement
from os.path import isfile
from utils import *

@get('static/(?P<path>.+)')
def static(handler, request, path, v = None):
	request['wrappers'] = False

	filename = stripTags(path)
	types = {
		'css': 'text/css',
		'js': 'text/javascript',
		'png': 'image/png'
		}

	if not isfile("static/" + filename):
		return handler.error("Invalid static argument", "Static resource <b>%s</b> does not exist" % filename)

	ext = filename[filename.rfind('.')+1:]
	if ext in types:
		handler.contentType = types[ext]

	with open("static/" + filename) as f:
		print f.read()
