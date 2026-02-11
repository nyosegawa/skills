# FastMCP Proxy Pattern for MCP Light

## 概要

FastMCP の `as_proxy` を使って、既存MCPサーバーをラップし description だけを差し替える。

## 基本パターン

```python
"""Light版MCPサーバー: description を1行に圧縮"""

from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

# 元のMCPサーバーをプロキシとして接続
proxy_client = ProxyClient("npx @notionhq/notion-mcp-server")

# Light版サーバーを作成
server = FastMCP.as_proxy(proxy_client, name="notion-light")

# description を差し替え
LIGHT_DESCRIPTIONS = {
    "notion-search": "Search Notion workspace and connected sources. See notion-best-practices skill for usage details.",
    "notion-fetch": "Retrieve a Notion page or database by URL or ID. See notion-best-practices skill for usage details.",
    "notion-create-pages": "Create Notion pages in a database or standalone. See notion-best-practices skill for usage details.",
    "notion-update-page": "Update a Notion page's properties or content. See notion-best-practices skill for usage details.",
    "notion-create-database": "Create a new Notion database with specified schema. See notion-best-practices skill for usage details.",
    "notion-create-comment": "Add a comment to a Notion page. See notion-best-practices skill for usage details.",
    "notion-get-comments": "Get all comments of a Notion page. See notion-best-practices skill for usage details.",
    "notion-move-pages": "Move Notion pages or databases to a new parent. See notion-best-practices skill for usage details.",
    "notion-update-data-source": "Update a Notion data source's properties or schema. See notion-best-practices skill for usage details.",
    "notion-query-database-view": "Query data from a Notion database using a view's filters and sorts. See notion-best-practices skill for usage details.",
    "notion-duplicate-page": "Duplicate a Notion page. See notion-best-practices skill for usage details.",
    "notion-get-teams": "Get Notion workspace teams. See notion-best-practices skill for usage details.",
    "notion-get-users": "Get Notion workspace users. See notion-best-practices skill for usage details.",
}

for tool in server.list_tools():
    if tool.name in LIGHT_DESCRIPTIONS:
        tool.description = LIGHT_DESCRIPTIONS[tool.name]
```

## pyproject.toml

```toml
[project]
name = "notion-light-mcp"
version = "0.1.0"
description = "Light version of Notion MCP server with compressed descriptions"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.0.0",
]

[project.scripts]
notion-light-mcp = "server:server.run"
```

## 実行方法

```bash
# 開発時
fastmcp run server.py

# Claude Code に追加
claude mcp add notion-light -- fastmcp run server.py
```

## 注意事項

- FastMCP 2.x 以降が必要
- `as_proxy` は元サーバーの全ツール・リソース・プロンプトをそのまま転送する
- description の差し替えはメモリ上で行われ、元サーバーには影響しない
- inputSchema は一切変更しない
