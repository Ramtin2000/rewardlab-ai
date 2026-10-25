import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
RUNS_DIR = Path(os.environ.get("REWARDLAB_RUNS_DIR", REPO_ROOT / "runs"))
