# Lab Proof: NormalObjects Strict Complaint Processor (LangGraph)

## 1. What Was Built and How the Artifacts Relate

We implemented a strict, inspectable complaint-processing state machine for the *NormalObjects* bureau using LangGraph. The repository consists of five coordinated artifacts:

1. **[`normalobjects_langgraph.py`](normalobjects_langgraph.py) (Core State Machine & Evidence Helpers)**:
   - **Import-Safe Initialization**: Importing the module has no side effects (`load_dotenv()` and `ChatOpenAI` are never called at import time). Environment loading is handled explicitly by `load_project_env()` (resolving `.env` relative to `PROJECT_DIR`), and model construction is handled by `create_llm(model="gpt-4o-mini", temperature=0.0)`.
   - **Typed State (`ComplaintState`)**: Tracks 11 fields across the graph lifecycle: `complaint`, `raw_category` (exact classifier string prior to normalization), `category` (normalized via `normalize_category()`), `workflow_path`, `status`, `is_valid`, `validation_reason`, `evidence`, `investigation`, `resolution`, and `closure`.
   - **Six Workflow Nodes with Explicit Dependency Injection**:
     - *LLM-backed nodes* (bound via `functools.partial` in `build_workflow(llm)`):
       - `intake_node(state, llm)`: Classifies the complaint, preserves `raw_category`, and normalizes single-token categories via `normalize_category()`.
       - `investigate_node(state, llm)`: Looks up `LORE[state["category"]]`, saves that canonical text in `state["evidence"]`, and applies an intended prompt-level constraint instructing the LLM to investigate the complaint using only that lore text.
       - `resolve_node(state, llm)`: Applies an intended prompt-level constraint instructing the LLM to draft a 1–2 sentence resolution using only `state["investigation"]` (receiving neither the raw `complaint` nor the `LORE` dictionary directly).
     - *Deterministic Python nodes* (zero LLM invocations):
       - `validate_node(state)`: Checks `state["category"] in VALID_CATEGORIES` (`["portal", "monster", "psychic", "environmental"]`) and records `is_valid` and `validation_reason`.
       - `close_node(state)`: Formats `closure` for valid complaints and sets `status = "closed"`.
       - `reject_node(state)`: Formats `closure` with `state["validation_reason"]` for invalid complaints and sets `status = "rejected"`.
   - **Graph Topology & Conditional Routing**:
     - `START → intake → validate`
     - Conditional edge from `validate` via `route_after_validation(state)`: routes deterministically *after* `validate_node` to `investigate` when `state["is_valid"]` is `True` (`investigate → resolve → close → END`) and to `reject` when `state["is_valid"]` is `False` (`reject → END`). Note that rejection (`validate → reject`) is deterministic *after* an unsupported category is produced by `intake_node`, whereas the LLM classifier in `intake_node` can still misclassify an out-of-scope input into one of the four canonical categories.

2. **[`Lab_normalobjects_langgraph.ipynb`](Lab_normalobjects_langgraph.ipynb) (Executed Walkthrough Notebook)**:
   - Imports the implementation from [`normalobjects_langgraph.py`](normalobjects_langgraph.py) and executes all 6 lab steps live against `gpt-4o-mini` (`temperature=0.0`): Step 1 state initialization (`cell-02`, `cell-03`), Step 2 manual node-chain verification (`cell-05`, `cell-06`), Step 3 graph compilation (`cell-08`), Step 4 execution across all 5 sample complaints (`cell-10`), Step 5 Mermaid diagram and path visualization (`cell-12`, `cell-13`), and Step 6 single-LLM baseline comparison and evidence persistence (`cell-15`, `cell-16`).

3. **[`execution_evidence.json`](execution_evidence.json) (Serialized Live Run Evidence)**:
   - Written by `save_execution_evidence()` at the end of `cell-15` during the live notebook run. Captures `model_settings`, `manual_chain_run`, all 5 `complaint_runs` (with `raw_category`, `category`, `is_valid`, `validation_reason`, `workflow_path`, `formatted_path`, `node_logs`, `evidence`, `investigation`, `resolution`, `closure`, `status`), `summary_counts` (`4 closed`, `1 rejected`), `mermaid_diagram`, and `baseline_comparisons`.

4. **[`requirements.txt`](requirements.txt) (Pinned Environment Dependencies)**:
   - Pins the 8 direct runtime, notebook, and testing packages to the exact versions installed in `.venv`: `langgraph==1.2.19`, `langchain-openai==1.7.3`, `langchain-core==1.7.3`, `python-dotenv==1.2.4`, `jupyter==1.1.1`, `ipykernel==7.4.0`, `ipython==9.18.0`, and `pytest==9.2.0`.

5. **[`test_normalobjects_langgraph.py`](test_normalobjects_langgraph.py) (Offline Unit Test Suite)**:
   - Tests import-time safety, exact preservation of `VALID_CATEGORIES`/`LORE`/`TEST_COMPLAINTS`, `normalize_category()` edge cases (whitespace/punctuation stripping vs. empty, unknown, `other`, internal-punctuation, and multiword rejection), prompt isolation between `investigate_node` and `resolve_node`, deterministic execution of `validate_node`/`close_node`/`reject_node`, state isolation across runs, and offline evidence serialization.
   - *Verification status distinction*: We verified [`test_normalobjects_langgraph.py`](test_normalobjects_langgraph.py) via static code inspection; in addition, the project owner reported an offline `pytest` execution result of **17 passed and 13 dependency deprecation warnings** (labeled here explicitly as **owner-reported**).

---

## 2. Primary Proof Query (Exact Portal Complaint)

Our primary proof trace uses **Complaint #1 (`complaint_runs[0]`)** from the compiled LangGraph execution in Step 4 (`cell-10` of [`Lab_normalobjects_langgraph.ipynb`](Lab_normalobjects_langgraph.ipynb) and `complaint_runs[0]` in [`execution_evidence.json`](execution_evidence.json)):

```text
The Downside Up portal opens at different times each day. How do I predict when?
```

> **Note on the two portal executions captured in the notebook**:
> The notebook executes this portal complaint twice in separate steps:
> 1. **`manual_chain_run` (`cell-06`, Step 2)**: Calls `run_manual_node_chain(test_complaints[0], llm)` to verify the five valid-route node functions before graph compilation.
> 2. **`complaint_runs[0]` (`cell-10`, Step 4 — Primary Proof Example)**: Invokes the compiled LangGraph state machine `app.invoke(create_initial_state(test_complaints[0]))` with conditional routing.
>
> We keep these two runs strictly distinct below because, even at `temperature=0.0`, the two separate LLM invocations produced different wording in `investigation` and `resolution`.

---

## 3. Actual Graph Path, Node Log Lines, and Exact Source Lore (`complaint_runs[0]`)

### 3.1 Classification, Validation, and Graph Path
- **Raw Category (`raw_category`)**: `'portal'`
- **Normalized Category (`category`)**: `'portal'`
- **Validation Result (`is_valid`)**: `True`
- **Validation Reason (`validation_reason`)**:
  ```text
  Normalized category 'portal' (from raw output 'portal') is in VALID_CATEGORIES ['portal', 'monster', 'psychic', 'environmental'].
  ```
- **Recorded `workflow_path`**:
  ```json
  ["intake", "validate", "investigate", "resolve", "close"]
  ```
- **Formatted Path (`formatted_path`)**:
  ```text
  intake → validate → investigate → resolve → close
  ```

### 3.2 Exact Captured `[NODE]` Log Lines (`complaint_runs[0]["node_logs"]`)
```text
[INTAKE] Processing complaint...
[INTAKE] Raw category: 'portal' -> Normalized: 'portal'
[INTAKE] Categorized as: portal
[VALIDATE] Checking category against VALID_CATEGORIES...
[VALIDATE] Valid complaint category 'portal'.
[INVESTIGATE] Retrieving canonical lore for category 'portal'...
[INVESTIGATE] Evidence recorded and investigation complete: The Downside Up portal opens when the barrier between worlds is weak, and its timing is influenced by electrical activity rather than a set clock. To predict when the portal will open, you should monitor electrical activity in your area, as fluctuations may indicate when the barrier is weak and a portal is likely to appear.
[RESOLVE] Drafting resolution strictly from investigation findings...
[RESOLVE] Resolution generated: To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances.
[CLOSE] Case closed under category 'portal'. Verified resolution: To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances.
```

### 3.3 Exact Retrieved Source Lore (`complaint_runs[0]["evidence"]` / `LORE["portal"]`)
```text
Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.
```

---

## 4. Exact Captured Final Output (`complaint_runs[0]` vs. `manual_chain_run`)

### 4.1 Primary Graph Execution Output (`complaint_runs[0]`, Step 4 / `cell-10`)
- **`investigation`**:
  > "The Downside Up portal opens when the barrier between worlds is weak, and its timing is influenced by electrical activity rather than a set clock. To predict when the portal will open, you should monitor electrical activity in your area, as fluctuations may indicate when the barrier is weak and a portal is likely to appear."
- **`resolution`**:
  > "To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances."
- **`closure`**:
  > "Case closed under category 'portal'. Verified resolution: To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances."
- **`status`**: `"closed"`

### 4.2 Separate Manual Node-Chain Execution Output (`manual_chain_run`, Step 2 / `cell-06`)
For direct comparison, the earlier manual chain run on the same complaint at `temperature=0.0` produced the following `[INVESTIGATE]`, `[RESOLVE]`, and `[CLOSE]` log outputs:
- **`manual_chain_run` `[INVESTIGATE]`**:
  > "The Downside Up portal opens when the barrier between worlds is weak, and its timing is influenced by electrical activity rather than a set clock. Therefore, to predict when the portal will open, one must monitor electrical activity in the environment, as this will determine the portal's availability each day."
- **`manual_chain_run` `[RESOLVE]`**:
  > "To effectively predict the opening of the Downside Up portal, it is essential to monitor local electrical activity, as fluctuations in this activity directly influence the portal's availability. Implementing a real-time electrical monitoring system will enhance our ability to anticipate portal openings."
- **`manual_chain_run` `[CLOSE]`**:
  > "Case closed under category 'portal'. Verified resolution: To effectively predict the opening of the Downside Up portal, it is essential to monitor local electrical activity, as fluctuations in this activity directly influence the portal's availability. Implementing a real-time electrical monitoring system will enhance our ability to anticipate portal openings."

---

## 5. Claim-to-Source Trace Table (Supported Statements, Inferences, and Unsupported Additions)

The table below maps the claims in our primary proof (`complaint_runs[0]`), its counterpart (`manual_chain_run`), and the remaining valid complaints (`complaint_runs[1..3]`) against `LORE[category]`, distinguishing **Supported Statements**, **Inferences**, and **Unsupported Additions / Overstatements**:

| Run / Node Field | Exact Output Clause | Canonical Source (`LORE[category]`) | Grounding Classification | Trace Analysis |
|---|---|---|---|---|
| `complaint_runs[0]` (`portal`) — `investigation` | *"The Downside Up portal opens when the barrier between worlds is weak..."* | `LORE["portal"]`: *"Portals open when the barrier between worlds is weak."* | **Supported Statement** | Direct paraphrase of the first sentence of `LORE["portal"]`. |
| `complaint_runs[0]` (`portal`) — `investigation` | *"...and its timing is influenced by electrical activity rather than a set clock."* | `LORE["portal"]`: *"Their timing follows electrical activity, not the clock."* | **Supported Statement** | Direct paraphrase of the second sentence of `LORE["portal"]`. |
| `complaint_runs[0]` (`portal`) — `investigation` | *"To predict when the portal will open, you should monitor electrical activity in your area, as fluctuations may indicate when the barrier is weak and a portal is likely to appear."* | `LORE["portal"]`: *"Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock."* | **Inference (Hedged)** | The lore states that timing *follows* electrical activity, so looking at electrical activity rather than a clock is a reasonable inference in response to *"How do I predict when?"*; however, the lore does **not** state that electrical *fluctuations* indicate when the barrier is weak. |
| `complaint_runs[0]` (`portal`) — `resolution` | *"To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances."* | `LORE["portal"]` (via `state["investigation"]`) | **Unsupported Addition / Overstatement** | `resolve_node` upgrades the hedged *"fluctuations may indicate when the barrier is weak"* from `investigation` into the definitive causal claim *"these changes indicate a weakening barrier between worlds"* and asserts that monitoring fluctuations will *"effectively predict"* portal openings. `LORE["portal"]` states a descriptive relationship with electrical activity, not a validated forecasting method. |
| `complaint_runs[0]` (`portal`) — `closure` | *"Case closed under category 'portal'. Verified resolution: ..."* | Deterministic template in `close_node` | **Unsupported Label (Template Artifact)** | `close_node` prefixes the resolution with `"Verified resolution:"` deterministically, even though no node in the graph verifies factual entailment against `LORE["portal"]`. |
| `manual_chain_run` (`portal`) — `resolution` | *"Implementing a real-time electrical monitoring system will enhance our ability to anticipate portal openings."* | `LORE["portal"]` (via `manual_chain_run` `investigation`) | **Unsupported Addition** | Neither `LORE["portal"]` nor the `manual_chain_run` investigation mentions hardware/instrumentation such as a *"real-time electrical monitoring system"*. |
| `complaint_runs[1]` (`monster`) — `investigation` & `resolution` | *"Demogorgons primarily act alone when hunting... However, they can also follow a hive mind when a larger entity exerts control over them."* | `LORE["monster"]`: *"Demogorgons act alone when hunting, but follow a hive mind when a larger entity controls them."* | **Supported Statement** | Faithfully reflects both clauses of `LORE["monster"]`. (Note: explaining *"sometimes fight"* as *"their solitary instincts prevail in the absence of such control"* is an **Inference**, since the lore mentions acting alone when hunting but does not explicitly mention Demogorgons fighting one another.) |
| `complaint_runs[2]` (`psychic`) — `investigation` | *"El's inability to lift heavy rocks with her psychic power is likely due to the energy drain associated with moving larger or heavier objects... Additionally, if she experiences nosebleeds, this could indicate that she is pushing her limits..."* | `LORE["psychic"]`: *"Psychic power drains the user's energy. Bigger or heavier objects need more energy, and nosebleeds are a warning sign."* | **Supported Statement + Conditional Inference** | Accurately grounds the heavy-rock limitation in energy drain and frames nosebleeds conditionally (*"if she experiences nosebleeds"*). |
| `complaint_runs[2]` (`psychic`) — `resolution` | *"The occurrence of nosebleeds suggests she is pushing her limits, further impacting her ability to lift these items."* | `LORE["psychic"]` (via `state["investigation"]`) | **Unsupported Addition (Condition Turned into Fact)** | The complaint (*"El can move things with her mind but can't lift heavy rocks. Why?"*) never states that El had a nosebleed, and `investigation` wrote *"if she experiences nosebleeds"*. `resolve_node` dropped the `"if"` and asserted *"The occurrence of nosebleeds"* as an observed fact. |
| `complaint_runs[3]` (`environmental`) — `investigation` | *"The investigation into the complaint reveals that creatures from the Downside Up disturb electricity, causing lights to flicker and power lines to react when they are in proximity."* | `LORE["environmental"]`: *"Creatures from the Downside Up disturb electricity: lights flicker and power lines react when they are near."* | **Supported Statement** | Directly grounded in `LORE["environmental"]`. |
| `complaint_runs[3]` (`environmental`) — `resolution` | *"To mitigate the disturbances caused by creatures from the Downside Up, it is recommended to implement measures that limit their proximity to electrical systems... Further monitoring of electrical infrastructure in affected areas is advised to assess ongoing impacts."* | `LORE["environmental"]` (via `state["investigation"]`) | **Unsupported Addition** | `LORE["environmental"]` and `state["investigation"]` only describe *why* power lines react when creatures are near. `resolve_node` invents operational interventions (*"implement measures that limit their proximity to electrical systems"* and *"Further monitoring of electrical infrastructure"*) that do not appear in the lore or investigation. |

---

## 6. Observed Failures and Limitations

Inspecting the captured evidence in [`execution_evidence.json`](execution_evidence.json) reveals six concrete limitations in how the workflow operates in practice:

1. **Descriptive Lore vs. Validated Forecasting (`complaint_runs[0]` and `manual_chain_run`)**:
   - `LORE["portal"]` contains two descriptive sentences: *"Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock."*
   - Because the user asks *"How do I predict when?"*, `investigate_node` and `resolve_node` extrapolate from correlation (*timing follows electrical activity*) into an operational forecasting procedure (*"monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds"* in `complaint_runs[0]`, and *"Implementing a real-time electrical monitoring system"* in `manual_chain_run`). The lore never establishes a validated forecasting method or states that electrical fluctuations precede a weakening barrier.

2. **`resolve_node` Introduces Unsourced Operational Prescriptions (`complaint_runs[3]`, Environmental)**:
   - In `complaint_runs[3]`, `investigate_node` stayed close to `LORE["environmental"]`:
     > *"The investigation into the complaint reveals that creatures from the Downside Up disturb electricity, causing lights to flicker and power lines to react when they are in proximity. This interaction suggests that the presence of these creatures interferes with the normal functioning of electrical systems, leading to the observed strange reactions."*
   - However, because `resolve_node` is prompted to *"Write a short resolution (1-2 sentences) based ONLY on the investigation finding"* for a *"why"* question whose lore contains no remediation steps, the LLM invented ungrounded policy recommendations:
     > *"To mitigate the disturbances caused by creatures from the Downside Up, it is recommended to implement measures that limit their proximity to electrical systems, thereby reducing flickering lights and erratic power line behavior. Further monitoring of electrical infrastructure in affected areas is advised to assess ongoing impacts."*
   - Neither proximity-control barriers nor electrical-infrastructure monitoring programs exist in `state["investigation"]` or `LORE["environmental"]`. This demonstrates that source-only prompting in `investigate_node` and `resolve_node` is an intended prompt-level constraint, not a proven guarantee of grounded generation.

3. **Prompt-Chaining Drift: Conditional Warning Turned into Asserted Fact (`complaint_runs[2]`, Psychic)**:
   - Because `resolve_node` only sees `state["investigation"]` (and does not see `state["complaint"]` or `LORE["psychic"]`), small phrasing shifts compound across the chain. In `complaint_runs[2]`, `investigate_node` noted conditionally: *"Additionally, if she experiences nosebleeds, this could indicate that she is pushing her limits"*. `resolve_node` compressed this into: *"The occurrence of nosebleeds suggests she is pushing her limits, further impacting her ability to lift these items"*—asserting that nosebleeds occurred when the user's complaint never mentioned them.

4. **Misleading `"Verified resolution:"` Prefix in `close_node`**:
   - `close_node` is a deterministic Python formatting step:
     ```python
     closure = f"Case closed under category '{category}'. Verified resolution: {resolution}"
     ```
   - Labeling the output `"Verified resolution:"` is a misleading template string: the workflow validates only that `state["category"] in VALID_CATEGORIES` during `validate_node`. There is no post-generation verification node checking whether `investigation` or `resolution` is entailed by `state["evidence"]`.

5. **`status = "closed"` Signifies Graph Completion, Not Factual Grounding or Real-World Resolution**:
   - Setting `status = "closed"` in `close_node` means only that a complaint passed category validation and traversed `intake → validate → investigate → resolve → close` to `END`. It does not prove that every claim in `resolution` is supported by `LORE`, nor does it execute an external action that fixes the anomaly.

6. **Non-Repeatability, Classifier Vulnerability, and Run-to-Run Wording Variation Even at `temperature=0.0`**:
   - Conditional routing (`route_after_validation`) is deterministic **given the validated state**, and `validate_node`, `close_node`, and `reject_node` are deterministic Python functions. Specifically, rejection (`validate → reject`) is deterministic *after* an unsupported category is produced by `intake_node`; however, the LLM classifier in `intake_node` can still misclassify an out-of-scope or ambiguous input into one of the four canonical categories (which would bypass `reject_node` and retrieve the wrong `LORE[category]` entry).
   - Furthermore, `intake_node`, `investigate_node`, and `resolve_node` are live LLM calls. A single notebook execution cannot prove run-to-run stability; in fact, our own evidence file proves the opposite: running the exact same portal complaint at `temperature=0.0` in `manual_chain_run` (`cell-06`) and moments later in `complaint_runs[0]` (`cell-10`) produced noticeably different `investigation` and `resolution` strings.

---

## 7. Comparison with the Two Actual Single-LLM Baseline Responses

In Step 6 (`cell-15`), we passed `test_complaints[0]` (valid portal complaint) and `test_complaints[4]` (invalid random complaint) directly to `ask_single_llm(complaint, llm)` (`llm.invoke([HumanMessage(content=complaint)])` with no graph, no validation guardrail, and no `LORE`).

### 7.1 Valid Complaint Baseline (`test_complaints[0]`)
- **LangGraph `closure` (`complaint_runs[0]`)**:
  > `Case closed under category 'portal'. Verified resolution: To effectively predict the opening of the Downside Up portal, monitor local electrical activity for fluctuations, as these changes indicate a weakening barrier between worlds. This approach will allow for timely awareness of potential portal appearances.`
- **Single LLM Call Response (`baseline_comparisons["valid_complaint"]["single_llm_response"]`)**:
  ```text
  To predict when the Downside Up portal opens, you can follow these steps:

  1. **Historical Data**: Gather data on the opening times of the portal over a period of time. Look for patterns or trends in the times it opens each day.

  2. **Identify Patterns**: Analyze the data for any recurring patterns. For example, does it open at similar times on certain days of the week? Are there any specific intervals between openings?

  3. **External Factors**: Consider any external factors that might influence the opening times, such as events, lunar cycles, or other relevant occurrences.

  4. **Create a Model**: If you have enough data, you could create a predictive model using statistical methods or machine learning techniques to forecast future opening times based on past behavior.

  5. **Stay Updated**: Keep an eye on any announcements or updates from the source that manages the portal, as they may provide clues or schedules for when it will open.

  6. **Community Insights**: Engage with a community of other users who may also be tracking the portal. They might have insights or additional data that can help refine your predictions.

  By combining these approaches, you should be able to make more informed predictions about when the Downside Up portal will open.
  ```
- **Observed Contrast**: The single-LLM baseline does not use the supplied `LORE` and introduces unsupported assumptions (such as lunar cycles, historical opening logs, official schedules, and community insights). While general techniques like historical data analysis and statistical or machine learning models are not inherently contradictory to the lore, the baseline fails to identify the lore's stated link to electrical activity rather than clock time (*"Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock."*).

### 7.2 Invalid Complaint Baseline (`test_complaints[4]`)
- **LangGraph `closure` (`complaint_runs[4]`)**:
  > `Complaint rejected by strict validation guardrail. Reason: Normalized category 'other' (from raw output 'other') is not in VALID_CATEGORIES ['portal', 'monster', 'psychic', 'environmental'].`
- **Single LLM Call Response (`baseline_comparisons["invalid_complaint"]["single_llm_response"]`)**:
  ```text
  It seems like you're looking for a humorous or absurd complaint about something random. Here’s an example:

  "I would like to formally complain about the fact that my pet goldfish, Bubbles, refuses to engage in deep philosophical discussions with me. I have tried everything from Plato to existentialism, yet all I get in return is a blank stare and the occasional bubble. This lack of intellectual stimulation is quite disappointing and frankly, I expected more from a creature that spends all day swimming in circles!"

  Feel free to let me know if you need something different!
  ```
- **Observed Contrast**: In the LangGraph run, `intake_node` classified `test_complaints[4]` as `'other'`, after which `validate_node` and `route_after_validation` deterministically routed it to `reject_node` (`intake → validate → reject`, `status = 'rejected'`). (Note that this rejection is deterministic *after* `intake_node` produces an unsupported category; the LLM classifier in `intake_node` could still misclassify an out-of-scope input into one of the four canonical categories.) By contrast, the unconstrained single LLM call had no validation or rejection mechanism at all and treated the invalid input as a creative writing prompt about a pet goldfish named *Bubbles*.

### 7.3 Structured Comparison Table

| Dimension | LangGraph State Machine (`compile_workflow(llm)`) | One LLM Call (`ask_single_llm(complaint, llm)`) |
|---|---|---|
| **Same answer every run?** | **Conditional routing (`route_after_validation`) and rule nodes (`validate`, `close`, `reject`) are deterministic given the state, but LLM text generation is not identical across invocations even at `temperature=0.0`.** Comparing `manual_chain_run` (`cell-06`) and `complaint_runs[0]` (`cell-10`) on the exact same portal complaint shows identical category classification (`'portal'`) and path (`intake → validate → investigate → resolve → close`), but different generated sentences in `investigation` and `resolution`. | **Not established by this run.** Only one baseline response per complaint (`single_llm_valid` and `single_llm_invalid`) was captured in `cell-15`, so run-to-run repeatability of the single-LLM call was not empirically tested across multiple invocations; structurally, it also lacks a multi-step state schema or deterministic routing. |
| **Invalid complaint rejected?** | **Yes for `complaint_runs[4]`, with deterministic rejection *after* an unsupported category is produced.** `intake_node` classified `test_complaints[4]` as `'other'`, and `validate_node` + `route_after_validation` deterministically routed it to `reject_node` (`intake → validate → reject`, `status = 'rejected'`). However, because `intake_node` relies on an LLM classifier, it can still misclassify an out-of-scope input into one of the four canonical categories. | **No.** Without a validation guardrail or rejection path, the single LLM call answered `test_complaints[4]` by writing a humorous monologue about a pet goldfish named *Bubbles* refusing to discuss Plato and existentialism. |
| **Path visible?** | **Yes.** Every step is recorded in `state["workflow_path"]` and emitted as `[INTAKE]`, `[VALIDATE]`, `[INVESTIGATE]`, `[RESOLVE]`, `[CLOSE]`, or `[REJECT]` log lines stored in [`execution_evidence.json`](execution_evidence.json). | **No.** A single `llm.invoke(...)` call exposes no intermediate decision steps, validation checks, or routing path. |
| **Source of each claim?** | **Explicitly recorded in `state["evidence"]` (`LORE[category]`), enabling claim-by-claim auditing.** Reviewers can verify which statements come from `LORE` (e.g., portal timing following electrical activity rather than the clock) and identify where `investigate_node` or `resolve_node` extrapolates beyond the intended prompt-level constraint (e.g., claiming electrical fluctuations predict a weakening barrier, asserting nosebleeds in `complaint_runs[2]`, or adding proximity/infrastructure controls in `complaint_runs[3]`). | **Unverified parametric memory.** The single-LLM baseline does not use the supplied `LORE` and introduces unsupported assumptions (such as lunar cycles, historical opening logs, official schedules, and community insights); while historical analysis and machine learning are not inherently contradictory to the lore, the baseline fails to identify the lore's stated link to electrical activity rather than clock time. |
| **Best for which client case?** | **Rule-governed, auditable workflows** where out-of-scope categories must be deterministically rejected once flagged by intake, execution paths must be logged, and generated claims must be audited against an explicit evidence record. | **Open-ended creative drafting or informal ideation** where strict input rejection, canonical source binding, and step-level auditability are not required. |
