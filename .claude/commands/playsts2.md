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

## Decision Logging (VERY IMPORTANT)
You MUST call `log_agent_decision(decision="...")` to record your thinking. This is the most valuable output of the run. Be detailed and analytical.

### Per-Turn Logging (every combat turn, every map choice, every event, etc.)
- Call `log_agent_decision` BEFORE executing actions each turn.
- Format: `"[Turn X] <context>: <analysis and reasoning>"`
- Include: what you see (hand, energy, enemy intents, HP), what you considered, what you chose and WHY.
- For combat turns, include: damage calculations, energy math, and why you prioritized offense vs defense.
- Example: `"[Turn 3] Combat vs Jaw Worm: Enemy intends Attack 11. I have 3 energy, hand: Strike(1), Defend(1), Bash(2). Bash+Strike = 14 dmg but leaves me unblocked for 11. Defend+Strike = 6 dmg + 5 block, net -6 HP. Going all offense because Jaw Worm has 12 HP left — Bash(8)+Strike(6)=14 kills it, taking 11 is worth ending the fight."`

### Per-Combat Summary (after each fight ends)
- When combat ends (you see rewards screen), call `log_agent_decision` with a combat retrospective.
- Format: `"[Combat Summary] <enemy> Floor <N>: <what happened>"`
- Include: how many turns it took, HP lost, key moments (mistakes, lucky draws, good plays), what you'd do differently.

### Per-Act Summary (after defeating the boss)
- After each act boss is defeated, call `log_agent_decision` with an act retrospective.
- Format: `"[Act X Summary]: <full act review>"`
- Include: deck evolution (what cards added/removed/upgraded), relic pickups, path choices, HP management, biggest challenges, strategic pivots.
- Evaluate: was the deck building coherent? What archetype emerged? What was the win condition?

### Game Over / Victory Summary
- If you die or win, call `log_agent_decision` with a full game retrospective.
- Format: `"[Game Over - Floor X]"` or `"[Victory!]"`
- Include: what went right, what went wrong, the 3 most impactful decisions of the run, what you'd change if replaying.

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
