# Vercel Serverless Function entry for Flask

import os, sys
from app import app
from src.app import app

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    # Import the Flask app object from your original app
    from app import app  # 'src' is on path, so 'app.py' inside src is importable
except Exception as e:
    # Fallback: create a minimal app to expose error
    from flask import Flask
    app = Flask(__name__)
    @app.get("/")
    def _fallback():
        return f"Error importando app original: {e}", 500
