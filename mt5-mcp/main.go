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

	if err := server.ServeStdio(s); err != nil {
		fmt.Fprintf(os.Stderr, "[mt5-mcp] server error: %v\n", err)
		os.Exit(1)
	}
}
