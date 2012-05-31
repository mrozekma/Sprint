import markdown

standardExtensions = ['nl2br', 'fenced_code', 'sane_lists'] # 'codehilite'

extensions = standardExtensions[:]
import markdown_extensions
for v in markdown_extensions.__dict__.values():
	try:
		if issubclass(v, markdown.Extension) and v != markdown.Extension:
			extensions.append(v())
	except TypeError:
		pass

md = markdown.Markdown(output_format = 'html4', safe_mode = 'escape', lazy_ol = False, extensions = extensions)

class Markdown:
	@staticmethod
	def head(selector = None):
		print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/prettify/sunburst.css\">"
		print "<script src=\"/static/prettify/prettify.js\" type=\"text/javascript\"></script>"
		if selector:
			print "<script type=\"text/javascript\">"
			print "$(document).ready(function() {"
			print "    $('%s').addClass('prettyprint');" % selector
			print "    prettyPrint();"
			print "});"
			print "</script>"


	@staticmethod
	def render(text):
		return md.convert(text)
