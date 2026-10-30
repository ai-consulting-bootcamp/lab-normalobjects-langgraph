# Lab Proof: NormalObjects Complaint Processor

## 1. What I built
A strict complaint processor with LangGraph (`gpt-4o-mini`, temperature 0). Every complaint follows a fixed path, and only one decision point (after validation) can change the road.

```
START → intake → validate ──(valid)──→ investigate → resolve → close → END
                     └──(invalid)──→ reject → END
```

**State** (`ComplaintState`, a TypedDict that travels through the graph): `complaint`, `category`, `workflow_path`, `status`, plus one field per node result: `is_valid`, `validation_reason`, `evidence`, `investigation`, `resolution`, `closure_message`.

| Node | Job | LLM? |
|---|---|---|
| intake | Categorize the complaint (portal / monster / psychic / environmental / other) | Yes |
| validate | Clean the category (`strip`, `lower`), check it against `VALID_CATEGORIES`, save the reason | No |
| investigate | Answer using ONLY `LORE[category]`, save the lore as `evidence` | Yes |
| resolve | Short fix based ONLY on the investigation, "do not add new facts" | Yes |
| close / reject | Final message, status `closed` or `rejected` (with the reason) | No |

Every node adds its name to `workflow_path` and prints a log line.

```python
def route_after_validation(state: ComplaintState) -> Literal["investigate", "reject"]:
    if state["is_valid"]:
        return "investigate"
    return "reject"

workflow = StateGraph(ComplaintState)
# add_node for intake, validate, investigate, resolve, close, reject
workflow.add_edge(START, "intake")
workflow.add_edge("intake", "validate")
workflow.add_conditional_edges("validate", route_after_validation,
                               {"investigate": "investigate", "reject": "reject"})
workflow.add_edge("investigate", "resolve")
workflow.add_edge("resolve", "close")
workflow.add_edge("close", END)
workflow.add_edge("reject", END)
app = workflow.compile()
```

## 2. Query
> "The Downside Up portal opens at different times each day. How do I predict when?"

## 3. Evidence (workflow path + log lines + lore used)
```
[INTAKE] Categorized as: portal
[VALIDATE] valid=True | 'portal' is a known category.
[INVESTIGATE] Lore used: Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
[RESOLVE] To improve user experience, implement a real-time notification system ...
[CLOSE] Closing complaint.
```

All 5 test complaints:

| Status | Category | Path |
|---|---|---|
| closed | portal | intake → validate → investigate → resolve → close |
| closed | monster | intake → validate → investigate → resolve → close |
| closed | psychic | intake → validate → investigate → resolve → close |
| closed | environmental | intake → validate → investigate → resolve → close |
| rejected | other | intake → validate → reject |

As expected: 4 closed, 1 rejected. The invalid complaint never reached the investigate or resolve LLM calls.

## 4. Final output
**Investigation:**
> The timing of the Downside Up portal's opening is influenced by electrical activity rather than a set schedule. Since this activity can vary, predicting the exact times for the portal's opening each day is not possible.

**Resolution / closure message:**
> Complaint closed (portal). Resolution: To improve user experience, implement a real-time notification system that alerts users when the Downside Up portal is about to open, based on detected electrical activity.

**Rejected complaint:**
> Complaint rejected. Reason: 'other' is not one of ['portal', 'monster', 'psychic', 'environmental'].

## 5. Trace (which claim comes from which lore line?)
Lore: *"Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock."*

| Claim | Node | Source |
|---|---|---|
| Timing is influenced by electrical activity, not a set schedule | investigate | ✅ "Their timing follows electrical activity, not the clock." |
| "This activity can vary, so predicting exact times is not possible" | investigate | ⚠️ Inference: the lore says nothing about predictability |
| Alerts "based on detected electrical activity" | resolve | ✅ Follows from the same lore line |
| "To improve user experience" | resolve | ❌ Invented |
| "Implement a real-time notification system that alerts users" | resolve | ❌ Invented: a product idea, not in the lore |

The investigation is mostly grounded. The invention starts in the **resolve** node, even though its prompt says "Do not add new facts".

## 6. Failure or limitation
1. **The resolve node adds new facts and contradicts the investigation.** The investigation says predicting the opening is "not possible"; the resolution then promises alerts "when the portal is about to open". The prompt rule "do not add new facts" was not enough. The graph makes the path safe, but each LLM node can still invent within its own step.
2. **Same path, different words.** In my manual node test the same complaint gave "monitor electrical activity closely"; in the graph run it gave "implement a real-time notification system". Temperature 0 did not make the text identical. The workflow is deterministic; the LLM output inside it is not.
3. **Validation depends on the LLM's category.** The validate node uses plain code, but the category comes from the intake LLM. A complaint that is miscategorized as "other" would be rejected even if it is valid, and the routing would be correct but the decision wrong.

Possible fixes: pass the lore into the resolve prompt too, add a grounding check node after resolve (reject the answer if it contains claims not in the lore), or add human approval before close.

## 7. LangGraph vs. one LLM call
Same complaints, one `llm.invoke` with no graph, no lore and no validation.

**Portal, one LLM call:** 7 generic steps (collect data, look for patterns, "lunar phases, weather conditions", calculate averages, use a calendar, build a prediction model). It never mentions electrical activity and assumes the portal has a "schedule", which the lore explicitly contradicts ("not the clock").

**Invalid complaint, one LLM call:** not rejected. The model misread the message as a request and wrote its own absurd complaint about socks and shoes.

| | LangGraph | One LLM call |
|---|---|---|
| Same answer every run? | Same path and status every run; wording can still vary | No, everything can change |
| Invalid complaint rejected? | Yes, with a reason, before any further LLM call | No, it answered anyway (sock complaint) |
| Path visible? | Yes: `workflow_path`, log lines, graph drawing | No, one black box |
| Source of each claim? | `evidence` field holds the lore; each claim can be checked | None, general knowledge or invention |
| Best for which client case? | Processes that must be auditable and consistent: complaint handling, claims, compliance, support tickets | Quick drafts and brainstorming where no source or audit trail is needed |

**Conclusion:** LangGraph controls the *road* (which steps, in which order, when to stop), but not what the LLM writes inside each step. For a client, the graph gives traceability and a safe reject path; grounding still needs its own check.