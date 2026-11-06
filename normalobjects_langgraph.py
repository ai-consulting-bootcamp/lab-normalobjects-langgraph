"""LangGraph workflow for handling supported Hawkins complaints."""

import os
import re
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


load_dotenv(Path(__file__).with_name(".env"))

CATEGORIES = {"portal", "monster", "psychic", "environmental", "other"}
SUPPORTED_CATEGORIES = {"portal", "monster", "psychic", "environmental"}


class ComplaintState(TypedDict):
    """Information passed between the nodes for one complaint."""

    complaint: str
    category: str
    is_valid: bool
    validation_status: str
    validation_reason: str
    investigation: str
    resolution: str
    final_output: str
    workflow_path: list[str]
    status: str


SAMPLE_COMPLAINTS = [
    "The Downside Up portal opens at different times each day. How do I predict when?",
    "Demogorgons sometimes work together and sometimes fight. What's their deal?",
    "El can move things with her mind but can't lift heavy rocks. Why?",
    "Why do creatures and power lines react so strangely together?",
    "This is not a valid complaint about something random",
]

# These short records give the investigation node a consistent evidence source.
# Their topic wording follows the records in the previous LangChain lab.
INVESTIGATION_NOTES = {
    "portal": (
        "Hawkins records say unstable portals can hum, flicker, and react to nearby "
        "power. They do not provide a schedule for portal openings."
    ),
    "monster": (
        "Hawkins records describe local monsters as attracted to food, blood, and "
        "generally poor security. They do not explain why monsters cooperate or fight."
    ),
    "psychic": (
        "Hawkins records say psychic activity often spikes near dimensional "
        "disturbances. They do not specify limits on lifting ability."
    ),
    "environmental": (
        "Hawkins records report that unusual electrical surges can precede a portal "
        "disturbance. This does not establish that creatures cause the surges."
    ),
}


_classifier = None


def get_classifier() -> ChatOpenAI:
    """Create the complaint classifier once, using the key loaded from the environment."""
    global _classifier
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Put it in the environment or the local .env file."
        )
    if _classifier is None:
        _classifier = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return _classifier


def _parse_category(response_text: str) -> str:
    """Read a category from the model response; use 'other' if it is unrecognized."""
    first_line = response_text.strip().lower().splitlines()[0]
    first_line = first_line.strip(" `\"'.,:;!?()[]{}")
    if first_line in CATEGORIES:
        return first_line
    match = re.search(r"\b(portal|monster|psychic|environmental|other)\b", response_text.lower())
    return match.group(1) if match else "other"


def intake_node(state: ComplaintState) -> dict:
    """Categorize the complaint with the LLM and record the intake state."""
    prompt = f"""Categorize this Downside Up complaint into exactly one category:
- portal: portal timing, location, or behavior
- monster: creature behavior, including demogorgons
- psychic: psychic abilities or limitations
- environmental: electricity, weather, or physical environment
- other: anything else

Complaint: {state['complaint']}

Respond with only one category name: portal, monster, psychic, environmental, or other."""
    response = get_classifier().invoke([HumanMessage(content=prompt)])
    category = _parse_category(str(response.content))
    workflow_path = state["workflow_path"] + ["intake"]
    print(
        f"[INTAKE] category={category} | status=categorized "
        f"| workflow_path={' -> '.join(workflow_path)}"
    )
    return {
        "category": category,
        "status": "categorized",
        "workflow_path": workflow_path,
    }


def validation_node(state: ComplaintState) -> dict:
    """Accept supported categories and reject complaints categorized as 'other'."""
    is_valid = state["category"] in SUPPORTED_CATEGORIES
    if is_valid:
        validation_status = "accepted"
        reason = f"'{state['category']}' is a supported complaint category."
        status = "validated"
    else:
        validation_status = "rejected"
        reason = "The complaint is outside the four supported categories."
        status = "rejected"
    workflow_path = state["workflow_path"] + ["validation"]
    print(
        f"[VALIDATION] {validation_status} | evidence={reason} "
        f"| status={status} | workflow_path={' -> '.join(workflow_path)}"
    )
    return {
        "is_valid": is_valid,
        "validation_status": validation_status,
        "validation_reason": reason,
        "status": status,
        "workflow_path": workflow_path,
    }


def investigation_node(state: ComplaintState) -> dict:
    """Look up the note for the validated category and store it as evidence."""
    investigation = INVESTIGATION_NOTES[state["category"]]
    workflow_path = state["workflow_path"] + ["investigation"]
    print(
        f"[INVESTIGATION] evidence={investigation} "
        f"| workflow_path={' -> '.join(workflow_path)}"
    )
    return {
        "investigation": investigation,
        "status": "investigated",
        "workflow_path": workflow_path,
    }


def resolution_node(state: ComplaintState) -> dict:
    """Choose a conservative next step based on the category's investigation note."""
    resolutions = {
        "portal": (
            "Keep a dated log of opening times and nearby power changes. The records "
            "give no schedule, so treat this as observation rather than prediction."
        ),
        "monster": (
            "Secure food and observe the creatures from a safe distance. The records "
            "do not explain why they cooperate or fight."
        ),
        "psychic": (
            "Do not assume a cause for the lifting limit. Track what feels manageable "
            "and avoid unsafe lifting; the records do not specify a strength limit."
        ),
        "environmental": (
            "Record when the power changes and keep clear of electrical equipment. "
            "The records suggest an association, not proof of cause."
        ),
    }
    resolution = resolutions[state["category"]]
    workflow_path = state["workflow_path"] + ["resolution"]
    print(
        f"[RESOLUTION] {resolution} "
        f"| workflow_path={' -> '.join(workflow_path)}"
    )
    return {
        "resolution": resolution,
        "status": "resolved",
        "workflow_path": workflow_path,
    }


def closure_node(state: ComplaintState) -> dict:
    """Close a processed complaint or return a rejection without resolving it."""
    if state["is_valid"]:
        final_output = f"{state['resolution']} Evidence: {state['investigation']}"
        status = "closed"
    else:
        final_output = f"Rejected: {state['validation_reason']}"
        status = "rejected"
    workflow_path = state["workflow_path"] + ["closure"]
    print(
        f"[CLOSURE] status={status} | workflow_path={' -> '.join(workflow_path)}"
    )
    return {
        "final_output": final_output,
        "status": status,
        "workflow_path": workflow_path,
    }


def route_after_validation(state: ComplaintState) -> str:
    """Send accepted complaints to investigation and rejected ones to closure."""
    return "investigation" if state["is_valid"] else "closure"


def build_workflow():
    """Connect the five nodes into a graph with a validation-based branch."""
    workflow = StateGraph(ComplaintState)
    workflow.add_node("intake", intake_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("investigation", investigation_node)
    workflow.add_node("resolution", resolution_node)
    workflow.add_node("closure", closure_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "validation")
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {"investigation": "investigation", "closure": "closure"},
    )
    workflow.add_edge("investigation", "resolution")
    workflow.add_edge("resolution", "closure")
    workflow.add_edge("closure", END)
    return workflow.compile()


def run_complaint(app, complaint: str) -> ComplaintState:
    """Run one complaint and print its final state for an inspectable trace."""
    print(f"\nComplaint: {complaint}")
    initial_state: ComplaintState = {
        "complaint": complaint,
        "category": "",
        "is_valid": False,
        "validation_status": "pending",
        "validation_reason": "",
        "investigation": "",
        "resolution": "",
        "final_output": "",
        "workflow_path": [],
        "status": "received",
    }
    result = app.invoke(initial_state)
    print(f"Executed nodes: {' -> '.join(result['workflow_path'])}")
    print(f"Final status: {result['status']}")
    print(f"Final output: {result['final_output']}")
    return result


def main() -> int:
    """Run all five lab samples and report API or workflow errors clearly."""
    try:
        app = build_workflow()
        for complaint in SAMPLE_COMPLAINTS:
            run_complaint(app, complaint)
    except Exception as exc:
        details = str(exc)
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            details = details.replace(api_key, "[REDACTED]")
        print(f"Workflow failed ({type(exc).__name__}): {details}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
