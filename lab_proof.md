## 3. Evidence

The following evidence comes from the first complaint in the saved five-complaint test run in `Lab_normalobjects_langgraph.ipynb`.

Complaint: The Downside Up portal opens at different times each day. How do I predict when?

### Workflow path

```text
intake ? validate ? investigate ? resolve ? close
```

The complaint was categorized as `portal` and passed validation. Across the five saved tests, four complaints finished with status `closed`; the unrelated complaint was categorized as `other` and followed `intake ? validate ? reject`, finishing with status `rejected`.

### Logs

These are the recorded log lines for the selected complaint:

```text
[INTAKE] Processing complaint...
[INTAKE] Categorized as: portal

[VALIDATION] Validating complaint...
[VALIDATION] Valid: True. Complaint falls within known categories.

[INVESTIGATION] Investigating complaint...
[INVESTIGATION] Analysis: The lore indicates that portals, including the Downside Up portal, open based on the weakness of the barrier between worlds, which is influenced by electrical activity rather than a set schedule. This means that the timing of the portal's opening is unpredictable and varies daily. 

Summary of evidence: 
- Portals open when the barrier is weak.
- The timing is determined by electrical activity, not by the clock.

Analysis: Since the opening of the Downside Up portal is contingent upon fluctuating electrical activity, there is no reliable method to predict its opening times. The variability in electrical conditions means that one cannot establish a consistent pattern or schedule for when the portal will be accessible. Therefore, it is inherently unpredictable.

[RESOLUTION] Resolving the issue...
[RESOLVE] Issue resolved: Thank you for reaching out! Unfortunately, the Downside Up portal opens based on fluctuating electrical activity, which means its timing is unpredictable and varies daily. While I understand this can be frustrating, there isn't a reliable method to predict when it will open.

[CLOSE] Closing complaint...
[CLOSE] Your complaint has been processed. Thank you for reaching out! Unfortunately, the Downside Up portal opens based on fluctuating electrical activity, which means its timing is unpredictable and varies daily. While I understand this can be frustrating, there isn't a reliable method to predict when it will open. This case is now closed.
```

### Lore used

The exact text stored in the result's `evidence` field was:

> Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.

## 4. Final output

The exact `resolution` was:

> Thank you for reaching out! Unfortunately, the Downside Up portal opens based on fluctuating electrical activity, which means its timing is unpredictable and varies daily. While I understand this can be frustrating, there isn't a reliable method to predict when it will open.

Final status: `closed`.

The closure node appended a closing message and marked the case closed. This status means processing finished; it does not prove that every generated claim was verified.

## 5. Trace

- **Timing depends on electrical activity:** supported by the lore sentence, ?Their timing follows electrical activity, not the clock.?
- **Opening times vary daily:** stated in the complaint, but not independently established by the lore.
- **Electrical activity fluctuates:** an inference made by the model; the supplied lore does not explicitly describe fluctuations.
- **Timing is unpredictable and there is no reliable prediction method:** not established by the lore. Timing following electrical activity does not prove prediction is impossible. The evidence only lacks a prediction method.
- **Friendly greeting and acknowledgement of frustration:** conversational wording, rather than factual claims about the fictional world.

A more carefully grounded response would explain that timing follows electrical activity rather than the clock, and that the supplied lore does not explain how to predict openings. This is a suggested correction, not the actual recorded output.

## 6. Failure or limitation

### Observed grounding limitation

Despite instructions to use only the supplied lore, the investigation concluded that portal timing was inherently unpredictable. The resolution repeated that unsupported conclusion. Restricting the prompt and saving evidence made the issue inspectable, but did not automatically prevent it.

This limitation remains unresolved in the recorded run. An improvement would be to check the investigation and resolution against the original lore before closure, explicitly distinguishing missing information from evidence that something is impossible.

### Execution issue encountered during development

Testing also produced `KeyError: 'is_valid'` during routing and later `KeyError: 'investigation'` during resolution. The notebook's saved execution counts showed that the graph had been built before the updated state definition was executed. Rerunning the state definition, dependent node definitions, and graph-building cell in order addressed the inconsistent definitions; the later saved five-complaint run completed successfully.

## 7. LangGraph vs. one LLM call

The comparison used the same portal complaint. The direct call was:

```python
answer = llm.invoke([HumanMessage(content=test_complaints[0])])
print(answer.content)
```

It used the same configured model through LangChain, without the graph or supplied lore. This compares two application designs, rather than proving that one library inherently produces better answers.

### Actual direct-call answer

To predict when the Downside Up portal opens each day, you can follow these steps:

1. **Collect Data**: Start by recording the opening times of the portal over several days. Note the date and the exact time it opens.

2. **Look for Patterns**: Analyze the data you've collected to identify any patterns. Check if the opening times follow a specific schedule, such as opening at the same time on certain days of the week or if there are any noticeable trends.

3. **Consider External Factors**: Sometimes, external factors such as events, lunar phases, or other occurrences might influence the opening times. Keep track of any such events that coincide with the portal's opening.

4. **Use Statistical Methods**: If you have enough data, you can apply statistical methods to predict future opening times. This could involve calculating averages, medians, or using more complex algorithms if you're familiar with them.

5. **Community Insights**: If there is a community or forum related to the Downside Up portal, consider reaching out to others who may have insights or additional data that could help you predict the opening times.

6. **Trial and Error**: If all else fails, you might need to rely on trial and error. Keep checking at various times throughout the day to see if you can identify a consistent opening window.

By following these steps, you should be able to make more informed predictions about when the Downside Up portal will open each day.

### Comparison with the graph result

- **Answer content:** the graph answer connected timing to electrical activity. The direct call suggested recording times, finding patterns, considering lunar phases or events, using statistical methods, consulting a community, and trying different times. Those suggestions were not backed by the lab's lore, which was not provided to that call.
- **Evidence:** the graph saved the exact lore used, allowing individual claims to be checked. The direct call did not provide an inspectable source for its suggestions. The graph still made the unsupported prediction-impossibility claim identified above.
- **Rejection:** the graph rejected the unrelated fifth complaint in the saved test run. No saved direct-call output for that invalid complaint was available, so its rejection behavior cannot be compared from this evidence.
- **Traceability:** the graph recorded category, validation reason, workflow path, and node logs. The direct call returned answer text without an equivalent application workflow trace.
- **Repeatability:** the graph defines fixed processing routes, but its LLM-generated wording is not guaranteed to be identical. The separately saved portal rerun used different wording. A systematic repeatability test was not performed for the direct call.
- **Client fit:** the graph approach suits complaint processing that needs explicit validation, controlled routing, and evidence records. A direct call suits simpler conversational tasks where that workflow is unnecessary. Either approach needs additional checks when unsupported claims matter.
