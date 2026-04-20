import json
from pathlib import Path
from typing import TypedDict


class MemoryEntry(TypedDict):
    role: str
    text: str


class MemoryStore:
    def __init__(self, file_path: str = "memory.json", max_entries: int = 20):
        base_dir = Path(__file__).resolve().parent
        requested_path = Path(file_path)
        self.path = (
            requested_path
            if requested_path.is_absolute()
            else base_dir / requested_path
        )
        self.max_entries = max_entries
        self._data: dict[str, list[MemoryEntry]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = raw
        except (json.JSONDecodeError, OSError):
            self._data = {}
            self._save()

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_history(self, user_id: int) -> list[MemoryEntry]:
        return self._data.get(str(user_id), [])

    def add_pair(self, user_id: int, user_text: str, assistant_text: str) -> None:
        key = str(user_id)
        history = self._data.setdefault(key, [])
        history.extend(
            [
                {"role": "user", "text": user_text},
                {"role": "assistant", "text": assistant_text},
            ]
        )
        self._data[key] = history[-self.max_entries :]
        self._save()
