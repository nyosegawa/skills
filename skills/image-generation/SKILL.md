---
name: image-generation
description: Gemini画像生成APIを使ってブログ記事やドキュメント用の図・イラストを生成する。Use when user asks to "画像生成", "図を作って", "generate image", "create diagram", "イラスト作って", "図示して", or wants to create visual assets for articles.
compatibility: Requires Python 3.10+, google-genai (pip install google-genai), and GEMINI_API_KEY environment variable. Claude Code only.
metadata:
  author: nyosegawa
  version: 1.0.0
---

# Image Generation with Gemini

Gemini の画像生成 API を使って、ブログ記事やドキュメント用の図・イラストを生成するスキル。

## Prerequisites

1. **google-genai**: `python3 -c "from google import genai; print('OK')"` — if missing: `pip install google-genai`
2. **Pillow**: `python3 -c "from PIL import Image; print('OK')"` — if missing: `pip install Pillow` (JPEG→PNG変換に必要)
3. **GEMINI_API_KEY**: 環境変数に設定されていること

## Usage

### スクリプト実行

`scripts/generate_image.py` を使って画像を生成する。

```bash
# 基本
python3 scripts/generate_image.py "prompt text" /path/to/output.png

# モデル指定
python3 scripts/generate_image.py --model gemini-3-pro-image-preview "prompt text" /path/to/output.png
```

デフォルトモデルは `gemini-3-pro-image-preview`。高品質な図の生成に適している。

スクリプトの場所はスキルディレクトリ内: `~/.claude/skills/image-generation/scripts/generate_image.py`
またはリポジトリ内: `~/src/github.com/nyosegawa/skills/skills/image-generation/scripts/generate_image.py`

## Prompt Guidelines

### 技術ブログ向きのスタイル

技術記事に挿入する図は以下の方針で生成する。

- **ダイアグラム・アーキテクチャ図**: 「A clean, minimal technical diagram showing ...」のように指示する。白背景で色数を抑えたシンプルなスタイルが記事に合う
- **概念図**: 「A simple illustration explaining the concept of ...」のように指示する
- **比較図**: 「A side-by-side comparison diagram of A vs B, showing ...」のように指示する

### デザイン統一（複数画像生成時の最重要ルール）

1つの記事・ドキュメントに複数の画像を入れる場合、全画像のデザインを統一すること。画像ごとにトーンが異なると全体の品質が大幅に下がる。

**方法**: 最初にスタイルテンプレートプロンプトをシェル変数として定義し、全画像のプロンプトの冒頭に付与する。

```bash
# 全画像で共有するスタイルテンプレート
STYLE="A modern, polished infographic with a white background. Use a vibrant blue (#2563EB) as the primary color and soft gray (#F1F5F9) as secondary. Rounded rectangles with subtle drop shadows. Clean, modern aesthetic like a well-designed slide deck. Large, bold text. Professional and visually appealing."

# 各画像はこのように生成
python3 scripts/generate_image.py "$STYLE [個別の図の内容]" /path/to/output.png
```

スタイルテンプレートは記事のトーンに応じて調整してよいが、1記事内では必ず同じテンプレートを使う。

### 日本語テキストのベストプラクティス

Geminiは日本語テキストの描画が不安定。以下のルールで崩壊を防ぐ:

1. **ラベルは短くする**: 1ラベル5文字以内が理想。「リポジトリ衛生」(6文字)はOK、「構造化テキストインターフェースを確保する」は長すぎる
2. **漢字を減らす**: 漢字が多いほど崩壊しやすい。ひらがな・カタカナを混ぜると安定する
3. **情報量を絞る**: 1つの図に詰め込みすぎない。余白を十分にとる
4. **日本語を主体にする**: 「英語メイン + 日本語補足」ではなく「日本語メイン + ツール名のみ英語」にする
5. **プロンプトは日本語で書く**: 日本語の図を生成するときはプロンプト自体も日本語で書くと出力の日本語品質が上がる

### 文字数制限（厳守）

1つの画像に含めるテキスト要素の総量を制限する。これを守らないと日本語が崩壊する。

| 項目 | 上限 |
|------|------|
| テキスト要素（ボックス、ラベル等）の総数 | 10個以下 |
| 1つのラベルの文字数 | 日本語7文字以内、英語15文字以内 |
| 図全体の日本語文字数合計 | 50文字以内 |

上限を超えそうな場合は、図を2枚に分割するか、情報を削って本質だけに絞る。「記事本文で補足すればよい」と割り切ること。

### プロンプトの書き方

Gemini の画像生成は自然言語でプロンプトを書く。昔のStable Diffusion的なタグ羅列ではなく、文章として何を描いてほしいかを説明する。

良い例:
```
A clean technical diagram on white background showing the architecture of a speech recognition system.
On the left, a waveform labeled "Audio Input (16kHz)" feeds into a box labeled "wav2vec2 CNN Feature Extractor (frozen)".
An arrow goes down to "Transformer Encoder (24 layers)".
From layer 12, a branch goes right to "Phoneme CTC Head" outputting phoneme symbols.
From layer 24, another branch goes right to "Kana CTC Head" outputting hiragana characters.
Use a blue color scheme. Keep it minimal and professional.
```

悪い例:
```
architecture, diagram, speech recognition, wav2vec2, CTC, blue, white background, minimal
```

### アスペクト比

- ブログの本文幅に合わせる場合: 16:9 または 4:3
- 正方形: 1:1
- デフォルトは 16:9 を推奨

## Output

- Gemini API は JPEG を返すが、.png 指定時はスクリプトが自動で PNG に変換する
- ブログ記事用の場合、保存先は `~/src/github.com/nyosegawa/nyosegawa.github.io/img/{slug}/{image-name}.png`
- Markdown での参照: `![alt text](/img/{slug}/{image-name}.png)`

## 生成後の検証（必須）

生成した画像は必ず `read_file` で視覚的に確認すること。以下をチェックする:

1. **日本語の可読性**: 漢字が崩壊していないか。「だいたい読める」は不合格。完全に読めることが条件
2. **テキストの完全性**: ラベルが途切れていないか
3. **矢印の方向**: 意図した方向を向いているか
4. **デザインの統一性**: 同一記事の他の画像とトーンが揃っているか
5. **わかりやすさ**: 情報が詰め込まれすぎていないか。図としてパッと見て理解できるか

問題がある場合は即座に再生成する。複数画像を生成した場合は、最後に全画像を並べて統一性を最終チェックする。

## Limitations

- SynthID 透かしが自動付与される
- テキスト描画は不得意な場合がある（特に日本語テキスト）— 上記「日本語テキストのベストプラクティス」に従うことで軽減できる
- 1リクエストにつき1画像が基本
- 同じプロンプトでも毎回異なるデザインが出るため、デザイン統一にはスタイルテンプレートプロンプトが必須
