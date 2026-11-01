"""Deterministic complaint workflow. All lore below is invented lab data."""

import json
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Evidence(TypedDict):
    source_id: str
    category: str
    factual_content: str
    recommended_action: str


class ComplaintState(TypedDict):
    complaint: str
    category: str
    valid: bool
    validation_reason: str
    evidence: list[Evidence]
    resolution: str
    status: str
    workflow_path: list[str]


# Fictional rules for this lab, not claims about canonical story lore.
KNOWLEDGE_BASE: list[Evidence] = [
    {
        "source_id": "NO-PORTAL-001",
        "category": "portal",
        "factual_content": "Downside Up portal opening times vary. No reliable prediction rule is available in this record.",
        "recommended_action": "Record observed opening times; do not promise a predicted opening.",
    },
    {
        "source_id": "NO-MONSTER-001",
        "category": "monster",
        "factual_content": "Demogorgons cooperate when pursuing shared prey and fight over scarce food.",
        "recommended_action": "Observe from a distance and record whether food or shared prey is present.",
    },
    {
        "source_id": "NO-PSYCHIC-001",
        "category": "psychic",
        "factual_content": "El's telekinesis has a limited lifting capacity. This record gives no numerical weight limit or explanation of its cause.",
        "recommended_action": "Avoid heavier lifting attempts and record the observed limitation.",
    },
    {
        "source_id": "NO-ENV-001",
        "category": "environmental",
        "factual_content": "Creature activity near power lines coincides with electrical disturbances. A causal mechanism is unavailable in this record.",
        "recommended_action": "Record the location and timing of disturbances from a distance.",
    },
]

COMPLAINTS = (
    "The Downside Up portal opens at different times each day.\nHow do I predict when?",
    "Demogorgons sometimes work together and sometimes fight.\nWhat's their deal?",
    "El can move things with her mind but can't lift heavy rocks.\nWhy?",
    "Why do creatures and power lines react so strangely together?",
    "This is not a valid complaint about something random",
)


def intake(state: ComplaintState) -> dict:
    text = state["complaint"].casefold()
    # Power lines take precedence over creature words in mixed complaints.
    rules = (
        ("environmental", r"\bpower lines?\b|\belectrical disturbances?\b"),
        ("portal", r"\bportals?\b|\bdownside up\b"),
        ("monster", r"\bdemogorgons?\b|\bmonsters?\b"),
        ("psychic", r"\bel\b|\btelekinesis\b|\bpsychic\b"),
    )
    category = next((name for name, pattern in rules if re.search(pattern, text)), "other")
    return {
        "category": category, "valid": False, "validation_reason": "",
        "evidence": [], "resolution": "", "status": "processing",
        "workflow_path": ["intake"],
    }


def validate(state: ComplaintState) -> dict:
    valid = bool(state["complaint"].strip()) and state["category"] != "other"
    return {
        "valid": valid,
        "validation_reason": "Recognized complaint category." if valid else "Empty or unrelated complaint; no supported category.",
        "workflow_path": state["workflow_path"] + ["validate"],
    }


def investigate(state: ComplaintState) -> dict:
    return {
        "evidence": [dict(record) for record in KNOWLEDGE_BASE if record["category"] == state["category"]],
        "workflow_path": state["workflow_path"] + ["investigate"],
    }


def resolve(state: ComplaintState) -> dict:
    response = "\n".join(
        f'[{record["source_id"]}] {record["factual_content"]} Recommended action: {record["recommended_action"]}'
        for record in state["evidence"]
    ) or "Evidence is unavailable. No supported resolution can be provided."
    return {"resolution": response, "workflow_path": state["workflow_path"] + ["resolve"]}


def close(state: ComplaintState) -> dict:
    return {
        "status": "resolved" if state["valid"] else "rejected",
        "resolution": state["resolution"] if state["valid"] else f'Rejected: {state["validation_reason"]}',
        "workflow_path": state["workflow_path"] + ["close"],
    }


def build_workflow():
    graph = StateGraph(ComplaintState)
    for node in (intake, validate, investigate, resolve, close):
        graph.add_node(node.__name__, node)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "validate")
    graph.add_conditional_edges("validate", lambda state: state["valid"], {True: "investigate", False: "close"})
    graph.add_edge("investigate", "resolve")
    graph.add_edge("resolve", "close")
    graph.add_edge("close", END)
    return graph.compile()


workflow = build_workflow()


def process_complaint(complaint: str) -> ComplaintState:
    return workflow.invoke({"complaint": complaint})


if __name__ == "__main__":
    for complaint in COMPLAINTS:
        print(json.dumps(process_complaint(complaint), indent=2))
