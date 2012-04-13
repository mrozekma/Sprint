from BaseHTTPServer import HTTPServer
from HTTPHandler import HTTPHandler
from Cron import Cron
from Settings import PORT
from Update import check

check()

server = HTTPServer(('', PORT), HTTPHandler)
Cron.start()
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
