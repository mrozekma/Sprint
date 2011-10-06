from __future__ import division

from rorn.ResponseWriter import ResponseWriter

from utils import *

inf = float('inf')

class ProgressBar:
	# zeroDivZero means the progress should be 0 if amt == total == 0. It will be 100 if False. In either case, it will be infinity if amt > 0
	# style is a map of percentages to styles to apply to div.progress-current; the highest percentage <= this bar's percentage will be applied
	def __init__(self, label, amt, total, pcnt = None, zeroDivZero = True, style = None):
		self.label = label
		self.amt = amt
		self.total = total
		if pcnt:
			self.pcnt = pcnt
		elif total == 0:
			self.pcnt = inf if amt > 0 else 0 if zeroDivZero else 100
		else:
			self.pcnt = amt / total * 100

		if isinstance(style, dict):
			topPcnt = maxOr(filter(lambda p: p <= self.pcnt, style.keys()))
			self.cls = style[topPcnt] if topPcnt in style else None
		elif isinstance(style, str):
			self.cls = style
		else:
			self.cls = ''

	def __str__(self):
		w = ResponseWriter()
		if self.label:
			print "%s " % self.label
		print "<div class=\"task-progress-total\" style=\"position: relative; top: 5px\">"
		if self.pcnt > 0:
			print "<div class=\"progress-current%s\" style=\"width: %d%%;\">" % (" %s" % self.cls, min(self.pcnt, 100))
		print "<span class=\"progress-percentage\">%d/%d hours (%s%%)</span>" % (self.amt, self.total, '&#8734;' if self.pcnt == inf else "%d" % self.pcnt)
		if self.pcnt > 0:
			print "</div>"
		print "</div>"
		return w.done().replace("\n", "")
