from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from datetime import datetime
import urlparse
import logging
import logging.handlers
import uuid
import Cookie
import os

logger = logging.getLogger('')
logger.setLevel(logging.INFO)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler('/home/ubuntu/event_ingestion/tracking_logs/server.log', maxBytes=10485760, backupCount=20)
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class TrackingPixelHandler(BaseHTTPRequestHandler):	
    def do_GET(self):
		parsed_path = urlparse.urlparse(self.path)
		path = parsed_path.path
		
		if(path == '/_.gif'):
			logEvent(self, parsed_path)
			
		if(path == '/index.html'):
			servePage(self)

def logEvent(self, parsed_path):
	## Generate Event Id
	event_id = uuid.uuid1()
	
	## Get Server Time
	now = datetime.utcnow()
	server_time = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-"  + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second)
	
	## Get context_id from Cookie
	context_id = "-"
	if "Cookie" in self.headers:
		cookie = Cookie.SimpleCookie(self.headers["Cookie"])
		try:
			context_id = cookie['context_id'].value
		except KeyError:
			print 'No context_id set in cookie'
	
	query_params = urlparse.parse_qs(parsed_path.query)
	
	## Get page_name from query parameters
	if(query_params.has_key('pageName')):
		page_name = query_params.get('pageName')[0]
	else:
		page_name = '-'
	
	## Get action from query parameters
	if(query_params.has_key('action')):
		action = query_params.get('action')[0]
	else:
		action = '-'
		
	## Set event delimiter to |
	delimiter = '|'
	
	## Construct event
	event = "event_id=%s%scontext_id=%s%spage_name=%s%saction=%s%sserver_time=%s" % (event_id, delimiter, context_id, delimiter, page_name, delimiter, action, delimiter, server_time)
	
	## Log event
	print event
	logger.info(event)
	self.send_response(200)
	self.end_headers()

def generateContextId(self):
	cookie = Cookie.SimpleCookie()
	context_id = uuid.uuid4()
	cookie["context_id"] = context_id
	print cookie.output()
	self.wfile.write(cookie.output())
	self.end_headers()
	
def servePage(self):
	try:
		f = open('index.html')
		self.send_response(200)
		self.send_header('Content-Type', 'text/html')
		if "Cookie" in self.headers:
			cookie = Cookie.SimpleCookie(self.headers["Cookie"])
			try:
				context_id = cookie['context_id'].value
				self.end_headers()
			except KeyError:
				generateContextId(self)
		else:
			generateContextId(self)
		self.end_headers()
		self.wfile.write(f.read())
	except IOError:
		self.send_error(404, 'file not found')
		
if __name__ == '__main__':    
    server = HTTPServer(('', 9000), TrackingPixelHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
