---
name: sakasegawa-blog-writer
description: 渡された文章を校正してブログに投稿する。Use when user asks to "記事を投稿", "ブログに投稿", "publish post", "記事を公開", "校正して投稿", "ブログ公開" etc.
---

# sakasegawa-blog-writer

渡された文章を校正し、ブログに投稿するスキル。

## 出力先

- リポジトリ: `~/src/github.com/nyosegawa/nyosegawa.github.io`
- 出力先: `posts/{slug}.md`（slug はトピックに基づく英語ケバブケース）
- フロントマター形式（Lume Simple Blog テーマ）:

```yaml
---
title: "記事タイトル"
description: "記事の説明（1-2文）"
date: YYYY-MM-DD
tags: [タグ1, タグ2]
author: 逆瀬川ちゃん
---
```

- 「この記事はCoding Agentを使って執筆されています。」はCSSで自動挿入されるため、記事本文には書かない
- 記事冒頭の挨拶の後、適切な位置に `<!--more-->` を入れる（トップページの抜粋範囲を制御するため）

## Instructions

### Step 1: 校正

ユーザーから渡された文章に対して以下を校正する。

1. 誤字脱字の修正
2. 句読点の調整（リスト項目末尾の句点を除去など）
3. Markdown記法の修正（見出しレベル、リンク形式など）
4. URLが生のまま記述されていればMarkdownリンク形式 `[タイトル](URL)` に変換
5. フロントマターが不足していれば補完（title, description, date, tags, author）

校正結果をユーザーに提示し、変更点を簡潔に説明する。

### Step 2: 投稿

**投稿前に必ずユーザーの確認を得ること。**

1. 校正済みの記事をユーザーに提示する
2. ユーザーから承認を得たら、ブログリポジトリで以下を実行する:

```bash
cd ~/src/github.com/nyosegawa/nyosegawa.github.io
python3 scripts/gen-og-images.py
git add posts/{slug}.md og/{slug}.png
git commit -m "Add post: {記事タイトル}"
git push origin main
```

3. push が完了したら、公開 URL を伝える:
   - `https://nyosegawa.com/posts/{slug}/`

**重要: ユーザーの明示的な承認なしに git push しないこと。**

## 数式の記述

ブログ（Lume）はKaTeXプラグインを導入済み。数式はLaTeX記法で記述できる。

- **ディスプレイ数式**: ` ```math ` コードブロックを使う
- **インライン数式**: 本文中では太字やインラインコードで代用する（`$...$` は未有効化）
- `_` を含む数式は `$$...$$` だとMarkdownパーサーにイタリックと解釈されるので ` ```math ` コードブロックを使う
