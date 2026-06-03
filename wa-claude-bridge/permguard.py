#!/usr/bin/env python3
"""permguard.py — Claude Code PreToolUse hook. Enforce ROLE permission.
Baca tool-call dari stdin (JSON hook), role dari env CLAUDE_ROLE, putuskan allow/deny.
Confirm-patterns (order/deploy) hanya lolos bila CLAUDE_CONFIRM=1 (di-set bot setelah user /confirm)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roles

def out(decision, reason=""):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": decision,
        "permissionDecisionReason": reason}}))
    sys.exit(0)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        out("allow")  # gagal parse → jangan blokir alur normal
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    role = os.environ.get("CLAUDE_ROLE", roles.DEFAULT_ROLE)
    confirmed = os.environ.get("CLAUDE_CONFIRM", "0") == "1"

    # 1) tool-level (Write/Edit utk read-only)
    dec, why = roles.check_tool(role, tool)
    if dec == "deny":
        out("deny", why)

    # 2) Bash command-level
    if tool == "Bash":
        cmd = ti.get("command", "")
        dec, why = roles.check_bash(role, cmd)
        if dec == "deny":
            out("deny", why)
        if dec == "confirm" and not confirmed:
            out("deny", why + " Kirim '/confirm' di WhatsApp lalu ulangi instruksi.")
    out("allow")

if __name__ == "__main__":
    main()
