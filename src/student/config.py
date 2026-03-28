"""
config.py - 設定ファイル読み書き管理

PyInstaller --onefile でビルドした場合、config.json は
exe と同じディレクトリに配置される。
"""

import json
import os
import sys
from typing import Any

_DEFAULTS: dict = {
    "base_url": "http://localhost:8000",
    "token": "",
    "student_number": "",
    "language": "ja",
    "google_client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "google_client_secret": "YOUR_CLIENT_SECRET",
}

_cache: dict | None = None


def _path() -> str:
    """config.json の絶対パスを返す。exe/スクリプト両対応。"""
    if getattr(sys, "frozen", False):
        # PyInstaller でビルドされた exe
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    # スクリプトとして実行
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load() -> dict:
    """設定ファイルを読み込んでキャッシュする。"""
    global _cache
    p = _path()
    if not os.path.exists(p):
        _cache = _DEFAULTS.copy()
        _write(_cache)
        return _cache.copy()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
        # 不足キーをデフォルト値で補完
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        _cache = data
        return _cache.copy()
    except Exception:
        _cache = _DEFAULTS.copy()
        return _cache.copy()


def _write(cfg: dict) -> None:
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def get(key: str, default: Any = None) -> Any:
    global _cache
    if _cache is None:
        load()
    return _cache.get(key, default)  # type: ignore[union-attr]


def update(**kwargs: Any) -> None:
    global _cache
    cfg = load()
    cfg.update(kwargs)
    _cache = cfg
    _write(cfg)


def clear_token() -> None:
    update(token="", student_number="")
