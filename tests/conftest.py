import sys
from pathlib import Path

# Ensure src/ is on sys.path for all tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
