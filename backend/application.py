"""Elastic Beanstalk WSGI entrypoint.

EB's Python platform looks for a callable named ``application`` (configured via
``WSGIPath: application:application`` in ``.ebextensions/02_python.config``).
Gunicorn's Uvicorn worker serves this same object — see ``Procfile``.
"""

from main import app

application = app
