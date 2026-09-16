from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RequestSpec


class RelayStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.home() / ".relay"
        self.root.mkdir(parents=True, exist_ok=True)
        self.history_path = self.root / "history.json"
        self.saved_path = self.root / "saved.json"

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def _write(path: Path, items: list[dict[str, Any]]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    def history(self) -> list[dict[str, Any]]:
        return self._read(self.history_path)

    def add_history(self, spec: RequestSpec, status: int | None = None, elapsed_ms: float | None = None) -> None:
        items = self.history()
        items.insert(0, {"request": spec.to_dict(), "status": status, "elapsed_ms": elapsed_ms})
        self._write(self.history_path, items[:80])

    def saved(self) -> list[dict[str, Any]]:
        return self._read(self.saved_path)

    def save_request(self, name: str, spec: RequestSpec) -> None:
        name = name.strip() or f"{spec.method} {spec.url}"
        items = [item for item in self.saved() if item.get("name") != name]
        items.insert(0, {"name": name, "request": spec.to_dict()})
        self._write(self.saved_path, items)

    def delete_saved(self, name: str) -> None:
        self._write(self.saved_path, [item for item in self.saved() if item.get("name") != name])
