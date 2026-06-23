import sys, os

project_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from asgiref.wsgi import WsgiToAsgi
from app.main import app

# Wrap FastAPI ASGI app for WSGI (PythonAnywhere compatibility)
from mangum import Mangum
application = Mangum(app, lifespan="off")
