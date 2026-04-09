# Web会議録画 ナレッジレポート自動生成システム

Web会議の録画ファイルとタイムスタンプ付き文字起こしテキストから、画像付きの読みやすいナレッジレポート（Word形式）を自動生成するツール群です。

## 目次

- [システム概要](#システム概要)
- [動作環境](#動作環境)
- [インストール手順](#インストール手順)
- [ディレクトリ構成](#ディレクトリ構成)
- [使い方](#使い方)
- [CLIツール詳細](#cliツール詳細)
- [トラブルシューティング](#トラブルシューティング)

## システム概要

本システムは以下の4つのCLIツールで構成されています：

1. **detect_scene_changes.py** - 動画からフレーム差分でシーンチェンジを自動検出
2. **merge_events.py** - transcript.txt の VISUAL_EVENT タイムスタンプを補正
3. **extract_frame.py** - 動画から指定時間のフレーム画像を抽出
4. **convert_to_docx.py** - MarkdownファイルをWordファイルに変換

AI Agent（Claude Code等）がこれらのツールを使用して、文字起こしテキストから自動的にナレッジレポートを生成します。

## 動作環境

- **OS:** Windows / macOS / Linux
- **言語:** Python 3.x
- **Pythonパッケージ:**
  - `Pillow>=10.0.0` (画像処理用、detect_scene_changes.py で使用)
- **外部依存ツール:**
  - `ffmpeg` (画像抽出・シーンチェンジ検出用)
  - `pandoc` (ドキュメント変換用)

外部ツールの実行ファイルは以下の順序で検索されます（優先度順）：

1. **`bin/` ディレクトリ** （最優先）
2. **プロジェクトルート** （スクリプトと同じディレクトリ）
3. **システム PATH**

## インストール手順

### 1. Python のインストール

Python 3.x がインストールされていることを確認してください：

```bash
python --version
```

インストールされていない場合は、[Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストールしてください。

### 2. ffmpeg のインストール

**注意:** `extract_frame.py` と `detect_scene_changes.py` は `ffmpeg` と `ffprobe` を使用します。以下のいずれかの方法でインストールしてください。

#### 方法A: ローカル配置（推奨）

実行ファイルを `bin/` ディレクトリに配置すると、自動的に優先的に使用されます。PATHを通す必要がありません。

**Windows の場合:**

1. [ffmpeg公式サイト](https://ffmpeg.org/download.html)からWindows用ビルドをダウンロード
2. ZIPファイルを解凍
3. `ffmpeg.exe` と `ffprobe.exe` を `bin/` ディレクトリにコピー

**macOS の場合:**

1. [ffmpeg公式サイト](https://ffmpeg.org/download.html)からmacOS用ビルドをダウンロード、またはHomebrewでインストール後にパスからコピー
2. `ffmpeg` と `ffprobe` を `bin/` ディレクトリにコピー

**Linux の場合:**

1. パッケージマネージャでインストール後にパスからコピー、またはバイナリをダウンロード
2. `ffmpeg` と `ffprobe` を `bin/` ディレクトリにコピー

```text
project_root/
├── bin/
│   ├── ffmpeg          # bin/ に配置（最優先）
│   └── ffprobe         # bin/ に配置（最優先）
├── extract_frame.py
└── ...
```

> **注意:** プロジェクトルート直下に配置しても認識されますが、`bin/` ディレクトリが優先されます。

#### 方法B: パッケージマネージャを使用

**Windows (Winget):**

```powershell
winget install ffmpeg
```

**macOS (Homebrew):**

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt install ffmpeg
```

#### 方法C: 手動インストール（PATHを通す）

1. [ffmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード
2. 適当なフォルダに配置
3. 環境変数PATHに追加

**インストール確認：**

```bash
ffmpeg -version
ffprobe -version
```

### 3. pandoc のインストール

**注意:** `convert_to_docx.py` は `pandoc` を使用します。以下のいずれかの方法でインストールしてください。

#### 方法A: ローカル配置（推奨）

実行ファイルを `bin/` ディレクトリに配置すると、自動的に優先的に使用されます。PATHを通す必要がありません。

**Windows の場合:**

1. [pandoc公式サイト](https://pandoc.org/installing.html)からWindows用インストーラーをダウンロード
2. インストーラーを実行せず、7-Zip等で解凍（またはインストール後にインストール先からコピー）
3. `pandoc.exe` を `bin/` ディレクトリにコピー

**macOS / Linux の場合:**

1. [pandoc公式サイト](https://pandoc.org/installing.html)からダウンロード、またはパッケージマネージャでインストール後にパスからコピー
2. `pandoc` を `bin/` ディレクトリにコピー

```text
project_root/
├── bin/
│   ├── pandoc          # bin/ に配置（最優先）
│   └── ...
├── convert_to_docx.py
└── ...
```

#### 方法B: パッケージマネージャを使用

**Windows (Winget):**

```powershell
winget install pandoc
```

**macOS (Homebrew):**

```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt install pandoc
```

#### 方法C: 手動インストール

1. [pandoc公式サイト](https://pandoc.org/installing.html)からダウンロード
2. インストーラーを実行（Windows）または適切な場所に配置（macOS/Linux）
3. インストール完了後、新しいターミナルを開く

**インストール確認：**

```bash
pandoc --version
```

### 4. Pythonパッケージのインストール

```bash
python -m pip install -r requirements.txt
```

### 5. ディレクトリの作成

プロジェクトルートで以下のコマンドを実行して、必要なディレクトリを作成します：

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path input, output, output/images, bin
```

**macOS / Linux:**

```bash
mkdir -p input output output/images bin
```

### 6. 入力ファイルの配置

#### `transcript.txt`の準備

1. 動画ファイルをAI Chatにアップロードする
2. `transcription_prompt.md`に記載されているプロンプトを使用して、文字起こしを行う
3. AI Chatの出力結果を`transcript.txt`として保存する
4. `transcript.txt`を`input`ディレクトリに配置する

#### `video.mp4`の準備

1. 対象の動画ファイル（手順1でアップロードした動画）を`video.mp4`にリネームする
2. `input`ディレクトリに配置する

最終的なファイル構成：

- `input/video.mp4` - Web会議の録画ファイル
- `input/transcript.txt` - タイムスタンプ付き文字起こしテキスト

## ディレクトリ構成

```text
project_root/
├── bin/                        # 外部ツール（優先的に使用される）
│   ├── ffmpeg                  # ffmpeg バイナリ（オプション）
│   ├── ffprobe                 # ffprobe バイナリ（オプション）
│   └── pandoc                  # pandoc バイナリ（オプション）
├── input/
│   ├── video.mp4               # 元のWeb会議録画ファイル
│   └── transcript.txt          # [HH:MM:SS] 形式のタイムスタンプと <VISUAL_EVENT: ...> が含まれた文字起こし
├── output/
│   ├── report.md               # Agentが生成する中間マークダウンファイル
│   ├── report.docx             # 最終出力されるWordファイル
│   └── images/                 # 抽出されたフレーム画像の保存先
├── bin_utils.py                # クロスプラットフォーム対応ユーティリティ（パス解決）
├── detect_scene_changes.py     # シーンチェンジ自動検出CLIスクリプト
├── merge_events.py             # VISUAL_EVENTタイムスタンプ補正CLIスクリプト
├── extract_frame.py            # 画像抽出CLIスクリプト
├── convert_to_docx.py          # Word変換CLIスクリプト
├── requirements.txt            # 必要なPythonパッケージ
├── transcription_prompt.md     # 動画ファイルからtranscript.txtを作成するためのプロンプト
├── agent_prompt.md             # Agent実行用システムプロンプト
└── README.md                   # このファイル
```

## 使い方

### 手動実行の場合

#### 0. シーンチェンジ検出とタイムスタンプ補正（推奨）

```bash
# シーンチェンジ検出
python detect_scene_changes.py --video input/video.mp4 --output output/scene_changes.json

# タイムスタンプ補正
python merge_events.py --transcript input/transcript.txt --scene-changes output/scene_changes.json --output input/transcript_corrected.txt
```

#### 1. 画像の抽出

```bash
python extract_frame.py --video input/video.mp4 --time 00:05:30 --output output/images/frame_001.jpg
```

#### 2. Markdownレポートの作成

`output/report.md` を作成し、画像リンクを含めます：

```markdown
# ナレッジレポート

## 概要
会議の概要を記載...

## 重要な場面

### 00:05:30 - スライドの説明
![スライド画像](images/frame_001.jpg)

説明文...
```

#### 3. Wordファイルへの変換

```bash
python convert_to_docx.py --input output/report.md --output output/report.docx
```

### AI Agent による自動実行

`agent_prompt.md` の指示に従ってAI Agentを実行してください。
Agentは自動的にシーンチェンジ検出とタイムスタンプ補正を行ってからレポートを生成します。

## CLIツール詳細

### detect_scene_changes.py

動画からフレーム差分を用いてスライド切り替え等のシーンチェンジを自動検出します。

**機能：**

- 動画から指定間隔でフレームを抽出し、連続フレーム間の差分を計算
- 差分が閾値を超えたタイミングをシーンチェンジとして検出
- 結果をJSON形式で出力

**使用方法：**

```bash
python detect_scene_changes.py --video <動画ファイルのパス> [--threshold <差分閾値>] [--interval <抽出間隔>] [--output <出力先JSON>]
```

**オプション：**

| オプション | 短縮形 | デフォルト | 説明 |
| --- | --- | --- | --- |
| --video | -v | （必須） | 動画ファイルのパス |
| --threshold | -t | 30.0 | シーンチェンジと判定する差分閾値（0.0〜255.0） |
| --interval | -i | 1.0 | フレーム抽出間隔（秒） |
| --output | -o | なし | 出力先JSONファイルのパス（省略時は標準出力） |

**使用例：**

```bash
python detect_scene_changes.py -v input/video.mp4 -o output/scene_changes.json
python detect_scene_changes.py -v input/video.mp4 -t 25 -i 0.5 -o output/scene_changes.json
```

### merge_events.py

transcript.txt 内の VISUAL_EVENT タイムスタンプを、detect_scene_changes.py の検出結果に基づいて補正します。

**機能：**

- 各 VISUAL_EVENT のタイムスタンプを最も近いシーンチェンジ時刻に補正
- 補正の最大許容差を設定可能
- ドライランモードで結果確認が可能

**使用方法：**

```bash
python merge_events.py --transcript <transcriptファイル> --scene-changes <シーンチェンジJSON> --output <出力先>
```

**オプション：**

| オプション | 短縮形 | デフォルト | 説明 |
| --- | --- | --- | --- |
| --transcript | -t | （必須） | 元の transcript.txt のパス |
| --scene-changes | -s | （必須） | detect_scene_changes.py の出力 JSON のパス |
| --output | -o | （必須） | 補正済み transcript の出力先パス |
| --max-tolerance | なし | 30.0 | タイムスタンプ補正の最大許容差（秒） |
| --dry-run | なし | False | 結果を標準出力に表示のみ |

**使用例：**

```bash
python merge_events.py -t input/transcript.txt -s output/scene_changes.json -o input/transcript_corrected.txt
python merge_events.py -t input/transcript.txt -s output/scene_changes.json -o input/transcript_corrected.txt --dry-run
```

### extract_frame.py

動画から指定時間のフレームを抽出して画像として保存します。Windows / macOS / Linux 対応。

**機能：**

- 動画の指定時間から1フレームを抽出
- ffprobeを使用して動画の長さを事前チェック（指定時間が範囲外の場合はエラー表示）
- `bin/` ディレクトリのバイナリを優先使用

**使用方法：**

```bash
python extract_frame.py --video <動画ファイルのパス> --time <HH:MM:SS> --output <出力先画像ファイルのパス>
```

**オプション：**

| オプション | 短縮形 | 必須 | 説明 |
| --- | --- | --- | --- |
| --video | -v | はい | 動画ファイルのパス |
| --time | -t | はい | 抽出する時間（HH:MM:SS 形式） |
| --output | -o | はい | 出力先画像ファイルのパス |

**使用例：**

```bash
python extract_frame.py -v input/video.mp4 -t 00:10:15 -o output/images/frame_002.png
```

**終了コード：**

- `0`: 成功
- `1`: 失敗（エラーメッセージは標準エラー出力に出力されます）

### convert_to_docx.py

MarkdownファイルをWord（.docx）ファイルに変換します。Windows / macOS / Linux 対応。

**機能：**

- MarkdownファイルをWord（.docx）ファイルに変換
- 画像リンク（相対パス）を正しく埋め込み
- `bin/` ディレクトリのバイナリを優先使用

**使用方法：**

```bash
python convert_to_docx.py --input <入力Markdownのパス> --output <出力Wordのパス>
```

**オプション：**

| オプション | 短縮形 | 必須 | 説明 |
| --- | --- | --- | --- |
| --input | -i | はい | 入力Markdownファイルのパス |
| --output | -o | はい | 出力Wordファイルのパス |

**使用例：**

```bash
python convert_to_docx.py -i output/report.md -o output/report.docx
```

**終了コード：**

- `0`: 成功
- `1`: 失敗（エラーメッセージは標準エラー出力に出力されます）

**注意：**

- Markdown内の画像リンクは相対パスで記載してください
- 例: `![画像](images/frame_001.jpg)`

## トラブルシューティング

### ffmpeg が見つかりません

**エラーメッセージ：**

```text
エラー: ffmpeg が見つかりません。bin/ ディレクトリまたはプロジェクトルートに配置するか、PATHを通してください。
```

**解決方法：**

1. **ローカル配置（推奨）:** `ffmpeg` と `ffprobe` を `bin/` ディレクトリに配置
2. **PATHを確認:** `ffmpeg -version` でインストール済みか確認
3. ターミナルを再起動して再試行

### pandoc が見つかりません

**エラーメッセージ：**

```text
エラー: pandoc が見つかりません。bin/ ディレクトリまたはプロジェクトルートに配置するか、PATHを通してください。
```

**解決方法：**

1. **ローカル配置（推奨）:** `pandoc` を `bin/` ディレクトリに配置
2. **PATHを確認:** `pandoc --version` でインストール済みか確認
3. ターミナルを再起動して再試行

### 動画ファイルが見つかりません

**エラーメッセージ：**

```text
エラー: 動画ファイルが見つかりません: <パス>
```

**解決方法：**

1. ファイルパスが正しいか確認
2. パスにスペースが含まれる場合は引用符で囲む
3. 相対パスの場合、カレントディレクトリを確認

### 指定時間が動画の範囲外

**エラーメッセージ：**

```text
エラー: 指定された時間 XX:XX:XX は動画の範囲外です。
```

**解決方法：**

1. 動画の長さを確認
2. 正しい時間を指定して再実行

### 画像がWordに埋め込まれない

**解決方法：**

1. Markdown内の画像パスが正しい相対パスか確認
2. 画像ファイルが存在するか確認
3. `output/report.md` から `output/images/frame_001.jpg` を参照する場合、パスは `images/frame_001.jpg`

## ライセンス

このプロジェクトは内部利用を目的としています。