#!/usr/bin/env python3
"""
画像抽出CLI - 動画の指定時間から1フレームの画像を切り出して保存するスクリプト

bin/ ディレクトリまたはプロジェクトルートに ffmpeg / ffprobe が存在する場合、
それらを優先的に使用します。Windows / macOS / Linux 対応。

Usage:
    python extract_frame.py --video <動画ファイルのパス> --time <HH:MM:SS> --output <出力先画像ファイルのパス>
"""

import argparse
import json
import os
import subprocess
import sys

from bin_utils import find_executable, get_subprocess_kwargs


def get_ffmpeg_path() -> str:
    """
    ffmpeg のパスを取得する
    bin/ ディレクトリ → プロジェクトルート → システムPATH の順で検索する

    Returns:
        ffmpeg のパス
    """
    return find_executable("ffmpeg")


def get_ffprobe_path() -> str:
    """
    ffprobe のパスを取得する
    bin/ ディレクトリ → プロジェクトルート → システムPATH の順で検索する

    Returns:
        ffprobe のパス
    """
    return find_executable("ffprobe")


# ffmpeg / ffprobe のパスをキャッシュ
_FFMPEG_PATH = get_ffmpeg_path()
_FFPROBE_PATH = get_ffprobe_path()


def parse_time_to_seconds(time_str: str) -> float:
    """
    HH:MM:SS 形式の時間文字列を秒数に変換する

    Args:
        time_str: HH:MM:SS 形式の時間文字列

    Returns:
        秒数

    Raises:
        ValueError: 時間形式が無効な場合
    """
    parts = time_str.split(":")
    if len(parts) != 3:
        raise ValueError(
            f"時間形式が無効です: {time_str}。HH:MM:SS 形式で指定してください。"
        )

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
    except ValueError:
        raise ValueError(f"時間形式が無効です: {time_str}。数値で指定してください。")

    if minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
        raise ValueError(
            f"時間形式が無効です: {time_str}。分と秒は0-59の範囲で指定してください。"
        )

    return hours * 3600 + minutes * 60 + seconds


def check_ffmpeg() -> bool:
    """
    ffmpeg が利用可能かチェックする

    Returns:
        ffmpeg が利用可能な場合 True
    """
    try:
        result = subprocess.run(
            [_FFMPEG_PATH, "-version"],
            capture_output=True,
            text=True,
            **get_subprocess_kwargs(),
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_video_duration(video_path: str) -> float | None:
    """
    ffprobe を使用して動画の長さ（秒）を取得する

    Args:
        video_path: 動画ファイルのパス

    Returns:
        動画の長さ（秒）、取得できない場合は None
    """
    try:
        cmd = [
            _FFPROBE_PATH,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            video_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            **get_subprocess_kwargs(),
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        duration_str = data.get("format", {}).get("duration")
        if duration_str:
            return float(duration_str)
        return None
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        return None


def extract_frame(video_path: str, time_str: str, output_path: str) -> bool:
    """
    動画から指定時間のフレームを抽出して画像として保存する

    Args:
        video_path: 動画ファイルのパス
        time_str: HH:MM:SS 形式の抽出時間
        output_path: 出力先画像ファイルのパス

    Returns:
        成功時 True、失敗時 False
    """
    # パスの正規化
    video_path = os.path.normpath(video_path)
    output_path = os.path.normpath(output_path)

    # 入力ファイルの存在確認
    if not os.path.exists(video_path):
        print(f"エラー: 動画ファイルが見つかりません: {video_path}", file=sys.stderr)
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

    # 時間の変換
    try:
        time_seconds = parse_time_to_seconds(time_str)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return False

    # ffmpeg の存在確認
    if not check_ffmpeg():
        print(
            "エラー: ffmpeg が見つかりません。bin/ ディレクトリまたはプロジェクトルートに配置するか、PATHを通してください。",
            file=sys.stderr,
        )
        return False

    # ffprobe を使用して動画の長さを取得し、指定時間が範囲内かチェック
    video_duration = get_video_duration(video_path)
    if video_duration is not None and time_seconds >= video_duration:
        print(
            f"エラー: 指定された時間 {time_str} ({time_seconds:.1f}秒) は動画の長さ ({video_duration:.1f}秒) を超えています。",
            file=sys.stderr,
        )
        return False

    # ffmpeg コマンドの構築
    # -ss: 開始時間（秒）
    # -i: 入力ファイル
    # -vframes 1: 1フレームのみ抽出
    # -q:v 2: 高画質設定（1-31、小さいほど高画質）
    # -y: 上書き確認なし
    ffmpeg_cmd = [
        _FFMPEG_PATH,
        "-ss",
        str(time_seconds),
        "-i",
        video_path,
        "-vframes",
        "1",
        "-q:v",
        "2",
        "-y",
        output_path,
    ]

    try:
        # ffmpeg の実行
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            **get_subprocess_kwargs(),
        )

        if result.returncode != 0:
            # ffmpeg のエラーメッセージを解析
            error_msg = result.stderr.strip()
            if "Invalid data found when processing input" in error_msg:
                print(
                    f"エラー: 動画ファイルが破損しているか、サポートされていない形式です: {video_path}",
                    file=sys.stderr,
                )
            elif "Duration" in error_msg and time_seconds > 0:
                # 動画の長さを取得して時間が範囲外かチェック
                print(
                    f"エラー: 指定された時間 {time_str} は動画の範囲外です。",
                    file=sys.stderr,
                )
            else:
                print(
                    f"エラー: ffmpeg の実行に失敗しました: {error_msg}", file=sys.stderr
                )
            return False

        # 出力ファイルの存在確認
        if not os.path.exists(output_path):
            print(
                f"エラー: 画像ファイルが作成されませんでした。時間 {time_str} は動画の範囲外の可能性があります。",
                file=sys.stderr,
            )
            return False

        print(f"成功: 画像を抽出しました -> {output_path}")
        return True

    except Exception as e:
        print(f"エラー: 予期しないエラーが発生しました: {e}", file=sys.stderr)
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="動画から指定時間のフレームを抽出して画像として保存します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python extract_frame.py --video input/video.mp4 --time 00:05:30 --output output/images/frame_001.jpg
    python extract_frame.py -v input/video.mp4 -t 00:10:15 -o output/images/frame_002.png
        """,
    )

    parser.add_argument("--video", "-v", required=True, help="動画ファイルのパス")

    parser.add_argument(
        "--time", "-t", required=True, help="抽出する時間（HH:MM:SS 形式）"
    )

    parser.add_argument(
        "--output", "-o", required=True, help="出力先画像ファイルのパス"
    )

    args = parser.parse_args()

    success = extract_frame(args.video, args.time, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()