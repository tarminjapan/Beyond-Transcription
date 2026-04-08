#!/usr/bin/env python3
"""
VISUAL_EVENT タイムスタンプ補正CLI - detect_scene_changes.py の検出結果を用いて
transcript.txt 内の VISUAL_EVENT タイムスタンプを実際のシーンチェンジ時刻に補正するスクリプト

Usage:
    python merge_events.py --transcript input/transcript.txt --scene-changes output/scene_changes.json --output input/transcript_corrected.txt
"""

import argparse
import json
import os
import re
import sys


def parse_timestamp_to_seconds(timestamp: str) -> float | None:
    """
    HH:MM:SS または MM:SS 形式のタイムスタンプを秒数に変換する。
    """
    parts = timestamp.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return None
    except ValueError:
        return None


def seconds_to_timestamp(seconds: float) -> str:
    """秒数を HH:MM:SS 形式のタイムスタンプに変換する"""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def find_nearest_scene_change(
    event_seconds: float,
    scene_changes: list[dict],
    max_tolerance: float = 30.0,
) -> dict | None:
    """
    指定された時刻に最も近いシーンチェンジを検索する。

    Args:
        event_seconds: VISUAL_EVENT の時刻（秒）
        scene_changes: 検出されたシーンチェンジのリスト
        max_tolerance: 最大許容差（秒）。これより遠いシーンチェンジは無視される。

    Returns:
        最も近いシーンチェンジの情報、または None
    """
    nearest = None
    min_diff = float("inf")

    for sc in scene_changes:
        sc_seconds = sc["seconds"]
        diff = abs(sc_seconds - event_seconds)
        if diff < min_diff and diff <= max_tolerance:
            min_diff = diff
            nearest = sc

    return nearest


def merge_events(
    transcript_path: str,
    scene_changes_path: str,
    output_path: str,
    max_tolerance: float = 30.0,
    dry_run: bool = False,
) -> bool:
    """
    transcript.txt の VISUAL_EVENT タイムスタンプを補正する。

    Args:
        transcript_path: 元の transcript.txt のパス
        scene_changes_path: detect_scene_changes.py の出力 JSON のパス
        output_path: 補正済み transcript の出力先パス
        max_tolerance: タイムスタンプ補正の最大許容差（秒）
        dry_run: True の場合、結果を標準出力に表示するのみ（ファイル出力しない）

    Returns:
        成功時 True
    """
    # ファイルの存在確認
    if not os.path.exists(transcript_path):
        print(
            f"エラー: transcriptファイルが見つかりません: {transcript_path}",
            file=sys.stderr,
        )
        return False

    if not os.path.exists(scene_changes_path):
        print(
            f"エラー: シーンチェンジJSONファイルが見つかりません: {scene_changes_path}",
            file=sys.stderr,
        )
        return False

    # シーンチェンジデータの読み込み
    with open(scene_changes_path, "r", encoding="utf-8") as f:
        scene_changes = json.load(f)

    print(f"読み込み: {len(scene_changes)}件のシーンチェンジ")
    print()

    # transcript の読み込み
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # VISUAL_EVENT 行のパターン
    # [HH:MM:SS] <VISUAL_EVENT: ...> または [MM:SS] <VISUAL_EVENT: ...>
    visual_event_pattern = re.compile(
        r"^(\[(\d{1,2}:\d{2}(?::\d{2})?)\])\s*<VISUAL_EVENT:\s*(.+?)>\s*$"
    )

    # タイムスタンプ付き行のパターン（VISUAL_EVENT以外）
    timestamp_pattern = re.compile(r"^(\[(\d{1,2}:\d{2}(?::\d{2})?)\])\s*(.+)$")

    corrected_lines = []
    correction_count = 0

    print("=== タイムスタンプ補正 ===")
    print()

    for line in lines:
        line_stripped = line.rstrip("\n").rstrip("\r")

        # VISUAL_EVENT 行かチェック
        ve_match = visual_event_pattern.match(line_stripped)
        if ve_match:
            original_timestamp_str = ve_match.group(2)
            event_description = ve_match.group(3)

            event_seconds = parse_timestamp_to_seconds(original_timestamp_str)
            if event_seconds is None:
                print(
                    f"  警告: タイムスタンプをパースできません: {original_timestamp_str} → スキップ"
                )
                corrected_lines.append(line_stripped)
                continue

            # 最も近いシーンチェンジを検索
            nearest = find_nearest_scene_change(
                event_seconds, scene_changes, max_tolerance
            )

            if nearest:
                new_timestamp = nearest["timestamp"]
                new_seconds = nearest["seconds"]
                diff = abs(new_seconds - event_seconds)

                if diff > 0:
                    corrected_line = (
                        f"[{new_timestamp}] <VISUAL_EVENT: {event_description}>"
                    )
                    print(
                        f"  補正: [{original_timestamp_str}] → [{new_timestamp}] (差={diff:.1f}秒) {event_description[:50]}..."
                    )
                    corrected_lines.append(corrected_line)
                    correction_count += 1
                else:
                    corrected_lines.append(line_stripped)
            else:
                print(
                    f"  警告: 近接するシーンチェンジなし: [{original_timestamp_str}] → そのまま"
                )
                corrected_lines.append(line_stripped)
        else:
            corrected_lines.append(line_stripped)

    print()
    print(f"補正完了: {correction_count}件のタイムスタンプを補正しました。")

    # 結果の出力
    output_text = "\n".join(corrected_lines) + "\n"

    if dry_run:
        print("\n=== 補正済み transcript（プレビュー）===")
        print(output_text)
    else:
        # 出力ディレクトリの作成
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"\n結果を保存しました: {output_path}")

    return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="transcript.txt の VISUAL_EVENT タイムスタンプを実際のシーンチェンジ時刻に補正します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python merge_events.py --transcript input/transcript.txt --scene-changes output/scene_changes.json --output input/transcript_corrected.txt
    python merge_events.py -t input/transcript.txt -s output/scene_changes.json -o input/transcript_corrected.txt --max-tolerance 20
    python merge_events.py -t input/transcript.txt -s output/scene_changes.json -o input/transcript_corrected.txt --dry-run
        """,
    )

    parser.add_argument(
        "--transcript",
        "-t",
        required=True,
        help="元の transcript.txt のパス",
    )
    parser.add_argument(
        "--scene-changes",
        "-s",
        required=True,
        help="detect_scene_changes.py の出力 JSON ファイルのパス",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="補正済み transcript の出力先パス",
    )
    parser.add_argument(
        "--max-tolerance",
        type=float,
        default=30.0,
        help="タイムスタンプ補正の最大許容差（秒、デフォルト: 30.0）。これより遠いシーンチェンジは無視されます。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルを出力せず、結果を標準出力に表示のみ",
    )

    args = parser.parse_args()

    success = merge_events(
        transcript_path=args.transcript,
        scene_changes_path=args.scene_changes,
        output_path=args.output,
        max_tolerance=args.max_tolerance,
        dry_run=args.dry_run,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
