from time import time
from camoufox.sync_api import Camoufox

EXPIRATION = 20*60
HEADLESS = False

class Preloader:
	def __init__(self):
		self.manager = Camoufox(os="windows", humanize=1.2, headless=HEADLESS)
		self.browser = self.manager.__enter__()
		self.cache = {}

	def __del__(self):
		self.manager.__exit__()

	def trigger(self, board, thread_id):
		url = f"https://sys.4chan.org/captcha?board={board}&thread_id={thread_id}"

		page = self.browser.new_page()
		page.goto(url)
		page.wait_for_load_state("domcontentloaded")

		child = None
		def catch_captcha_child(frame):
			nonlocal child
			if frame.url.startswith("blob:https://challenges.cloudflare.com"):	# This element is within all the #shadow-root, so it lets us bypass them
				child = frame
				return True
			return False
		page.wait_for_event("framenavigated", catch_captcha_child)
		child.parent_frame.wait_for_load_state("domcontentloaded")
		captcha = child.frame_element().get_property("previousSibling")	# Bypass the cloudflare closed shadow root
		captcha.wait_for_selector("#verifying", state="hidden")

		twister = None
		def handle_captcha_redirect(request):
			nonlocal twister
			return url in request.url and (twister := request.response().json()) or False
		captcha.click()
		page.wait_for_event("requestfinished", handle_captcha_redirect)

		# TODO: Use this data to change the request at the start
		self.cache.setdefault(board, {})
		self.cache[board][thread_id] = {"time": time(), "twister": twister}

		return twister
