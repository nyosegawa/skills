---
name: mcp-light-generator
description: MCPサーバーの「Light版」を生成する。descriptionを1行に圧縮し、ベストプラクティスをAgent Skillとして分離する。Use when user asks to "MCP Light版を作って", "MCPを軽量化", "Light MCP", "mcp-light", "create light mcp", "compress mcp descriptions", "MCP description圧縮", or wants to reduce MCP tool definition token usage.
---

# MCP Light Generator

MCPサーバーのツール定義(description)を分析し、「判断用1行サマリー」と「実行時ベストプラクティス」に分離する。出力は2つ: Light版MCPサーバー(FastMCP proxy) + ベストプラクティスSkill。

## 背景

MCPツールのdescriptionには2種類の情報が混在している:
- **判断用情報**: 「Notionにページを作成する」— ツールを使うかの判断に必要。1行で済む
- **実行時ベストプラクティス**: 「data_source_idを使え」「先にfetchしろ」— 実際にツールを使う瞬間まで不要

MCP Lightはこれを分離し、前者をLight版MCPサーバーのdescriptionに、後者をAgent Skillに外出しする。

## 手順

### Step 1: 対象MCPサーバーの特定

ユーザーにMCPサーバー名を確認する。例:
- `@notionhq/notion-mcp-server`
- `@anthropic/github-mcp-server`
- カスタムMCPサーバー

### Step 2: ツール定義の収集

ToolSearch を使って対象MCPサーバーの全ツールをロードする。

```
ToolSearch: "+{server-prefix}" で全ツールを検索
```

各ツールの以下を記録する:
- `name`: ツール名
- `description`: 元のdescription全文
- `inputSchema`: パラメータスキーマ（変更しない）

### Step 3: description の分離

各ツールのdescriptionを分析し、2つに分離する。

#### 3a. Light版サマリー（1-2行）

以下のルールで圧縮する:
- **何をするか**を1文で書く（英語、動詞始まり）
- 末尾に `See {server}-best-practices skill for usage details.` を付ける
- inputSchemaの情報は含めない（スキーマ自体が残るため）
- 例: `Create Notion pages in a database or standalone. See notion-best-practices skill for usage details.`

#### 3b. ベストプラクティス（Skill用）

元のdescriptionから以下を抽出する:
- パラメータの制約・特殊形式（日付形式、特殊プレフィックスなど）
- 推奨ワークフロー（「先にfetchしてからcreateする」など）
- エラー回避のコツ
- 具体的な使用例

### Step 4: 出力ファイルの生成

出力先ディレクトリをユーザーに確認し、以下の構造で生成する。
`references/fastmcp-proxy-pattern.md` を参照してFastMCPプロキシのコードパターンを確認する。

```
{server-name}-light/
├── mcp/
│   ├── server.py          # FastMCP proxyサーバー
│   └── pyproject.toml     # パッケージ定義
└── skill/
    └── {server-name}-best-practices/
        └── SKILL.md        # ベストプラクティスSkill
```

#### server.py の構造

```python
from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

LIGHT_DESCRIPTIONS = {
    "tool-name": "1-line summary. See {server}-best-practices skill for usage details.",
    # ... 全ツール分
}

proxy_client = ProxyClient("npx @original/mcp-server")
server = FastMCP.as_proxy(proxy_client, name="{server-name}-light")

for tool in server.list_tools():
    if tool.name in LIGHT_DESCRIPTIONS:
        tool.description = LIGHT_DESCRIPTIONS[tool.name]
```

#### SKILL.md の構造

```markdown
---
name: {server-name}-best-practices
description: Best practices for {Server Name} MCP tools. Auto-loaded when using {server-name}-light MCP server. Contains parameter formats, recommended workflows, and error prevention tips.
---

# {Server Name} Best Practices

## 共通ルール
[全ツール共通のルール・制約]

## {tool-name-1}
[ツール固有のベストプラクティス]

## {tool-name-2}
...
```

### Step 5: トークン削減レポート

圧縮前後のトークン数を概算し、レポートを出力する。

```
## トークン削減レポート

| ツール名 | 元のdescription | Light版 | 削減率 |
|---|---|---|---|
| tool-1 | ~500 tokens | ~20 tokens | 96% |
| ... | ... | ... | ... |

### サマリー
- 元のdescription合計: ~X tokens
- Light版description合計: ~Y tokens
- inputSchema（不変）: ~Z tokens
- description単体の削減率: XX%
- 常時コンテキストの削減率: XX%（description + schema 基準）
```

トークン数は「英語1単語 ≈ 1.3 tokens、1文字（日本語）≈ 2-3 tokens」で概算する。正確な計測が必要な場合はtiktokenを使用する。

### Step 6: インストール手順の提示

生成が完了したら、以下のインストール手順を提示する:

```bash
# 1. Light版MCPサーバーをインストール
pip install -e ./{server-name}-light/mcp/

# 2. Claude CodeにMCPサーバーを追加
claude mcp add {server-name}-light -- python -m {server_name}_light

# 3. ベストプラクティスSkillを配置
cp -r ./{server-name}-light/skill/{server-name}-best-practices/ ~/.claude/skills/

# 4. 元のMCPサーバーを無効化（任意）
claude mcp remove {original-server-name}
```

## 重要なルール

- **inputSchemaは絶対に変更しない** — パラメータ構造はそのまま保持する
- **情報は捨てない** — descriptionから取り除いた情報は全てSkillに移す
- **ツール名は変えない** — 元のMCPサーバーと同じツール名を使う
- **共通ルールを抽出する** — 複数ツールに共通するパターン（日付形式など）は共通セクションにまとめる
