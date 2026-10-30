# Lab Proof: NormalObjects Complaint Processor

## 1. What I built
An intake → validation → investigation → resolution → closure workflow. Investigation retrieves the category's fact from `LORE`; resolution uses that fact as its evidence.

## 2. Query
“The Downside Up portal opens at different times each day. How do I predict when?”

## 3. Evidence (workflow path + log lines + lore used)
```text
portal, monster, psychic, environmental:
['intake', 'validation', 'investigation', 'resolution', 'closure']
other:
['intake', 'validation', 'reject']
```
Retrieved `LORE` evidence:
- `portal`: Portals open when the barrier between worlds is weak; timing follows electrical activity, not the clock.
- `monster`: Demogorgons act alone when hunting, but follow a hive mind when a larger entity controls them.
- `psychic`: Psychic power drains the user's energy; bigger or heavier objects need more energy, and nosebleeds are a warning sign.
- `environmental`: Creatures from the Downside Up disturb electricity; lights flicker and power lines react when they are near.
- `other`: No lore retrieved; the complaint is rejected.

## 4. Final output
The `portal`, `monster`, `psychic`, and `environmental` test complaints were categorized, marked valid, and closed. Each resolution repeated the corresponding lore evidence above. The `other` complaint was marked invalid and rejected with: “The complaint could not be processed.”

## 5. Trace (which claim comes from which lore line?)
Each investigation retrieves `LORE[category]`, and each resolution restates that evidence:
- Portal timing and electrical activity → `LORE["portal"]`.
- Demogorgons hunting alone or following a hive mind → `LORE["monster"]`.
- Psychic energy limits, object weight, and nosebleeds → `LORE["psychic"]`.
- Creatures affecting electricity, lights, and power lines → `LORE["environmental"]`.
- The `other` category has no matching lore entry, so it is rejected rather than given an unsupported resolution.

## 6. Failure or limitation
The LLM assigns the category, so a wrong category could retrieve unrelated lore. Also, `closure_node` currently leaves `final_message` empty for successful complaints; the resolution is present in state but is not assembled into a final user-facing message. The “other” test is rejected as expected.

## 7. LangGraph vs. one LLM call
LangGraph validates and routes complaints, records the workflow path, and grounds its resolution in a stored lore entry. A single LLM call is simpler and produces a free-form answer, but provides no workflow trace or source evidence; in the notebook's invalid-complaint example, it responds instead of rejecting the complaint.
