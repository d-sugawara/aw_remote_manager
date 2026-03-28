"""
main.py - エントリポイント
"""

import sys
import os

# スクリプトの親ディレクトリを import パスに追加（PyInstaller 対応）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
