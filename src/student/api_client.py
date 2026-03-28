"""
api_client.py - サーバー API との通信を担当するクライアント
"""

from typing import Optional
import requests


class APIError(Exception):
    """API からエラーレスポンスが返された場合の例外"""

    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _auth_headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _parse(self, resp: requests.Response) -> dict:
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text or "Unknown error"}
        if resp.ok:
            return data
        raise APIError(data.get("message", "Unknown error"), resp.status_code)

    # ------------------------------------------------------------------
    # 認証
    # ------------------------------------------------------------------

    def login_with_google(self, google_id_token: str) -> dict:
        """POST /api/student/auth - Google ID トークンでログイン"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/student/auth",
                json={"google_id_token": google_id_token},
                timeout=15,
            )
            return self._parse(resp)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")

    def check_auth(self) -> dict:
        """GET /api/student/auth - トークン有効性確認"""
        try:
            resp = requests.get(
                f"{self.base_url}/api/student/auth",
                headers=self._auth_headers(),
                timeout=10,
            )
            return self._parse(resp)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")

    def logout(self) -> dict:
        """POST /api/student/logout"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/student/logout",
                headers=self._auth_headers(),
                timeout=10,
            )
            return self._parse(resp)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")

    # ------------------------------------------------------------------
    # キャプチャアップロード
    # ------------------------------------------------------------------

    def upload_capture(self, student_number: str, image_b64: str) -> dict:
        """POST /api/student/capture/{student_number}"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/student/capture/{student_number}",
                json={"image": image_b64},
                headers=self._auth_headers(),
                timeout=20,
            )
            return self._parse(resp)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")
