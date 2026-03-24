# STS2 MCP — AI Gameplay Guide

## MCP Tool Calling Tips

### State Polling — Token Efficiency
- **Call `get_game_state` ONCE per turn**, at the start of your turn. Do NOT poll state between card plays.
- After `combat_end_turn`, call `get_game_state` once to see your new hand for the next turn. If it shows `is_play_phase: false` or `turn: enemy`, call once more to advance.
- **ALWAYS use `format="markdown"`** — it is far more token-efficient than JSON and contains all needed info.
- Do NOT call `get_game_state` "just to check" — only call when you need to make a decision.

### Card Index Shifting & Batch Play
- **CRITICAL**: Playing a card removes it from hand and shifts all indices. **ALWAYS play cards from RIGHT to LEFT** (highest index first) to keep lower indices stable.
- **Batch Play by Default**: Plan your full turn sequence from the turn-start state and execute multiple `combat_play_card` calls sequentially without checking state.
- **EXCEPTION - When to Re-check**: You MUST pause your batch execution and re-call `get_game_state(format="markdown")` mid-turn ONLY IF a recently played card or action has unpredictable results. This includes:
  1. Drawing new cards (Card Draw).
  2. Random hand generation or random discarding.
  3. Triggering an enemy phase change, split, or dynamic intent shift.
- When targeting, always provide `target` for single-target cards. Entity IDs are UPPER_SNAKE_CASE with a `_0` suffix (e.g. `KIN_PRIEST_0`).

### Event & Reward Flow
- Events: `event_choose_option`. After choosing, there's often a "Proceed" option at index 0.
- Rest sites: `rest_choose_option`, then `proceed_to_map`.
- Rewards: claim from right-to-left (highest index first) to avoid index shifting. Card rewards open a sub-screen; use `rewards_pick_card` or `rewards_skip_card`.

### Potions
- `use_potion(slot=N)` — slot is the potion slot index, not a card index.
- Potions don't cost energy or count as card plays. Use buff potions BEFORE playing cards.

---

## General Strategy

### Core Principles
1. **HP is a resource, not a score.** Take calculated damage to deal more. Don't waste energy on block when enemies aren't attacking.
2. **Deck quality > deck size.** Skip card rewards if nothing synergizes. A lean deck draws key cards more often.
3. **Front-load damage.** Killing enemies faster means less total damage taken.
4. **Read intents carefully.** Sleep/Buff = go all-out offense. Attack = balance block and damage. Debuff = usually no damage, offense turn.

### Combat Sequencing (General)
1. Play 0-cost utility/setup cards first.
2. Play skills before attacks when possible — many mechanics reward this order (e.g. Slow debuff on enemies stacks per card played).
3. Play biggest attacks last to benefit from accumulated buffs/debuffs.
4. Check enemy HP — if you can kill this turn, skip blocking entirely.

### Map Pathing
- **Elites** give relics — fight them when healthy (>70% HP).
- **Rest before Boss** — heal if below 80% HP. Boss fights are long and punishing.
- **Unknown nodes** are safer than Elites. Good at medium HP.
- **Shops** — visit with 100+ gold.
- **Deck quality matters more than quantity** — don't add cards just because they're offered.

### Boss Fights
- **Kill the leader, not the minions.** Enemies with "Minion" power flee when their leader dies.
- Use potions aggressively in boss fights — they don't carry between acts.
- Boss fights are wars of attrition. The longer they go, the more enemies scale with Strength buffs.

### Potion Usage
- Don't hoard potions. Dying with full potions is the worst outcome.
- Use permanent-value potions (Fruit Juice = +5 Max HP) early in any combat.
- Use buff potions (Flex Potion) on turns with multiple attacks.

### Common Mistakes
- Blocking when enemies are sleeping/buffing — waste of energy.
- Not checking card indices after playing — indices shift left.
- Taking too long to kill bosses — enemies scale every turn.
- Adding mediocre cards that dilute the deck before boss fights.
