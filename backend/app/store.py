from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_STORE_PATH = BASE_DIR / "data" / "store.json"


class JsonStore:
    def __init__(self, store_path: str | None = None) -> None:
        # Проверяем, выполняемся ли мы в среде Vercel
        self.is_vercel = bool(os.environ.get('VERCEL_ENV'))

        if self.is_vercel:
            # В среде Vercel используем переменные окружения для хранения данных
            self.store_key = "STORE_DATA"
        else:
            # В локальной среде используем файловое хранилище
            configured_path = store_path or os.getenv("STORE_PATH")
            if configured_path:
                path = Path(configured_path)
                self.store_path = path if path.is_absolute() else BASE_DIR / configured_path
            else:
                self.store_path = DEFAULT_STORE_PATH

            # Создаем директорию для хранения только в локальной среде
            self.store_path.parent.mkdir(parents=True, exist_ok=True)

        self._ensure_exists()

    def _ensure_exists(self) -> None:
        if not self.is_vercel:
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
        if self.is_vercel:
            # Читаем данные из переменной окружения
            data_str = os.environ.get(self.store_key, "")
            if data_str:
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError:
                    pass
            # Если нет данных, возвращаем пустую структуру
            return {"filials": []}
        else:
            with self.store_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def write(self, data: dict[str, Any]) -> None:
        if self.is_vercel:
            # В среде Vercel данные не сохраняются между вызовами,
            # поэтому просто обновляем в памяти
            # В production среде следует использовать внешнее хранилище
            os.environ[self.store_key] = json.dumps(data, ensure_ascii=False)
        else:
            with self.store_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

