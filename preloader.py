import json
from time import time
from playwright.sync_api import TimeoutError
from camoufox.sync_api import Camoufox

EXPIRATION = 20*60
HEADLESS = False

class Preloader:
	def __init__(self):
		self.manager = Camoufox(os="windows", humanize=1.2, headless=HEADLESS)
		self.browser = self.manager.__enter__()
		self.context = self.browser.new_context()
		self.cache = {}

	def __del__(self):
		self.context.close()
		self.browser.close()
		self.manager.__exit__()

	def trigger(self, board, thread_id):
		url = f"https://sys.4chan.org/captcha?board={board}&thread_id={thread_id}"

		page = self.context.new_page()
		page.goto(url)
		page.wait_for_load_state("domcontentloaded")

		if page.evaluate("document.querySelector('body > h1') != null"):
			bypass = None
			def catch_captcha_bypass(frame):
				nonlocal bypass
				if frame.url.startswith("blob:https://challenges.cloudflare.com"):	# This iframe is within all the #shadow-root, so it lets us bypass them
					bypass = frame
					return True
				return False
			page.wait_for_event("framenavigated", catch_captcha_bypass)
			bypass.parent_frame.wait_for_load_state("domcontentloaded")
			captcha = bypass.frame_element().get_property("previousSibling")	# Bypass the closed shadow root to the main Cloudflare wrapper
			captcha.wait_for_selector("#verifying", state="hidden")
			captcha.click()

		result = page.locator("body > pre")
		result.wait_for()
		twister = json.loads(result.text_content())

		# TODO: Use this data to change the request at the start
		self.cache.setdefault(board, {})
		self.cache[board][thread_id] = {"time": time(), "twister": twister}

		return twister
