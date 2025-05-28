// ==UserScript==
// @name        Junyuu-chan
// @description Preload Cloudflare captchas and 4chan delays
// @author      detrebear
// @version     0.1
// @namespace   https://github.com/detrebear/junyuu-chan
// @include     /https?:\/\/boards\.4chan\.org/[^/]+/thread/\d+/
// @grant       none
// ==/UserScript==

const HOST = "127.0.0.1";
const PORT = 1337;

(async () => {
	const [_, board, thread_id] = window.location.pathname.match(/\/([^/]+)\/thread\/(\d+)/);
	const response = await fetch(`http://${HOST}:${PORT}/?board=${board}&thread_id=${thread_id}`, {method: "GET"});
	if (response.status === 200) {
		const data = await response.json();
		window.localStorage.setItem("4chan-tc-ticket", data["ticket"]);
	}
})();
