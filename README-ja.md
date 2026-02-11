# Skills 保管庫

[English (README.md)](README.md)

逆瀬川 (Sakasegawa) の個人的なスキル保管庫: <https://x.com/gyakuse>

## ディレクトリ概要

- `skills`: このリポジトリで作成したオリジナル skill
- `reference_docs`: Skill 作成時に役立つ外部ドキュメントや参照資料
- `reference_skills`: 外部 GitHub リポジトリから取り込んだ skill サンプル
- `scripts`: 参照資料の取得・生成に使うユーティリティスクリプト

## `skills`

### repo-analyzer

[gtc](https://github.com/nyosegawa/gemini-tree-token-counter) と Gemini 3 Pro を使って、任意の GitHub / ローカルリポジトリを分析するスキル。

- GitHub URL・ローカルパスの両方に対応
- アーキテクチャ分析、セキュリティ監査、コード品質レビュー、依存関係分析など
- gtc のトークン数を使った正確なコスト見積もりを API 呼び出し前に提示
- すべての Gemini API 呼び出し前にユーザー確認を要求
- 大規模リポジトリでは Gemini を使って最適な抽出コマンドを自動設計

**前提条件:** Python 3.10+, `gtc`, `google-genai`, `GEMINI_API_KEY`

```bash
pip install gemini-tree-token-counter google-genai
export GEMINI_API_KEY="your_key_here"
```

## `reference_docs`

`reference_docs` には、skill 作成に有用な外部ドキュメントを格納します。

- `reference_docs/skill-bestpractice.md` は Anthropic のコンテンツを元にしています:
  <https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf>
- このファイルは Anthropic コンテンツ由来のため、`.gitignore` で除外します。
- 必要な場合はスクリプトで再生成できます。

### `skill-bestpractice.md` の生成

```bash
export GEMINI_API_KEY="your_actual_api_key_here"
pip install google-genai pymupdf requests
python scripts/convert_guide_to_md.py
```

生成先:

- `reference_docs/skill-bestpractice.md`

注意:

- 実行前に `GEMINI_API_KEY` を設定してください。
- 生成コストはおおよそ `$0.15-$0.20`（`20-30円`程度）です。

### Gemini 3 / Nano Banana ドキュメントを `.md` で取得

```bash
curl -L "https://ai.google.dev/gemini-api/docs/gemini-3.md.txt" \
  -o reference_docs/gemini-3-developers-guide.md
curl -L "https://ai.google.dev/gemini-api/docs/image-generation.md.txt" \
  -o reference_docs/image-generation-nanobanana.md
```

生成先:

- `reference_docs/gemini-3-developers-guide.md`
- `reference_docs/image-generation-nanobanana.md`

## `reference_skills`

このディレクトリのルール:

- 追加できるのは、許容ライセンス（MIT または Apache-2.0）の skill のみです。
- 各取り込み済み skill ディレクトリには、上流のライセンスファイル（例: `LICENSE.txt`）を保持してください。
- 再利用前に、各 skill 内のサードパーティ資産・ライセンス（ネストされたものを含む）を確認してください。
- ディレクトリ名は次の命名規則に従ってください:
  `{github-username}-{github-repositoryname}-{skillname}`

例:

- `anthropics-skills-webapp-testing`
