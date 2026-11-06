# Proof of Learning: Strict Complaint Processor

## Workflow

`normalobjects_langgraph.py` stores the complaint, LLM category, validation result, investigation evidence, resolution, final output, status, and executed-node path in `ComplaintState`. The five nodes handle intake, validation, investigation, resolution, and closure. Validation routes supported categories through investigation and resolution; `other` goes directly to closure for rejection.

## Recorded run

**Complaint:** The Downside Up portal opens at different times each day. How do I predict when?

The run produced these state changes and path:

```text
[INTAKE] category=portal | status=categorized | workflow_path=intake
[VALIDATION] accepted | evidence='portal' is a supported complaint category. | status=validated | workflow_path=intake -> validation
[INVESTIGATION] evidence=Hawkins records say unstable portals can hum, flicker, and react to nearby power. They do not provide a schedule for portal openings. | workflow_path=intake -> validation -> investigation
[RESOLUTION] Keep a dated log of opening times and nearby power changes. The records give no schedule, so treat this as observation rather than prediction. | workflow_path=intake -> validation -> investigation -> resolution
[CLOSURE] status=closed | workflow_path=intake -> validation -> investigation -> resolution -> closure
Final status: closed
```

**Final output:** Keep a dated log of opening times and nearby power changes. The records give no schedule, so treat this as observation rather than prediction. Evidence: Hawkins records say unstable portals can hum, flicker, and react to nearby power. They do not provide a schedule for portal openings.

All five sample complaints were run. The unrelated complaint was categorized as `other`, rejected by validation, and closed through `intake -> validation -> closure`; it did not enter investigation or resolution.

## Limitation

The portal record contains no opening schedule. The workflow can suggest recording times and nearby power changes, but it cannot predict an opening time from the available evidence.

## Comparison with the LangChain agent

The previous `normalobjects_langchain.py` uses `create_agent` with four tools and a prompt that lets the model select and combine tools as it sees fit. The LangGraph processor uses an LLM for categorization, then follows developer-defined nodes and a conditional edge: supported categories proceed through investigation and resolution, while `other` is rejected. This gives the LangGraph workflow more control over the allowed path, and its path is predictable once categorization is complete. Categorization itself still depends on the LLM. The LangChain trace records selected tools and their outputs; this LangGraph trace records node order, validation state, and final status.
