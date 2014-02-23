from markdown import Markdown

from rorn.ResponseWriter import ResponseWriter
from rorn.Box import *
from rorn.code import showCode

from Privilege import requirePriv
from Task import Task
from Button import *
from utils import *

pages = []
def test(url, name, **kw):
	def wrap(f):
		e = {'url': url, 'name': name}
		pages.append(e)
		kw['statics'] = ['test'] + ensureList(kw['statics'] if 'statics' in kw else [])
		if 'post' in kw and kw['post']:
			del kw['post']
			e['method'] = 'post'
			return post(url, **kw)(f)
		else:
			e['method'] = 'get'
			return get(url, **kw)(f)
	return wrap

@test('test/code', 'Code')
def code(handler, filename, line):
	handler.title('Code')
	requirePriv(handler, 'Dev')

	showCode(filename, int(line), 2)

@test('test/test', 'Test')
def testGet(handler):
	handler.title('Test')
	requirePriv(handler, 'Dev')
	print "<form method=\"post\" action=\"/test/test\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"one\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"two\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"three\">"
	print "<input type=\"submit\" value=\"Submit\">"
	print "</form>"

@test('test/test', 'Test', post = True)
def testPost(handler, p_test):
	requirePriv(handler, 'Dev')
	print p_test

@test('test/(?P<num>[0-9]+)/regex', 'Regex')
def testRegex(handler, num):
	handler.title('Test Regex')
	requirePriv(handler, 'Dev')
	print num

@test('test/chosen', 'Chosen')
def chosen(handler):
	handler.title('Test')
	requirePriv(handler, 'Dev')
	print "<script type=\"text/javascript\">"
	print "$(document).ready(function() {"
	print "$('select').css('width', '500px').chosen();"
	print "});"
	print "</script>"
	print "<select id=\"one\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"two\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"three\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"four\"><option>one</option><option>two</option><option>three</option></select>"

@test('test/hours-test', 'Hours')
def hoursTest(handler):
	handler.title('Hours Test')
	requirePriv(handler, 'Dev')

	from Sprint import Sprint
	sprint = Sprint.load(2)

	from datetime import datetime, timedelta
	from User import User
	tasks = sprint.getTasks()
	oneday = timedelta(1)
	start, end = tsToDate(sprint.start), tsToDate(sprint.end)

	print "<script type=\"text/javascript\" src=\"/static/highcharts/js/highcharts.js\"></script>"
	print """
<script type=\"text/javascript\"> //"
$(document).ready(function() {
	chart = new Highcharts.Chart({
		chart: {
			renderTo: 'chart',
			defaultSeriesType: 'line',
			zoomType: 'x',
		},

		credits: {
			enabled: false
		},

		title: {
			text: '%s'
		},

		xAxis: {
			type: 'datetime',
			dateTimeLabelFormats: {
				day: '%%a'
			},
			tickInterval: 24 * 3600 * 1000,
			maxZoom: 48 * 3600 * 1000,
			title: {
				text: 'Day'
			}
		},

		yAxis: {
			min: 0,
			title: {
				text: 'Hours'
			}
		},

		series: [
""" % sprint

	for user in sprint.members:
		print "{"
		print "name: '%s'," % user.username
		print "pointStart: %d," % (sprint.start * 1000)
		print "pointInterval: 24 * 3600 * 1000,"
		print "data: [",
		userTasks = filter(lambda t: user in t.assigned, tasks)
		seek = start
		while seek <= end:
			print "%d," % sum(t.hours if t else 0 for t in [t.getRevisionAt(seek) for t in userTasks]),
			seek += oneday
		print "],"
		print "visible: true"
		print "},"

	print """
]
	});
console.log(chart);
});
</script>
"""
	print "<div id=\"chart\"></div>"

@test('test/boxes', 'Boxes')
def testBoxes(handler):
	handler.title('Boxes')
	requirePriv(handler, 'Dev')

	print Box("Box", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print Box("Box (red)", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum", clr = 'red')
	print Box("Box (green)", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum", clr = 'green')
	print ErrorBox("ErrorBox", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print WarningBox("WarningBox", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print SuccessBox("SuccessBox", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print InfoBox("InfoBox", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print LoginBox()
	print CollapsibleBox("CollapsibleBox", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pharetra ornare tortor, a ornare nibh aliquam et. Cras ultricies rutrum magna et elementum")
	print InfoBox("Timeout", "This box times out in 5 seconds", close = 5)
	print InfoBox("Close", "This box can be closed", close = True)

@test('test/savebutton', 'Save Button')
def testSaveButton(handler):
	handler.title('Save Button')
	requirePriv(handler, 'Dev')

	print "<script type=\"text/javascript\">"
	print "$(document).ready(function() {"
	print "$('#save-button').savebutton();"
	print "});"
	print "</script>"

	print "<form method=\"post\" action=\"/test/savebutton\">"
	print "<button id=\"save-button\">Post</button>"
	print "</form>"

@test('test/savebutton', 'Save Button', post = True)
def testSaveButtonPost(handler):
	handler.title('Save Button')
	requirePriv(handler, 'Dev')

	print "Post"

@test('test/markdown', 'Markdown')
def testMarkdown(handler):
	handler.title('Markdown')
	requirePriv(handler, 'Dev')

	md = Markdown(output_format = 'html4', safe_mode = 'escape', lazy_ol = False, extensions = ['nl2br', 'fenced_code', 'codehilite'])
	tests = [
		"test",
		"test *test* test",
		"* one\n* two\n* three",
		"one\ntwo",
		"<b>test</b>",
		"http://google.com/",
		"[Google](http://google.com/)",
		"    int x;\n    x++;\n    printf(\"%d\\n\", 4);",
		"foo\n~~~\nint x;\n~~~",
	]

	print """
<link rel="stylesheet" type="text/css" href="/markdown.css">
<style type="text/css">
table.tests {
    width: 100%;
}

table.tests > td {
    border: 1px solid #000;
}
</style>
"""

	print "<table class=\"tests\" border=\"1\" cellspacing=\"0\">"
	print "<tr><th>Plain</th><th>Markdown</th></tr>"
	for plain in tests:
		print "<tr><td><pre>%s</pre></td><td>%s</td></tr>" % (stripTags(plain), md.convert(plain))
	print "</table>"

@test('test/querystr', 'Query String')
def testQueryStr(handler, a = None, b = None, c = None, d = None):
	handler.title('Query String')
	requirePriv(handler, 'Dev')
	from pprint import pprint
	print "<pre>"
	sys.stdout.write("a = ")
	pprint(a)
	sys.stdout.write("b = ")
	pprint(b)
	sys.stdout.write("c = ")
	pprint(c)
	sys.stdout.write("d = ")
	pprint(d)
	print "</pre>"

@test('test/error', 'Error')
def testError(handler):
	requirePriv(handler, 'Dev')
	raise RuntimeError("Test")
