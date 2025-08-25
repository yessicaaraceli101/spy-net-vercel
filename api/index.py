# api/index.py — punto de entrada para Vercel Serverless con Flask

import os
import sys
import logging

# === Config de paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # .../api
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))     # proyecto
SRC_DIR  = os.path.join(ROOT_DIR, "src")                     # .../src

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# === Logging verboso para ver errores en Vercel ===
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("api.index")

try:
    # Importa la app real desde src/app.py
    from app import app  # ← tu archivo src/app.py debe definir `app = Flask(__name__, ...)`
    # Modo debug para que los stacktraces aparezcan en Logs de Vercel
    app.config.setdefault("DEBUG", True)
    log.info("Flask app importada correctamente desde src/app.py")

except Exception as e:
    # Fallback: si falló el import, exponemos una mini app para ver el error
    log.exception("Error importando la app real desde src/app.py")
    from flask import Flask

    app = Flask(__name__)
    app.config["DEBUG"] = True

    @app.get("/")
    def _fallback_root():
        # Mostramos el error de import para que se vea en el navegador / logs
        return (
            "No se pudo importar la app real desde src/app.py. "
            "Revisá los logs de Vercel para el stacktrace.",
            500,
        )

    @app.get("/health")
    def _fallback_health():
        return {"ok": False, "reason": "import_failed"}, 500