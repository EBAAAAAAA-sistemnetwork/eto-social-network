import sys, os
sys.path.insert(0, '/home/THIS26/eto-social-network/backend')

from mangum import Mangum
from app.main import app

api_handler = Mangum(app, lifespan="off")
FRONTEND_DIR = '/home/THIS26/eto-social-network/frontend/dist'

MIME = {
    '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
    '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2',
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    if path.startswith('/api/'):
        return api_handler(environ, start_response)
    if path.startswith('/assets/'):
        safe = path.replace('..', '').lstrip('/')
        filepath = os.path.join(FRONTEND_DIR, safe)
        if os.path.isfile(filepath):
            ext = os.path.splitext(filepath)[1]
            start_response('200 OK', [('Content-Type', MIME.get(ext, 'text/plain'))])
            with open(filepath, 'rb') as f:
                return [f.read()]
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'not found']
    safe = path.replace('..', '').lstrip('/')
    filepath = os.path.join(FRONTEND_DIR, safe) if safe else os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.isfile(filepath) and safe:
        start_response('200 OK', [('Content-Type', 'text/html')])
        with open(filepath, 'rb') as f:
            return [f.read()]
    index = os.path.join(FRONTEND_DIR, 'index.html')
    start_response('200 OK', [('Content-Type', 'text/html')])
    with open(index, 'rb') as f:
        return [f.read()]
