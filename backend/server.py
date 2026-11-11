"""Sahaay backend entrypoint.

The pod's supervisor runs `uvicorn server:app`, so the Flask (WSGI) app is wrapped
with asgiref's WsgiToAsgi adapter. For a plain local run, `python server.py`
starts Flask's built-in server instead — same routes, same behaviour.
"""
from asgiref.wsgi import WsgiToAsgi

from sahaay import create_app

flask_app = create_app()
# `app` is what uvicorn serves (server:app); it forwards every request to the Flask app.
app = WsgiToAsgi(flask_app)

if __name__ == "__main__":
    # Local / offline mode: python server.py  →  http://localhost:8001
    flask_app.run(host="0.0.0.0", port=8001, debug=True)
