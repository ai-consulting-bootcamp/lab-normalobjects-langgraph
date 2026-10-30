# Lab Proof: NormalObjects Complaint Processor

## 1. What I built

A strict complaint processor built with LangGraph. Every complaint goes through a fixed state machine, and each node writes its result into a shared state, so every answer can be traced.

```
START → intake → validate ──(valid)──→ investigate → resolve → close → END
                     │
                     └──(invalid)──→ reject → END
```

- **intake**: the LLM puts the complaint into one category (portal, monster, psychic, environmental, other)
- **validate**: a rule check, not an LLM call. The category must be in `VALID_CATEGORIES`. Saves `is_valid` and `reason`
- **investigate**: looks up `LORE[category]` and asks the LLM to answer **only** from that text. Saves the lore as `evidence`
- **resolve**: the LLM writes a 1–2 sentence fix based **only** on the investigation
- **close / reject**: writes the final message and sets status to `closed` or `rejected`

Every node adds its name to `workflow_path` and prints a log line.

Full code: `Lab_normalobjects_langgraph.ipynb`. Key parts:

```python
class ComplaintState(TypedDict):
    complaint: str
    category: str
    workflow_path: List[str]
    status: str
    is_valid: bool
    reason: str
    evidence: str
    investigation: str
    resolution: str
    closure: str
```

```python
# investigate_node: grounding step
lore = LORE[state["category"]]
investigation_prompt = f"""Answer the complaint using ONLY the lore below.
Do not add any information that is not in the lore.

Lore: {lore}

Complaint: {complaint}"""
```

```python
def route_after_validation(state: ComplaintState) -> Literal["investigate", "reject"]:
    if state["is_valid"]:
        return "investigate"
    else:
        return "reject"

workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {"investigate": "investigate", "reject": "reject"}
)
```

## 2. Query

> The Downside Up portal opens at different times each day. How do I predict when?

## 3. Evidence (workflow path + log lines + lore used)

**Workflow path:** `intake → validate → investigate → resolve → close`

**Log lines (graph run, `app.invoke`):**

```
[INTAKE] Categorized as: portal
[VALIDATE] Valid: True | Reason: Category 'portal' is a valid category.
[INVESTIGATE] Evidence used: Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
[INVESTIGATE] Finding: The Downside Up portal opens when the barrier between worlds is weak, and its timing is influenced by electrical activity rather than the clock. To predict when it might open, you should monitor electrical activity in your area, as this will give you a better indication of when the portal is likely to appear.
[RESOLVE] Resolution: To predict when the Downside Up portal will open, monitor the electrical activity in your area, as its timing is influenced by this activity rather than the clock.
[CLOSE] Complaint closed. Category: portal. Resolution: ...
```

**Lore used (`LORE["portal"]`):**

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

**All 5 test complaints:**

| Complaint | Category | Status | Path |
|---|---|---|---|
| Portal opens at different times | portal | closed | intake → validate → investigate → resolve → close |
| Demogorgons work together / fight | monster | closed | intake → validate → investigate → resolve → close |
| El can't lift heavy rocks | psychic | closed | intake → validate → investigate → resolve → close |
| Creatures and power lines | environmental | closed | intake → validate → investigate → resolve → close |
| "Not a valid complaint about something random" | other | rejected | intake → validate → reject |

Result: 4 closed, 1 rejected, as expected. Rejection reason: `Category 'other' is not in ['portal', 'monster', 'psychic', 'environmental'].`

## 4. Final output

> Complaint closed. Category: portal. Resolution: To predict when the Downside Up portal will open, monitor the electrical activity in your area, as its timing is influenced by this activity rather than the clock.

## 5. Trace (which claim comes from which lore line?)

| Claim in resolution | Lore line | Supported? |
|---|---|---|
| "its timing is influenced by this activity rather than the clock" | "Their timing follows electrical activity, not the clock." | Yes, directly |
| "monitor the electrical activity" | Same line: timing follows electrical activity | Yes, a reasonable action derived from the lore |
| "in your area" | Not in the lore | **No**, added by the LLM |
| (Investigation) "opens when the barrier between worlds is weak" | "Portals open when the barrier between worlds is weak." | Yes, directly |

## 6. Failure or limitation

**The "use ONLY the lore" instruction is a request, not a guarantee.** The resolution adds "in your area", which the lore does not say. The lore never links portal timing to the user's location. The same thing happens in the psychic case: the resolution says lifting rocks needs "more energy than her psychic power can provide", while the lore only says heavier objects need more energy.

Nothing in the graph catches this. The workflow guarantees the **path** (validated, lore attached as evidence), but not that every **sentence** stays inside the evidence. A fix would be an extra `verify` node between `resolve` and `close` that checks each claim against `evidence` and sends unsupported answers back or to a human.

A second limitation is that validation depends entirely on the LLM's category label. If intake returns `"portal."` or a wrong category, a valid complaint gets rejected or matched to the wrong lore, and the exact string match won't catch it.

## 7. LangGraph vs. one LLM call

Same portal complaint, sent as a single `llm.invoke` with no graph and no lore. The model treated the portal as something in a game. It suggested tracking opening times, lunar phases, "events in the game", community forums and developer announcements. **None of it comes from the NormalObjects lore**, and it never mentions electrical activity. For the invalid complaint it did not reject anything: it **wrote a made-up complaint about a pet goldfish**.

| | LangGraph | One LLM call |
|---|---|---|
| Same answer every run? | Path, category and status were identical. Wording can still drift even at temperature 0: the portal finding was worded slightly differently in my manual node test and in the graph run, while the resolution stayed the same | Not controlled. Long, open-ended answer with no fixed structure |
| Invalid complaint rejected? | Yes. Routed to `reject` with a stated reason | No. It produced a fictional complaint instead |
| Path visible? | Yes. `workflow_path` plus a log line per node | No. Only the final text |
| Source of each claim? | `evidence` field holds the exact lore line, so each claim can be checked (section 5) | Unknown. General model knowledge, which can't be traced |
| Best for which client case? | Processes that need audit and consistency: complaints, claims, support tickets, compliance | Quick, low-stakes, open questions where traceability doesn't matter |
