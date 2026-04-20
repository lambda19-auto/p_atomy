import json
from pathlib import Path
from typing import TypedDict


class MemoryEntry(TypedDict):
    role: str
    text: str


class MemoryStore:
    def __init__(self, file_name: str = "memory.json"):
        self.path = Path.cwd() / file_name
        self.max_entries = 20
        self._data: dict[str, list[MemoryEntry]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = self._sanitize_loaded_data(raw)
            else:
                self._data = {}
        except (json.JSONDecodeError, OSError):
            self._data = {}
            self._save()

    def _sanitize_loaded_data(self, raw: dict[object, object]) -> dict[str, list[MemoryEntry]]:
        sanitized: dict[str, list[MemoryEntry]] = {}

        for user_key, history in raw.items():
            if not isinstance(user_key, str) or not isinstance(history, list):
                continue

            valid_entries: list[MemoryEntry] = []
            for entry in history:
                if not isinstance(entry, dict):
                    continue

                role = entry.get("role")
                text = entry.get("text")
                if isinstance(role, str) and isinstance(text, str):
                    valid_entries.append({"role": role, "text": text})

            sanitized[user_key] = valid_entries[-self.max_entries :]

        return sanitized

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
