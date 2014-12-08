from json import dumps as toJS

from WebSocket import WebSocket, PORT

@get('dyn.js')
def dynJS(handler):
	handler.wrappers = False
	handler.log = False
	handler.contentType = 'text/javascript'

	print "function get_websocket_port() {return %s;}" % toJS(PORT if WebSocket.available() else False)
