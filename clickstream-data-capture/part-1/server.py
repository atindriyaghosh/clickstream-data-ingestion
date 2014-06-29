from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from time import gmtime, strftime
import urlparse
import logging
import logging.handlers
import uuid
import Cookie

logger = logging.getLogger('')
logger.setLevel(logging.INFO)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler('/var/log/tracking_logs/server.log', maxBytes=10485760, backupCount=20)
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class TrackingPixelHandler(BaseHTTPRequestHandler):	
    def do_GET(self):
		parsed_path = urlparse.urlparse(self.path)
		path = parsed_path.path
		
		if(path == '/_.gif'):
			logEvent(self, parsed_path)
			self.send_response(200)
			self.end_headers()
			
		if(path == '/index.html'):
			servePage(self)

def logEvent(self, parsed_path):
	## Generate Event Id
	event_id = uuid.uuid1()
	
	## Get Server Time
	server_time = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
	
	## Get context_id from Cookie
	user_id = "-"
	if "Cookie" in self.headers:
		cookie = Cookie.SimpleCookie(self.headers["Cookie"])
		try:
			user_id = cookie['user_id'].value
		except KeyError:
			print 'No user_id set in cookie'
	
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
	event = "event_id=%s%suser_id=%s%spage_name=%s%saction=%s%sserver_time=%s" % (event_id, delimiter, user_id, delimiter, page_name, delimiter, action, delimiter, server_time)
	
	## Log event
	print event
	logger.info(event)

def generateUserId(self):
	cookie = Cookie.SimpleCookie()
	user_id = uuid.uuid4()
	cookie["user_id"] = user_id
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
				user_id = cookie['user_id'].value
				self.end_headers()
			except KeyError:
				generateUserId(self)
		else:
			generateUserId(self)
		self.end_headers()
		self.wfile.write(f.read())
	except IOError:
		self.send_error(404, 'file not found')
		
if __name__ == '__main__':    
    server = HTTPServer(('', 9000), TrackingPixelHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
