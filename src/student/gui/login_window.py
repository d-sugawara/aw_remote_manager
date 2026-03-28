"""
gui/login_window.py - Googleログイン画面
"""

import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from PIL import Image, ImageDraw, ImageTk

import config
import i18n


# ──────────────────────────────────────────────
# カラーパレット
# ──────────────────────────────────────────────
BG = "#0d0d1a"
CARD = "#1a1a2e"
ACCENT = "#4285F4"
ACCENT_DARK = "#2a6dd9"
BTN_FG = "#ffffff"
TEXT = "#e8e8f0"
SUBTEXT = "#8888aa"
ERROR_COLOR = "#ff5555"
SUCCESS_COLOR = "#55cc88"


def _make_logo() -> Image.Image:
    """カメラ + Gマーク風のロゴ画像を生成"""
    size = 88
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 背景円グラデーション風（単色）
    d.ellipse([0, 0, size - 1, size - 1], fill=(66, 133, 244, 255))

    # カメラボディ
    d.rounded_rectangle([14, 26, 74, 66], radius=6, fill=(255, 255, 255, 255))

    # レンズ外枠
    d.ellipse([28, 30, 60, 62], fill=(66, 90, 200, 255))
    # レンズ中心
    d.ellipse([34, 36, 54, 56], fill=(255, 255, 255, 255))
    # レンズ輝点
    d.ellipse([36, 38, 43, 45], fill=(200, 220, 255, 200))

    # フラッシュ
    d.rounded_rectangle([60, 26, 72, 36], radius=2, fill=(255, 255, 255, 255))

    return img


class LoginWindow:
    """Google OAuth ログイン画面"""

    def __init__(self, parent: tk.Tk, app: "Any") -> None:  # noqa: F821
        self.parent = parent
        self.app = app

        self.win = tk.Toplevel(parent)
        self.win.title(i18n.t("login_title"))
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)  # 閉じさせない

        W, H = 460, 540
        self.win.geometry(f"{W}x{H}")
        self._center(W, H)
        self._build()
        self.win.lift()
        self.win.focus_force()

    # ──────────────────────────────────────────
    # レイアウト構築
    # ──────────────────────────────────────────

    def _build(self) -> None:
        root = self.win

        # ── ロゴ ──
        logo_pil = _make_logo()
        self._logo_img = ImageTk.PhotoImage(logo_pil)
        tk.Label(root, image=self._logo_img, bg=BG).pack(pady=(52, 0))

        # ── タイトル ──
        tk.Label(
            root,
            text=i18n.t("app_name"),
            bg=BG, fg=TEXT,
            font=tkfont.Font(family="Segoe UI", size=20, weight="bold"),
        ).pack(pady=(14, 2))

        tk.Label(
            root,
            text=i18n.t("login_subtitle"),
            bg=BG, fg=SUBTEXT,
            font=tkfont.Font(family="Segoe UI", size=11),
        ).pack(pady=(0, 30))

        # ── カード ──
        card = tk.Frame(root, bg=CARD, padx=36, pady=28)
        card.pack(padx=44, fill="x")

        # エラー / ステータスメッセージ
        self._msg_var = tk.StringVar()
        self._msg_color_var = ERROR_COLOR
        self._msg_label = tk.Label(
            card,
            textvariable=self._msg_var,
            bg=CARD, fg=ERROR_COLOR,
            font=tkfont.Font(family="Segoe UI", size=10),
            wraplength=340, justify="center",
        )

        # Google サインインボタン
        self._btn = tk.Button(
            card,
            text=i18n.t("google_login"),
            bg=ACCENT, fg=BTN_FG,
            font=tkfont.Font(family="Segoe UI", size=12, weight="bold"),
            relief="flat", bd=0, padx=20, pady=0,
            cursor="hand2",
            activebackground=ACCENT_DARK,
            activeforeground=BTN_FG,
            command=self._on_click,
        )
        self._btn.pack(fill="x", ipady=12)
        self._btn.bind("<Enter>", lambda _: self._btn.config(bg=ACCENT_DARK))
        self._btn.bind("<Leave>", lambda _: self._btn.config(bg=ACCENT))

        # フッター
        tk.Label(
            root,
            text=i18n.t("powered_by"),
            bg=BG, fg=SUBTEXT,
            font=tkfont.Font(family="Segoe UI", size=9),
        ).pack(pady=(14, 0))

    # ──────────────────────────────────────────
    # ユーティリティ
    # ──────────────────────────────────────────

    def _center(self, w: int, h: int) -> None:
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

    def _set_msg(self, text: str, color: str = ERROR_COLOR) -> None:
        self._msg_label.config(fg=color)
        self._msg_var.set(text)
        self._msg_label.pack(pady=(0, 14))

    def _clear_msg(self) -> None:
        self._msg_var.set("")
        self._msg_label.pack_forget()

    def show_error(self, message: str) -> None:
        """外部からエラーメッセージを表示"""
        self._set_msg(message, ERROR_COLOR)
        self._btn.config(state="normal", text=i18n.t("google_login"))

    # ──────────────────────────────────────────
    # Google 認証フロー
    # ──────────────────────────────────────────

    def _on_click(self) -> None:
        cid = config.get("google_client_id", "")
        csecret = config.get("google_client_secret", "")
        if (
            not cid
            or cid == "YOUR_CLIENT_ID.apps.googleusercontent.com"
            or not csecret
            or csecret == "YOUR_CLIENT_SECRET"
        ):
            self._set_msg(i18n.t("config_error"), ERROR_COLOR)
            return

        self._btn.config(state="disabled", text=i18n.t("authenticating"))
        self._clear_msg()
        self._set_msg(i18n.t("open_browser_hint"), SUBTEXT)
        self._msg_label.config(fg=SUBTEXT)

        threading.Thread(target=self._do_auth, daemon=True).start()

    def _do_auth(self) -> None:
        import os
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            client_config = {
                "installed": {
                    "client_id": config.get("google_client_id"),
                    "client_secret": config.get("google_client_secret"),
                    "redirect_uris": ["http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            scopes = ["openid", "email", "profile"]
            flow = InstalledAppFlow.from_client_config(client_config, scopes)
            credentials = flow.run_local_server(port=0, open_browser=True)

            id_token: Optional[str] = credentials.id_token
            if not id_token:
                raise ValueError("Google から ID トークンが取得できませんでした")

            # バックエンドへ送信
            from api_client import APIClient, APIError

            client = APIClient(config.get("base_url", "http://localhost:8000"))
            result = client.login_with_google(id_token)

            token = result.get("token", "")
            student_number = result.get("student_number", "")
            self.win.after(0, lambda: self._on_success(token, student_number))

        except Exception as e:
            msg = str(e)
            self.win.after(0, lambda m=msg: self.show_error(m))

    def _on_success(self, token: str, student_number: str) -> None:
        self.win.withdraw()
        self.app.on_login_success(token, student_number)

    def destroy(self) -> None:
        try:
            self.win.destroy()
        except Exception:
            pass
