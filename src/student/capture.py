"""
capture.py - スクリーンキャプチャ・ウィンドウ一覧取得
"""

import base64
import io
from typing import Any, Dict, List, Optional

import mss
from PIL import Image

try:
    import win32gui
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False


# ──────────────────────────────────────────────
# 内部ユーティリティ
# ──────────────────────────────────────────────

def _to_b64(img: Image.Image, quality: int = 70) -> str:
    """PIL Image を base64 JPEG 文字列に変換"""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _grab(region: dict) -> Image.Image:
    """mss で指定領域をキャプチャして PIL Image を返す"""
    with mss.mss() as sct:
        shot = sct.grab(region)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


# ──────────────────────────────────────────────
# キャプチャ（ base64 返却）
# ──────────────────────────────────────────────

def capture_fullscreen() -> str:
    """全モニター結合キャプチャ → base64 JPEG"""
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[0])   # monitors[0] = 全モニター結合
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return _to_b64(img)


def capture_window(hwnd: int) -> str:
    """指定 HWND のウィンドウをキャプチャ → base64 JPEG"""
    if not _HAS_WIN32:
        return capture_fullscreen()
    try:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, h = r - l, b - t
        if w <= 0 or h <= 0:
            return capture_fullscreen()
        img = _grab({"top": t, "left": l, "width": w, "height": h})
        return _to_b64(img)
    except Exception:
        return capture_fullscreen()


# ──────────────────────────────────────────────
# サムネイル（ PIL Image 返却）
# ──────────────────────────────────────────────

_THUMB_SIZE = (240, 135)


def get_fullscreen_thumbnail() -> Optional[Image.Image]:
    """全画面サムネイル"""
    try:
        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            img.thumbnail(_THUMB_SIZE, Image.LANCZOS)
            return img
    except Exception:
        return None


def get_window_thumbnail(hwnd: int) -> Optional[Image.Image]:
    """ウィンドウサムネイル"""
    if not _HAS_WIN32:
        return None
    try:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, h = r - l, b - t
        if w <= 0 or h <= 0:
            return None
        img = _grab({"top": t, "left": l, "width": w, "height": h})
        img.thumbnail(_THUMB_SIZE, Image.LANCZOS)
        return img
    except Exception:
        return None


# ──────────────────────────────────────────────
# ウィンドウ一覧
# ──────────────────────────────────────────────

def list_windows() -> List[Dict[str, Any]]:
    """表示中の通常ウィンドウ一覧を返す [{hwnd, title}, ...]"""
    if not _HAS_WIN32:
        return []

    results: List[Dict[str, Any]] = []

    def _cb(hwnd: int, _: Any) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.IsIconic(hwnd):   # 最小化は除外
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            if (r - l) < 100 or (b - t) < 100:   # 極小ウィンドウを除外
                return
        except Exception:
            return
        results.append({"hwnd": hwnd, "title": title})

    win32gui.EnumWindows(_cb, None)
    return results
