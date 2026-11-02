"""NormalObjects Strict Complaint Processor implemented with LangGraph.

This module implements a rule-governed state machine for processing Downside Up
complaints:
    START -> intake -> validate --(valid)--> investigate -> resolve -> close -> END
                          |
                          +--(invalid)--> reject -> END

Design highlights:
- Importing this module has no side effects: it does not read `.env` or
  instantiate `ChatOpenAI` at import time.
- LLM-backed nodes (`intake_node`, `investigate_node`, `resolve_node`) accept an
  explicit `llm` dependency, injected cleanly via `functools.partial` inside
  `build_workflow(llm)`.
- Deterministic nodes (`validate_node`, `close_node`, `reject_node`) execute
  purely in Python without invoking the language model.
- `intake_node` records both the exact `raw_category` returned by the model and
  the cleaned `category` produced by `normalize_category`.
- `investigate_node` grounds its analysis strictly in `LORE[category]` and saves
  that lore string in `state["evidence"]`.
- `resolve_node` derives its recommendation strictly from `state["investigation"]`
  without receiving the raw complaint or lore dictionary directly.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from functools import partial
import io
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypedDict, TypeVar

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

PROJECT_DIR: Path = Path(__file__).resolve().parent
DEFAULT_ENV_PATH: Path = PROJECT_DIR / ".env"
DEFAULT_EVIDENCE_PATH: Path = PROJECT_DIR / "execution_evidence.json"
DEFAULT_MODEL: str = "gpt-4o-mini"
DEFAULT_TEMPERATURE: float = 0.0

CATEGORY_STRIP_CHARS: str = " \t\r\n.!?,;:'\"`"

VALID_CATEGORIES: List[str] = ["portal", "monster", "psychic", "environmental"]

LORE: Dict[str, str] = {
    "portal": "Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.",
    "monster": "Demogorgons act alone when hunting, but follow a hive mind when a larger entity controls them.",
    "psychic": "Psychic power drains the user's energy. Bigger or heavier objects need more energy, and nosebleeds are a warning sign.",
    "environmental": "Creatures from the Downside Up disturb electricity: lights flicker and power lines react when they are near.",
}

TEST_COMPLAINTS: List[str] = [
    "The Downside Up portal opens at different times each day. How do I predict when?",
    "Demogorgons sometimes work together and sometimes fight. What's their deal?",
    "El can move things with her mind but can't lift heavy rocks. Why?",
    "Why do creatures and power lines react so strangely together?",
    "This is not a valid complaint about something random",  # Should be rejected
]

# Alias matching the variable name used in the lab notebook and instructions
test_complaints: List[str] = TEST_COMPLAINTS

T = TypeVar("T")


class ComplaintState(TypedDict):
    """Typed state dictionary flowing through the LangGraph complaint workflow."""

    complaint: str
    raw_category: str
    category: str
    workflow_path: List[str]
    status: str
    is_valid: bool
    validation_reason: str
    evidence: str
    investigation: str
    resolution: str
    closure: str


def load_project_env(dotenv_path: Optional[Path] = None) -> bool:
    """Load environment variables from the project `.env` file without exposing secrets.

    Args:
        dotenv_path: Optional explicit path to a `.env` file. Defaults to
            `PROJECT_DIR / ".env"` so execution does not depend on the caller's
            current working directory.

    Returns:
        True if `OPENAI_API_KEY` is present and non-empty in `os.environ`, False otherwise.
    """
    resolved_path = Path(dotenv_path).resolve() if dotenv_path is not None else DEFAULT_ENV_PATH
    load_dotenv(dotenv_path=resolved_path)
    return bool(os.environ.get("OPENAI_API_KEY"))


def create_llm(
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    load_env: bool = True,
) -> ChatOpenAI:
    """Create a configured `ChatOpenAI` instance after optionally loading `.env`."""
    if load_env:
        load_project_env()
    return ChatOpenAI(model=model, temperature=temperature)


def create_initial_state(complaint: str) -> ComplaintState:
    """Create a fresh initial `ComplaintState` for a single complaint run."""
    return {
        "complaint": complaint,
        "raw_category": "",
        "category": "",
        "workflow_path": [],
        "status": "new",
        "is_valid": False,
        "validation_reason": "",
        "evidence": "",
        "investigation": "",
        "resolution": "",
        "closure": "",
    }


def normalize_category(raw_text: str) -> str:
    """Normalize a raw category output from the LLM classifier.

    Policy:
    - Strips surrounding whitespace and punctuation (`" \\t\\r\\n.!?,;:'\\"`"`),
      then converts to lowercase.
    - Single-token responses with incidental formatting such as `"  PORTAL. "`
      normalize cleanly to `"portal"`.
    - Empty strings, whitespace-only strings, `"unknown"`, `"other"`, or
      multiword responses containing internal whitespace (such as
      `"portal or monster"` or `"category: portal"`) remain outside
      `VALID_CATEGORIES` and are rejected by `validate_node`.
    """
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)
    cleaned = raw_text.strip(CATEGORY_STRIP_CHARS).lower()
    if not cleaned:
        return ""
    if any(ch.isspace() for ch in cleaned):
        return " ".join(cleaned.split())
    return cleaned


def intake_node(state: ComplaintState, llm: Any) -> ComplaintState:
    """Step 1: Intake - Parse and categorize the complaint using the LLM."""
    print("\n[INTAKE] Processing complaint...")

    complaint = state["complaint"]

    categorization_prompt = f"""Categorize this Downside Up complaint into one of these categories:
- portal: Issues with portal timing, location, or behavior
- monster: Issues with creature behavior (demogorgons, etc.)
- psychic: Issues with psychic abilities or limitations
- environmental: Issues with electricity, weather, or physical environment
- other: Anything else

Complaint: {complaint}

Respond with ONLY the category name (portal, monster, psychic, environmental, or other)."""

    response = llm.invoke([HumanMessage(content=categorization_prompt)])
    raw_category = (
        response.content if isinstance(response.content, str) else str(response.content)
    )
    category = normalize_category(raw_category)

    new_state: ComplaintState = {
        **state,
        "raw_category": raw_category,
        "category": category,
        "workflow_path": [*state.get("workflow_path", []), "intake"],
        "status": "intake",
    }

    print(f"[INTAKE] Raw category: {raw_category!r} -> Normalized: {category!r}")
    print(f"[INTAKE] Categorized as: {category}")
    return new_state


def validate_node(state: ComplaintState) -> ComplaintState:
    """Step 2: Validate - Deterministically verify whether the category is supported."""
    print("[VALIDATE] Checking category against VALID_CATEGORIES...")

    raw_category = state.get("raw_category", "")
    category = state.get("category", "")
    is_valid = category in VALID_CATEGORIES

    if is_valid:
        validation_reason = (
            f"Normalized category '{category}' (from raw output {raw_category!r}) "
            f"is in VALID_CATEGORIES {VALID_CATEGORIES}."
        )
        print(f"[VALIDATE] Valid complaint category '{category}'.")
    else:
        validation_reason = (
            f"Normalized category '{category}' (from raw output {raw_category!r}) "
            f"is not in VALID_CATEGORIES {VALID_CATEGORIES}."
        )
        print(f"[VALIDATE] Invalid complaint category '{category}'. Routing to reject.")

    new_state: ComplaintState = {
        **state,
        "is_valid": is_valid,
        "validation_reason": validation_reason,
        "workflow_path": [*state.get("workflow_path", []), "validate"],
        "status": "validated",
    }
    return new_state


def investigate_node(state: ComplaintState, llm: Any) -> ComplaintState:
    """Step 3: Investigate - Look up canonical lore and answer strictly from that lore."""
    category = state["category"]
    lore_text = LORE[category]
    complaint = state["complaint"]

    print(f"[INVESTIGATE] Retrieving canonical lore for category '{category}'...")

    investigation_prompt = f"""You are investigating a Downside Up complaint for the NormalObjects bureau.
Answer the complaint using ONLY the canonical lore provided below.
Do not invent facts, causes, or mechanisms outside the provided lore text.

Canonical Lore ({category}):
{lore_text}

Complaint:
{complaint}

Provide a concise investigation finding grounded strictly in the canonical lore."""

    response = llm.invoke([HumanMessage(content=investigation_prompt)])
    investigation = (
        response.content.strip()
        if isinstance(response.content, str)
        else str(response.content).strip()
    )

    print(f"[INVESTIGATE] Evidence recorded and investigation complete: {investigation}")

    new_state: ComplaintState = {
        **state,
        "evidence": lore_text,
        "investigation": investigation,
        "workflow_path": [*state.get("workflow_path", []), "investigate"],
        "status": "investigated",
    }
    return new_state


def resolve_node(state: ComplaintState, llm: Any) -> ComplaintState:
    """Step 4: Resolve - Propose a short fix based strictly on the investigation finding."""
    investigation = state["investigation"]

    print("[RESOLVE] Drafting resolution strictly from investigation findings...")

    resolution_prompt = f"""You are drafting a short operational fix for a NormalObjects case file.
Write a short resolution (1-2 sentences) based ONLY on the investigation finding below.
Do not introduce outside lore, assumptions, or unverified claims.

Investigation Finding:
{investigation}

Short Resolution (1-2 sentences):"""

    response = llm.invoke([HumanMessage(content=resolution_prompt)])
    resolution = (
        response.content.strip()
        if isinstance(response.content, str)
        else str(response.content).strip()
    )

    print(f"[RESOLVE] Resolution generated: {resolution}")

    new_state: ComplaintState = {
        **state,
        "resolution": resolution,
        "workflow_path": [*state.get("workflow_path", []), "resolve"],
        "status": "resolved",
    }
    return new_state


def close_node(state: ComplaintState) -> ComplaintState:
    """Step 5a: Close - Deterministically format the final closure message."""
    category = state.get("category", "")
    resolution = state.get("resolution", "")

    closure = (
        f"Case closed under category '{category}'. "
        f"Verified resolution: {resolution}"
    )
    print(f"[CLOSE] {closure}")

    new_state: ComplaintState = {
        **state,
        "closure": closure,
        "workflow_path": [*state.get("workflow_path", []), "close"],
        "status": "closed",
    }
    return new_state


def reject_node(state: ComplaintState) -> ComplaintState:
    """Step 5b: Reject - Deterministically reject invalid complaints with the validation reason."""
    reason = state.get("validation_reason", "Category failed validation rules.")

    closure = f"Complaint rejected by strict validation guardrail. Reason: {reason}"
    print(f"[REJECT] {closure}")

    new_state: ComplaintState = {
        **state,
        "closure": closure,
        "workflow_path": [*state.get("workflow_path", []), "reject"],
        "status": "rejected",
    }
    return new_state


def route_after_validation(
    state: ComplaintState,
) -> Literal["investigate", "reject"]:
    """Deterministic conditional routing function evaluated after `validate_node`."""
    if state.get("is_valid", False):
        return "investigate"
    return "reject"


def build_workflow(llm: Any) -> StateGraph:
    """Construct the uncompiled LangGraph `StateGraph` with `llm` bound to LLM nodes."""
    workflow = StateGraph(ComplaintState)

    workflow.add_node("intake", partial(intake_node, llm=llm))
    workflow.add_node("validate", validate_node)
    workflow.add_node("investigate", partial(investigate_node, llm=llm))
    workflow.add_node("resolve", partial(resolve_node, llm=llm))
    workflow.add_node("close", close_node)
    workflow.add_node("reject", reject_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "validate")
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "investigate": "investigate",
            "reject": "reject",
        },
    )
    workflow.add_edge("investigate", "resolve")
    workflow.add_edge("resolve", "close")
    workflow.add_edge("close", END)
    workflow.add_edge("reject", END)

    return workflow


def compile_workflow(llm: Any) -> Any:
    """Build and compile the NormalObjects complaint processor graph."""
    return build_workflow(llm).compile()


def run_manual_node_chain(complaint: str, llm: Any) -> ComplaintState:
    """Run the valid 5-node chain manually (`intake -> validate -> investigate -> resolve -> close`)."""
    state = create_initial_state(complaint)
    state = intake_node(state, llm=llm)
    state = validate_node(state)
    state = investigate_node(state, llm=llm)
    state = resolve_node(state, llm=llm)
    state = close_node(state)
    return state


class _TeeStdout(io.TextIOBase):
    """Internal helper stream that writes simultaneously to standard output and a buffer."""

    def __init__(self, primary: Any, buffer: io.StringIO) -> None:
        self._primary = primary
        self._buffer = buffer

    def write(self, s: str) -> int:
        self._primary.write(s)
        return self._buffer.write(s)

    def flush(self) -> None:
        self._primary.flush()
        self._buffer.flush()


def run_callable_with_logs(func: Callable[[], T]) -> Tuple[T, List[str]]:
    """Execute `func()` while teeing stdout so `[NODE]` logs are both displayed and captured."""
    buffer = io.StringIO()
    tee = _TeeStdout(sys.stdout, buffer)
    with redirect_stdout(tee):
        result = func()
    lines = [line.strip() for line in buffer.getvalue().splitlines() if line.strip()]
    return result, lines


def run_complaint_with_logs(
    app: Any, complaint: str
) -> Tuple[ComplaintState, List[str]]:
    """Invoke a compiled LangGraph workflow on `complaint` and capture printed `[NODE]` logs."""
    initial_state = create_initial_state(complaint)
    return run_callable_with_logs(lambda: app.invoke(initial_state))


def format_workflow_path(workflow_path: List[str]) -> str:
    """Format a workflow path list using arrow notation (`intake → validate → ...`)."""
    return " → ".join(workflow_path)


def ask_single_llm(complaint: str, llm: Any) -> str:
    """Send a complaint directly to a single unconstrained LLM call (no graph, no lore)."""
    response = llm.invoke([HumanMessage(content=complaint)])
    return (
        response.content.strip()
        if isinstance(response.content, str)
        else str(response.content).strip()
    )


def build_execution_evidence(
    *,
    model_name: str,
    temperature: float,
    manual_chain_state: ComplaintState,
    manual_chain_logs: List[str],
    complaint_results: List[Tuple[ComplaintState, List[str]]],
    mermaid_diagram: str,
    single_llm_valid_response: str,
    single_llm_invalid_response: str,
) -> Dict[str, Any]:
    """Assemble a complete, inspectable JSON structure from a single live notebook run."""
    complaint_runs: List[Dict[str, Any]] = []
    closed_count = 0
    rejected_count = 0

    for idx, (state, logs) in enumerate(complaint_results, start=1):
        status = state.get("status", "")
        if status == "closed":
            closed_count += 1
        elif status == "rejected":
            rejected_count += 1

        complaint_runs.append(
            {
                "index": idx,
                "complaint": state["complaint"],
                "raw_category": state["raw_category"],
                "category": state["category"],
                "is_valid": state["is_valid"],
                "validation_reason": state["validation_reason"],
                "workflow_path": list(state["workflow_path"]),
                "formatted_path": format_workflow_path(state["workflow_path"]),
                "node_logs": list(logs),
                "evidence": state["evidence"],
                "investigation": state["investigation"],
                "resolution": state["resolution"],
                "closure": state["closure"],
                "status": status,
            }
        )

    valid_run = complaint_runs[0] if complaint_runs else {}
    invalid_run = complaint_runs[-1] if complaint_runs else {}

    return {
        "model_settings": {
            "model": model_name,
            "temperature": temperature,
        },
        "manual_chain_run": {
            "complaint": manual_chain_state["complaint"],
            "raw_category": manual_chain_state["raw_category"],
            "category": manual_chain_state["category"],
            "workflow_path": list(manual_chain_state["workflow_path"]),
            "formatted_path": format_workflow_path(manual_chain_state["workflow_path"]),
            "node_logs": list(manual_chain_logs),
            "status": manual_chain_state["status"],
        },
        "complaint_runs": complaint_runs,
        "summary_counts": {
            "closed": closed_count,
            "rejected": rejected_count,
            "total": len(complaint_runs),
        },
        "mermaid_diagram": mermaid_diagram,
        "baseline_comparisons": {
            "valid_complaint": {
                "complaint": valid_run.get("complaint", ""),
                "langgraph_category": valid_run.get("category", ""),
                "langgraph_workflow_path": valid_run.get("workflow_path", []),
                "langgraph_evidence": valid_run.get("evidence", ""),
                "langgraph_investigation": valid_run.get("investigation", ""),
                "langgraph_resolution": valid_run.get("resolution", ""),
                "langgraph_closure": valid_run.get("closure", ""),
                "langgraph_status": valid_run.get("status", ""),
                "single_llm_response": single_llm_valid_response,
            },
            "invalid_complaint": {
                "complaint": invalid_run.get("complaint", ""),
                "langgraph_raw_category": invalid_run.get("raw_category", ""),
                "langgraph_category": invalid_run.get("category", ""),
                "langgraph_workflow_path": invalid_run.get("workflow_path", []),
                "langgraph_validation_reason": invalid_run.get("validation_reason", ""),
                "langgraph_closure": invalid_run.get("closure", ""),
                "langgraph_status": invalid_run.get("status", ""),
                "single_llm_response": single_llm_invalid_response,
            },
        },
    }


def save_execution_evidence(
    evidence_data: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> Path:
    """Save the captured execution evidence dictionary to JSON on disk."""
    target_path = (
        Path(output_path).resolve() if output_path is not None else DEFAULT_EVIDENCE_PATH
    )
    target_path.write_text(
        json.dumps(evidence_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target_path
