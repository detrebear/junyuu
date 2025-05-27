import sys
import requests
import time
import os
import json
from threading import Thread
from preloader import Preloader
from server import Server

refresh = 20*60
update = 60
save = 10
host = "127.0.0.1"
port = 1337
file = "tickets.json"
boards = ["g"]
headless = True
args = sys.argv[1:]
while len(args) > 0:
	arg = args.pop(0)
	if arg in ["-h", "--help"]:
		print(
			f"Usage: {sys.argv[0]} [OPTION...] [BOARD...]\n\n" +
			f"Options:\n" +
			f"  -a HOST     Bind HTTP server to address (default: 127.0.0.1) \n" +
			f"  -p PORT     Bind HTTP server to port (default: 1337) \n" +
			f"  -o FILE     File to save the tickets to (default: tickets.json)\n" +
			f"  -s SECONDS  Delay between tickets saves (default: 10s)\n" +
			f"  -r SECONDS  Delay between tickets refreshes (default: 20min)\n" +
			f"  -u SECONDS  Delay between thread list updates (default: 1min)\n" +
			f"  -w          Show browser window\n" +
			f"  -h, --help  Show this help message"
		)
		exit()
	elif arg == "-w":
		headless = False
	elif arg == "-a":
		host = args.pop(0)
	elif arg == "-p":
		port = int(args.pop(0))
	elif arg == "-r":
		refresh = int(args.pop(0))
	elif arg == "-u":
		update = int(args.pop(0))
	elif arg == "-s":
		save = int(args.pop(0))
	elif arg == "-o":
		file = args.pop(0)
	else:
		boards.append(arg)

# API Rule 2
update = max(update, 10)
refresh = max(refresh, 10)

def server(address, port, tickets):
	server = Server(address, port, tickets)
	server.serve_forever()

def saver(tickets, delay):
	while True:
		with open(file, "w") as f:
			json.dump(tickets, f)
		time.sleep(delay)

tickets = {}
if os.path.isfile(file):
	with open(file, "r") as f:
		tickets = json.load(f)

Thread(target=server, args=(host, port, tickets)).start()
Thread(target=saver, args=(tickets, save)).start()

preloader = Preloader(headless=headless)
last_refresh = 0
last_update = 0
while True:
	now = time.time()
	if now - last_update >= update:
		since = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(last_update))	# API Rule 3
		for board in boards:
			print(f"==> Performing update of /{board}/...")
			response = requests.get(f"https://a.4cdn.org/{board}/threads.json", headers={"If-Modified-Since": since})
			if response.status_code == 304:
				continue
			assert response.ok

			available_threads = {
				f"{thread["no"]}"
				for page in response.json()
				for thread in page["threads"]
			}
			for thread_id in list(tickets.get(board, {}).keys()):
				if thread_id not in available_threads:	# Remove dead threads
					tickets[board].pop(thread_id)

			missing_threads = {
				thread for thread in available_threads
				if thread not in tickets.get(board, {})	# Was already fetched, let the refresh logic handle it
			}
			for i, thread_id in enumerate(missing_threads):
				print(f"{i}/{len(missing_threads)}", end="\r")
				tickets.setdefault(board, {})[thread_id] = preloader.trigger(board, thread_id)
				time.sleep(1)	# API Rule 1

		last_update = now

	if now - last_refresh >= refresh:
		for board in boards:
			print(f"==> Performing refresh of /{board}/...")
			for thread_id in tickets.get(board, {}):
				print(f"{i}/{len(tickets[board])}", end="\r")
				tickets[board][thread_id] = preloader.trigger(board, thread_id)
				time.sleep(1)

		last_refresh = now

	time.sleep(1)
