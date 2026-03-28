"""
app.py - アプリケーションコア

・Tkinter (main thread) + pystray (daemon thread) を協調動作させる
・1 秒ごとのキャプチャループを別スレッドで実行
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional

import pystray
from PIL import Image, ImageDraw

import config
import i18n
from api_client import APIClient, APIError


# ──────────────────────────────────────────────────────────────────────
# トレイアイコン画像生成
# ──────────────────────────────────────────────────────────────────────

def _make_tray_icon() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 背景円
    d.ellipse([0, 0, size - 1, size - 1], fill=(66, 133, 244, 255))
    # カメラボディ
    d.rounded_rectangle([10, 20, 54, 48], radius=4, fill=(255, 255, 255, 240))
    # レンズ外
    d.ellipse([22, 24, 42, 44], fill=(66, 90, 200, 255))
    # レンズ中
    d.ellipse([27, 29, 37, 39], fill=(255, 255, 255, 255))
    # フラッシュ
    d.rounded_rectangle([46, 20, 54, 28], radius=2, fill=(255, 255, 255, 255))
    return img


# ──────────────────────────────────────────────────────────────────────
# App クラス
# ──────────────────────────────────────────────────────────────────────

class App:
    def __init__(self) -> None:
        # 設定読み込み・i18n 初期化
        cfg = config.load()
        i18n.set_lang(cfg.get("language", "ja"))

        # Tkinter ルート（不可視）
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("AW Remote Manager")

        # キャプチャ制御
        self._capturing = False
        self._capture_target: Optional[Dict[str, Any]] = None   # None = 全画面
        self._capture_lock = threading.Lock()

        # トレイアイコン
        self._icon: Optional[pystray.Icon] = None

        # ウィンドウ参照
        self._login_win: Any = None
        self._selector_win: Any = None

    # ──────────────────────────────────────────
    # 起動
    # ──────────────────────────────────────────

    def run(self) -> None:
        # 起動直後に認証確認をスケジュール
        self.root.after(200, self._check_auth_and_start)

        # pystray を daemon スレッドで起動
        threading.Thread(target=self._run_tray, daemon=True).start()

        # Tkinter メインループ
        self.root.mainloop()

    # ──────────────────────────────────────────
    # 認証確認
    # ──────────────────────────────────────────

    def _check_auth_and_start(self) -> None:
        token = config.get("token", "")
        if not token:
            self._show_login()
            return

        def _check() -> None:
            try:
                base_url = config.get("base_url", "http://localhost:8000")
                client = APIClient(base_url, token)
                client.check_auth()
                # 有効 → キャプチャ開始
                self.root.after(0, self._start_capture)
                self._notify(i18n.t("startup_balloon"))
            except APIError as e:
                self.root.after(0, lambda msg=e.message: self._show_login(msg))

        threading.Thread(target=_check, daemon=True).start()

    # ──────────────────────────────────────────
    # ログイン
    # ──────────────────────────────────────────

    def _show_login(self, error_message: Optional[str] = None) -> None:
        from gui.login_window import LoginWindow
        if self._login_win is not None:
            try:
                self._login_win.win.deiconify()
                if error_message:
                    self._login_win.show_error(error_message)
            except Exception:
                self._login_win = None

        if self._login_win is None:
            self._login_win = LoginWindow(self.root, self)
            if error_message:
                self._login_win.show_error(error_message)

    def on_login_success(self, token: str, student_number: str) -> None:
        """LoginWindow から呼ばれるコールバック"""
        config.update(token=token, student_number=student_number)
        self._login_win = None
        self._start_capture()
        self._notify(i18n.t("login_success_balloon"))

    # ──────────────────────────────────────────
    # キャプチャループ
    # ──────────────────────────────────────────

    def _start_capture(self) -> None:
        if self._capturing:
            return
        self._capturing = True
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _stop_capture(self) -> None:
        self._capturing = False

    def _capture_loop(self) -> None:
        import capture as cap

        while self._capturing:
            try:
                token = config.get("token", "")
                student_number = config.get("student_number", "")
                base_url = config.get("base_url", "http://localhost:8000")

                if not token or not student_number:
                    time.sleep(1)
                    continue

                with self._capture_lock:
                    target = self._capture_target

                if target is None or target.get("type") == "fullscreen":
                    image_b64 = cap.capture_fullscreen()
                else:
                    image_b64 = cap.capture_window(target["hwnd"])

                client = APIClient(base_url, token)
                client.upload_capture(student_number, image_b64)

            except APIError:
                pass
            except Exception:
                pass

            time.sleep(1)

    def set_capture_target(self, target: Dict[str, Any]) -> None:
        with self._capture_lock:
            self._capture_target = target

    # ──────────────────────────────────────────
    # システムトレイ
    # ──────────────────────────────────────────

    def _run_tray(self) -> None:
        icon_img = _make_tray_icon()
        self._icon = pystray.Icon(
            "AW Remote Manager",
            icon_img,
            "AW Remote Manager",
            menu=self._build_menu(),
        )
        self._icon.run()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: i18n.t("select_capture"),
                self._menu_select_capture,
            ),
            pystray.MenuItem(
                lambda item: i18n.t("logout"),
                self._menu_logout,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: i18n.t("language"),
                pystray.Menu(
                    pystray.MenuItem(
                        lambda item: i18n.t("language_ja"),
                        lambda: self._set_lang("ja"),
                        checked=lambda item: i18n.get_lang() == "ja",
                        radio=True,
                    ),
                    pystray.MenuItem(
                        lambda item: i18n.t("language_en"),
                        lambda: self._set_lang("en"),
                        checked=lambda item: i18n.get_lang() == "en",
                        radio=True,
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: i18n.t("exit"),
                self._menu_exit,
            ),
        )

    # ──────────────────────────────────────────
    # メニューアクション
    # ──────────────────────────────────────────

    def _menu_select_capture(self, icon=None, item=None) -> None:
        self.root.after(0, self._show_capture_selector)

    def _show_capture_selector(self) -> None:
        from gui.capture_selector import CaptureSelectorWindow
        CaptureSelectorWindow(self.root, self)

    def _menu_logout(self, icon=None, item=None) -> None:
        self.root.after(0, self._do_logout_dialog)

    def _do_logout_dialog(self) -> None:
        result = messagebox.askokcancel(
            i18n.t("logout_confirm_title"),
            i18n.t("logout_confirm"),
            parent=self.root,
        )
        if not result:
            return

        def _logout() -> None:
            try:
                token = config.get("token", "")
                base_url = config.get("base_url", "http://localhost:8000")
                client = APIClient(base_url, token)
                client.logout()
                config.clear_token()
                self._stop_capture()
                self.root.after(0, self._show_login)
                self._notify(i18n.t("logout_success_balloon"))
            except APIError as e:
                self._notify(f"{i18n.t('logout_failed_balloon')}: {e.message}")

        threading.Thread(target=_logout, daemon=True).start()

    def _set_lang(self, lang: str) -> None:
        i18n.set_lang(lang)
        config.update(language=lang)
        # メニューを再構築して即反映
        if self._icon:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()

    def _menu_exit(self, icon=None, item=None) -> None:
        self._stop_capture()
        if self._icon:
            self._icon.stop()
        self.root.after(0, self.root.quit)

    # ──────────────────────────────────────────
    # バルーン通知
    # ──────────────────────────────────────────

    def _notify(self, message: str) -> None:
        def show() -> None:
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(i18n.t("app_name"), message, duration=5, threaded=False)
            except Exception:
                if self._icon and self._icon.HAS_NOTIFICATION:
                    try:
                        self._icon.notify(message, i18n.t("app_name"))
                    except Exception:
                        pass
        threading.Thread(target=show, daemon=True).start()
