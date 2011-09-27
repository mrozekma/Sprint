from __future__ import division

from rorn.ResponseWriter import ResponseWriter

inf = float('inf')

class ProgressBar:
	def __init__(self, label, amt, total, pcnt = None, zeroDivZero = True):
		self.label = label
		self.amt = amt
		self.total = total
		if pcnt:
			self.pcnt = pcnt
		elif total == 0:
			self.pcnt = inf if amt > 0 else 0 if zeroDivZero else 100
		else:
			self.pcnt = amt / total * 100

	def __str__(self):
		w = ResponseWriter()
		if self.label:
			print "%s " % self.label
		print "<div class=\"task-progress-total\" style=\"position: relative; top: 5px\">"
		if self.pcnt > 0:
			print "<div class=\"progress-current%s\" style=\"width: %d%%;\">" % (' progress-current-red' if self.pcnt > 100 else '', min(self.pcnt, 100))
		print "<span class=\"progress-percentage\">%d/%d hours (%s%%)</span>" % (self.amt, self.total, '&#8734;' if self.pcnt == inf else "%d" % self.pcnt)
		if self.pcnt > 0:
			print "</div>"
		print "</div>"
		return w.done().replace("\n", "")
