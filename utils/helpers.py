import json
import random
from pathlib import Path


def load_json(path: str | Path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: str | Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def random_color() -> str:
    return f"#{random.randint(0, 0xFFFFFF):06x}"
