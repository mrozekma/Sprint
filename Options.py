from optparse import OptionParser

options = None
def option(key = None):
	assert options is not None
	return getattr(options, key) if key else options

def parse():
	parser = OptionParser()
	parser.add_option('-d', '--daemon', action = 'store_true', dest = 'daemon', default = False, help = "Daemonize (run in background). See also --pidfile")
	parser.add_option('--pidfile', dest = 'pidfile', help = "Pidfile when daemonizing")
	parser.add_option('--dev', action = 'store_true', dest = 'dev', default = False, help = "Run in developer mode (for debugging)")
	parser.add_option('--init', action = 'store_const', const = 'init', dest = 'mode', default = 'run', help = "Initialize the database on a new install")
	parser.add_option('--update', action = 'store_const', const = 'update', dest = 'mode', help = "Update the database after a pull")

	global options
	options, args = parser.parse_args()
	return option()
