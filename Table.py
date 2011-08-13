from rorn.ResponseWriter import ResponseWriter

class Table:
	def __init__(self, cls = None):
		self.cls = cls
		self.headers = None
		self.elements = []
		self.cols = 0
		self.widths = []

	def __iadd__(self, element):
		self.elements.append(element)
		self.cols = max(self.cols, len(element))
		return self

	def __imul__(self, headers):
		self.headers = headers
		self.cols = max(self.cols, len(headers))
		return self

	def __imod__(self, widths):
		self.widths = widths
		return self

	def __str__(self):
		w = ResponseWriter()
		try:
			print "<table%s>" % {True: "", False: " class=\"%s\"" % self.cls}[self.cls == None]
			widths = Table.extend(self.widths, self.cols, None)
			if self.headers:
				print "<tr>" + ''.join(["<th>%s</th>" % x for x in Table.extend(self.headers, self.cols, '&nbsp;')]) + "</tr>"
			for i in range(len(self.elements)):
				ext = Table.extend(self.elements[i], self.cols, '&nbsp;')
				print "<tr>" + ''.join(["<td%s>%s</td>" % (" style=\"width: %s\"" % widths[i] if widths[i] else "", ext[i]) for i in range(self.cols)]) + "</tr>"
			print "</table>"
			return w.done()
		except:
			w.done()
			raise

	@staticmethod
	def extend(row, length, filler):
		if len(row) >= length:
			return row
		return [row[i] if i < len(row) else filler for i in range(length)]

class LRTable(Table):
	class LengthError(Exception): pass

	def __iadd__(self, element):
		if(len(element) != 2):
			raise LengthError()
		return Table.__iadd__(self, element)

	def __imul__(self, element):
		if(len(element) != 2):
			raise LengthError()
		return Table.__imul__(self, element)

	def __imod__(self, element):
		if(len(element) != 2):
			raise LengthError()
		return Table.__imod__(self, element)

	def __setitem__(self, k, v):
		self += (k, v)

	def __str__(self):
		w = ResponseWriter()
		print "<table class=\"list\">"
		if self.headers:
			print "<tr><th class=\"left\">%s</th><th class=\"right\">%s</th></tr>" % self.headers
		for element in self.elements:
			print "<tr><td class=\"left\">%s</td><td class=\"right\">%s</td></tr>" % element
		print "</table>"
		return w.done()

class ClickableTable(Table):
	def __init__(self, cls = None):
		Table.__init__(self, cls)
		self.urls = []

	def __iadd__(self, element):
		self.urls.append(element[0])
		return Table.__iadd__(self, element[1:])

	def __str__(self):
		rtn = Table.__str__(self)
		for url in self.urls:
			rtn = rtn.replace("<tr><td", "<tr onMouseOver=\"hltable_over(this)\" onMouseOut=\"hltable_out(this)\" onClick=\"hltable_click('%s')\"><td" % url, 1)
		return rtn
