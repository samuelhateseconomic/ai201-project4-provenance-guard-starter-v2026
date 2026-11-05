"""
Inputs for the five acceptance criteria. `run_eval.py` runs every scenario three
times and records the actual HTTP and audit-log responses.
"""

import csv
from pathlib import Path

import config


_ATTACKS_PATH = Path(__file__).parent / "attack_set" / "attacks.csv"


def _attack_texts(ids: set[str], family: str) -> list[str]:
    if not _ATTACKS_PATH.is_file():
        raise FileNotFoundError(f"Attack-set file not found: {_ATTACKS_PATH}")

    with _ATTACKS_PATH.open(encoding="utf-8", newline="") as attack_file:
        rows = {
            row["id"]: row
            for row in csv.DictReader(attack_file)
            if row["id"] in ids
        }

    missing = ids - rows.keys()
    if missing:
        raise ValueError(f"Missing attack-set examples: {', '.join(sorted(missing))}")

    wrong_family = [
        attack_id for attack_id, row in rows.items()
        if row["family"] != family
    ]
    if wrong_family:
        raise ValueError(
            f"Expected {family} examples, found other families: "
            f"{', '.join(sorted(wrong_family))}"
        )

    return [rows[attack_id]["text"] for attack_id in sorted(ids)]


_HUMAN_PROXY = _attack_texts(
    {f"FP{i:02}" for i in range(1, 9)},
    "false_positive",
)
_AI_EVASIONS = _attack_texts(
    {f"EV{i:02}" for i in range(1, 11)},
    "evasion",
)
_COVERAGE_TEXTS = _attack_texts(
    {"EV01", "EV02", "EV10"},
    "evasion",
)
_APPEAL_TEXTS = (
    _attack_texts(
        {f"FP{i:02}" for i in range(1, 8)},
        "false_positive",
    )
    + _attack_texts({"EV01", "EV02", "EV10"}, "evasion")
)

_BOUNDARY_TEXT = (
    "A writer submits a complete piece of original work for review. "
    * (config.MAX_SUBMISSION_CHARS // 60 + 1)
)[:config.MAX_SUBMISSION_CHARS]
_LONG_TEXT = _BOUNDARY_TEXT + "x"

SCENARIOS = [
    {
        "name": "attack-set false-positive proxy",
        "criterion": 1,
        "target": "0 of 8 known-human examples labeled AI in each run",
        "metric": "false_positives",
        "texts": _HUMAN_PROXY,
    },
    {
        "name": "human and AI score separation",
        "criterion": 2,
        "target": "at least 7/8 human ≤0.35 and 8/10 AI ≥0.65 per run",
        "metric": "score_separation",
        "groups": {
            "human": _HUMAN_PROXY,
            "ai": _AI_EVASIONS,
        },
        "minimum_human": 7,
        "minimum_ai": 8,
    },
    {
        "name": "all three labels reachable",
        "criterion": 3,
        "target": "3 of 3 labels in each run",
        "metric": "label_coverage",
        "texts": _COVERAGE_TEXTS,
    },
    {
        "name": "appeals recorded exactly once",
        "criterion": 4,
        "target": "10 of 10 appeals return under_review and log once",
        "metric": "appeals",
        "workflow": "appeals",
        "texts": _APPEAL_TEXTS,
        "reasoning": "I wrote this work and request a review.",
    },
    {
        "name": "invalid and boundary text handling",
        "criterion": 5,
        "target": "5 of 5 expected responses and health checks",
        "metric": "bad_input",
        "expected_statuses": [400, 400, 400, 200, 413],
        "bodies": [
            {"text": "", "creator_id": "eval_empty"},
            {"text": "   ", "creator_id": "eval_whitespace"},
            {"creator_id": "eval_missing_text"},
            {"text": _BOUNDARY_TEXT, "creator_id": "eval_max_length"},
            {"text": _LONG_TEXT, "creator_id": "eval_over_limit"},
        ],
    },
]


def validate() -> list[str]:
    """Validate all scenario shapes before starting the evaluation run."""
    problems = []
    criteria = []

    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")
        if scenario.get("criterion") is not None:
            criteria.append(scenario["criterion"])

        payload_sources = sum(bool(scenario.get(key)) for key in ("texts", "groups", "bodies"))
        if payload_sources != 1:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') must have exactly one "
                "of texts, groups, or bodies"
            )

        if scenario.get("groups"):
            for group, texts in scenario["groups"].items():
                if not texts:
                    problems.append(f"scenario {i}, group '{group}' has no texts")
                for j, text in enumerate(texts, 1):
                    if not isinstance(text, str) or not text.strip():
                        problems.append(
                            f"scenario {i}, group '{group}' text {j} is empty or not a string"
                        )

        if scenario.get("texts"):
            for j, text in enumerate(scenario["texts"], 1):
                if not isinstance(text, str) or not text.strip():
                    problems.append(f"scenario {i}, text {j} is empty or not a string")
                elif text.startswith("REPLACE ME"):
                    problems.append(f"scenario {i}, text {j} is still a placeholder")

        if scenario.get("bodies"):
            for j, body in enumerate(scenario["bodies"], 1):
                if not isinstance(body, dict):
                    problems.append(f"scenario {i}, body {j} is not a request-body dict")

        if scenario.get("workflow") == "appeals" and not scenario.get("reasoning"):
            problems.append(f"scenario {i} needs reasoning for its appeal workflow")

        if scenario.get("metric") == "bad_input":
            expected = scenario.get("expected_statuses", [])
            if len(expected) != len(scenario.get("bodies", [])):
                problems.append(f"scenario {i} needs one expected status per request body")

    if sorted(criteria) != [1, 2, 3, 4, 5]:
        problems.append("scenarios must cover criteria 1 through 5 exactly once")

    return problems
