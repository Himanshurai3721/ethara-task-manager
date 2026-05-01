"""
Entry point for the Team Task Manager API.

Development:
    cd backend
    python run.py

Production (gunicorn):
    gunicorn "run:app" --bind 0.0.0.0:5000
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
