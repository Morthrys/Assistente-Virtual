# storage.py
import os
import json
from typing import Any, Dict

# Pasta base onde ficam os arquivos
BASE_DIR = "data"
os.makedirs(BASE_DIR, exist_ok=True)

_storage: Dict[str, Dict[str, Any]] = {}

def _get_path(typ: str) -> str:
    """
    Monta o caminho do arquivo para um tipo
    """
    return os.path.join(BASE_DIR, f"{typ}_map.json")

def load_data() -> None:
    """
    Carrega os dados salvos
    """
    global _storage
    _storage = {}
    for fname in os.listdir(BASE_DIR):
        if fname.endswith("_map.json"):
            typ = fname.replace("_map.json", "")
            path = os.path.join(BASE_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _storage[typ] = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                _storage[typ] = {}

def save_data(typ: str) -> None:
    path = _get_path(typ)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_storage.get(typ, {}), f, indent=2, ensure_ascii=False)

def get_data(typ: str) -> Dict[str, Any]:
    if typ not in _storage:
        _storage[typ] = {}
    return _storage[typ]

def set_data(typ: str, key: str, value: Any) -> None:
    if typ not in _storage:
        _storage[typ] = {}
    _storage[typ][key] = value
    save_data(typ)

def delete_data(typ: str, key: str) -> None:
    if typ in _storage and key in _storage[typ]:
        del _storage[typ][key]
        save_data(typ)