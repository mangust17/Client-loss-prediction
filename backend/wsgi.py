import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

# Только для локальной отладки (неиспользуется при gunicorn)
if __name__ == "__main__":
    app.run()
