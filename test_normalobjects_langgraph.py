"""Offline unit test suite for the NormalObjects Strict Complaint Processor.

All tests execute completely offline using deterministic mock/fake LLM objects.
No `.env` file is read and no network or OpenAI API calls are made.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any, List
from unittest.mock import patch

from langchain_core.messages import AIMessage
import pytest

import normalobjects_langgraph as nlg


class RecordingMockLLM:
    """Offline mock LLM that records prompts and returns scripted responses."""

    def __init__(self, scripted_responses: List[str] | None = None) -> None:
        self.scripted_responses: List[str] = list(scripted_responses or [])
        self.calls: List[str] = []

    def invoke(self, messages: List[Any]) -> AIMessage:
        prompt_text = messages[0].content if messages else ""
        self.calls.append(prompt_text)

        if self.scripted_responses:
            return AIMessage(content=self.scripted_responses.pop(0))

        # Default heuristic routing for the 5 standard sample complaints
        if "Categorize this Downside Up complaint" in prompt_text:
            lowered = prompt_text.lower()
            if "portal opens at different times" in lowered:
                return AIMessage(content="portal")
            if "demogorgons sometimes work together" in lowered:
                return AIMessage(content="monster")
            if "move things with her mind" in lowered:
                return AIMessage(content="psychic")
            if "creatures and power lines" in lowered:
                return AIMessage(content="environmental")
            return AIMessage(content="other")

        if "Canonical Lore" in prompt_text:
            if "Portals open when the barrier" in prompt_text:
                return AIMessage(
                    content="Portal timing follows electrical activity when the barrier between worlds is weak, rather than following the clock."
                )
            if "Demogorgons act alone when hunting" in prompt_text:
                return AIMessage(
                    content="Demogorgons hunt alone by default, but coordinate as a hive mind when controlled by a larger entity."
                )
            if "Psychic power drains the user's energy" in prompt_text:
                return AIMessage(
                    content="Using psychic abilities drains energy; heavier objects require more energy and cause nosebleeds as a warning sign."
                )
            if "Creatures from the Downside Up disturb electricity" in prompt_text:
                return AIMessage(
                    content="Nearby Downside Up creatures disturb electrical systems, making lights flicker and power lines react."
                )

        if "Investigation Finding:" in prompt_text:
            return AIMessage(
                content="Monitor local conditions according to the recorded investigation finding and follow bureau safety protocols."
            )

        return AIMessage(content="Mock single-call response.")


def test_import_has_no_dotenv_or_chatopenai_side_effects() -> None:
    """Importing or reloading `normalobjects_langgraph` must not call `load_dotenv` or `ChatOpenAI`."""
    try:
        with patch("dotenv.load_dotenv") as mock_dotenv, patch(
            "langchain_openai.ChatOpenAI"
        ) as mock_chat_openai:
            sys.modules.pop("normalobjects_langgraph", None)
            reloaded = importlib.import_module("normalobjects_langgraph")
            assert mock_dotenv.call_count == 0
            assert mock_chat_openai.call_count == 0
            assert reloaded.DEFAULT_MODEL == "gpt-4o-mini"
            assert reloaded.DEFAULT_TEMPERATURE == 0.0
    finally:
        sys.modules["normalobjects_langgraph"] = nlg


def test_exact_supplied_constants_preserved() -> None:
    """Verify `VALID_CATEGORIES`, `LORE`, and `TEST_COMPLAINTS` match the lab specification."""
    assert nlg.VALID_CATEGORIES == ["portal", "monster", "psychic", "environmental"]

    expected_lore = {
        "portal": "Portals open when the barrier between worlds is weak. Their timing follows electrical activity, not the clock.",
        "monster": "Demogorgons act alone when hunting, but follow a hive mind when a larger entity controls them.",
        "psychic": "Psychic power drains the user's energy. Bigger or heavier objects need more energy, and nosebleeds are a warning sign.",
        "environmental": "Creatures from the Downside Up disturb electricity: lights flicker and power lines react when they are near.",
    }
    assert nlg.LORE == expected_lore

    expected_complaints = [
        "The Downside Up portal opens at different times each day. How do I predict when?",
        "Demogorgons sometimes work together and sometimes fight. What's their deal?",
        "El can move things with her mind but can't lift heavy rocks. Why?",
        "Why do creatures and power lines react so strangely together?",
        "This is not a valid complaint about something random",
    ]
    assert nlg.TEST_COMPLAINTS == expected_complaints
    assert nlg.test_complaints == expected_complaints


def test_complaint_state_schema_has_no_redundant_fields() -> None:
    """Verify `ComplaintState` has the exact 11 clean fields with `raw_category` and `category`."""
    expected_keys = {
        "complaint",
        "raw_category",
        "category",
        "workflow_path",
        "status",
        "is_valid",
        "validation_reason",
        "evidence",
        "investigation",
        "resolution",
        "closure",
    }
    assert set(nlg.ComplaintState.__annotations__.keys()) == expected_keys
    initial = nlg.create_initial_state("Sample complaint")
    assert set(initial.keys()) == expected_keys
    assert initial["workflow_path"] == []
    assert initial["status"] == "new"
    assert initial["is_valid"] is False


def test_normalize_category_single_token_with_whitespace_and_punctuation() -> None:
    """Single valid category tokens with surrounding whitespace/punctuation normalize cleanly."""
    mock_llm = RecordingMockLLM(
        scripted_responses=[
            "  PORTAL. ",
            "Portals follow electrical activity when the barrier is weak.",
            "Track electrical surges rather than clock time to anticipate portal openings.",
        ]
    )
    app = nlg.compile_workflow(mock_llm)
    result = app.invoke(nlg.create_initial_state(nlg.TEST_COMPLAINTS[0]))

    assert result["raw_category"] == "  PORTAL. "
    assert result["category"] == "portal"
    assert result["is_valid"] is True
    assert result["workflow_path"] == [
        "intake",
        "validate",
        "investigate",
        "resolve",
        "close",
    ]
    assert result["status"] == "closed"


@pytest.mark.parametrize(
    "raw_output",
    [
        "",
        "   ",
        "unknown",
        "other",
        "portal or monster",
        "category: portal",
        "portal/monster",
    ],
)
def test_invalid_and_multiword_categories_are_rejected(raw_output: str) -> None:
    """Empty, unknown, other, internal-punctuation, and multiword classifier outputs fail validation and route to reject."""
    mock_llm = RecordingMockLLM(scripted_responses=[raw_output])
    app = nlg.compile_workflow(mock_llm)
    result = app.invoke(nlg.create_initial_state("Ambiguous or invalid complaint"))

    assert result["raw_category"] == raw_output
    assert result["category"] not in nlg.VALID_CATEGORIES
    assert result["is_valid"] is False
    assert result["workflow_path"] == ["intake", "validate", "reject"]
    assert result["status"] == "rejected"
    assert result["evidence"] == ""
    assert result["investigation"] == ""
    assert result["resolution"] == ""
    assert "rejected" in result["closure"].lower()
    # Only intake_node should have called the LLM; validate and reject are deterministic
    assert len(mock_llm.calls) == 1


def test_five_sample_complaints_produce_four_closed_and_one_rejected() -> None:
    """Running the 5 sample complaints through the compiled graph yields 4 closed and 1 rejected."""
    mock_llm = RecordingMockLLM()
    app = nlg.compile_workflow(mock_llm)

    results = [
        app.invoke(nlg.create_initial_state(complaint))
        for complaint in nlg.TEST_COMPLAINTS
    ]

    closed = [r for r in results if r["status"] == "closed"]
    rejected = [r for r in results if r["status"] == "rejected"]

    assert len(closed) == 4
    assert len(rejected) == 1

    expected_categories = ["portal", "monster", "psychic", "environmental"]
    for res, expected_cat in zip(results[:4], expected_categories):
        assert res["category"] == expected_cat
        assert res["is_valid"] is True
        assert res["evidence"] == nlg.LORE[expected_cat]
        assert res["workflow_path"] == [
            "intake",
            "validate",
            "investigate",
            "resolve",
            "close",
        ]

    assert results[4]["category"] == "other"
    assert results[4]["is_valid"] is False
    assert results[4]["workflow_path"] == ["intake", "validate", "reject"]


def test_node_logs_emitted_for_valid_and_invalid_paths() -> None:
    """Verify `[NODE]` log markers are printed and captured for both valid and invalid runs."""
    mock_llm = RecordingMockLLM()
    app = nlg.compile_workflow(mock_llm)

    valid_state, valid_logs = nlg.run_complaint_with_logs(app, nlg.TEST_COMPLAINTS[0])
    assert valid_state["status"] == "closed"
    joined_valid_logs = "\n".join(valid_logs)
    for tag in ["[INTAKE]", "[VALIDATE]", "[INVESTIGATE]", "[RESOLVE]", "[CLOSE]"]:
        assert tag in joined_valid_logs
    assert "[REJECT]" not in joined_valid_logs

    invalid_state, invalid_logs = nlg.run_complaint_with_logs(
        app, nlg.TEST_COMPLAINTS[4]
    )
    assert invalid_state["status"] == "rejected"
    joined_invalid_logs = "\n".join(invalid_logs)
    for tag in ["[INTAKE]", "[VALIDATE]", "[REJECT]"]:
        assert tag in joined_invalid_logs
    for skipped_tag in ["[INVESTIGATE]", "[RESOLVE]", "[CLOSE]"]:
        assert skipped_tag not in joined_invalid_logs


def test_investigate_and_resolve_prompt_isolation() -> None:
    """Verify `investigate_node` uses `LORE[category]` and `resolve_node` uses ONLY `investigation`."""
    unique_complaint = "The Downside Up portal opens at different times each day. UNIQUE_COMPLAINT_MARKER_XYZ"
    unique_investigation = "UNIQUE_INVESTIGATION_FINDING_ABC: Portal timing tracks electrical activity."

    mock_llm = RecordingMockLLM(
        scripted_responses=[
            "portal",
            unique_investigation,
            "Deploy electrical activity sensors to anticipate portal openings.",
        ]
    )
    app = nlg.compile_workflow(mock_llm)
    result = app.invoke(nlg.create_initial_state(unique_complaint))

    assert len(mock_llm.calls) == 3
    intake_prompt, investigate_prompt, resolve_prompt = mock_llm.calls

    # 1. Intake prompt receives the complaint
    assert unique_complaint in intake_prompt

    # 2. Investigate prompt receives both the complaint and the exact LORE["portal"] string
    assert nlg.LORE["portal"] in investigate_prompt
    assert unique_complaint in investigate_prompt
    assert result["evidence"] == nlg.LORE["portal"]

    # 3. Resolve prompt receives ONLY the investigation finding, NOT the complaint or raw LORE
    assert unique_investigation in resolve_prompt
    assert unique_complaint not in resolve_prompt
    assert nlg.LORE["portal"] not in resolve_prompt


def test_deterministic_nodes_never_call_llm() -> None:
    """`validate_node`, `close_node`, and `reject_node` are pure Python functions taking only `state`."""
    state = nlg.create_initial_state("Sample portal complaint")
    state["raw_category"] = "portal"
    state["category"] = "portal"

    validated_state = nlg.validate_node(state)
    assert validated_state["is_valid"] is True
    assert validated_state["workflow_path"] == ["validate"]

    validated_state["resolution"] = "Track electrical activity."
    closed_state = nlg.close_node(validated_state)
    assert closed_state["status"] == "closed"
    assert "Track electrical activity." in closed_state["closure"]
    assert closed_state["workflow_path"] == ["validate", "close"]

    invalid_state = nlg.create_initial_state("Random invalid input")
    invalid_state["raw_category"] = "other"
    invalid_state["category"] = "other"
    invalid_validated = nlg.validate_node(invalid_state)
    assert invalid_validated["is_valid"] is False
    rejected_state = nlg.reject_node(invalid_validated)
    assert rejected_state["status"] == "rejected"
    assert rejected_state["workflow_path"] == ["validate", "reject"]


def test_state_isolation_across_sequential_runs() -> None:
    """Sequential runs must not share or mutate `workflow_path` or state fields."""
    mock_llm = RecordingMockLLM()
    app = nlg.compile_workflow(mock_llm)

    initial_1 = nlg.create_initial_state(nlg.TEST_COMPLAINTS[0])
    initial_2 = nlg.create_initial_state(nlg.TEST_COMPLAINTS[4])

    res_1 = app.invoke(initial_1)
    res_2 = app.invoke(initial_2)

    assert initial_1["workflow_path"] == []
    assert initial_2["workflow_path"] == []
    assert res_1["workflow_path"] == [
        "intake",
        "validate",
        "investigate",
        "resolve",
        "close",
    ]
    assert res_2["workflow_path"] == ["intake", "validate", "reject"]
    assert res_1["workflow_path"] is not res_2["workflow_path"]


def test_manual_chain_and_evidence_capture_offline(tmp_path: Path) -> None:
    """Verify `run_manual_node_chain`, `ask_single_llm`, and evidence serialization offline."""
    mock_llm = RecordingMockLLM()
    app = nlg.compile_workflow(mock_llm)

    manual_state, manual_logs = nlg.run_callable_with_logs(
        lambda: nlg.run_manual_node_chain(nlg.TEST_COMPLAINTS[0], mock_llm)
    )
    assert manual_state["workflow_path"] == [
        "intake",
        "validate",
        "investigate",
        "resolve",
        "close",
    ]
    assert manual_state["status"] == "closed"
    assert any("[INTAKE]" in line for line in manual_logs)

    complaint_results = [
        nlg.run_complaint_with_logs(app, complaint)
        for complaint in nlg.TEST_COMPLAINTS
    ]
    mermaid_text = app.get_graph().draw_mermaid()
    single_valid = nlg.ask_single_llm(nlg.TEST_COMPLAINTS[0], mock_llm)
    single_invalid = nlg.ask_single_llm(nlg.TEST_COMPLAINTS[4], mock_llm)

    evidence = nlg.build_execution_evidence(
        model_name=nlg.DEFAULT_MODEL,
        temperature=nlg.DEFAULT_TEMPERATURE,
        manual_chain_state=manual_state,
        manual_chain_logs=manual_logs,
        complaint_results=complaint_results,
        mermaid_diagram=mermaid_text,
        single_llm_valid_response=single_valid,
        single_llm_invalid_response=single_invalid,
    )

    output_file = tmp_path / "evidence.json"
    saved_path = nlg.save_execution_evidence(evidence, output_path=output_file)
    assert saved_path == output_file.resolve()
    assert saved_path.exists()

    loaded = json.loads(saved_path.read_text(encoding="utf-8"))
    assert loaded["model_settings"] == {"model": "gpt-4o-mini", "temperature": 0.0}
    assert loaded["manual_chain_run"]["workflow_path"] == [
        "intake",
        "validate",
        "investigate",
        "resolve",
        "close",
    ]
    assert loaded["summary_counts"] == {"closed": 4, "rejected": 1, "total": 5}
    assert len(loaded["complaint_runs"]) == 5
    for run_entry in loaded["complaint_runs"]:
        assert "raw_category" in run_entry
        assert "category" in run_entry
        assert "node_logs" in run_entry
        assert "workflow_path" in run_entry
        assert "evidence" in run_entry
        assert "investigation" in run_entry
        assert "resolution" in run_entry
        assert "closure" in run_entry
    assert (
        loaded["baseline_comparisons"]["valid_complaint"]["single_llm_response"]
        == single_valid
    )
    assert (
        loaded["baseline_comparisons"]["invalid_complaint"]["single_llm_response"]
        == single_invalid
    )
