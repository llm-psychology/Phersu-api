import os
from pathlib import Path
API_DATA_DIR = Path(os.getenv("API_DATA_DIR", "data/api")).resolve()
STATIC_DIR = Path(__file__).with_name("static")
