# Lab Proof: NormalObjects Complaint Processor


# Lab Proof: NormalObjects Complaint Processor

## 1. What I Built

I built a structured complaint-processing workflow using LangGraph.

The workflow consists of six nodes:

1. **Intake:** Receives the complaint and uses an LLM to identify its category.
2. **Validation:** Checks whether the category is included in `VALID_CATEGORIES`.
3. **Investigation:** Retrieves relevant information from `LORE` and uses it as evidence to investigate the complaint.
4. **Resolution:** Generates a short resolution based only on the investigation findings.
5. **Closure:** Records the final resolution and marks the complaint as `closed`.
6. **Rejection:** Rejects complaints that fail validation and marks them as `rejected`.

### Workflow Logic

After validation, the workflow follows one of two paths:

**Valid complaint:**

`START → intake → validate → investigate → resolve → close → END`

**Invalid complaint:**

`START → intake → validate → reject → END`

### Testing Results

I tested the workflow using five sample complaints.

- Four complaints were successfully processed and closed.
- One complaint was rejected because it did not match a supported category.
- The workflow recorded the path followed by each complaint.

This demonstrates how LangGraph can control workflow execution, apply validation rules, and make the processing steps traceable.

## 2. Query

### Test Complaint

"The Downside Up portal opens at different times each day. How do I predict when?"

### Purpose of the Test

The purpose of this test was to verify whether the LangGraph workflow could:

1. Receive and categorise the complaint correctly.
2. Validate the complaint against the supported categories.
3. Retrieve relevant information from the provided `LORE`.
4. Generate an answer based on the available evidence.
5. Record the workflow path and final status.

### Expected Behaviour

- **Category:** `portal`
- **Validation:** Valid
- **Evidence source:** `LORE["portal"]`
- **Expected workflow path:** `intake → validate → investigate → resolve → close`
- **Expected final status:** `closed`

## 3. Evidence (Workflow Path + Logs + LORE)

### 3.1 Workflow Path

The tested complaint followed this path:

`intake → validate → investigate → resolve → close`

Final status: `closed`

### 3.2 Workflow Logs

The notebook execution produced the following logs:

```text
[INTAKE] Processing complaint...
[INTAKE] Categorized as: portal

[VALIDATE] Checking complaint category...
[VALIDATE] Category 'portal' is supported.

[INVESTIGATE] Investigating complaint...
[INVESTIGATE] Category: portal
```

These logs show that the complaint was categorised as `portal`, passed validation, and reached the investigation node.

### 3.3 Retrieved Evidence (LORE)

The investigation node retrieved the following text from `LORE["portal"]`:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

**Evidence source:** The `LORE` dictionary defined in Step 2a of the notebook.

### 3.4 Evidence Verification

The retrieved evidence states that portal timing is associated with electrical activity rather than a fixed clock schedule.

The investigation node uses this evidence to answer the complaint, while the resolution node uses the investigation result to prepare its response.

## 4. Final Output

### Complaint

The Downside Up portal opens at different times each day. How do I predict when?

### Identified Category

`portal`
The workflow identified the selected test complaint as belonging
to the `portal` category.

The system also supports three other valid categories:
`monster`, `psychic`, and `environmental`.

Complaints classified as `other` are rejected during validation.

### Investigation Result

The timing of the Downside Up portal openings is influenced by electrical activity rather than a set schedule. Since the barrier between worlds weakens in relation to this electrical activity, predicting the exact times the portal will open each day is not possible with the available evidence. You may need to monitor electrical activity patterns to gain insights, but specific predictions cannot be made based solely on the information provided.

### Final Resolution

Resolution: Due to the unpredictable nature of the Downside Up portal openings, it is recommended to monitor electrical activity patterns regularly. While specific times for portal openings cannot be confirmed, observing these patterns may provide insights that could help in anticipating future openings.

### Closure Message

Complaint processed successfully. Resolution: Resolution: Due to the unpredictable nature of the Downside Up portal openings, it is recommended to monitor electrical activity patterns regularly. While specific times for portal openings cannot be confirmed, observing these patterns may provide insights that could help in anticipating future openings.

### Final Status

`closed`

## 5. Trace (Which Claim Comes From Which LORE Line?)

### Evidence Source

The investigation node retrieved information from `LORE["portal"]`:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

### Claim-to-Evidence Trace

| Claim in the AI Response | Supporting LORE Evidence | Assessment |
|---|---|---|
| Portal openings occur when the barrier between worlds is weak. | "Portals open when the barrier between worlds is weak." | Directly supported |
| Portal timing is influenced by electrical activity. | "Their timing follows electrical activity, not the clock." | Directly supported |
| Portal openings do not follow a fixed clock schedule. | "Their timing follows electrical activity, not the clock." | Supported |
| Monitoring electrical activity may help anticipate openings. | LORE establishes a relationship with electrical activity. | Reasonable suggestion, but not proven |
| Exact opening times cannot be predicted from the available evidence. | LORE provides no exact timing or prediction method. | A limitation of the available evidence |

### Traceability Conclusion

The investigation result is primarily grounded in the retrieved portal LORE.

However, the suggestion to monitor electrical activity is an inference rather than an explicitly documented prediction method.

The workflow therefore provides a traceable evidence source, but the generated answer still requires checking to distinguish supported facts from suggestions.

## 6. Failure or Limitation

### Limitation 1: Duplicate Text in the Closure Message

During testing, I noticed that the final closure message contained the phrase:

`Resolution: Resolution:`

This happened because the resolution node generated a response beginning with "Resolution:", while the closure node also added the same label.

**Impact:**

The complaint was still processed successfully, but the final message contained unnecessary repetition.

**Possible Improvement:**

Modify the closure node to avoid adding "Resolution:" when the resolution text already contains it.

### Limitation 2: Insufficient Evidence for Exact Predictions

The test complaint asked how to predict when the Downside Up portal would open.

The available LORE states:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

However, this information does not explain how to calculate or predict the exact opening times.

**Impact:**

The AI could explain the relationship between electrical activity and portal openings, but it could not provide a reliable prediction method.

**Possible Improvement:**

Provide additional evidence containing measurable electrical activity patterns and historical portal-opening data, if such data becomes available.

### Conclusion

The workflow successfully processed valid complaints and rejected the invalid test complaint.

However, successful execution does not automatically guarantee a perfectly formatted or fully supported answer.

These limitations demonstrate why AI-generated responses should be reviewed for accuracy, evidence and clarity.

## 7. LangGraph vs. One LLM Call

### Comparison

I compared the LangGraph workflow with a direct LLM call using the same test complaints.

| Question | LangGraph Workflow | One LLM Call |
|---|---|---|
| Same answer every run? | Not guaranteed; LLM wording may vary. | Not guaranteed; responses may vary. |
| Invalid complaint rejected? | Yes, the validation node rejected the invalid test complaint. | No, the LLM generated a humorous complaint instead. |
| Workflow path visible? | Yes, each processing step was recorded in `workflow_path`. | No structured workflow path was recorded. |
| Source of each claim? | The retrieved `LORE` evidence was stored and could be inspected. | No specific evidence source was supplied. |
| Best use case? | Controlled processes requiring validation and traceability. | Open-ended questions and creative conversations. |

### Observations from Testing

**LangGraph Workflow**

The LangGraph workflow processed four valid complaints and rejected one invalid complaint.

For valid complaints, the workflow followed:

`intake → validate → investigate → resolve → close`

For the invalid complaint, it followed:

`intake → validate → reject`

This demonstrates how LangGraph can enforce a defined workflow and record the steps taken.

**Direct LLM Call**

When I submitted the portal question directly to the LLM, it suggested ideas such as tracking historical opening times, patterns and lunar cycles.

However, these suggestions were not supported by the provided portal `LORE`.

When I submitted the invalid complaint, the LLM generated a humorous example instead of rejecting the request.

### Conclusion

LangGraph was more suitable for this complaint-processing task because it provided:

- A structured sequence of processing steps.
- Validation and rejection of unsupported categories.
- Retrieval of relevant evidence.
- A visible workflow path for reviewing the results.

A direct LLM call was simpler, but it did not enforce the same validation rules or provide an evidence-based processing structure.

Although LangGraph offers better control and traceability, the quality of its final answers still depends on the available evidence and the behaviour of the LLM.
