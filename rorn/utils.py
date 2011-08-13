import hashlib


# http://smitbones.blogspot.com/2008/01/python-strip-html-tags-function.html
def stripTags(value):
    # "Return the given HTML with all tags stripped."
    # return re.sub(r'<[^>]*?>', '', value)
	return value.replace("<", "&lt;")

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
