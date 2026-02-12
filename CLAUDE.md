# CLAUDE.md

逆瀬川のスキルリポジトリ。Claude Code のスキルを管理する。

## リポジトリ構成

- `skills/` - 公開スキル（環境依存なし、誰でも使える）
- `private_skills/` - 個人用スキル（ローカルパス等の環境依存あり）
- `reference_docs/` - スキル作成時の参考ドキュメント
- `reference_skills/` - 外部から取り込んだ参考スキル（ライセンス付き）
- `scripts/` - ユーティリティスクリプト

## スキル作成フロー

### 1. ディレクトリ作成

公開スキルは `skills/`、個人用は `private_skills/` に配置する。

```
skills/{skill-name}/
├── SKILL.md          # 必須。フロントマター + 本体
├── references/       # 任意。詳細ドキュメント
├── scripts/          # 任意。実行スクリプト
└── assets/           # 任意。テンプレート等
```

- フォルダ名はケバブケース（例: `repo-analyzer`）
- `SKILL.md` は大文字小文字を正確に

### 2. SKILL.md を書く

```yaml
---
name: skill-name
description: 何をするスキルか。Use when user asks to ... や日本語のトリガーフレーズも含める。
---
```

- description にはトリガーフレーズを含める（英語・日本語両方）
- 本体は progressive disclosure を意識：SKILL.md はコア手順、詳細は `references/` に分離
- 詳しい書き方は `reference_docs/skill-bestpractice.md` を参照

### 3. symlink を作成

```bash
./scripts/sync-skills.sh
```

`skills/` と `private_skills/` 以下の全スキルを `~/.claude/skills/` にsymlinkで配置する。
新スキル追加後に1回実行すればよい。既存のsymlinkはスキップされる。

### 4. テスト

Claude Code で実際にスキルが発火するか確認する。
- 想定するトリガーフレーズで呼び出されるか
- 手順通りに実行されるか
- 関係ないクエリで誤発火しないか

### 5. コミット & プッシュ

```bash
git add skills/{name}/ # or private_skills/{name}/
git commit -m "feat: add {name} skill"
git push origin main
```

## reference_skills のルール

- MIT または Apache-2.0 ライセンスのスキルのみ追加可
- ライセンスファイル（`LICENSE.txt` 等）を必ず保持する
- ディレクトリ名: `{github-username}-{github-reponame}-{skillname}`
