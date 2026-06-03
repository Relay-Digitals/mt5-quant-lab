"""roles.py — definisi ROLE & aturan permission untuk WA→Claude bridge.
Dipakai oleh permguard.py (hook PreToolUse) untuk enforce per-role.
Role aktif dibaca dari env CLAUDE_ROLE (di-set bridge per pesan)."""
import re

# Pola perintah berbahaya (regex, case-insensitive) yang menyentuh sistem live / trading.
ORDER_PATTERNS = [
    r"orders?/send", r"order_send", r"position[_/]close", r"pending[_/]?send",
    r"position[_/]modify", r"/api/orders", r"mt5_order_send", r"mt5_position_close",
    r"carina\.stockbit", r"order/v2/(buy|sell)",
]
DEPLOY_PATTERNS = [
    r"\bsystemctl\b", r"\bpct\b", r"\bcrontab\b", r"\bapt\b", r"\bpip install",
    r"\brm\s+-rf\b", r"\bmkfs\b", r"\bdd\s+if=", r">\s*/etc/", r"\bshutdown\b", r"\breboot\b",
]

ROLES = {
    "research": {
        "label": "🔬 Research (read-only)",
        "desc": "Riset strategi + backtest + baca data. TIDAK bisa ubah file/service/trading.",
        "allow_write": False,          # Write/Edit/NotebookEdit ditolak
        "block_bash": ORDER_PATTERNS + DEPLOY_PATTERNS,
        "confirm_bash": [],
    },
    "deploy": {
        "label": "🛠️ Deploy",
        "desc": "Riset + ubah skrip + pasang/restart service. TIDAK bisa kirim order broker.",
        "allow_write": True,
        "block_bash": ORDER_PATTERNS,  # masih blokir order/trading
        "confirm_bash": DEPLOY_PATTERNS,
    },
    "live": {
        "label": "🔴 Live (order broker)",
        "desc": "Semua, termasuk kirim order broker. WAJIB konfirmasi tiap order.",
        "allow_write": True,
        "block_bash": [],
        "confirm_bash": ORDER_PATTERNS + DEPLOY_PATTERNS,
    },
}
DEFAULT_ROLE = "research"

def get_role(name):
    return ROLES.get(name or DEFAULT_ROLE, ROLES[DEFAULT_ROLE])

def check_bash(role_name, command):
    """return ('allow'|'deny'|'confirm', alasan)"""
    r = get_role(role_name)
    for pat in r["block_bash"]:
        if re.search(pat, command, re.I):
            return ("deny", f"Role '{role_name}' tidak boleh perintah ini (pola: {pat}). Ganti role dgn /role.")
    for pat in r.get("confirm_bash", []):
        if re.search(pat, command, re.I):
            return ("confirm", f"Perintah sensitif (pola: {pat}) — butuh konfirmasi.")
    return ("allow", "")

def check_tool(role_name, tool_name):
    r = get_role(role_name)
    if tool_name in ("Write", "Edit", "NotebookEdit") and not r["allow_write"]:
        return ("deny", f"Role '{role_name}' read-only — tidak boleh {tool_name}.")
    return ("allow", "")
