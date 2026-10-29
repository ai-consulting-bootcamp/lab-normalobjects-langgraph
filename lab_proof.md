# Lab Proof: NormalObjects Complaint Processor

## 1. What I built

I built a LangGraph complaint-processing workflow for the Hawkins Lab / Downside Up scenario. The app accepts a complaint, classifies it into a valid category, validates whether it is in-scope, investigates it using a fixed lore base, drafts a response, and closes the case with a recorded workflow path.

The workflow is implemented in `normalobjects_langgraph.ipynb` as a `StateGraph` with these nodes:

- intake
- validate
- reject (terminal invalid branch)
- investigate
- resolve
- close

The main state is defined as a `TypedDict` with fields for `complaint`, `category`, `lore`, `findings`, `resolution`, `summary`, `workflow_path`, and `status`.

## 2. Query

The notebook starts with this example complaint:

```python
initial_state = {
    "complaint": "The Downside Up portal opens at different times each day. How do I predict when?",
    "category": "",
    "lore": "",
    "findings": "",
    "resolution": "",
    "workflow_path": [],
    "status": "new",
}
```

and the valid categories are:

- `portal`
- `monster`
- `psychic`
- `environmental`

Anything else is rejected.

The workflow path is:

```text
intake → validate → investigate → resolve → close
              │
              └── invalid ─→ reject
```

This is codified in the notebook with:

```python
graph.add_edge(START, "intake")
graph.add_edge("intake", "validate")
graph.add_conditional_edges("validate", route_after_validate, {"investigate": "investigate", "reject": "reject"})
graph.add_edge("investigate", "resolve")
graph.add_edge("resolve", "close")
graph.add_edge("close", END)
graph.add_edge("reject", END)
```

## 3. Evidence (workflow path + log lines + lore used)

The lore dictionary is explicitly defined as:

```python
LORE = {
    "portal": "Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.",
    "monster": "Demogorgons act alone when hunting, but follow a hive mind when a larger entity controls them.",
    "psychic": "Psychic power drains the user's energy. Bigger or heavier objects need more energy, and nosebleeds are a warning sign.",
    "environmental": "Creatures from the Downside Up disturb electricity: lights flicker and power lines react when they are near.",
}
```

The observed runtime trace from the notebook shows:

```text
[INTAKE] Processing complaint...
[INTAKE] Categorized as: portal

[INVESTIGATE] Looking up lore and analyzing...

[RESOLVE] Drafting resolution...

[CLOSE] Building final record...
path: ['intake', 'validate', 'investigate', 'resolve', 'close']
```

The notebook also tests multiple complaints and shows:

```text
['intake', 'validate', 'investigate', 'resolve', 'close'] closed
['intake', 'validate', 'investigate', 'resolve', 'close'] closed
['intake', 'validate', 'investigate', 'resolve', 'close'] closed
['intake', 'validate', 'investigate', 'resolve', 'close'] closed
['intake', 'validate', 'reject'] rejected
```

That final rejected case is the invalid complaint:

```python
"This is not a valid complaint about something random"
```

## 4. Final output

For the sample portal complaint, the notebook produces a case closure summary shaped like this:

```text
CASE CLOSED
Category:   portal
Complaint:  The Downside Up portal opens at different times each day. How do I predict when?
Findings:   1. The root cause ...
Resolution: Dear [Complainant's Name], ...
Path:       intake -> validate -> investigate -> resolve -> close
```

The actual generated investigation findings for the portal complaint are:

```text
1. The root cause of the issue is the unpredictable nature of the Downside Up portal's opening times, which vary daily.

2. The part of the lore that explains this is that portals open when the barrier between worlds is weak, and their timing is influenced by electrical activity rather than a fixed schedule.

3. The lore does not cover specific methods for predicting electrical activity or how to measure the strength of the barrier between worlds. It also does not provide information on the duration of portal openings or any external factors that might influence their occurrence.
```

The final response is grounded in these findings and explicitly says if the lore is silent, the system does not invent unsupported details.

## 5. Trace (which claim comes from which lore line?)

This is the trace for the portal complaint:

- Claim: the portal opens unpredictably
  - Source: `LORE["portal"] = "Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock."`

- Claim: the root cause is variable electrical activity and barrier weakness
  - Source: the same portal lore line plus the LLM investigation prompt, which instructs the model to use only that lore.

- Claim: there is no precise prediction mechanism in the known lore
  - Source: the notebook’s `investigate` function explicitly says to list anything the lore does not cover so the model does not invent facts.

- Claim: the response should recommend monitoring electrical activity and local conditions
  - Source: the `resolve` step uses the findings and then writes a practical response while staying honest about missing information.

In other words, the notebook is designed so the model reasons from a small fixed lore dataset and refuses to invent unsupported facts.

## 6. Failure or limitation

This workflow is intentionally narrow and has a few important limitations:

- It only recognizes four in-scope categories: `portal`, `monster`, `psychic`, and `environmental`.
- It relies on an LLM to classify complaints, so classification errors are possible.
- It uses a small static lore dictionary, not a real knowledge base or retrieval system.
- The workflow does not verify claims against external ground truth; it only reasons within the supplied lore.
- The `resolve` step can only be as reliable as the findings, and if the lore is incomplete, it is supposed to say so honestly instead of inventing details.

The notebook explicitly handles the invalid case by rejecting non-matching categories, which is a good guardrail, but it is still a highly controlled toy example, not production-grade triage.

## 7. LangGraph vs. one LLM call

A single LLM call would have been much simpler, for example: one prompt that asks the model to classify, investigate, and draft a resolution in one shot.

The LangGraph version is better because it separates responsibilities into explicit stages:

- `intake` classifies the complaint
- `validate` checks whether it is in scope
- `investigate` grounds the answer in a fixed lore source
- `resolve` drafts a response
- `close` records a final structured summary

This gives the workflow several benefits:

- state is tracked across steps (`workflow_path`, `status`, `category`, `findings`)
- invalid inputs can be routed to `reject`
- each stage can be debugged and inspected independently
- the system produces a durable record of the case flow
- the pipeline is easier to extend than a single black-box prompt

So the notebook demonstrates that LangGraph adds structure, auditing, and control flow over a bare one-shot LLM response, which is exactly the point of using a graph-based orchestration pattern.