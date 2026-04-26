import os
import sys

# Добавляем путь к backend директории
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app

# Vercel requires a variable named "app" to be exported
# This will be used as the entry point for the server