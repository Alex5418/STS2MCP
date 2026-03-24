Play Slay the Spire 2 using the MCP tools (`mcp__sts2__*`). Your goal is to play as well as possible and win the run.

## Setup
1. Read `AGENTS.md` for general strategy and MCP calling tips.
2. Read `GUIDE.md` for hero-specific strategies. If the current hero isn't covered, adapt and add notes after boss fights.
3. Call `get_game_state(format="markdown")` to see the current state and begin playing.

## Gameplay Loop
- **Map**: Evaluate paths. Prefer elites when healthy, rest sites before bosses.
- **Combat**: Read intents. Plan your ENTIRE turn sequence upfront, then execute all card plays in a batch (see Token Budget rules below). Play from right-to-left indices to avoid index shift bugs.
- **Events**: Evaluate options based on current HP, gold, and deck needs.
- **Rewards**: Skip cards that don't synergize. Claim gold and relics. Potions if slots open.
- **Rest Sites**: Heal if below 80% HP before boss. Otherwise upgrade or train (Girya).
- **Shop**: Buy if 100+ gold and something useful is available.

## Decision Logging
- **Before every significant action**, call `log_agent_decision(decision="...")` with a single string explaining your reasoning.
- Start with a context label, e.g. `"Combat turn 3: ..."`, `"Card reward: ..."`, `"Map: ..."`.
- Key decision points: each combat turn (card sequence plan), card rewards, map path choices, shop purchases, rest site choices, event options.
- Be specific: mention enemy intents, HP thresholds, card synergies, or strategic goals that influenced your choice.

## Token Budget Rules (CRITICAL)
These rules exist to prevent token exhaustion. Follow them strictly.

### 1. Minimize `get_game_state` Calls
- Call `get_game_state` ONCE at the **start of each turn** (or when entering a new screen). This is your primary state read.
- Do NOT call `get_game_state` between individual card plays. You already know your hand from the turn-start state.
- Do NOT call `get_game_state` after `combat_end_turn` unless the response indicates an unexpected situation. The next turn's state will come when you call it at the start of your next turn.
- Exception: call `get_game_state` mid-turn ONLY if a card effect makes the board state unpredictable (e.g., draw cards, random effects, enemy summons).

### 2. Batch Card Plays
- At the start of each combat turn, plan your COMPLETE sequence of card plays based on the single state read.
- Execute all `combat_play_card` calls back-to-back. Play cards from RIGHT to LEFT (highest index first) to keep lower indices stable.
- **Exception**: Pause the batch and re-call `get_game_state(format="markdown")` mid-turn ONLY if a played card has unpredictable results (card draw, random discard, enemy phase change/split).
- After all cards are played, call `combat_end_turn`. Do NOT query state before ending turn.

### 3. Always Use Markdown Format
- ALWAYS call `get_game_state(format="markdown")`. Never use `format="json"`.
- Markdown is significantly more token-efficient than JSON while containing all the information you need.

### 4. Other Important Rules
- Use potions BEFORE playing cards when they grant buffs (e.g. Flex Potion).
- Focus fire on bosses — minions flee when the leader dies.

## Learning & Updating
- **After each boss is defeated**, review what worked and what didn't. Update `GUIDE.md` with new insights — hero-specific tips, boss strategies, card evaluations, or sequencing discoveries.
- If playing a hero not yet in `GUIDE.md`, create a new section for them.
