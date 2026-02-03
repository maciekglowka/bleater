import os


def int_or_none(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


OLLAMA_HOST = os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")
OLLAMA_NUM_CTX = int_or_none(os.environ.get("NUM_CTX")) or 16384

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")

SERVER_BIND_ADDR = os.environ.get("SERVER_BIND_ADDR") or "127.0.0.1"
SERVER_HOST = os.environ.get("SERVER_HOST") or "127.0.0.1"
SERVER_PORT = int_or_none(os.environ.get("SERVER_PORT")) or 9999
