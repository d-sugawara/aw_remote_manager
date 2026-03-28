"""
i18n.py - 国際化テキスト管理（日本語 / English）
"""

_lang = "ja"

_strings: dict = {
    "ja": {
        "app_name": "AW リモートマネージャー",
        "login_title": "ログイン",
        "login_subtitle": "学習監視システム",
        "google_login": "Googleでサインイン",
        "authenticating": "認証中...",
        "open_browser_hint": "ブラウザでGoogleアカウントにサインインしてください",
        "login_success_balloon": "ログインが完了しました",
        "startup_balloon": "リモートマネージャーを起動しました",
        "logout": "ログアウト",
        "logout_confirm_title": "ログアウト確認",
        "logout_confirm": "ログアウトしますか？",
        "logout_success_balloon": "ログアウトしました。",
        "logout_failed_balloon": "ログアウトに失敗しました",
        "select_capture": "共有画面の選択",
        "fullscreen": "全画面",
        "all_monitors": "全モニター",
        "language": "言語設定",
        "language_ja": "日本語",
        "language_en": "英語 (English)",
        "exit": "終了",
        "ok": "OK",
        "cancel": "キャンセル",
        "select_target_title": "キャプチャ対象の選択",
        "select_target_desc": "キャプチャする画面またはウィンドウを選択してください",
        "confirm": "確定",
        "error": "エラー",
        "config_error": (
            "設定エラー: config.json の google_client_id と\n"
            "google_client_secret を正しく設定してください。"
        ),
        "google_auth_error": "Google認証に失敗しました。",
        "powered_by": "Powered by Google OAuth 2.0",
        "loading_windows": "ウィンドウ一覧を取得中...",
        "no_windows": "表示できるウィンドウがありません",
    },
    "en": {
        "app_name": "AW Remote Manager",
        "login_title": "Sign In",
        "login_subtitle": "Remote Learning Monitor",
        "google_login": "Sign in with Google",
        "authenticating": "Authenticating...",
        "open_browser_hint": "Please sign in with your Google account in the browser",
        "login_success_balloon": "Login completed.",
        "startup_balloon": "Remote Manager started.",
        "logout": "Logout",
        "logout_confirm_title": "Confirm Logout",
        "logout_confirm": "Are you sure you want to logout?",
        "logout_success_balloon": "Logged out successfully.",
        "logout_failed_balloon": "Logout failed",
        "select_capture": "Select Capture Target",
        "fullscreen": "Full Screen",
        "all_monitors": "All Monitors",
        "language": "Language",
        "language_ja": "日本語 (Japanese)",
        "language_en": "English",
        "exit": "Exit",
        "ok": "OK",
        "cancel": "Cancel",
        "select_target_title": "Select Capture Target",
        "select_target_desc": "Select the screen or window to capture",
        "confirm": "Confirm",
        "error": "Error",
        "config_error": (
            "Config error: Please set google_client_id and\n"
            "google_client_secret in config.json."
        ),
        "google_auth_error": "Google authentication failed.",
        "powered_by": "Powered by Google OAuth 2.0",
        "loading_windows": "Loading window list...",
        "no_windows": "No windows available",
    },
}


def set_lang(lang: str) -> None:
    global _lang
    if lang in _strings:
        _lang = lang


def get_lang() -> str:
    return _lang


def t(key: str) -> str:
    return _strings.get(_lang, _strings["ja"]).get(key, key)
