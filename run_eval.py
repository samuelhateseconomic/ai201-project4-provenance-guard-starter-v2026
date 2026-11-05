#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *you* thought
to test, and the two rarely overlap much. Both count.

Fill in `scenarios.py` first — that's where each criterion's test inputs live.
The false-positive proxy is the supplied attack set; a personal-writing test
still needs samples you actually wrote. Label coverage uses examples spanning
the observed score range.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here.

This does the sending and the recording. It does not decide whether a trial
passed — it measures the explicit target recorded with each scenario.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def texts_for(scenario):
    """Return each text with its expected origin group, when provided."""
    groups = scenario.get("groups")
    if groups:
        return [
            (group, text)
            for group, texts in groups.items()
            for text in texts
        ]
    return [(None, text) for text in scenario.get("texts", [])]


def bodies_for(scenario, trial_number):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {
            "text": text,
            "creator_id": f"eval_{scenario['criterion']}_t{trial_number}_{i}",
        }
        for i, (_, text) in enumerate(texts_for(scenario), 1)
    ]


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def request_json(requests, method, url, *, body=None, timeout):
    """Return status and JSON content, preserving non-JSON responses as evidence."""
    response = requests.request(method, url, json=body, timeout=timeout)
    try:
        payload = response.json() if response.content else {}
        json_error = None
    except ValueError as exc:
        payload = {}
        json_error = f"{type(exc).__name__}: {exc}"
    return response, payload, json_error


def run_appeals(requests, scenario, trial_number, args):
    """Submit and appeal each sample, then verify its single audit event."""
    results = []
    for i, (_, text) in enumerate(texts_for(scenario), 1):
        creator_id = f"eval_appeal_t{trial_number}_{i}"
        try:
            submission, submitted, submit_error = request_json(
                requests,
                "POST",
                f"{args.url}/submit",
                body={"text": text, "creator_id": creator_id},
                timeout=args.timeout,
            )
            result = {
                "creator_id": creator_id,
                "submission_status": submission.status_code,
                "submission": submitted,
                "submission_json_error": submit_error,
            }

            content_id = submitted.get("content_id")
            if not content_id:
                result.update({
                    "appeal_status": None,
                    "appeal": None,
                    "audit_appeal_records": 0,
                    "error": "Submission returned no content_id.",
                })
                results.append(result)
                continue

            appeal_response, appeal_payload, appeal_error = request_json(
                requests,
                "POST",
                f"{args.url}/appeal",
                body={
                    "content_id": content_id,
                    "reasoning": scenario["reasoning"],
                },
                timeout=args.timeout,
            )
            log_response, log_payload, log_error = request_json(
                requests,
                "GET",
                f"{args.url}/log",
                timeout=args.timeout,
            )
            matching_appeals = [
                entry for entry in log_payload.get("entries", [])
                if entry.get("content_id") == content_id
                and entry.get("event") == "appeal"
            ]
            result.update({
                "content_id": content_id,
                "appeal_status": appeal_response.status_code,
                "appeal": appeal_payload,
                "appeal_json_error": appeal_error,
                "audit_log_status": log_response.status_code,
                "audit_log_json_error": log_error,
                "audit_appeal_records": len(matching_appeals),
                "audit_appeal_record": matching_appeals[0] if matching_appeals else None,
            })
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            results.append({
                "creator_id": creator_id,
                "status": None,
                "error": f"{type(exc).__name__}: {exc}",
            })
    return results


def metric_for(scenario, results):
    """Evaluate one trial against the scenario's stated measurable target."""
    metric = scenario["metric"]
    if metric == "false_positives":
        false_positives = sum(result.get("guess") == "ai" for result in results)
        return f"{false_positives}/{len(results)} AI", false_positives == 0

    if metric == "score_separation":
        human = [r for r in results if r.get("group") == "human"]
        ai = [r for r in results if r.get("group") == "ai"]
        human_pass = sum(
            isinstance(r.get("combined_score"), (int, float))
            and r["combined_score"] <= 0.35
            for r in human
        )
        ai_pass = sum(
            isinstance(r.get("combined_score"), (int, float))
            and r["combined_score"] >= 0.65
            for r in ai
        )
        passed = (
            human_pass >= scenario["minimum_human"]
            and ai_pass >= scenario["minimum_ai"]
        )
        return f"H {human_pass}/{len(human)}; AI {ai_pass}/{len(ai)}", passed

    if metric == "label_coverage":
        labels = {result.get("guess") for result in results}
        expected = {"human", "unsure", "ai"}
        return f"{len(labels & expected)}/3 labels", labels >= expected

    if metric == "appeals":
        passed_count = sum(
            result.get("submission_status") == 200
            and result.get("appeal_status") == 200
            and result.get("appeal", {}).get("status") == "under_review"
            and result.get("audit_appeal_records") == 1
            and result.get("audit_appeal_record", {}).get("reasoning")
            == scenario["reasoning"]
            and bool(result.get("audit_appeal_record", {}).get("timestamp"))
            and result.get("audit_appeal_record", {}).get("status")
            == "under_review"
            for result in results
        )
        return f"{passed_count}/{len(results)}", passed_count == len(results)

    if metric == "bad_input":
        expected_statuses = scenario["expected_statuses"]
        passed_count = sum(
            i < len(expected_statuses)
            and result.get("status") == expected_statuses[i]
            and result.get("health_status") == 200
            and result.get("json_error") is None
            for i, result in enumerate(results)
        )
        return f"{passed_count}/{len(expected_statuses)}", passed_count == len(expected_statuses)

    raise ValueError(f"Unknown evaluation metric: {metric}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '—'})")

        trials = []
        for trial_number in range(1, args.trials + 1):
            if scenario.get("workflow") == "appeals":
                results = run_appeals(requests, scenario, trial_number, args)
            elif scenario["metric"] == "bad_input":
                results = []
                for i, body in enumerate(scenario["bodies"]):
                    try:
                        response, payload, json_error = request_json(
                            requests,
                            "POST",
                            f"{args.url}/submit",
                            body=body,
                            timeout=args.timeout,
                        )
                        health, _, _ = request_json(
                            requests,
                            "GET",
                            f"{args.url}/health",
                            timeout=5,
                        )
                        results.append({
                            "status": response.status_code,
                            "response": payload,
                            "json_error": json_error,
                            "health_status": health.status_code,
                            "sent": describe(body),
                        })
                    except Exception as exc:  # noqa: BLE001
                        results.append({
                            "status": None,
                            "error": f"{type(exc).__name__}: {exc}",
                            "sent": describe(body),
                        })
            else:
                results = []
                for i, (group, text) in enumerate(texts_for(scenario), 1):
                    body = bodies_for(scenario, trial_number)[i - 1]
                    try:
                        response, payload, json_error = request_json(
                            requests,
                            "POST",
                            f"{args.url}/submit",
                            body=body,
                            timeout=args.timeout,
                        )
                        results.append({
                            "status": response.status_code,
                            "content_id": payload.get("content_id"),
                            "guess": payload.get("guess"),
                            "confidence": payload.get("confidence"),
                            "model_score": payload.get("model_score"),
                            "style_score": payload.get("style_score"),
                            "combined_score": payload.get("combined_score"),
                            "label": payload.get("label"),
                            "json_error": json_error,
                            "group": group,
                            "sent": text[:70],
                        })
                    except Exception as exc:  # noqa: BLE001
                        results.append({
                            "status": None,
                            "error": f"{type(exc).__name__}: {exc}",
                            "group": group,
                            "sent": text[:70],
                        })

            summary, _ = metric_for(scenario, results)
            trials.append({"results": results, "summary": summary})
            print(f"  trial {trial_number}: {summary}")

        rows.append({"scenario": scenario, "trials": trials})

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Each run cell reports the measured result for its criterion. A criterion",
        "is MET only when its target holds in all three trials.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        summaries = [trial["summary"] for trial in row["trials"]]
        met = all(
            metric_for(scenario, trial["results"])[1]
            for trial in row["trials"]
        )
        lines.append(
            f"| {name} | {scenario['target']} | "
            f"{' | '.join(summaries)} | {'MET' if met else 'MISSED'} |"
        )

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, trial in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(trial["results"], indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
