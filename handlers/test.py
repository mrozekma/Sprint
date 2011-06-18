from ResponseWriter import ResponseWriter
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plt
from pylab import figure, pie, axes, title
from Task import Task
from Button import *
from Box import ErrorBox
from utils import *

@get('test')
def test(handler, request):
	handler.title('Test')
	print "<form method=\"post\" action=\"/test\">"
	print "<input type=\"hidden\" name=\"test\" value=\"one\">"
	print "<input type=\"hidden\" name=\"test\" value=\"two\">"
	print "<input type=\"hidden\" name=\"test\" value=\"\">"
	print "<input type=\"hidden\" name=\"test\" value=\"three\">"
	print "<input type=\"submit\" value=\"Submit\">"
	print "</form>"

@post('test')
def testPost(handler, request, p_test):
	print p_test

# @get('test')
# def test(handler, request):
	# print """
# <style type=\"text/css\">
# .b {font-weight: bold}
# </style>

# <script type="text/javascript">
# $(document).ready(function() {
	# four = $('.four');
    # two = four.prevAll('.two:last');
    # two.addClass('b');
# });
# </script>"""
	# print "<div class=\"one\">one</div>"
	# print "<div class=\"two\">two</div>"
	# print "<div class=\"three\">three</div>"
	# print "<div class=\"four\">four</div>"
	# print "<div class=\"five\">five</div>"
	# print "<div class=\"two\">two</div>"

# @get('test')
# def test(handler, request):
	# print """
# <link href="/static/foo/stylesheets/jquery.treeTable.css" rel="stylesheet" type="text/css" />
# <!-- <script type="text/javascript" src="/static/foo/javascripts/jquery.treeTable.js"></script> -->
# <script src="/static/jquery.tablednd_0_5.js" type="text/javascript"></script>
# <script type="text/javascript">
# $(document).ready(function() {
	# $('#test').treeTable({
		# initialState: 'expanded'
	# });
	# $('#test').tableDnD({
		# onDragStart: function(tbl, row) {
			# if($(row).hasClass('child-of-node-1')) {
				# // $('table tr').addClass('nodrop');
				# // $('.child-of-node-1').removeClass('nodrop');
				# // $('#log').html("Started");
			# } else {
				# // $('#node-1, .child-of-node-1').addClass('nodrop');
				# // $('.child-of-node-1').hide();
			# }
		# },

		# onDrop: function(tbl, row) {
			# // $('table tr').removeClass('nodrop');
			# $('.child-of-node-1').show();
			# if($(row).attr('id') == 'node-1') {
				# $('.child-of-node-1').insertAfter(row);
			# }
		# }
	# });

	# $('#add').click(function() {
		# $('#node-5').addClass('child-of-node-1');
	# });
# });
# </script>

# <div id="log">x</div>
# <button id="add">Add child class to five</button>

# <table id="test">
# <tr id="node-1"><td>one</td><td>two</td></tr>
# <tr id="node-2" class="child-of-node-1"><td>three lorem ipsum</td><td>four</td></tr>
# <tr id="node-3" class="child-of-node-1"><td>seven</td><td>eight</td></tr>
# <tr id="node-4" class="child-of-node-1"><td>nine</td><td>ten</td></tr>
# <tr id="node-5"><td>five</td><td>six</td></tr>
# <tr id="node-6"><td>eleven</td><td>twelve</td></tr>
# <tr id="node-7"><td>thirteen</td><td>fourteen</td></tr>
# <tr id="node-8"><td>fifteen</td><td>sixteen</td></tr>
# </table>
# """

# @get('test')
# def test(handler, request, ajax = False):
	# if ajax:
		# request['wrappers'] = False
		# request['code'] = 299
		# print "woo"
		# done()

	# print """
# <script type="text/javascript">
# $(document).ready(function() {
	# $('#foo').click(function() {
		# $.ajax({
			# url: '/test?ajax',
			# success: function(data, text, request) {
				# alert(request.status);
				# alert(data);
			# }
		# });
	# });
# });
# </script>

# <button id="foo">Test</button>
# """

"""
@get('test')
def test(handler, request, foo, bar):
	print "foo = %s<br>" % foo
	print "bar = %s<br>" % bar
"""

"""
@get('test')
def test(handler, request):
	if len(request['path']) != 1:
		print ErrorBox('Fail', "%s: %s" % (len(request), request))
		done()

	test(handler, request, int(request['path'][0]))

def test(handler, request, id):
	print id
	print "<hr>"

	print Button('test', '#')
	print Button('mini', '#').mini()
	print Button('selected', '#').selected()
	print Button('positive', '#').positive()
	print Button('negative', '#').negative()
	# tasks = Task.loadAll()
	# for task in tasks:
		# print "%s<br>" % task.id
		# print "%s<br>" % task.revision
		# print "%s<br>" % task.sprint
		# print "%s<br>" % task.creator
		# print "%s<br>" % task.assigned
		# print "%s<br>" % task.name
		# print "%s<br>" % task.timestamp
		# print "<hr>"
	# tasks[0].name = 'web-revision'
	# tasks[0].revise()
"""

"""
@get('test')
def test(handler, request):
	request['wrappers'] = False
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

@get('test2')
def test2(handler, request):
	request['wrappers'] = False
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
"""
