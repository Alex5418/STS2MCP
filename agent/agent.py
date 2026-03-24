"""STS2 Local Agent — Main game loop.

Usage:
    python agent.py                    # Run with default model
    python agent.py --model phi4:14b   # Run with specific model
"""

import argparse
import json
import time
import os
from datetime import datetime

from openai import OpenAI
from game_api import GameAPI
from tools import get_tools_for_state
from prompts import get_prompt_for_state
from config import (
    OLLAMA_BASE_URL, OLLAMA_API_KEY, ACTIVE_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS,
    MAX_RETRIES_PER_ACTION, MAX_HISTORY_TURNS,
    TURN_TIMEOUT_SECONDS,
    LOG_DIR, LOG_THINKING,
)


# ──────────────────────────────────────────────
# Logger
# ──────────────────────────────────────────────

class RunLogger:
    """Logs every LLM call and game action to JSONL."""

    def __init__(self, model_name: str):
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = model_name.replace(":", "-").replace("/", "-")
        self.path = os.path.join(LOG_DIR, f"run_{safe_model}_{ts}.jsonl")
        self.file = open(self.path, "a", encoding="utf-8")
        print(f"[LOG] Writing to {self.path}")

    def log(self, entry: dict):
        entry["timestamp"] = datetime.now().isoformat()
        self.file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.file.flush()

    def close(self):
        self.file.close()


# ──────────────────────────────────────────────
# Tool executor
# ──────────────────────────────────────────────

def execute_tool_call(game: GameAPI, name: str, args: dict) -> str:
    """Execute a tool call against the game API. Returns result as string."""
    try:
        dispatch = {
            "play_card":                lambda: game.play_card(args["card_index"], args.get("target")),
            "end_turn":                 lambda: game.end_turn(),
            "use_potion":               lambda: game.use_potion(args["slot"], args.get("target")),
            "combat_select_card":       lambda: game.combat_select_card(args["card_index"]),
            "combat_confirm_selection": lambda: game.combat_confirm_selection(),
            "choose_map_node":          lambda: game.choose_map_node(args["index"]),
            "claim_reward":             lambda: game.claim_reward(args["index"]),
            "pick_card_reward":         lambda: game.pick_card_reward(args["card_index"]),
            "skip_card_reward":         lambda: game.skip_card_reward(),
            "proceed":                  lambda: game.proceed(),
            "choose_rest_option":       lambda: game.choose_rest_option(args["index"]),
            "shop_purchase":            lambda: game.shop_purchase(args["index"]),
            "choose_event_option":      lambda: game.choose_event_option(args["index"]),
            "advance_dialogue":         lambda: game.advance_dialogue(),
            "select_card":              lambda: game.select_card(args["index"]),
            "confirm_selection":        lambda: game.confirm_selection(),
            "treasure_claim_relic":     lambda: game.treasure_claim_relic(args["index"]),
            "select_relic":             lambda: game.select_relic(args["index"]),
            "skip_relic_selection":     lambda: game.skip_relic_selection(),
        }

        if name not in dispatch:
            return json.dumps({"status": "error", "error": f"Unknown tool: {name}"})

        result = dispatch[name]()
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


# ──────────────────────────────────────────────
# Main agent loop
# ──────────────────────────────────────────────

def run_agent(model: str):
    """Main agent loop."""
    print(f"\n{'='*60}")
    print(f"  STS2 Local Agent")
    print(f"  Model: {model}")
    print(f"{'='*60}\n")

    llm = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
    game = GameAPI()
    logger = RunLogger(model)

    # Conversation history — resets each new screen context
    history: list[dict] = []
    last_state_type = None
    error_count = 0
    step = 0

    try:
        while True:
            step += 1

            # ── 1. Get game state ──
            try:
                state_text = game.get_state("markdown")
                state_json = game.get_state_json()
                state_type = state_json.get("state_type", "unknown")
            except Exception as e:
                print(f"[ERROR] Can't reach game: {e}")
                print("  Is STS2 running with the mod enabled?")
                time.sleep(3)
                continue

            # Handle terminal states
            if state_type == "menu":
                print("[INFO] No run in progress. Start a run in STS2!")
                time.sleep(5)
                continue

            if state_type == "unknown":
                print(f"[INFO] Unknown state, waiting... ({state_json})")
                time.sleep(2)
                continue

            # ── 2. Reset history on screen change ──
            if state_type != last_state_type:
                history = []
                last_state_type = state_type
                error_count = 0
                print(f"\n--- State: {state_type} ---")

            # ── 3. Build messages ──
            system_prompt = get_prompt_for_state(state_type)
            tools = get_tools_for_state(state_type)

            if not tools:
                print(f"[WARN] No tools for state '{state_type}', trying proceed...")
                try:
                    game.proceed()
                except Exception:
                    pass
                time.sleep(1)
                continue

            messages = [{"role": "system", "content": system_prompt}]

            # Add trimmed history
            messages.extend(history[-MAX_HISTORY_TURNS * 2:])

            # Add current state as the latest user message
            messages.append({
                "role": "user",
                "content": f"Current game state:\n\n{state_text}\n\nChoose your action.",
            })

            # ── 4. Call LLM ──
            t0 = time.time()
            try:
                response = llm.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                    timeout=TURN_TIMEOUT_SECONDS,
                )
            except Exception as e:
                print(f"[ERROR] LLM call failed: {e}")
                time.sleep(2)
                continue

            latency = int((time.time() - t0) * 1000)
            msg = response.choices[0].message

            # Extract thinking (Qwen3's <think> blocks)
            thinking = ""
            content = msg.content or ""
            if "<think>" in content and "</think>" in content:
                start = content.index("<think>") + 7
                end = content.index("</think>")
                thinking = content[start:end].strip()

            # ── 5. Handle tool calls ──
            if not msg.tool_calls:
                print(f"  [Step {step}] No tool call. LLM said: {content[:200]}")
                logger.log({
                    "step": step, "state_type": state_type,
                    "action": "no_tool_call", "content": content[:500],
                    "latency_ms": latency,
                })
                error_count += 1
                if error_count >= MAX_RETRIES_PER_ACTION:
                    print("  [WARN] Too many non-tool responses, forcing proceed...")
                    try:
                        game.proceed()
                    except Exception:
                        pass
                    error_count = 0
                time.sleep(1)
                continue

            # Process each tool call
            for tc in msg.tool_calls:
                tool_name = tc.function.name

                # Parse arguments (handle Ollama quirk: sometimes string, sometimes dict)
                raw_args = tc.function.arguments
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                elif isinstance(raw_args, dict):
                    args = raw_args
                else:
                    args = {}

                # Execute
                print(f"  [Step {step}] {tool_name}({args}) ", end="")
                result_str = execute_tool_call(game, tool_name, args)
                result = json.loads(result_str)

                status = result.get("status", "?")
                if status == "ok":
                    print(f"✓ {result.get('message', '')}")
                    error_count = 0
                else:
                    print(f"✗ {result.get('error', 'unknown error')}")
                    error_count += 1

                # Log
                logger.log({
                    "step": step,
                    "model": model,
                    "state_type": state_type,
                    "tool": tool_name,
                    "args": args,
                    "result_status": status,
                    "result_message": result.get("message") or result.get("error"),
                    "thinking": thinking if LOG_THINKING else None,
                    "latency_ms": latency,
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(response.usage, "completion_tokens", None),
                })

                # Add to history
                history.append({"role": "assistant", "content": None, "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tool_name, "arguments": json.dumps(args)}}
                ]})
                history.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

            # Brief pause to let game process
            time.sleep(0.5)

            # Safety: if too many errors, force end turn or proceed
            if error_count >= MAX_RETRIES_PER_ACTION:
                print("  [WARN] Max retries hit, forcing next state...")
                if state_type in ("monster", "elite", "boss"):
                    try:
                        game.end_turn()
                    except Exception:
                        pass
                else:
                    try:
                        game.proceed()
                    except Exception:
                        pass
                error_count = 0
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n[INFO] Agent stopped by user (Ctrl+C)")
    finally:
        logger.close()
        print(f"[INFO] Log saved to {logger.path}")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STS2 Local Agent")
    parser.add_argument("--model", default=ACTIVE_MODEL, help="Ollama model name")
    args = parser.parse_args()
    run_agent(args.model)
