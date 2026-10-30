# Lab Proof — NormalObjects Strict Complaint Processor (LangGraph)

## 1. Objective

Build and evaluate a structured complaint-processing workflow in LangGraph. Demonstrate that one complaint can be traced from the user query through categorization, validation, source retrieval, and final response.

The goal is to verify that the final response is supported by inspectable evidence, not merely that the workflow executes successfully.

**Implementation:** `normalobjects_langgraph.ipynb`

**Evidence source:** Local `LORE` Python dictionary (no vector database or external search required).

## 2. Workflow and Decision Logic

The workflow is implemented using `StateGraph(ComplaintState)`.

It uses an LLM for categorization, investigation, and resolution, while deterministic Python rules control validation and routing.

**Workflow structure:**

```text
START → intake → validate
                     ├── Valid → investigate → resolve → close → END
                     └── Invalid → reject → END
```

**Workflow nodes:**

- **Intake:** Classifies the complaint as `portal`, `monster`, `psychic`, `environmental`, or `other`.
- **Validate:** Accepts only categories defined in `VALID_CATEGORIES`.
- **Investigate:** Retrieves `LORE[category]`, saves the original information as evidence, and generates an investigation based only on that source.
- **Resolve:** Generates a short resolution based on the investigation.
- **Close:** Produces the final message and marks the complaint as closed.
- **Reject:** Rejects invalid complaints without unnecessary investigation or resolution.

Each node updates the shared state and records its execution in `workflow_path`.

**Core execution code:**

```python
result = app.invoke(initial_state)

print(result["workflow_path"])
print(result["evidence"])
print(result["resolution"])
print(result["status"])
```

## 3. Test Query and Observed Execution

**Input complaint:**

> The Downside Up portal opens at different times each day. How do I predict when?

**Observed category:** `portal`

**Validation:** `True`

**Validation reason:** `Category 'portal' is allowed.`

**Executed workflow path:**

```text
intake → validate → investigate → resolve → close
```

**Final status:** `closed`

LangGraph successfully selected and executed the valid complaint workflow.

## 4. Retrieved Evidence

The investigation node retrieved the following official information from `LORE["portal"]`:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

**Retrieval method:**

```python
lore_evidence = LORE[category]
```

This information was saved unchanged in the shared state under `evidence`.

The retrieved source can therefore be directly inspected and compared with the generated investigation and final resolution.

## 5. Captured Final Output

The following resolution was generated during Test Case 1 of the five-complaint evaluation:

> The timing of the Downside Up portal openings is influenced by fluctuations in electrical activity, making it impossible to predict exact opening times each day. Unfortunately, without a consistent schedule, you will need to remain attentive to changes in electrical activity to anticipate when the portals may open.

**Closure message:** `Your complaint has been processed.`

**Final workflow status:** `closed`

The complete workflow executed successfully and preserved the relevant evidence in its state.

## 6. Grounding Verification

The final answer was compared with the original LORE evidence.

**Supported statements:**

- Portal openings are connected to electrical activity.
- Portal timing follows electrical activity rather than clock time.

**Statements not fully supported by the source:**

- Electrical fluctuations are the specific mechanism responsible for portal timing.
- Predicting exact opening times is fundamentally impossible.
- Monitoring changes in electrical activity is a reliable way to anticipate portal openings.

The original LORE does not provide an exact prediction method or explain the relationship between electrical activity and portal openings in sufficient detail.

Therefore, the generated resolution contains plausible interpretations that are not explicitly supported by the available evidence.

## 7. Failure Mode and Limitation

**Observed failure mode: Unsupported inference during response generation.**

Although the correct LORE entry was retrieved, the final resolution introduced a recommendation to monitor electrical activity.

This recommendation sounds reasonable, but the source does not establish such a prediction method.

**Possible cause:**

The resolution node receives the LLM-generated investigation instead of independently verifying the final answer against the original evidence.

This creates a risk that unsupported interpretations introduced during investigation are carried forward or amplified during resolution.

**Suggested improvements:**

- Provide the original LORE evidence directly to the resolution node.
- Require the model to explicitly acknowledge insufficient information.
- Add an additional grounding-validation step before closing the complaint.
- Reject or revise responses containing unsupported claims.

This demonstrates that correct evidence retrieval alone does not guarantee a fully grounded final answer.

## 8. Additional Evaluation Results

The complete LangGraph workflow was tested with five complaints covering all available categories.

| Metric | Observed Result |
|---|---|
| Total test cases | 5 |
| Correct categories | 5/5 |
| Category accuracy | 100% |
| Correct workflow paths | 5/5 |
| Successfully closed complaints | 4 |
| Correctly rejected complaints | 1 |
| Exact LORE evidence matches | 4/4 |

**Valid complaint workflow:**

```text
START → intake → validate → investigate → resolve → close → END
```

**Invalid complaint workflow:**

```text
START → intake → validate → reject → END
```

The rejection path successfully skipped investigation and resolution.

**Evaluation limitation:**

The results demonstrate correct routing, categorization, and evidence transfer for these five test cases.

However, a small test set does not establish general classification reliability, and exact evidence matches do not guarantee that every generated statement is fully grounded.

## 9. LangGraph vs. LangChain Approach

LangGraph was selected because the complaint-processing task requires a structured and predictable workflow.

**LangGraph advantages:**

- Explicit control over workflow execution
- Deterministic validation and conditional routing
- Shared state across processing steps
- Traceable execution paths
- Controlled access to predefined evidence
- Clear separation between valid and rejected complaints

A more flexible LangChain tool-calling agent could dynamically select tools and determine which actions to perform.

However, this additional flexibility is not necessary for the current complaint-processing workflow.

For this use case, explicit orchestration provides greater transparency and control while still allowing LLM-based interpretation where needed.

## 10. Conclusion

The NormalObjects Strict Complaint Processor successfully demonstrates a structured LangGraph workflow combining LLM-based interpretation with deterministic validation and routing.

The implementation achieved correct categorization and workflow execution for all five test complaints and preserved the original LORE evidence for each accepted complaint.

The most important learning outcome is that **successful execution and correct retrieval do not automatically guarantee a fully grounded final response**.

The identified grounding limitation demonstrates why production-grade AI systems require explicit evidence verification, careful context management, and additional validation before presenting final answers as reliable.
