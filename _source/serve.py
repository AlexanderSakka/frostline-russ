"""Serve the site locally the way GitHub Pages does, so /hoodie finds hoodie.html.

  python3 _source/serve.py            # http://127.0.0.1:8765/
  python3 _source/serve.py 8770
"""
import http.server, os, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Pages(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def send_head(self):
        path, _, rest = self.path.partition('?')
        local = os.path.join(ROOT, urllib.parse.unquote(path).lstrip('/'))
        if path != '/' and not os.path.exists(local) and os.path.exists(local + '.html'):
            self.path = path + '.html' + ('?' + rest if rest else '')
        return super().send_head()


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Pages).serve_forever()
