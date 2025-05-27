import json
import time
from playwright.sync_api import TimeoutError
from camoufox.sync_api import Camoufox

class Preloader:
	def __init__(self, headless=True):
		self.manager = Camoufox(os="windows", humanize=0.4, headless=headless)
		self.browser = self.manager.__enter__()
		self.context = self.browser.new_context()

	def __del__(self):
		self.context.close()
		self.browser.close()
		self.manager.__exit__()

	def trigger(self, board, thread_id, previous_ticket=""):
		url = f"https://sys.4chan.org/captcha?board={board}&thread_id={thread_id}&ticket={previous_ticket}"

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

		page.wait_for_load_state("domcontentloaded")
		response = page.locator("body > pre")
		response.wait_for()
		twister = json.loads(response.text_content())
		page.close()

		cookie = next(filter(lambda cookie: cookie["name"] == "cf_clearance", self.context.cookies("https://4chan.org")))
		update = {
			"ticket": twister.get("ticket") or previous_ticket,
			"cf_clearance": cookie["value"],
			"wait": twister.get("pcd") or twister.get("cd") or (twister.get("challenge") and 0),
			"msg": twister.get("pcd_msg") or twister.get("error") or (twister.get("challenge") and "Success"),
			"stop": twister.get("error") != None and twister.get("cd") != None,
			"time": time.time()
		}
		return {key: value for key, value in update.items() if value != None}
