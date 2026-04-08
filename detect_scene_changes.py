#!/usr/bin/env python3
"""
シーンチェンジ検出CLI - 動画からフレーム差分を用いてスライド切り替え等のシーンチェンジを自動検出するスクリプト

【Windows環境専用】
このスクリプトと同じディレクトリに ffmpeg.exe / ffprobe.exe が存在する場合、
それらを優先的に使用します。

Usage:
    python detect_scene_changes.py --video <動画ファイルのパス> [--threshold <差分閾値>] [--interval <抽出間隔秒>] [--output <出力先パス>]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops

# Windows環境専用
if sys.platform != "win32":
    print("警告: このスクリプトはWindows環境専用です。", file=sys.stderr)


def get_ffmpeg_path() -> str:
    """
    ffmpeg.exe のパスを取得する
    スクリプトと同じディレクトリの ffmpeg.exe を優先し、なければPATHから探す
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(script_dir, "ffmpeg.exe")
    if os.path.isfile(local_ffmpeg):
        return local_ffmpeg
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """
    ffprobe.exe のパスを取得する
    スクリプトと同じディレクトリの ffprobe.exe を優先し、なければPATHから探す
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffprobe = os.path.join(script_dir, "ffprobe.exe")
    if os.path.isfile(local_ffprobe):
        return local_ffprobe
    return "ffprobe"


# ffmpeg / ffprobe のパスをキャッシュ
_FFMPEG_PATH = get_ffmpeg_path()
_FFPROBE_PATH = get_ffprobe_path()


def get_video_duration(video_path: str) -> float | None:
    """
    ffprobe を使用して動画の長さ（秒）を取得する
    """
    try:
        cmd = [
            _FFPROBE_PATH,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            os.path.normpath(video_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
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


def extract_frames_to_dir(
    video_path: str, interval: float, output_dir: str
) -> list[str]:
    """
    ffmpeg を使用して動画から指定間隔でフレームを抽出し、画像ファイルとして保存する。

    Args:
        video_path: 動画ファイルのパス
        interval: 抽出間隔（秒）
        output_dir: 出力先ディレクトリ

    Returns:
        抽出された画像ファイルパスのリスト（時系列順）
    """
    video_path = os.path.normpath(video_path)
    output_pattern = os.path.join(output_dir, "frame_%06d.jpg")

    # fps モードで抽出: 指定した間隔（秒）ごとに1フレーム
    fps = 1.0 / interval
    ffmpeg_cmd = [
        _FFMPEG_PATH,
        "-i",
        video_path,
        "-vf",
        f"fps={fps}",
        "-q:v",
        "5",
        "-y",
        output_pattern,
    ]

    try:
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0:
            print(
                f"エラー: ffmpeg フレーム抽出に失敗しました: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return []
    except FileNotFoundError:
        print("エラー: ffmpeg が見つかりません。", file=sys.stderr)
        return []

    # 抽出されたファイルを時系列順にソート
    files = sorted(
        [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
    )
    return files


# 比較用の縮小サイズ（高速化のため）
_COMPARE_SIZE = (320, 180)


def compute_image_diff(img1: Image.Image, img2: Image.Image) -> float:
    """
    2つの画像間の平均差分（0.0〜255.0）を計算する。
    高速化のため、画像を縮小してからPILのCレベル操作で比較する。
    """
    # 縮小して比較（高速化）
    img1_small = img1.convert("RGB").resize(_COMPARE_SIZE, Image.Resampling.BILINEAR)
    img2_small = img2.convert("RGB").resize(_COMPARE_SIZE, Image.Resampling.BILINEAR)

    # PILのCレベル差分演算（高速）
    diff = ImageChops.difference(img1_small, img2_small)

    # ヒストグラムから平均差分を計算
    # ヒストグラムは768値（R:0-255, G:0-255, B:0-255）
    hist = diff.histogram()
    total_diff = 0
    for ch in range(3):
        ch_hist = hist[ch * 256 : (ch + 1) * 256]
        total_diff += sum(val * count for val, count in enumerate(ch_hist))
    total_pixels = _COMPARE_SIZE[0] * _COMPARE_SIZE[1] * 3  # pixels × channels

    return total_diff / total_pixels


def seconds_to_timestamp(seconds: float) -> str:
    """秒数を HH:MM:SS 形式のタイムスタンプに変換する"""
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    secs = int(seconds) % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def detect_scene_changes(
    video_path: str,
    threshold: float = 30.0,
    interval: float = 1.0,
) -> list[dict]:
    """
    動画からシーンチェンジを検出する。

    Args:
        video_path: 動画ファイルのパス
        threshold: シーンチェンジと判定する差分の閾値（0.0〜255.0）
        interval: フレーム抽出間隔（秒）

    Returns:
        検出されたシーンチェンジ情報のリスト
        [{"timestamp": "HH:MM:SS", "seconds": float, "diff_score": float}, ...]
    """
    # 動画の長さを確認
    duration = get_video_duration(video_path)
    if duration is None:
        print("エラー: 動画の長さを取得できませんでした。", file=sys.stderr)
        return []

    print(f"動画の長さ: {duration:.1f}秒 ({seconds_to_timestamp(duration)})")
    print(f"フレーム抽出間隔: {interval}秒")
    print(f"差分閾値: {threshold}")
    print()

    # テンポラリディレクトリにフレームを抽出
    with tempfile.TemporaryDirectory() as temp_dir:
        print("フレームを抽出中...")
        frame_files = extract_frames_to_dir(video_path, interval, temp_dir)

        if len(frame_files) < 2:
            print("エラー: フレームが十分に抽出できませんでした。", file=sys.stderr)
            return []

        print(f"抽出フレーム数: {len(frame_files)}")
        print()

        # フレーム間の差分を計算
        print("シーンチェンジを検出中...")
        scene_changes = []

        prev_img = Image.open(frame_files[0])

        for i in range(1, len(frame_files)):
            current_img = Image.open(frame_files[i])
            diff_score = compute_image_diff(prev_img, current_img)

            if diff_score >= threshold:
                # このフレームのタイムスタンプを計算
                frame_seconds = i * interval
                timestamp = seconds_to_timestamp(frame_seconds)
                scene_changes.append(
                    {
                        "timestamp": timestamp,
                        "seconds": round(frame_seconds, 1),
                        "diff_score": round(diff_score, 2),
                    }
                )
                print(
                    f"  検出: {timestamp} ({frame_seconds:.1f}秒) 差分={diff_score:.2f}"
                )

            prev_img = current_img

    print()
    print(f"検出完了: {len(scene_changes)}件のシーンチェンジを検出しました。")
    return scene_changes


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="動画からフレーム差分を用いてシーンチェンジを自動検出します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python detect_scene_changes.py --video input/video.mp4
    python detect_scene_changes.py --video input/video.mp4 --threshold 25 --interval 0.5
    python detect_scene_changes.py -v input/video.mp4 -t 30 -i 1 -o output/scene_changes.json

出力形式 (JSON):
    [
      {"timestamp": "00:00:00", "seconds": 0.0, "diff_score": 255.0},
      {"timestamp": "00:03:48", "seconds": 228.0, "diff_score": 85.3},
      ...
    ]
        """,
    )

    parser.add_argument("--video", "-v", required=True, help="動画ファイルのパス")
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=30.0,
        help="シーンチェンジと判定する差分閾値（0.0〜255.0、デフォルト: 30.0）",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=1.0,
        help="フレーム抽出間隔（秒、デフォルト: 1.0）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="出力先JSONファイルのパス（省略時は標準出力）",
    )

    args = parser.parse_args()

    # 動画ファイルの存在確認
    if not os.path.exists(args.video):
        print(f"エラー: 動画ファイルが見つかりません: {args.video}", file=sys.stderr)
        sys.exit(1)

    # シーンチェンジ検出
    scene_changes = detect_scene_changes(
        video_path=args.video,
        threshold=args.threshold,
        interval=args.interval,
    )

    if not scene_changes:
        print("シーンチェンジは検出されませんでした。", file=sys.stderr)
        # 空のリストを出力
        scene_changes = []

    # 結果の出力
    output_json = json.dumps(scene_changes, indent=2, ensure_ascii=False)

    if args.output:
        # 出力ディレクトリの作成
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n結果を保存しました: {args.output}")
    else:
        print("\n--- 検出結果 (JSON) ---")
        print(output_json)


if __name__ == "__main__":
    main()
