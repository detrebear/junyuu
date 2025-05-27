import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
	def __init__(self, *args, tickets={}, **kwargs):
		self.tickets = tickets
		super().__init__(*args, **kwargs)

	def do_GET(self):
		query = parse_qs(urlparse(self.path).query)
		board = query["board"][0]
		thread_id = query["thread_id"][0]

		data = self.tickets.get(board, {}).get(thread_id, None)
		if data != None:
			self.send_response(200)
		else:
			self.send_response(404)

		self.send_header("Access-Control-Allow-Origin", "*")
		self.send_header("Content-Type", "application/json")
		self.end_headers()

		self.wfile.write(json.dumps(data).encode("utf-8"))

class Server(HTTPServer):
	def __init__(self, address, port, tickets):
		class HandlerWrapper(Handler):
			def __init__(self, *args, **kwargs):
				super().__init__(*args, tickets=tickets, **kwargs)

		super().__init__((address, port), HandlerWrapper)
