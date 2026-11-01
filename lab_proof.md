# Lab proof — reviewer entry point

Start here: [workflow](normalobjects_langgraph.py), [tests](test_workflow.py), [dependencies](requirements.txt).

Reproduce from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python normalobjects_langgraph.py
```

The records in `KNOWLEDGE_BASE` are explicitly fictional lab data, not verified story canon.

## Actual test run

Final verification in the clean submission clone used the existing environment:

Command: `/Users/seanl/Desktop/lab-normalobjects-langgraph/.venv/bin/python -m pytest -q`

The reproduction command above uses a local `.venv` with the same pinned dependencies.

```text
11 passed, 13 warnings in 0.16s
```

Warnings originated in LangSmith: `asyncio.iscoroutinefunction` is deprecated in Python 3.14.

This is the latest actual review run; the earlier implementation run reported 11 passed, 13 warnings in 0.66s. A separate review check parsed both recorded JSON event streams and final states below and compared them with fresh workflow executions. All four comparisons matched exactly.

## Mandatory requirement review

| Requirement | Evidence and review status |
| --- | --- |
| Five requested project files | Present: `normalobjects_langgraph.py`, `test_workflow.py`, `requirements.txt`, `lab_proof.md`, `.gitignore`. |
| `ComplaintState` uses `TypedDict` with all eight fields | Verified in source: complaint, category, valid, validation_reason, evidence, resolution, status, workflow_path. |
| Five nodes | Source defines and registers intake, validate, investigate, resolve, close. |
| Five intake categories | Rules produce portal, monster, psychic, environmental, or other. Keyword validation has the limitations listed below. |
| Validation rejects invalid/unrelated complaints | Required invalid example, empty strings, whitespace, and an unrelated elevator query are tested. Arbitrary semantic invalidity is not established. |
| Explicit fictional knowledge base | Four records, each with source_id, category, factual_content, recommended_action. |
| Evidence-only resolution and missing-evidence response | `resolve` copies retrieved facts/actions. Supported-case tests assert exact response equality; the empty-KB test asserts the unavailable-evidence message. |
| Closure status | Valid cases close as resolved; invalid cases close as rejected. |
| Required conditional graph | Source wires START → intake → validate, then investigate → resolve → close for valid cases or directly close for invalid cases, then END. START/END are graph sentinels, not entries in workflow_path. |
| All five specified complaints execute | Four parametrized supported cases plus the required invalid case run in pytest. |
| Valid complaints reach investigation | All four supported cases assert the full path and retrieved record; a separate portal stream test checks actual node execution. |
| Invalid complaints skip investigation and resolution | Rejected-case tests inspect actual streamed node names and assert the three-node path. |
| Supported resolutions cite source IDs | All four supported cases assert exact output including the expected source ID. |
| Workflow path recorded correctly | Supported and rejected paths asserted; actual streams checked for the portal and rejected cases. |
| Complete supported trace | Recorded below: original query, category, validation decision, source ID, exact evidence, response, and path; matched fresh execution during review. |
| Rejected trace | Recorded below and matched fresh execution; empty evidence and skipped nodes are visible. |
| Comparison on all five required dimensions | Author’s comparison is below; previous-agent execution evidence is unavailable. |
| Security exclusions | `.gitignore` excludes `.env` variants, virtual environments, caches, and common credential files. This does not detect secrets embedded in source or prove repository history is secret-free. |
| Simple local workflow | No UI, database, deployment, or external API calls in the workflow. |
| Written explanation and reflection ownership | Author’s explanations preserved; technical descriptions checked against source. |

## Complete supported execution

Actual node updates, in execution order:

```json
[
  {
    "intake": {
      "category": "portal",
      "valid": false,
      "validation_reason": "",
      "evidence": [],
      "resolution": "",
      "status": "processing",
      "workflow_path": [
        "intake"
      ]
    }
  },
  {
    "validate": {
      "valid": true,
      "validation_reason": "Recognized complaint category.",
      "workflow_path": [
        "intake",
        "validate"
      ]
    }
  },
  {
    "investigate": {
      "evidence": [
        {
          "source_id": "NO-PORTAL-001",
          "category": "portal",
          "factual_content": "Downside Up portal opening times vary. No reliable prediction rule is available in this record.",
          "recommended_action": "Record observed opening times; do not promise a predicted opening."
        }
      ],
      "workflow_path": [
        "intake",
        "validate",
        "investigate"
      ]
    }
  },
  {
    "resolve": {
      "resolution": "[NO-PORTAL-001] Downside Up portal opening times vary. No reliable prediction rule is available in this record. Recommended action: Record observed opening times; do not promise a predicted opening.",
      "workflow_path": [
        "intake",
        "validate",
        "investigate",
        "resolve"
      ]
    }
  },
  {
    "close": {
      "status": "resolved",
      "resolution": "[NO-PORTAL-001] Downside Up portal opening times vary. No reliable prediction rule is available in this record. Recommended action: Record observed opening times; do not promise a predicted opening.",
      "workflow_path": [
        "intake",
        "validate",
        "investigate",
        "resolve",
        "close"
      ]
    }
  }
]
```

Complete final state (original query, category, validation decision, source ID, exact retrieved content, final response, status, and workflow path):

```json
{
  "complaint": "The Downside Up portal opens at different times each day.\nHow do I predict when?",
  "category": "portal",
  "valid": true,
  "validation_reason": "Recognized complaint category.",
  "evidence": [
    {
      "source_id": "NO-PORTAL-001",
      "category": "portal",
      "factual_content": "Downside Up portal opening times vary. No reliable prediction rule is available in this record.",
      "recommended_action": "Record observed opening times; do not promise a predicted opening."
    }
  ],
  "resolution": "[NO-PORTAL-001] Downside Up portal opening times vary. No reliable prediction rule is available in this record. Recommended action: Record observed opening times; do not promise a predicted opening.",
  "status": "resolved",
  "workflow_path": [
    "intake",
    "validate",
    "investigate",
    "resolve",
    "close"
  ]
}
```

## Rejected complaint

Actual node updates, in execution order:

```json
[
  {
    "intake": {
      "category": "other",
      "valid": false,
      "validation_reason": "",
      "evidence": [],
      "resolution": "",
      "status": "processing",
      "workflow_path": [
        "intake"
      ]
    }
  },
  {
    "validate": {
      "valid": false,
      "validation_reason": "Empty or unrelated complaint; no supported category.",
      "workflow_path": [
        "intake",
        "validate"
      ]
    }
  },
  {
    "close": {
      "status": "rejected",
      "resolution": "Rejected: Empty or unrelated complaint; no supported category.",
      "workflow_path": [
        "intake",
        "validate",
        "close"
      ]
    }
  }
]
```

Complete final state (original query, category, validation decision, source ID, exact retrieved content, final response, status, and workflow path):

```json
{
  "complaint": "This is not a valid complaint about something random",
  "category": "other",
  "valid": false,
  "validation_reason": "Empty or unrelated complaint; no supported category.",
  "evidence": [],
  "resolution": "Rejected: Empty or unrelated complaint; no supported category.",
  "status": "rejected",
  "workflow_path": [
    "intake",
    "validate",
    "close"
  ]
}
```

## State and nodes

`ComplaintState` is a `TypedDict`. The caller supplies complaint; intake initializes the other fields. Nodes return partial dictionaries merged into state by LangGraph.

| Field | Meaning |
| --- | --- |
| complaint | Original complaint string, preserved throughout. |
| category | First matching keyword category, or other. |
| valid | Validation decision; initially false. |
| validation_reason | Explanation for acceptance or rejection. |
| evidence | Retrieved records containing source_id, category, factual_content, recommended_action. |
| resolution | Supported response, unavailable-evidence message, or rejection message. |
| status | processing after intake; resolved or rejected after close. |
| workflow_path | Ordered executed node names. |

1. `intake` case-folds the complaint, applies keyword rules, and initializes state. Environmental rules take precedence for mixed topics.
2. `validate` accepts a nonblank complaint whose category is not other and records its reason. This is keyword-based scope validation, not semantic verification.
3. `investigate` copies knowledge-base records matching the category into evidence.
4. `resolve` copies only retrieved factual_content and recommended_action, citing the source ID. Empty evidence produces exactly: “Evidence is unavailable. No supported resolution can be provided.”
5. `close` sets resolved for valid complaints and preserves their response; invalid complaints become rejected with the validation reason.

## Workflow routes

Both routes match `build_workflow`: the conditional edge maps true to investigate and false to close, and the other edges are explicit.

Valid:

```text
START → intake → validate → investigate → resolve → close → END
```

Invalid:

```text
START → intake → validate → close → END
```

START and END are graph sentinels; workflow_path contains node names only. The streamed traces show actual execution order for both branches, and pytest checks paths and streamed node execution.

## Meaning of resolved

`resolved` means the complaint completed the processing workflow. It does not mean a real-world problem was fixed. Valid complaints receive this status even when evidence is unavailable. This program does not execute recommended actions or modify external systems.

### Your explanation: risk of unsupported answers

Unsupported answers are risky because they may sound convincing even when they are not based on actual evidence. In our complaint processor, incorrect categorization could lead to irrelevant information being retrieved. The system should therefore only provide resolutions supported by its knowledge base and explicitly acknowledge when evidence is missing.

Evidence you can refer to: the portal record supplies no prediction rule; the psychic record supplies no numerical weight limit; the environmental record supplies no causal mechanism. The missing-evidence test temporarily empties the knowledge base and checks the exact fallback response.

### Your explanation: how the trace demonstrates grounding

The source ID identifies the knowledge-base record used during the investigation. The retrieved text shows the information available to the system, while the final response demonstrates how that information was applied to the complaint. By comparing these three elements, we can check whether the resolution is supported by the evidence rather than invented. The recorded workflow path also shows which processing steps were executed.

Review facts: the final response reproduces the retrieved factual content and recommended action with its source ID. The actual streamed updates show investigation before resolution. This demonstrates grounding for this recorded execution; a citation alone would not prove grounding, and these fictional records do not establish external truth. The exact-output tests provide additional evidence for all four supported examples.

## Comparison with your previous creative LangChain agent

In the previous LangChain lab, the agent had more freedom to decide how to use tools and generate creative responses to complaints. Tool selection and the final answer were less strictly controlled by a predefined workflow. In this LangGraph lab, we explicitly define each processing step and use conditional routing. This makes the process more predictable, easier to test, and easier to debug.

The previous-agent description above is the author's account; its code and outputs are not present in this project and have not been independently verified. The table organizes that account alongside observable facts about this workflow. These are comparisons of the two lab implementations, not universal claims about the frameworks.

| Dimension | Current workflow: observable behavior | Previous agent: your evidence and explanation |
| --- | --- | --- |
| Predictability | Fixed keyword rules and deterministic response formatting | More freedom to generate creative responses; final answers were less strictly controlled, according to the author's account. |
| Tool selection | One local retrieval function; no model selects tools | The agent had more freedom to decide how to use tools, according to the author's account. |
| Conditional routing | Validation selects investigation or immediate closure | Processing was less strictly controlled by a predefined workflow, according to the author's account. |
| Grounding | Copies retrieved facts/actions or reports unavailable evidence | Creative generation was described by the author; previous grounding constraints cannot be verified without execution evidence. |
| Traceability | Evidence, validation reason, node path, and streamed updates are inspectable | Previous logging and trace contents are unavailable, so completeness cannot be compared empirically. |

Previous-agent files were not found in this project, the fork, or the nearby course folder inspected during review. Previous-agent execution evidence is unavailable. The comparison relies on the author’s account and does not establish that the previous agent hallucinated or lacked logging.

## Limitations and review notes

- Classification uses keywords, not semantic understanding; keyword matches can accept irrelevant text and unlisted wording can be rejected.
- Mixed topics use the first matching category, with environmental rules first.
- Source IDs establish provenance within the fictional knowledge base, not external truth.
- Dependency versions match the installed environment; transitive dependencies are not locked.
- `.gitignore` excludes common secret and cache files; never place secrets in tracked source files.
- The three explanations were supplied by the author. Technical descriptions match source. No learning reflection has been written on the author’s behalf.
