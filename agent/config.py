"""Configuration for STS2 local agent."""

# --- LLM ---
OLLAMA_BASE_URL = "http://localhost:5001/v1"
OLLAMA_API_KEY = "ollama"  # Ollama doesn't need a real key

# Switch model here for A/B testing
#ACTIVE_MODEL = "qwen3.5:27b"
ACTIVE_MODEL = "koboldcpp"

# ACTIVE_MODEL = "phi4:14b"
# ACTIVE_MODEL = "glm4:9b"

LLM_TEMPERATURE = 0.3  # Low = more deterministic decisions
LLM_MAX_TOKENS = 4096  

# --- Game ---
GAME_BASE_URL = "http://localhost:15526"
GAME_API_URL = f"{GAME_BASE_URL}/api/v1/singleplayer"

# --- Agent ---
MAX_RETRIES_PER_ACTION = 3       # Retry on tool call errors
MAX_HISTORY_TURNS = 10           # Keep last N exchanges to avoid context overflow
TURN_TIMEOUT_SECONDS = 30        # Max time waiting for LLM response

# --- Logging ---
LOG_DIR = "logs"
LOG_THINKING = True              # Log Qwen3's <think> blocks
