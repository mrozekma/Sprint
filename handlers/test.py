try:
	import matplotlib
	matplotlib.use('Cairo')
	import matplotlib.pyplot as plt
	from pylab import figure, pie, axes, title
	plottingLib = True
except ImportError:
	plottingLib = False

from markdown import Markdown

from rorn.ResponseWriter import ResponseWriter
from rorn.Box import *
from rorn.code import showCode

from Privilege import admin
from Task import Task
from Button import *
from utils import *

@get('code')
def code(handler, filename, line):
	handler.title('Code')
	admin(handler)

	showCode(filename, int(line), 2)

@get('test')
def test(handler):
	handler.title('Test')
	print "<form method=\"post\" action=\"/test\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"one\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"two\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"\">"
	print "<input type=\"hidden\" name=\"test[]\" value=\"three\">"
	print "<input type=\"submit\" value=\"Submit\">"
	print "</form>"

@post('test')
def testPost(handler, p_test):
	print p_test

@get('test/(?P<num>[0-9]+)/regex')
def testRegex(handler, num):
	handler.title('Test Regex')
	print num

@get('test2')
def test2(handler):
	raise Exception("Lorem ipsum dolor sit amet, consectetur adipiscing elit")

@get('chosen')
def chosen(handler):
	handler.title('Test')
	from Privilege import dev
	dev(handler)
	print "<script type=\"text/javascript\">"
	print "$(document).ready(function() {"
	print "$('select').css('width', '500px').chosen();"
	print "});"
	print "</script>"
	print "<select id=\"one\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"two\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"three\"><option>one</option><option>two</option><option>three</option></select>"
	print "<select id=\"four\"><option>one</option><option>two</option><option>three</option></select>"

if plottingLib:
	@get('graph1')
	def test(handler):
		handler.wrappers = False
		handler.contentType = 'image/png'

		plt.clf()
		plt.cla()

		plt.title("Test Title ($\sqrt{\pi}$)")
		plt.xlabel("X axis")
		plt.ylabel("Y axis")
		plt.plot([1,2,5])
		plt.annotate("Annotation", (1, 2), (1.5, 1.95), arrowprops = {'facecolor': 'black', 'shrink': 0.05})

		w = ResponseWriter(False, False)
		w.clear()
		plt.savefig(w)
		print w.data

	@get('graph2')
	def graph2(handler):
		handler.wrappers = False
		handler.contentType = 'image/png'

		plt.clf()
		plt.cla()
		figure(1, figsize=(6,6))
		# ax = axes([0.1, 0.1, 0.8, 0.8])

		pie([150, 200, 400], labels = ['foo', 'bar', 'baz'], autopct = lambda x: "%d (%1.1f%%)" % (int(x*750/100), x))
		title('Raining Hogs and Dogs')

		w = ResponseWriter(False, False)
		w.clear()
		plt.savefig(w)
		print w.data

	@get('graph3')
	def graph3(handler):
		plt.clf()
		plt.cla()
		fig = figure()
		title('Test')

		pie([100, 100, 100], labels = ['test', 'test2', 'test3'], autopct = "%1.1f%%")

		w = ResponseWriter(False, False)
		w.clear()
		plt.savefig(w)
		handler.wrappers = False
		handler.contentType = 'image/png'
		print w.data

	@get('graph4')
	def graph4(handler):
		handler.title("Graph 4")

		print "<script type=\"text/javascript\" src=\"/static/highcharts/js/highcharts.js\"></script>"
		print """
<script type=\"text/javascript\"> //"
$(document).ready(function() {
	chart = new Highcharts.Chart({
		chart: {
			renderTo: 'foobar',
			defaultSeriesType: 'line',
			zoomType: 'x',
		},

		credits: {
			enabled: false
		},

		title: {
			text: 'foo'
		},

		xAxis: {
			type: 'datetime',
			dateTimeLabelFormats: {
				day: '%a'
			},
			tickInterval: 24 * 3600 * 1000,
			maxZoom: 48 * 3600 * 1000,
			title: {
				text: 'Day'
			}
		},

		series: [
			{
				name: 'Test Series',
				pointStart: Date.UTC(2011, 8, 15),
				pointInterval: 24 * 3600 * 1000,
				data: [1, 2, 3, 5, 6, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150],
				visible: true
			},

			{
				name: 'Test Series 2',
				pointStart: Date.UTC(2011, 8, 15),
				pointInterval: 24 * 3600 * 1000,
				data: [5, 5, 5, 5],
			}
		]
	});
console.log(chart);
});
</script>
"""
		print "<div id=\"foobar\"></div>"

@get('hours-test')
def hoursTest(handler):
	handler.title('Hours Test')

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

@get('icons')
def icons(handler):
	handler.title('Icons')
	admin(handler)

	def makeList(path, l = {}):
		from os import listdir
		from os.path import isdir
		for entry in listdir(path):
			full = "%s/%s" % (path, entry)
			if isdir(full):
				makeList(full, l)
			else:
				if path not in l:
					l[path] = []
				l[path].append(full)
		return l

	l = makeList('/home/mrozekma/icons')
	for scn, items in l.items():
		print "<h2>%s</h2>" % scn
		items.sort()
		for item in items:
			print "<img src=\"%s\" title=\"%s\">" % (item.replace('/home/mrozekma/icons', '/icons/show'), item)

@get('icons/show/(?P<path>.*)')
def iconsShow(handler, path):
	handler.wrappers = False
	admin(handler)

	filename = stripTags(path)
	types = {
		'css': 'text/css',
		'js': 'text/javascript',
		'png': 'image/png'
		}

	ext = filename[filename.rfind('.')+1:]
	if ext in types:
		handler.contentType = types[ext]

	with open("/home/mrozekma/icons/" + filename) as f:
		print f.read()

@get('test/bootstrap')
def testBootstrap(handler):
	handler.title('Bootstrap')
	admin(handler)

	print "<ul class=\"tabs\">"
	print "<li><a href=\"#\">One</a></li>"
	print "<li class=\"active\"><a href=\"#\">Two</a></li>"
	print "<li><a href=\"#\">Three</a></li>"
	print "<li><a href=\"#\">Four</a></li>"
	print "<li><a href=\"#\">Five</a></li>"
	print "</ul>"
	print "<div class=\"clear\"></div>"

	print "<div class=\"alert-message success\">Yay!</div>"
	print "<div class=\"alert-message danger\"><a href=\"#\" class=\"close\">x</a>Boo!</div>"

	print "Test <span class=\"label important\">Test</span><br>"
	print "<button class=\"btn success\">Test</button>"
	print "<br><br>"

	for type in ('error', 'warning', 'success', 'info', 'inverse'):
		print "<span class=\"badge badge-%s\">%s</span>&nbsp;" % (type, type)

@get('test/boxes')
def testBoxes(handler):
	handler.title('Boxes')
	admin(handler)

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

@get('test/savebutton')
def testSaveButton(handler):
	handler.title('Save Button')
	admin(handler)

	print "<script type=\"text/javascript\">"
	print "$(document).ready(function() {"
	print "$('#save-button').savebutton();"
	print "});"
	print "</script>"

	print "<form method=\"post\" action=\"/test/savebutton\">"
	print "<button id=\"save-button\">Post</button>"
	print "</form>"

@post('test/savebutton')
def testSaveButtonPost(handler):
	handler.title('Save Button')
	admin(handler)

	print "Post"

@get('test/markdown')
def testMarkdown(handler):
	handler.title('Markdown')
	admin(handler)

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

@get('test/querystr')
def testQueryStr(handler, a = None, b = None, c = None, d = None):
	handler.title('Query String')
	admin(handler)
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
