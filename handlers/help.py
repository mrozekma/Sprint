from Search import Search
from Note import Note

from utils import *

@get('help/search')
def helpSearch(handler, request):
	handler.title("Search")

	print "Searching is a combination of miscellaneous filters and a free-form task name fuzzy search. The search operators are:<br>"

	operators = [('assigned', "Comma-separated list of usernames the task is assigned to. Use \"me\" to refer to the current user"), ('status', "Comma-separated list of the task's current status"), ('hours', "The task's current hours. Also accepts several forms of range: <code>4-8</code>, <code>4-</code>, <code>&gt;4</code>, <code>&gt;=4</code>, etc."), ('goal', "Comma-separated list of goal colors"), ('created', "YYYYMMDD date (or range of dates) the task was created in"), ('modified', "YYYYMMDD date (or range of dates) the task was modified in")]

	print "<ul>"
	for (name, desc) in operators:
		print "<li><b>%s</b> &mdash; %s" % (name, desc)
	print "</ul>"

	print "Search operators are of the form <code>name:value</code>, e.g. <code>status:complete,deferred</code>. Fields can be quoted as necessary, e.g. <code>status:\"not started\"</code><br><br>"

	print "Any non-search operator is assumed to be part of the free-form task name search. For example, <code>foo hours:4 bar</code> shows all 4 hour tasks matching the string \"foo bar\". Task names must be at least %d%% similar to the free-form search to match<br><br>" % Search.minMatchPercent()

	print "The number of matching tasks is shown on the backlog dateline. The <img class=\"bumpdown\" src=\"/static/images/cross.png\"> icon cancels the search and shows all tasks"

@get('help/markdown')
def helpMarkdown(handler, request):
	handler.title("Markdown")

	print "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/prettify/sunburst.css\">"
	print "<style type=\"text/css\">"
	print "table.examples {width: 100%;}"
	print "table.examples td {vertical-align: top; border-top: 1px solid #000;}"
	print "table.examples td > * {margin: 4px;}"
	print "</style>"
	print "<script src=\"/static/prettify/prettify.js\" type=\"text/javascript\"></script>"
	print "<script src=\"/static/help-markdown.js\" type=\"text/javascript\"></script>"

	print "Markdown is used to format messages and task notes. The <a href=\"http://daringfireball.net/projects/markdown/\">official Markdown website</a> has pretty comprehensive documentation, but this page summarizes the syntax and lists some extensions"

	print "<h2>Basic syntax</h2>"
	print "This is standard markdown syntax; if you've used it before you can skip this section:<br><br>"

	examples(
		"plain text",
		"*italics*, _italics_\n**bold**, __bold__",
		"# header\n## sub header\n### sub sub header",
		"* unordered list\n* second bullet\n\n1. ordered list\n2. second item",
		"> blockquote\n> line 2\n> > nested",
		"    str = \"code blocks\"\n    str += \" are indented by four spaces\"\n    print str",
		"inline `monospaced text`",
		"horizontal lines:\n\n---",
		"Link to [this guide](/help/markdown)\n<http://google.com/>",
		"![alt text](/static/images/sun.png)",
		"escape markdown with \*backslashes\*",
	)

	print "<h2>Standard extensions</h2>"
	print "This is optional markdown functionality that is enabled here:<br><br>"

	examples(
		"single newlines are treated as such\nstandard markdown requires double newlines",
		"4. ordered lists respect their index,\ninstead of starting at 1",
		"fenced code blocks are available:\n\n~~~~~~\n// no indentation required\nint x;\nx++\n~~~~~~",
		"html is treated as <b>plain text</b>",
	)

	print "<h2>Custom extensions</h2>"
	print "These are extensions written specifically for this tool; they won't work anywhere else:<br><br>"

	examples(
		"svn revision r123",
		"bz123\nbug 123",
		handler.session['user'].safe.username,
	)

	print "<br>"

def examples(*texts):
	print "<table class=\"examples\" cellspacing=\"0\">"
	print "<tr><th>Source</th><th>Rendered</th></tr>"
	for plain in texts:
		print "<tr><td><pre>%s</pre></td><td class=\"markdown\">%s</td></tr>" % (stripTags(plain), Note(0, 0, plain).render())
	print "</table>"
