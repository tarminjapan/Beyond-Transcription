#!/usr/bin/env python3
"""
プラットフォーム共通ユーティリティ - 外部ツール（ffmpeg, ffprobe, pandoc）の
パス解決をクロスプラットフォーム（Windows / macOS / Linux）で行う。

優先順位:
  1. プロジェクトルートの bin/ ディレクトリ直下
  2. プロジェクトルート（スクリプトと同じディレクトリ）直下
  3. システム PATH
"""

import os
import subprocess
import sys


def _get_executable_name(base_name: str) -> str:
    """
    プラットフォームに応じた実行ファイル名を返す。

    Args:
        base_name: 拡張子なしのベース名（例: "ffmpeg"）

    Returns:
        プラットフォームに応じた実行ファイル名
    """
    if sys.platform == "win32":
        return f"{base_name}.exe"
    return base_name


def _get_project_root() -> str:
    """
    プロジェクトルートディレクトリ（このスクリプトが存在するディレクトリ）を取得する。
    """
    return os.path.dirname(os.path.abspath(__file__))


def find_executable(base_name: str) -> str:
    """
    外部ツールの実行ファイルパスを解決する。

    優先順位:
      1. <プロジェクトルート>/bin/<executable>
      2. <プロジェクトルート>/<executable>
      3. システム PATH（base_name のみ）

    Args:
        base_name: 拡張子なしのベース名（例: "ffmpeg", "ffprobe", "pandoc"）

    Returns:
        見つかった実行ファイルのパス、または base_name（システム PATH 用）
    """
    exe_name = _get_executable_name(base_name)
    project_root = _get_project_root()

    # 1. bin/ ディレクトリを優先
    bin_path = os.path.join(project_root, "bin", exe_name)
    if os.path.isfile(bin_path):
        return bin_path

    # 2. プロジェクトルート直下
    root_path = os.path.join(project_root, exe_name)
    if os.path.isfile(root_path):
        return root_path

    # 3. システム PATH
    return exe_name


def get_subprocess_kwargs(**kwargs) -> dict:
    """
    subprocess.run / subprocess.Popen 用の共通キーワード引数を返す。
    Windows環境では CREATE_NO_WINDOW フラグを追加してコンソールウィンドウを抑制する。

    Args:
        **kwargs: 追加のキーワード引数

    Returns:
        subprocess 用のキーワード引数辞書
    """
    result = dict(kwargs)
    if sys.platform == "win32":
        result["creationflags"] = subprocess.CREATE_NO_WINDOW
    return result