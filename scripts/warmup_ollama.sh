#!/usr/bin/env sh
set -eu

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:3b-instruct}"
OLLAMA_WARMUP_TIMEOUT_SECONDS="${OLLAMA_WARMUP_TIMEOUT_SECONDS:-300}"
OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-10m}"

echo "[ollama-warmup] Waiting for Ollama at $OLLAMA_BASE_URL..."
until curl -sf "$OLLAMA_BASE_URL/api/tags" >/dev/null; do
  sleep 2
done

echo "[ollama-warmup] Prewarming model $OLLAMA_MODEL..."
curl -sS "$OLLAMA_BASE_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$OLLAMA_MODEL\",\"prompt\":\"Warm up the model. Reply with one word: ready\",\"stream\":false,\"keep_alive\":\"$OLLAMA_KEEP_ALIVE\",\"options\":{\"num_predict\":8,\"num_ctx\":512}}" \
  --max-time "$OLLAMA_WARMUP_TIMEOUT_SECONDS" >/dev/null

echo "[ollama-warmup] Ollama model $OLLAMA_MODEL is warm."
