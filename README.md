# Beyond Transcription

Web会議の録画から、画像付きナレッジレポート（Word形式）を自動生成するツール群です。

## 必要なもの

- **Python 3.x**
- **ffmpeg** / **ffprobe** — 画像抽出・シーンチェンジ検出用
- **pandoc** — Word変換用

> `bin/` ディレクトリに実行ファイル（ffmpeg, ffprobe, pandoc）を配置すると、そちらが優先して使用されます。

- Pythonパッケージ: `pip install -r requirements.txt`

## 使い方

### 1. 文字起こし（transcript）の作成

1. AI Chat（ChatGPT / Claude 等）を開く
2. [`transcription_prompt.md`](transcription_prompt.md) の内容をプロンプトとしてコピペする
3. 動画ファイルをアップロードする
4. 出力結果を `input/transcript.txt` として保存する

### 2. レポートの作成

1. AI Agent（Claude Code / opencode 等）を起動する
2. [`agent_prompt.md`](agent_prompt.md) の内容をプロンプトとしてコピペして実行する
3. `output/report.docx` が自動生成される

## ディレクトリ構成

```text
input/
  ├── video.mp4            # 録画ファイル
  └── transcript.txt       # 文字起こしテキスト
output/
  ├── report.md            # Agentが生成する中間ファイル
  ├── report.docx          # 最終出力（Word）
  └── images/              # 抽出されたフレーム画像
```

## ライセンス

MIT Lisence
