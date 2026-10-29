# Lab Proof: NormalObjects Complaint Processor

## 1. What I built

I built a LangGraph complaint workflow with a typed shared state:

```text
START → intake → validate ── valid ──→ investigate → resolve → close → END
                         └─ invalid ─→ reject → END
```

The state records the complaint, category, validation result, reason, evidence,
resolution, closure message, status, and `workflow_path`.

The graph is invoked with:

```python
result = app.invoke({"complaint": complaint})
```

## 2. Query

```text
The Downside Up portal opens at different times each day. How do I predict when?
```

## 3. Evidence

The intake node categorized the complaint as `portal`.

Validation recorded:

```text
Category 'portal' is supported.
```

The investigation node retrieved this lore and stored it in `state["evidence"]`:

```text
Portals open when the barrier between worlds is weak. Their timing follows
electrical activity, not the clock.
```

The recorded workflow path was:

```text
intake → validate → investigate → resolve → close
```

Representative trace lines were:

```text
[ROUTE] Complaint is valid; sending it to investigate.
[INVESTIGATE] Category: portal
[INVESTIGATE] Evidence source: Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
[RESOLVE] Investigation evidence: Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
```

The five-complaint test produced four `closed` results and one `rejected` result.

## 4. Final output

```text
Complaint closed successfully. Resolution: The Downside Up portal opens at varying times each day due to its dependence on electrical activity rather than a set schedule. To predict when it will open, monitor electrical activity patterns in your area.
```

## 5. Trace: which claim comes from which lore line?

| Answer claim | Supporting evidence | Assessment |
|---|---|---|
| The portal does not follow a fixed schedule. | “Their timing follows electrical activity, not the clock.” | Supported paraphrase. |
| The portal opens at varying times. | “Their timing follows electrical activity, not the clock.” | Supported inference. |
| Monitor electrical activity patterns in your area. | No lore line explicitly recommends monitoring a local area. | Grounding risk; plausible but unsupported advice. |

## 6. Failure or limitation

The workflow constrains the prompts to use the lore, but the LLM can still add a
plausible recommendation that is not present in the source. The current state
stores the lore as evidence but does not automatically check every sentence of
the generated resolution against that evidence. A stronger version would add a
claim-checking or human-review node before closure and store the LLM's
investigation answer separately from the source evidence.

The invalid test complaint demonstrated the guardrail:

```text
Category: other
Status: rejected
Path: intake → validate → reject
```

## 7. LangGraph vs. one LLM call

| | LangGraph | One LLM call |
|---|---|---|
| Same answer every run? | More consistent because the path and prompts are fixed, although LLM output can still vary. | No guarantee. |
| Invalid complaint rejected? | Yes, through validation and conditional routing. | No built-in rejection step. |
| Path visible? | Yes, through `workflow_path`. | No. |
| Source of each claim? | The lore is stored in `evidence` and shown in the trace. | No explicit source trace. |
| Best use case | Strict, auditable complaint processing. | Fast, open-ended responses. |

