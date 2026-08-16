from __future__ import annotations

import os
from pathlib import Path

def find_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config.yaml").is_file():
        return cwd
    here = Path(__file__).resolve().parent.parent
    if (here / "config.yaml").is_file():
        return here
    return cwd


ROOT = find_root()
OUT_DIR = ROOT / "out"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "shorts.db"
CONFIG_PATH = ROOT / "config.yaml"
ENV_PATH = ROOT / ".env"
CLIENT_SECRETS = ROOT / "client_secrets.json"
TOKEN_PATH = ROOT / "token.json"
CHANNELS = ("돈이웃", "offscn")
DEFAULT_CHANNEL = "돈이웃"


def channel_dir(channel: str) -> Path:
    if channel not in CHANNELS:
        raise SystemExit("채널은 %s 중 하나" % ", ".join(CHANNELS))
    return OUT_DIR / channel


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def load_config(path: Path = CONFIG_PATH) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML 필요. pip install -r requirements.txt") from exc
    if not path.is_file():
        raise SystemExit("config.yaml 없음: %s" % path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("config.yaml 형식 오류")
    return data


def auto_publish() -> bool:
    return os.environ.get("AUTO_PUBLISH", "0").strip() in {"1", "true", "TRUE", "yes"}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in CHANNELS:
        (OUT_DIR / name).mkdir(parents=True, exist_ok=True)
