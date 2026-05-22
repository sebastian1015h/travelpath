import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.infrastructure.config.dependencies import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
