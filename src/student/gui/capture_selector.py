"""
gui/capture_selector.py - キャプチャ対象選択画面

全画面 + 起動中ウィンドウをサムネイル付きで一覧表示し
選択結果を app.set_capture_target() に渡す。
"""

import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageTk

import capture as cap
import i18n


# ──────────────────────────────────────────────
# カラーパレット
# ──────────────────────────────────────────────
BG = "#0d0d1a"
CARD_NORMAL = "#1a1a2e"
CARD_HOVER = "#22224a"
CARD_SEL = "#16213e"
ACCENT = "#4285F4"
TEXT = "#e8e8f0"
SUBTEXT = "#8888aa"
BORDER_NORMAL = "#2a2a4a"
BORDER_SEL = "#4285F4"

THUMB_W, THUMB_H = 220, 124


def _placeholder_thumb() -> Image.Image:
    """サムネイル取得失敗時の代替画像"""
    img = Image.new("RGB", (THUMB_W, THUMB_H), (30, 30, 60))
    d = ImageDraw.Draw(img)
    d.text((THUMB_W // 2 - 20, THUMB_H // 2 - 8), "No Preview", fill=(100, 100, 140))
    return img


class _Card(tk.Frame):
    """1 つの選択肢カード（サムネイル + ラベル）"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        thumb: Optional[Image.Image],
        on_select: callable,
    ) -> None:
        super().__init__(parent, bg=CARD_NORMAL, padx=8, pady=8, cursor="hand2")
        self._on_select = on_select
        self._selected = False

        raw = thumb if thumb is not None else _placeholder_thumb()
        raw = raw.resize((THUMB_W, THUMB_H), Image.LANCZOS)
        self._img = ImageTk.PhotoImage(raw)

        tk.Label(self, image=self._img, bg=CARD_NORMAL, bd=0).pack()

        tk.Label(
            self,
            text=label,
            bg=CARD_NORMAL, fg=TEXT,
            font=tkfont.Font(family="Segoe UI", size=10),
            wraplength=THUMB_W,
            justify="center",
        ).pack(pady=(6, 2))

        self._set_border(BORDER_NORMAL)

        for widget in self.winfo_children():
            widget.bind("<Button-1>", lambda _: self._on_select())
        self.bind("<Button-1>", lambda _: self._on_select())
        self.bind("<Enter>", lambda _: self._on_hover(True))
        self.bind("<Leave>", lambda _: self._on_hover(False))

    def _set_border(self, color: str) -> None:
        self.config(
            highlightbackground=color,
            highlightcolor=color,
            highlightthickness=2,
        )

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        bg = CARD_SEL if selected else CARD_NORMAL
        border = BORDER_SEL if selected else BORDER_NORMAL
        self.config(bg=bg)
        for w in self.winfo_children():
            w.config(bg=bg)
        self._set_border(border)

    def _on_hover(self, entering: bool) -> None:
        if self._selected:
            return
        self.config(bg=CARD_HOVER if entering else CARD_NORMAL)
        for w in self.winfo_children():
            w.config(bg=CARD_HOVER if entering else CARD_NORMAL)


class CaptureSelectorWindow:
    """キャプチャ対象選択ウィンドウ"""

    def __init__(self, parent: tk.Tk, app: "Any") -> None:  # noqa: F821
        self.parent = parent
        self.app = app
        self._cards: List[_Card] = []
        self._targets: List[Dict[str, Any]] = []
        self._selected_idx: Optional[int] = None
        self._thumb_refs: List[ImageTk.PhotoImage] = []

        self.win = tk.Toplevel(parent)
        self.win.title(i18n.t("select_target_title"))
        self.win.configure(bg=BG)
        self.win.resizable(True, True)

        W, H = 780, 560
        self.win.geometry(f"{W}x{H}")
        self._center(W, H)
        self._build()
        self.win.lift()
        self.win.focus_force()

        threading.Thread(target=self._load_items, daemon=True).start()

    # ──────────────────────────────────────────
    # レイアウト
    # ──────────────────────────────────────────

    def _build(self) -> None:
        root = self.win

        # ヘッダー
        header = tk.Frame(root, bg=BG, pady=16)
        header.pack(fill="x", padx=24)
        tk.Label(
            header,
            text=i18n.t("select_target_title"),
            bg=BG, fg=TEXT,
            font=tkfont.Font(family="Segoe UI", size=16, weight="bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=i18n.t("select_target_desc"),
            bg=BG, fg=SUBTEXT,
            font=tkfont.Font(family="Segoe UI", size=10),
        ).pack(anchor="w", pady=(2, 0))

        # スクロール可能なカードエリア
        outer = tk.Frame(root, bg=BG)
        outer.pack(fill="both", expand=True, padx=16)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=BG)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # ローディングラベル
        self._loading_label = tk.Label(
            self._scroll_frame,
            text=i18n.t("loading_windows"),
            bg=BG, fg=SUBTEXT,
            font=tkfont.Font(family="Segoe UI", size=11),
        )
        self._loading_label.pack(pady=40)

        # 下部ボタンバー
        bar = tk.Frame(root, bg="#13132a", pady=14)
        bar.pack(fill="x", side="bottom")

        self._confirm_btn = tk.Button(
            bar,
            text=i18n.t("confirm"),
            bg=ACCENT, fg="#fff",
            font=tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            relief="flat", bd=0, padx=28, pady=8,
            cursor="hand2",
            state="disabled",
            command=self._confirm,
        )
        self._confirm_btn.pack(side="right", padx=16)

        tk.Button(
            bar,
            text=i18n.t("cancel"),
            bg="#2a2a4a", fg=TEXT,
            font=tkfont.Font(family="Segoe UI", size=11),
            relief="flat", bd=0, padx=28, pady=8,
            cursor="hand2",
            command=self.win.destroy,
        ).pack(side="right", padx=(0, 8))

    # ──────────────────────────────────────────
    # アイテム読み込み（バックグラウンド）
    # ──────────────────────────────────────────

    def _load_items(self) -> None:
        # 全画面
        full_thumb = cap.get_fullscreen_thumbnail()
        items = [{"type": "fullscreen", "label": i18n.t("fullscreen"), "thumb": full_thumb}]

        # ウィンドウ一覧
        windows = cap.list_windows()
        for w in windows:
            thumb = cap.get_window_thumbnail(w["hwnd"])
            items.append({"type": "window", "hwnd": w["hwnd"], "label": w["title"], "thumb": thumb})

        self.win.after(0, lambda: self._render_items(items))

    def _render_items(self, items: List[Dict[str, Any]]) -> None:
        self._loading_label.destroy()
        self._targets = items

        cols = 3
        for idx, item in enumerate(items):
            row, col = divmod(idx, cols)

            def make_cb(i: int) -> callable:
                return lambda: self._select(i)

            card = _Card(
                self._scroll_frame,
                label=item["label"],
                thumb=item.get("thumb"),
                on_select=make_cb(idx),
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            self._cards.append(card)

        if not items:
            tk.Label(
                self._scroll_frame,
                text=i18n.t("no_windows"),
                bg=BG, fg=SUBTEXT,
                font=tkfont.Font(family="Segoe UI", size=11),
            ).pack(pady=40)

    # ──────────────────────────────────────────
    # 選択・確定
    # ──────────────────────────────────────────

    def _select(self, idx: int) -> None:
        for i, card in enumerate(self._cards):
            card.set_selected(i == idx)
        self._selected_idx = idx
        self._confirm_btn.config(state="normal")

    def _confirm(self) -> None:
        if self._selected_idx is None:
            return
        target = self._targets[self._selected_idx]
        self.app.set_capture_target(target)
        self.win.destroy()

    # ──────────────────────────────────────────
    # ユーティリティ
    # ──────────────────────────────────────────

    def _center(self, w: int, h: int) -> None:
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")
