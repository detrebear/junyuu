# junyuu

Skip the 4chan 120s delay by preloading the captcha challenge.

You'll need `xorg-server-xvfb`, `camoufox` and to add `userscript.js` to your browser. \
Then, run `main.py` and wait for the threads to process.

> [!WARNING]
> Don't expect this to work forever. The code is just a prototype and because currently it's synchronous, if you preload too many boards it probably won't work.
