"""
config.py - 設定ファイル読み書き管理 (暗号化対応)

PyInstaller --onefile でビルドした場合、config.enc は
exe と同じディレクトリに配置される。
"""

import json
import os
import sys
import base64
from typing import Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

_DEFAULTS: dict = {
    "base_url": "http://localhost:8000",
    "token": "",
    "student_number": "",
    "language": "ja",
    "google_client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "google_client_secret": "YOUR_CLIENT_SECRET",
}

_cache: dict | None = None
_SECRET_KEY = b'AwRemoteManagerSecretKey202611!!' # 32 bytes


def _path(ext: str = "enc") -> str:
    """設定ファイルの絶対パスを返す。"""
    filename = f"config.{ext}"
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def _encrypt_data(cfg: dict) -> bytes:
    data_bytes = json.dumps(cfg, ensure_ascii=False).encode('utf-8')
    iv = os.urandom(16)
    cipher = AES.new(_SECRET_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(data_bytes, AES.block_size))
    return base64.b64encode(iv + ciphertext)


def _decrypt_data(payload: bytes) -> dict:
    raw = base64.b64decode(payload)
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(_SECRET_KEY, AES.MODE_CBC, iv)
    data = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
    return json.loads(data)


def load() -> dict:
    """設定ファイルを読み込んでキャッシュする。"""
    global _cache
    enc_path = _path("enc")
    json_path = _path("json")

    # レガシーな config.json が存在する場合は読み込んでから enc へ移行し json を削除
    if os.path.exists(json_path) and not os.path.exists(enc_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _write(data)
            os.remove(json_path)
            _cache = data
            return _cache.copy()
        except Exception:
            pass

    if not os.path.exists(enc_path):
        _cache = _DEFAULTS.copy()
        _write(_cache)
        return _cache.copy()

    try:
        with open(enc_path, "rb") as f:
            payload = f.read()
        data = _decrypt_data(payload)
        
        # 不足キーをデフォルト値で補完
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        _cache = data
        return _cache.copy()
    except Exception:
        _cache = _DEFAULTS.copy()
        return _cache.copy()


def _write(cfg: dict) -> None:
    enc_data = _encrypt_data(cfg)
    with open(_path("enc"), "wb") as f:
        f.write(enc_data)


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
