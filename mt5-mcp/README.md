# mt5-mcp

MCP server (Go) yang expose 43 tool MetaTrader 5 — semua endpoint dari REST API
di CT 132 (http://192.168.0.116:8000) sebagai MCP tools yang bisa di-call oleh
Claude (Desktop, Code, atau any MCP client).

## Build

```bash
cd mt5-mcp
go build -o mt5-mcp .
# binary 11 MB, single static file, no deps
```

Cross-compile (optional):
```bash
GOOS=linux  GOARCH=amd64 go build -o mt5-mcp-linux-amd64 .
GOOS=darwin GOARCH=arm64 go build -o mt5-mcp-darwin-arm64 .
```

## Setup di Claude Code

Edit `~/.claude/settings.json` (atau `~/.claude/mcp.json`) — tambahkan:

```json
{
  "mcpServers": {
    "mt5": {
      "command": "/Users/ben/Downloads/AI-Selfhosted/mt5-mcp/mt5-mcp",
      "env": {
        "MT5_API_BASE": "http://192.168.0.116:8000"
      }
    }
  }
}
```

Atau lewat CLI:
```bash
claude mcp add mt5 /Users/ben/Downloads/AI-Selfhosted/mt5-mcp/mt5-mcp \
  --env MT5_API_BASE=http://192.168.0.116:8000
```

## Setup di Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mt5": {
      "command": "/Users/ben/Downloads/AI-Selfhosted/mt5-mcp/mt5-mcp",
      "env": {
        "MT5_API_BASE": "http://192.168.0.116:8000"
      }
    }
  }
}
```

Restart Claude Desktop. Tool `mt5_*` muncul di tool picker.

## Manual stdio test (tanpa Claude)

```bash
# list tools
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}';
 echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}';
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}') | ./mt5-mcp

# call a tool
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}';
 echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}';
 echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mt5_symbol_tick","arguments":{"symbol":"XAUUSD"}}}') | ./mt5-mcp
```

## 43 tools available

| Group | Tools |
|---|---|
| **meta** | `mt5_health`, `mt5_version`, `mt5_last_error`, `mt5_info`, `mt5_terminal`, `mt5_account` |
| **connection** | `mt5_login`, `mt5_shutdown` |
| **symbols** | `mt5_symbols_total`, `mt5_symbols_list`, `mt5_symbol_info`, `mt5_symbol_select`, `mt5_symbol_tick` |
| **market-data** | `mt5_bars`, `mt5_bars_from`, `mt5_bars_range`, `mt5_ticks_from`, `mt5_ticks_range` |
| **order-book** | `mt5_book_subscribe`, `mt5_book_get`, `mt5_book_release` |
| **positions** | `mt5_positions_total`, `mt5_positions_list`, `mt5_position_by_ticket` |
| **orders** | `mt5_orders_total`, `mt5_orders_list`, `mt5_order_by_ticket` |
| **history** | `mt5_deals_total`, `mt5_deals_list`, `mt5_orders_history_total`, `mt5_orders_history_list` |
| **calculators** | `mt5_calc_margin`, `mt5_calc_profit` |
| **constants** | `mt5_constants_list`, `mt5_constants_get` |
| **trading** ⚠ | `mt5_order_check`, `mt5_order_send`, `mt5_pending_check`, `mt5_pending_send`, `mt5_order_modify`, `mt5_order_cancel`, `mt5_position_modify`, `mt5_position_close` |

⚠ Trading tools `mt5_order_send`, `mt5_pending_send`, `mt5_position_close` adalah
**LIVE** dan **IRREVERSIBLE**. Default behavior untuk LLM agent: use `*_check`
variant dulu (dry-run), confirm, baru pakai `_send`.

## Env vars

| Var | Default | Description |
|---|---|---|
| `MT5_API_BASE` | `http://192.168.0.116:8000` | FastAPI backend URL |

## Logging

Server log ke **stderr** (stdout reserved for MCP protocol). Untuk debug:

```bash
./mt5-mcp 2> /tmp/mt5-mcp.log
```

## Source files

```
mt5-mcp/
├── main.go      # entry point + stdio transport
├── client.go    # HTTP client wrapper
├── tools.go     # 43 tool definitions + handlers (~550 LOC)
├── go.mod       # uses github.com/mark3labs/mcp-go
└── mt5-mcp      # built binary
```
