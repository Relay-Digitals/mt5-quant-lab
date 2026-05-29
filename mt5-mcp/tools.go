package main

import (
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// ─────────────────────────────────────────────────────────────────────────────
// helpers
// ─────────────────────────────────────────────────────────────────────────────

// result converts the HTTP response into an MCP tool result.
// On HTTP error we return an error result (still status 200 to MCP client)
// so the LLM can read the error string and try again.
func result(body string, err error) (*mcp.CallToolResult, error) {
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return mcp.NewToolResultText(body), nil
}

// jsonMap pulls a known-string field out of CallToolRequest args, returning ""
// if missing. Use req.RequireString in handlers when the field is mandatory.
func argStr(req mcp.CallToolRequest, key string) string {
	return req.GetString(key, "")
}
func argInt(req mcp.CallToolRequest, key string, def int) int {
	return req.GetInt(key, def)
}
func argFloat(req mcp.CallToolRequest, key string, def float64) float64 {
	return req.GetFloat(key, def)
}
func argBool(req mcp.CallToolRequest, key string, def bool) bool {
	return req.GetBool(key, def)
}

// ─────────────────────────────────────────────────────────────────────────────
// registerTools wires all 43 endpoints as MCP tools.
// ─────────────────────────────────────────────────────────────────────────────

func registerTools(s *server.MCPServer, c *HTTPClient) {
	registerMeta(s, c)
	registerConnection(s, c)
	registerSymbols(s, c)
	registerMarketData(s, c)
	registerOrderBook(s, c)
	registerPositions(s, c)
	registerOrders(s, c)
	registerHistory(s, c)
	registerCalculators(s, c)
	registerConstants(s, c)
	registerTrading(s, c)
}

// ─────────────────────────────────────────────────────────────────────────────
// 1) meta
// ─────────────────────────────────────────────────────────────────────────────

func registerMeta(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_health",
		mcp.WithDescription("MT5 API service health/version check"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/", nil))
	})

	s.AddTool(mcp.NewTool("mt5_version",
		mcp.WithDescription("MetaTrader 5 terminal build version"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/version", nil))
	})

	s.AddTool(mcp.NewTool("mt5_last_error",
		mcp.WithDescription("Last MT5 error code + message"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/last_error", nil))
	})

	s.AddTool(mcp.NewTool("mt5_info",
		mcp.WithDescription("Combined snapshot: version + terminal + account info"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/info", nil))
	})

	s.AddTool(mcp.NewTool("mt5_terminal",
		mcp.WithDescription("MT5 terminal info (build, connected, trade_allowed, paths)"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/terminal", nil))
	})

	s.AddTool(mcp.NewTool("mt5_account",
		mcp.WithDescription("Current account info (login, balance, equity, margin, currency, leverage)"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/account", nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 2) connection
// ─────────────────────────────────────────────────────────────────────────────

func registerConnection(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_login",
		mcp.WithDescription("Programmatic broker login (alternative to GUI login)"),
		mcp.WithNumber("login", mcp.Required(), mcp.Description("Broker login number")),
		mcp.WithString("password", mcp.Required(), mcp.Description("Broker password")),
		mcp.WithString("server", mcp.Required(), mcp.Description("Broker server, e.g. Exness-MT5Trial17")),
		mcp.WithNumber("timeout", mcp.Description("Timeout in ms (default 60000)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		payload := map[string]any{
			"login":    argInt(req, "login", 0),
			"password": argStr(req, "password"),
			"server":   argStr(req, "server"),
			"timeout":  argInt(req, "timeout", 60000),
		}
		return result(c.Post("/api/connect/login", payload))
	})

	s.AddTool(mcp.NewTool("mt5_shutdown",
		mcp.WithDescription("Force-disconnect from MT5 (next call auto-reinitializes)"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/connect/shutdown", nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 3) symbols
// ─────────────────────────────────────────────────────────────────────────────

func registerSymbols(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_symbols_total",
		mcp.WithDescription("Total number of symbols available"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/symbols/total", nil))
	})

	s.AddTool(mcp.NewTool("mt5_symbols_list",
		mcp.WithDescription("List symbols with optional filter and pagination"),
		mcp.WithString("filter", mcp.Description("Substring filter on name/description (case-insensitive)")),
		mcp.WithString("group", mcp.Description("MT5 group mask, e.g. '*USD*' or 'Forex\\\\*'")),
		mcp.WithNumber("limit", mcp.Description("Max results (default 100, max 10000)")),
		mcp.WithNumber("offset", mcp.Description("Skip first N (default 0)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("filter", argStr(req, "filter"), "group", argStr(req, "group"),
			"limit", argInt(req, "limit", 100), "offset", argInt(req, "offset", 0))
		return result(c.Get("/api/symbols", q))
	})

	s.AddTool(mcp.NewTool("mt5_symbol_info",
		mcp.WithDescription("Full symbol info: bid/ask, digits, lot constraints, swap, spread, filling modes"),
		mcp.WithString("symbol", mcp.Required(), mcp.Description("Symbol name, e.g. EURUSD")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		return result(c.Get(fmt.Sprintf("/api/symbols/%s", sym), nil))
	})

	s.AddTool(mcp.NewTool("mt5_symbol_select",
		mcp.WithDescription("Add or remove symbol from MarketWatch (enables ticks/bars retrieval)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithBoolean("enable", mcp.Description("true to add, false to remove (default true)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		enable := argBool(req, "enable", true)
		q := qv("enable", enable)
		return result(c.Post(fmt.Sprintf("/api/symbols/%s/select?%s", sym, q.Encode()), nil))
	})

	s.AddTool(mcp.NewTool("mt5_symbol_tick",
		mcp.WithDescription("Last tick: bid, ask, last, volume, timestamp"),
		mcp.WithString("symbol", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/tick", sym), nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 4) market data — bars + ticks
// ─────────────────────────────────────────────────────────────────────────────

func registerMarketData(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_bars",
		mcp.WithDescription("OHLC bars from a position offset (copy_rates_from_pos). Default: latest N bars"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithString("timeframe", mcp.Description("M1 M5 M15 M30 H1 H4 D1 W1 MN1 (default H1)")),
		mcp.WithNumber("count", mcp.Description("Number of bars (default 100, max 10000)")),
		mcp.WithNumber("from_pos", mcp.Description("Offset from latest (0 = latest)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		q := qv("timeframe", argStr(req, "timeframe"), "count", argInt(req, "count", 0),
			"from_pos", argInt(req, "from_pos", 0))
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/bars", sym), q))
	})

	s.AddTool(mcp.NewTool("mt5_bars_from",
		mcp.WithDescription("OHLC bars from a specific time backwards (copy_rates_from)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithString("timeframe", mcp.Description("M1 M5 M15 M30 H1 H4 D1 W1 MN1 (default H1)")),
		mcp.WithString("from_time", mcp.Required(), mcp.Description("ISO 8601 datetime or unix seconds")),
		mcp.WithNumber("count", mcp.Description("Number of bars (default 100)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		ft, err := req.RequireString("from_time")
		if err != nil {
			return result("", err)
		}
		q := qv("timeframe", argStr(req, "timeframe"), "from_time", ft, "count", argInt(req, "count", 0))
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/bars/from", sym), q))
	})

	s.AddTool(mcp.NewTool("mt5_bars_range",
		mcp.WithDescription("OHLC bars in a time range (copy_rates_range)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithString("timeframe", mcp.Description("Default H1")),
		mcp.WithString("from_time", mcp.Required()),
		mcp.WithString("to_time", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		ft, _ := req.RequireString("from_time")
		tt, _ := req.RequireString("to_time")
		q := qv("timeframe", argStr(req, "timeframe"), "from_time", ft, "to_time", tt)
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/bars/range", sym), q))
	})

	s.AddTool(mcp.NewTool("mt5_ticks_from",
		mcp.WithDescription("Tick stream from a time (copy_ticks_from)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithString("from_time", mcp.Required(), mcp.Description("ISO 8601 or unix seconds")),
		mcp.WithNumber("count", mcp.Description("Number of ticks (default 1000, max 100000)")),
		mcp.WithString("flags", mcp.Description("ALL | INFO | TRADE (default ALL)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		ft, _ := req.RequireString("from_time")
		q := qv("from_time", ft, "count", argInt(req, "count", 0), "flags", argStr(req, "flags"))
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/ticks/from", sym), q))
	})

	s.AddTool(mcp.NewTool("mt5_ticks_range",
		mcp.WithDescription("Tick stream in a time range (copy_ticks_range)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithString("from_time", mcp.Required()),
		mcp.WithString("to_time", mcp.Required()),
		mcp.WithString("flags", mcp.Description("ALL | INFO | TRADE")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		ft, _ := req.RequireString("from_time")
		tt, _ := req.RequireString("to_time")
		q := qv("from_time", ft, "to_time", tt, "flags", argStr(req, "flags"))
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/ticks/range", sym), q))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 5) order book (DOM L2)
// ─────────────────────────────────────────────────────────────────────────────

func registerOrderBook(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_book_subscribe",
		mcp.WithDescription("Subscribe to DOM L2 for a symbol (market_book_add). Note: many FX brokers don't publish DOM."),
		mcp.WithString("symbol", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		return result(c.Post(fmt.Sprintf("/api/symbols/%s/book/subscribe", sym), nil))
	})

	s.AddTool(mcp.NewTool("mt5_book_get",
		mcp.WithDescription("Get current DOM snapshot (market_book_get). Call subscribe first."),
		mcp.WithString("symbol", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		return result(c.Get(fmt.Sprintf("/api/symbols/%s/book", sym), nil))
	})

	s.AddTool(mcp.NewTool("mt5_book_release",
		mcp.WithDescription("Release DOM subscription (market_book_release)"),
		mcp.WithString("symbol", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		return result(c.Post(fmt.Sprintf("/api/symbols/%s/book/unsubscribe", sym), nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 6) positions (read)
// ─────────────────────────────────────────────────────────────────────────────

func registerPositions(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_positions_total",
		mcp.WithDescription("Total number of open positions"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/positions/total", nil))
	})

	s.AddTool(mcp.NewTool("mt5_positions_list",
		mcp.WithDescription("Open positions (optional filter by symbol, group mask, or ticket)"),
		mcp.WithString("symbol", mcp.Description("Filter by symbol")),
		mcp.WithString("group", mcp.Description("Symbol mask, e.g. '*USD*'")),
		mcp.WithNumber("ticket", mcp.Description("Specific position ticket")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("symbol", argStr(req, "symbol"), "group", argStr(req, "group"), "ticket", argInt(req, "ticket", 0))
		return result(c.Get("/api/positions", q))
	})

	s.AddTool(mcp.NewTool("mt5_position_by_ticket",
		mcp.WithDescription("Get a single open position by its ticket number"),
		mcp.WithNumber("ticket", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		t := argInt(req, "ticket", 0)
		if t == 0 {
			return result("", fmt.Errorf("ticket required"))
		}
		return result(c.Get(fmt.Sprintf("/api/positions/%d", t), nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 7) orders (read)
// ─────────────────────────────────────────────────────────────────────────────

func registerOrders(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_orders_total",
		mcp.WithDescription("Total number of pending orders"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/orders/total", nil))
	})

	s.AddTool(mcp.NewTool("mt5_orders_list",
		mcp.WithDescription("Pending orders (filter by symbol, group, or ticket)"),
		mcp.WithString("symbol", mcp.Description("")),
		mcp.WithString("group", mcp.Description("")),
		mcp.WithNumber("ticket", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("symbol", argStr(req, "symbol"), "group", argStr(req, "group"), "ticket", argInt(req, "ticket", 0))
		return result(c.Get("/api/orders", q))
	})

	s.AddTool(mcp.NewTool("mt5_order_by_ticket",
		mcp.WithDescription("Get a single pending order by ticket"),
		mcp.WithNumber("ticket", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		t := argInt(req, "ticket", 0)
		if t == 0 {
			return result("", fmt.Errorf("ticket required"))
		}
		return result(c.Get(fmt.Sprintf("/api/orders/%d", t), nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 8) history (deals + past orders)
// ─────────────────────────────────────────────────────────────────────────────

func registerHistory(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_deals_total",
		mcp.WithDescription("Number of executed deals in a date range (default last 7 days)"),
		mcp.WithNumber("days", mcp.Description("Default 7")),
		mcp.WithString("from_time", mcp.Description("ISO 8601 or unix (overrides days)")),
		mcp.WithString("to_time", mcp.Description("ISO 8601 or unix (overrides days)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("days", argInt(req, "days", 0), "from_time", argStr(req, "from_time"), "to_time", argStr(req, "to_time"))
		return result(c.Get("/api/deals/total", q))
	})

	s.AddTool(mcp.NewTool("mt5_deals_list",
		mcp.WithDescription("Deal history (executed transactions, including commissions and swaps)"),
		mcp.WithNumber("days", mcp.Description("Default 7")),
		mcp.WithString("from_time", mcp.Description("")),
		mcp.WithString("to_time", mcp.Description("")),
		mcp.WithString("group", mcp.Description("Symbol mask")),
		mcp.WithNumber("ticket", mcp.Description("Specific deal ticket")),
		mcp.WithNumber("position", mcp.Description("Position ticket")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("days", argInt(req, "days", 0),
			"from_time", argStr(req, "from_time"), "to_time", argStr(req, "to_time"),
			"group", argStr(req, "group"),
			"ticket", argInt(req, "ticket", 0), "position", argInt(req, "position", 0))
		return result(c.Get("/api/deals", q))
	})

	s.AddTool(mcp.NewTool("mt5_orders_history_total",
		mcp.WithDescription("Number of past orders in a date range"),
		mcp.WithNumber("days", mcp.Description("Default 7")),
		mcp.WithString("from_time", mcp.Description("")),
		mcp.WithString("to_time", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("days", argInt(req, "days", 0), "from_time", argStr(req, "from_time"), "to_time", argStr(req, "to_time"))
		return result(c.Get("/api/orders/history/total", q))
	})

	s.AddTool(mcp.NewTool("mt5_orders_history_list",
		mcp.WithDescription("Past orders (filled, cancelled, expired)"),
		mcp.WithNumber("days", mcp.Description("Default 7")),
		mcp.WithString("from_time", mcp.Description("")),
		mcp.WithString("to_time", mcp.Description("")),
		mcp.WithString("group", mcp.Description("")),
		mcp.WithNumber("ticket", mcp.Description("")),
		mcp.WithNumber("position", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		q := qv("days", argInt(req, "days", 0),
			"from_time", argStr(req, "from_time"), "to_time", argStr(req, "to_time"),
			"group", argStr(req, "group"),
			"ticket", argInt(req, "ticket", 0), "position", argInt(req, "position", 0))
		return result(c.Get("/api/orders/history", q))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 9) calculators
// ─────────────────────────────────────────────────────────────────────────────

func registerCalculators(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_calc_margin",
		mcp.WithDescription("Calculate required margin for a hypothetical order (order_calc_margin)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required(), mcp.Description("Lot size, e.g. 0.01")),
		mcp.WithString("side", mcp.Description("buy | sell (default buy)")),
		mcp.WithNumber("price", mcp.Description("Optional; null = use current ask/bid")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, err := req.RequireString("symbol")
		if err != nil {
			return result("", err)
		}
		payload := map[string]any{
			"symbol": sym,
			"volume": argFloat(req, "volume", 0),
			"side":   sideOrDefault(argStr(req, "side")),
		}
		if p := argFloat(req, "price", 0); p > 0 {
			payload["price"] = p
		}
		return result(c.Post("/api/calc/margin", payload))
	})

	s.AddTool(mcp.NewTool("mt5_calc_profit",
		mcp.WithDescription("Calculate hypothetical profit (order_calc_profit)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required()),
		mcp.WithString("side", mcp.Description("buy | sell")),
		mcp.WithNumber("price_open", mcp.Required()),
		mcp.WithNumber("price_close", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sym, _ := req.RequireString("symbol")
		payload := map[string]any{
			"symbol":      sym,
			"volume":      argFloat(req, "volume", 0),
			"side":        sideOrDefault(argStr(req, "side")),
			"price_open":  argFloat(req, "price_open", 0),
			"price_close": argFloat(req, "price_close", 0),
		}
		return result(c.Post("/api/calc/profit", payload))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 10) constants enumeration
// ─────────────────────────────────────────────────────────────────────────────

func registerConstants(s *server.MCPServer, c *HTTPClient) {
	s.AddTool(mcp.NewTool("mt5_constants_list",
		mcp.WithDescription("List all MT5 enum constant groups (TIMEFRAME, ORDER_TYPE, TRADE_RETCODE, ...)"),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Get("/api/constants", nil))
	})

	s.AddTool(mcp.NewTool("mt5_constants_get",
		mcp.WithDescription("Get all values for one enum group (e.g. TRADE_RETCODE → {DONE: 10009, ERROR: 10011, ...})"),
		mcp.WithString("group", mcp.Required(), mcp.Description("Group name, e.g. TIMEFRAME, TRADE_RETCODE, ORDER_FILLING")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		g, err := req.RequireString("group")
		if err != nil {
			return result("", err)
		}
		return result(c.Get(fmt.Sprintf("/api/constants/%s", g), nil))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// 11) trading (10 endpoints — the dangerous ones)
// ─────────────────────────────────────────────────────────────────────────────

func registerTrading(s *server.MCPServer, c *HTTPClient) {
	// market order check (dry-run)
	s.AddTool(mcp.NewTool("mt5_order_check",
		mcp.WithDescription("DRY-RUN market order: validate without sending. Returns retcode and margin impact."),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required()),
		mcp.WithString("side", mcp.Description("buy | sell")),
		mcp.WithNumber("sl", mcp.Description("Stop-loss price (0 = none)")),
		mcp.WithNumber("tp", mcp.Description("Take-profit price (0 = none)")),
		mcp.WithNumber("deviation", mcp.Description("Slippage in points (default 20)")),
		mcp.WithNumber("magic", mcp.Description("Magic number / strategy id")),
		mcp.WithString("comment", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/orders/check", marketPayload(req)))
	})

	// market order send (LIVE)
	s.AddTool(mcp.NewTool("mt5_order_send",
		mcp.WithDescription("LIVE market order — IRREVERSIBLE. Sends a real buy/sell at current price."),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required()),
		mcp.WithString("side", mcp.Description("buy | sell")),
		mcp.WithNumber("sl", mcp.Description("")),
		mcp.WithNumber("tp", mcp.Description("")),
		mcp.WithNumber("deviation", mcp.Description("")),
		mcp.WithNumber("magic", mcp.Description("")),
		mcp.WithString("comment", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/orders/send", marketPayload(req)))
	})

	// pending order check
	s.AddTool(mcp.NewTool("mt5_pending_check",
		mcp.WithDescription("DRY-RUN pending order (buy_limit/sell_limit/buy_stop/sell_stop/buy_stop_limit/sell_stop_limit)"),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required()),
		mcp.WithString("order_type", mcp.Required(),
			mcp.Description("buy_limit | sell_limit | buy_stop | sell_stop | buy_stop_limit | sell_stop_limit")),
		mcp.WithNumber("price", mcp.Required(), mcp.Description("Trigger/activation price")),
		mcp.WithNumber("stoplimit", mcp.Description("Only for buy_stop_limit/sell_stop_limit")),
		mcp.WithNumber("sl", mcp.Description("")),
		mcp.WithNumber("tp", mcp.Description("")),
		mcp.WithNumber("deviation", mcp.Description("")),
		mcp.WithNumber("magic", mcp.Description("")),
		mcp.WithString("comment", mcp.Description("")),
		mcp.WithNumber("expiration", mcp.Description("Unix timestamp; 0 = GTC")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/orders/pending/check", pendingPayload(req)))
	})

	// pending order send (LIVE)
	s.AddTool(mcp.NewTool("mt5_pending_send",
		mcp.WithDescription("LIVE pending order — IRREVERSIBLE. Places a real limit/stop order."),
		mcp.WithString("symbol", mcp.Required()),
		mcp.WithNumber("volume", mcp.Required()),
		mcp.WithString("order_type", mcp.Required()),
		mcp.WithNumber("price", mcp.Required()),
		mcp.WithNumber("stoplimit", mcp.Description("")),
		mcp.WithNumber("sl", mcp.Description("")),
		mcp.WithNumber("tp", mcp.Description("")),
		mcp.WithNumber("deviation", mcp.Description("")),
		mcp.WithNumber("magic", mcp.Description("")),
		mcp.WithString("comment", mcp.Description("")),
		mcp.WithNumber("expiration", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/orders/pending/send", pendingPayload(req)))
	})

	// modify pending order
	s.AddTool(mcp.NewTool("mt5_order_modify",
		mcp.WithDescription("Modify a pending order (price, SL, TP, expiration)"),
		mcp.WithNumber("ticket", mcp.Required()),
		mcp.WithNumber("price", mcp.Description("")),
		mcp.WithNumber("stoplimit", mcp.Description("")),
		mcp.WithNumber("sl", mcp.Description("")),
		mcp.WithNumber("tp", mcp.Description("")),
		mcp.WithNumber("expiration", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		payload := map[string]any{"ticket": argInt(req, "ticket", 0)}
		if v := argFloat(req, "price", 0); v != 0 {
			payload["price"] = v
		}
		if v := argFloat(req, "stoplimit", 0); v != 0 {
			payload["stoplimit"] = v
		}
		if v := argFloat(req, "sl", 0); v != 0 {
			payload["sl"] = v
		}
		if v := argFloat(req, "tp", 0); v != 0 {
			payload["tp"] = v
		}
		if v := argInt(req, "expiration", 0); v != 0 {
			payload["expiration"] = v
		}
		return result(c.Post("/api/orders/modify", payload))
	})

	// cancel pending order
	s.AddTool(mcp.NewTool("mt5_order_cancel",
		mcp.WithDescription("Cancel a pending order"),
		mcp.WithNumber("ticket", mcp.Required()),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		return result(c.Post("/api/orders/cancel", map[string]any{"ticket": argInt(req, "ticket", 0)}))
	})

	// modify position (SL/TP)
	s.AddTool(mcp.NewTool("mt5_position_modify",
		mcp.WithDescription("Modify SL / TP of an open position"),
		mcp.WithNumber("ticket", mcp.Required()),
		mcp.WithNumber("sl", mcp.Description("New stop-loss (0 = remove)")),
		mcp.WithNumber("tp", mcp.Description("New take-profit (0 = remove)")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		payload := map[string]any{
			"ticket": argInt(req, "ticket", 0),
			"sl":     argFloat(req, "sl", 0),
			"tp":     argFloat(req, "tp", 0),
		}
		return result(c.Post("/api/positions/modify", payload))
	})

	// close position
	s.AddTool(mcp.NewTool("mt5_position_close",
		mcp.WithDescription("Close an open position (full or partial)"),
		mcp.WithNumber("ticket", mcp.Required()),
		mcp.WithNumber("volume", mcp.Description("Partial close lot (null/0 = full)")),
		mcp.WithNumber("deviation", mcp.Description("Slippage in points (default 20)")),
		mcp.WithString("comment", mcp.Description("")),
	), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		payload := map[string]any{
			"ticket":    argInt(req, "ticket", 0),
			"deviation": argInt(req, "deviation", 20),
			"comment":   defaultStr(argStr(req, "comment"), "mt5-mcp close"),
		}
		if v := argFloat(req, "volume", 0); v > 0 {
			payload["volume"] = v
		}
		return result(c.Post("/api/positions/close", payload))
	})
}

// ─────────────────────────────────────────────────────────────────────────────
// shared payload builders
// ─────────────────────────────────────────────────────────────────────────────

func marketPayload(req mcp.CallToolRequest) map[string]any {
	sym, _ := req.RequireString("symbol")
	return map[string]any{
		"symbol":    sym,
		"volume":    argFloat(req, "volume", 0),
		"side":      sideOrDefault(argStr(req, "side")),
		"sl":        argFloat(req, "sl", 0),
		"tp":        argFloat(req, "tp", 0),
		"deviation": argInt(req, "deviation", 20),
		"magic":     argInt(req, "magic", 123456),
		"comment":   defaultStr(argStr(req, "comment"), "mt5-mcp"),
	}
}

func pendingPayload(req mcp.CallToolRequest) map[string]any {
	sym, _ := req.RequireString("symbol")
	ot, _ := req.RequireString("order_type")
	payload := map[string]any{
		"symbol":     sym,
		"volume":     argFloat(req, "volume", 0),
		"order_type": ot,
		"price":      argFloat(req, "price", 0),
		"stoplimit":  argFloat(req, "stoplimit", 0),
		"sl":         argFloat(req, "sl", 0),
		"tp":         argFloat(req, "tp", 0),
		"deviation":  argInt(req, "deviation", 20),
		"magic":      argInt(req, "magic", 123456),
		"comment":    defaultStr(argStr(req, "comment"), "mt5-mcp pending"),
	}
	if v := argInt(req, "expiration", 0); v > 0 {
		payload["expiration"] = v
	}
	return payload
}

func sideOrDefault(s string) string {
	if s == "buy" || s == "sell" {
		return s
	}
	return "buy"
}

func defaultStr(s, def string) string {
	if s == "" {
		return def
	}
	return s
}
