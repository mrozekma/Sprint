from utils import *

@get('svn/(?P<revision>[0-9]+)')
def svnRevision(handler, revision):
	revision = int(revision)
	handler.title("SVN revision %d" % revision)

	from Privilege import dev
	dev(handler)
