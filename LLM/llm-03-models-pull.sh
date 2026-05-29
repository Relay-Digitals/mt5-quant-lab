#!/usr/bin/env bash
# Run INSIDE CT 131 after llm-02-container-setup.sh.
# Pulls open-source coding models via Ollama (downloads to ${LLM_HOME}/models).
#
# Model budget on i3-1215U + Intel UHD iGPU (8 GB RAM CT):
#   qwen2.5-coder:7b           Q4_K_M  ~4.7 GB  default chat / Continue.dev edit
#   qwen2.5-coder:1.5b-base    Q4_K_M  ~1.0 GB  Continue.dev autocomplete
#   nomic-embed-text                    ~0.3 GB Open WebUI RAG embeddings
#   ----------------------------------------------------------
#   subtotal                                ~6 GB  (default install)
#
# Optional (uncomment if you accept slower inference + swap):
#   qwen2.5-coder:14b          Q4_K_M  ~9.0 GB  closer to Claude Sonnet — slow
#   deepseek-coder-v2:16b      Q4_K_M  ~9.4 GB  MoE, 2.4B active params, fast for size
set -euo pipefail

OLLAMA_PORT="${OLLAMA_PORT:-11434}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null \
  || fail "Ollama not reachable at :${OLLAMA_PORT}. Run llm-02-container-setup.sh first."

pull() {
  local model="$1"
  say "Pulling: $model"
  ollama pull "$model"
}

# ---- defaults ----
pull qwen2.5-coder:7b
pull qwen2.5-coder:1.5b-base
pull nomic-embed-text

# ---- optional larger models (uncomment to enable) ----
# pull qwen2.5-coder:14b
# pull deepseek-coder-v2:16b

say "Installed models:"
ollama list

cat <<'EOF'

================================================================
 Models ready.

 Quick test (chat):
   curl http://127.0.0.1:11434/api/chat -d '{
     "model": "qwen2.5-coder:7b",
     "messages": [{"role":"user","content":"Write a Python function to reverse a linked list."}],
     "stream": false
   }' | jq -r '.message.content'

 Switch default chat model in Open WebUI:
   Profile menu → Settings → General → Default model
================================================================
EOF
