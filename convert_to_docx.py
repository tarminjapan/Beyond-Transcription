#!/usr/bin/env python3
"""
Word変換CLI - 画像リンクを含むMarkdownファイルをWord（.docx）に変換するスクリプト

bin/ ディレクトリまたはプロジェクトルートに pandoc が存在する場合、
それを優先的に使用します。Windows / macOS / Linux 対応。

Usage:
    python convert_to_docx.py --input <入力Markdownのパス> --output <出力Wordのパス>
"""

import argparse
import os
import subprocess
import sys

from bin_utils import find_executable, get_subprocess_kwargs


def get_pandoc_path() -> str:
    """
    pandoc のパスを取得する
    bin/ ディレクトリ → プロジェクトルート → システムPATH の順で検索する

    Returns:
        pandoc のパス
    """
    return find_executable("pandoc")


def check_pandoc() -> bool:
    """
    pandoc がインストールされているかチェックする

    Returns:
        pandoc が利用可能な場合 True
    """
    pandoc_path = get_pandoc_path()
    try:
        result = subprocess.run(
            [pandoc_path, "--version"],
            capture_output=True,
            text=True,
            **get_subprocess_kwargs(),
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def convert_to_docx(input_path: str, output_path: str) -> bool:
    """
    MarkdownファイルをWordファイルに変換する

    Args:
        input_path: 入力Markdownファイルのパス
        output_path: 出力Wordファイルのパス

    Returns:
        成功時 True、失敗時 False
    """
    # パスの正規化
    input_path = os.path.normpath(input_path)
    output_path = os.path.normpath(output_path)

    # 入力ファイルの存在確認
    if not os.path.exists(input_path):
        print(
            f"エラー: Markdownファイルが見つかりません: {input_path}", file=sys.stderr
        )
        return False

    # 出力ディレクトリの作成（存在しない場合）
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(
                f"エラー: 出力ディレクトリを作成できません: {output_dir} - {e}",
                file=sys.stderr,
            )
            return False

    # pandoc の存在確認
    if not check_pandoc():
        print(
            "エラー: pandoc が見つかりません。bin/ ディレクトリまたはプロジェクトルートに配置するか、PATHを通してください。",
            file=sys.stderr,
        )
        return False

    # 入力ファイルのディレクトリを取得（画像の相対パス解決用）
    input_dir = os.path.dirname(os.path.abspath(input_path))

    # pandoc のパスを取得
    pandoc_path = get_pandoc_path()

    # pandoc コマンドの構築
    # --from markdown: 入力形式をMarkdownに指定
    # --to docx: 出力形式をWordに指定
    # --resource-path: 画像などのリソースを検索するパス
    # --standalone: 完全なドキュメントとして出力
    pandoc_cmd = [
        pandoc_path,
        "--from",
        "markdown",
        "--to",
        "docx",
        "--standalone",
        "--resource-path",
        input_dir,
        "--output",
        output_path,
        input_path,
    ]

    try:
        # pandoc の実行
        # 作業ディレクトリを入力ファイルのディレクトリに設定して、
        # 相対パスの画像が正しく解決されるようにする
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            cwd=input_dir,
            **get_subprocess_kwargs(),
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "pandoc: Error" in error_msg or "Error" in error_msg:
                print(
                    f"エラー: pandoc の実行に失敗しました: {error_msg}", file=sys.stderr
                )
            elif "Could not find" in error_msg:
                print(
                    f"エラー: 画像ファイルが見つかりません: {error_msg}",
                    file=sys.stderr,
                )
            else:
                print(f"エラー: 変換に失敗しました: {error_msg}", file=sys.stderr)
            return False

        # 出力ファイルの存在確認
        if not os.path.exists(output_path):
            print("エラー: Wordファイルが作成されませんでした。", file=sys.stderr)
            return False

        print(f"成功: Wordファイルを生成しました -> {output_path}")
        return True

    except Exception as e:
        print(f"エラー: 予期しないエラーが発生しました: {e}", file=sys.stderr)
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="MarkdownファイルをWord（.docx）ファイルに変換します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python convert_to_docx.py --input output/report.md --output output/report.docx
    python convert_to_docx.py -i output/report.md -o output/report.docx

注意:
    Markdown内の画像リンクは相対パスで記載してください。
    例: ![画像](images/frame_001.jpg)
        """,
    )

    parser.add_argument(
        "--input", "-i", required=True, help="入力Markdownファイルのパス"
    )

    parser.add_argument("--output", "-o", required=True, help="出力Wordファイルのパス")

    args = parser.parse_args()

    success = convert_to_docx(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()