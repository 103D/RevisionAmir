from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_STORE_PATH = BASE_DIR / "data" / "store.json"


class JsonStore:
    def __init__(self, store_path: str | None = None) -> None:
        configured_path = store_path or os.getenv("STORE_PATH")
        if configured_path:
            path = Path(configured_path)
            self.store_path = path if path.is_absolute() else BASE_DIR / configured_path
        else:
            self.store_path = DEFAULT_STORE_PATH

        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        if not self.store_path.exists():
            self.write({"filials": []})
            return

        try:
            current = self.read()
        except (json.JSONDecodeError, OSError):
            self.write({"filials": []})
            return

        if "filials" not in current or not isinstance(current["filials"], list):
            current["filials"] = []
            self.write(current)

    def read(self) -> dict[str, Any]:
        with self.store_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def write(self, data: dict[str, Any]) -> None:
        with self.store_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)