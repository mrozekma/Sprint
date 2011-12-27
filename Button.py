class Button:
	def __init__(self, text, url = '#', id = None, image = None, type = 'link'):
		self.text = text
		self.url = url
		self.id = id
		self.image = image
		self.type = type

		self.clazz = 'btn'

	def __str__(self):
		body = self.text
		if self.image:
			body = "<img src=\"/static/images/%s\">&nbsp;%s" % (self.image, body)

		id = "id=\"%s\" " % self.id if self.id else ''

		if self.type == 'link':
			return "<a %shref=\"%s\" class=\"%s\">%s</a>" % (id, self.url, self.clazz, body)
		if self.type == 'button':
			if self.url == '#':
				return "<button %sclass=\"%s\">%s</button>" % (id, self.clazz, body)
			elif self.url.startswith('javascript:'):
				return "<button %sclass=\"%s\" onClick=\"%s\">%s</button>" % (id, self.clazz, self.url, body)
			else:
				return "<button %sclass=\"%s\" onClick=\"document.location='%s'; return false;\">%s</button>" % (id, self.clazz, self.url, body)
		if self.type == 'submit':
			return "<button %sclass=\"%s\" onClick=\"this.form.submit();\">%s</button>" % (id, self.clazz, body)
		raise ValueError, "Unknown type '%s'" % self.type

	# MODIFIERS

	def simple(self):
		self.clazz = 'fancy'
		return self

	def mini(self):
		self.simple()
		self.clazz += ' mini'
		return self

	def positive(self):
		self.clazz += ' success'
		return self

	def negative(self):
		self.clazz += ' danger'
		return self

	def info(self):
		self.clazz += ' info'
		return self

	def selected(self):
		self.clazz += ' selected'
		return self

	def post(self):
		self.type = 'submit'
		return self
