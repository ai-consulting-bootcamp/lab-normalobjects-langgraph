# Lab Proof: NormalObjects Complaint Processor

## Workflow

```mermaid
flowchart TD
    A[Complaint] --> B[Intake: classify complaint]
    B --> C[Validate: check category]
    C -->|Valid| D[Investigate: use matching LORE]
    D --> E[Resolve: write a short answer]
    E --> F[Close: return final response]
    C -->|Invalid| G[Reject: explain reason]
    ```

## Query

“The Downside Up portal opens at different times each day. How do I predict when?”

## Evidence

The workflow retrieved this text from `LORE`:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

## Final Output

> Your complaint has been reviewed. Thank you for your complaint regarding the Downside Up portal's opening times. Our investigation has confirmed that the portal opens based on electrical activity rather than a set schedule, making it unpredictable. Unfortunately, this means there is no way to forecast when the portal will open each day.

## Batch Test

Five sample complaints were tested: 4 were closed and 1 was rejected. The invalid complaint followed `intake → validate → reject`.

## Comparison with One Direct LLM Call

The direct LLM response introduced system maintenance, updates, user demand, social media updates, and notifications. Those claims were not present in the source text.

## Failure or Limitation

The graph stored and displayed the source evidence, but its final answer overclaimed: the source says timing follows electrical activity; it does not say forecasting is impossible.