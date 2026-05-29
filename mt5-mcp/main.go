// mt5-mcp — MCP server exposing the MT5 REST API (http://192.168.0.116:8000)
// as 43 callable tools for Claude / any MCP client.
//
// Default backend is the CT 132 MT5 API. Override with MT5_API_BASE env var.
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/mark3labs/mcp-go/server"
)

const Version = "1.0.0"

func main() {
	apiBase := os.Getenv("MT5_API_BASE")
	if apiBase == "" {
		apiBase = "http://192.168.0.116:8000"
	}

	// log to stderr — stdout is reserved for MCP stdio transport
	log.SetOutput(os.Stderr)
	log.SetPrefix("[mt5-mcp] ")
	log.Printf("starting v%s, backend = %s", Version, apiBase)

	s := server.NewMCPServer(
		"mt5-mcp",
		Version,
		server.WithToolCapabilities(false),
	)

	client := NewHTTPClient(apiBase)
	registerTools(s, client)

	// Transport: stdio (default, untuk Claude lokal) atau SSE (server persisten di CT).
	if os.Getenv("MCP_TRANSPORT") == "sse" {
		addr := os.Getenv("MCP_ADDR")
		if addr == "" {
			addr = ":8765"
		}
		log.Printf("serving SSE on %s", addr)
		sse := server.NewSSEServer(s)
		if err := sse.Start(addr); err != nil {
			fmt.Fprintf(os.Stderr, "[mt5-mcp] SSE server error: %v\n", err)
			os.Exit(1)
		}
		return
	}

	if err := server.ServeStdio(s); err != nil {
		fmt.Fprintf(os.Stderr, "[mt5-mcp] server error: %v\n", err)
		os.Exit(1)
	}
}
