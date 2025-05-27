import json
from playwright.sync_api import TimeoutError
from camoufox.sync_api import Camoufox

class Preloader:
	def __init__(self, headless=True):
		self.manager = Camoufox(os="windows", humanize=1.2, headless=headless)
		self.browser = self.manager.__enter__()
		self.context = self.browser.new_context()
		self.cache = {}

	def __del__(self):
		self.context.close()
		self.browser.close()
		self.manager.__exit__()

	def trigger(self, board, thread_id):
		ticket = self.cache.get(board, {}).get(thread_id, {}).get("ticket")
		url = f"https://sys.4chan.org/captcha?board={board}&thread_id={thread_id}&ticket={ticket or ""}"

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

		response = page.locator("body > pre")
		response.wait_for()
		twister = json.loads(response.text_content())

		update = {
			"ticket": twister.get("ticket"),
			"cf_clearance": None,	# TODO
			"pcd": twister.get("pcd") or (twister.get("challenge") and 0),
			"pcd_msg": twister.get("pcd_msg") or (twister.get("challenge") and "Success")
		}
		self.cache \
			.setdefault(board, {}) \
			.setdefault(thread_id, {}) \
			.update({key: value for key, value in update.items() if value != None})
		return self.cache[board][thread_id]
