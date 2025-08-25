# api/index.py — punto de entrada para Vercel Serverless con Flask

import os
import sys

# Directorios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../api
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))       # proyecto
SRC_DIR  = os.path.join(ROOT_DIR, "src")                       # .../src

# Aseguramos que /src esté en sys.path
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Importamos la app Flask desde src/app.py
from app import app
