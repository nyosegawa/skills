# Skills 保管庫

[English (README.md)](README.md)

逆瀬川 (Sakasegawa) の個人的なスキル保管庫: <https://x.com/gyakuse>

## ディレクトリ概要

- `reference_docs`: Skill 作成時に役立つ外部ドキュメントや参照資料
- `reference_skills`: 外部 GitHub リポジトリから取り込んだ skill サンプル
- `scripts`: 参照資料の取得・生成に使うユーティリティスクリプト

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

## `reference_skills`

このディレクトリのルール:

- 追加できるのは、許容ライセンス（MIT または Apache-2.0）の skill のみです。
- 各取り込み済み skill ディレクトリには、上流のライセンスファイル（例: `LICENSE.txt`）を保持してください。
- 再利用前に、各 skill 内のサードパーティ資産・ライセンス（ネストされたものを含む）を確認してください。
- ディレクトリ名は次の命名規則に従ってください:
  `{github-username}-{github-repositoryname}-{skillname}`

例:

- `anthropics-skills-webapp-testing`
