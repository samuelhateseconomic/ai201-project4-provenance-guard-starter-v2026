# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. A writer sends `POST /submit` with a JSON object containing `text` and `creator_id`.
2. The route checks that the JSON and both fields are valid, rejects blank text, and returns an error for text over 10,000 characters.
3. `detector.model_signal` runs the text through the local language model and produces the model signal.
4. `stylometry.style_signal` measures sentence-length variation, vocabulary repetition, and punctuation density to produce the style signal.
5. `scoring.combine_signals` combines the two 0–1 scores using 60% model signal and 40% style signal.
6. `scoring.score_to_label` maps the combined score to a human, unsure, or AI guess and the full sentence shown to the reader.
7. The route creates a `content_id`, records the decision and both signal scores in `logs/audit.jsonl`, and returns the ID, scores, guess, confidence, and label as JSON.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to a local language model. Low perplexity becomes a higher AI-leaning score.

**Why that might differ between human and AI writing:** Generated text often uses likely next words and familiar phrasing, which can make it more predictable.

**What it can't see:** Predictability does not establish authorship. Plain, conventional human writing can be predictable, while unusual AI writing can be surprising.

### Signal two — the style signal

**What it measures:** Sentence-length variation, repeated vocabulary (1 minus type-token ratio), and punctuation density, without interpreting meaning.

**Why that might differ between human and AI writing:** Generated prose may use more even sentence lengths and repeat a narrower vocabulary. The current score also treats denser punctuation as more AI-like, but that is only a heuristic, not a validated difference.

**What it can't see:** It cannot understand meaning or identify an author. Editing sentence breaks, adding typos, or inserting quotations can change these measurements without changing authorship; type-token ratio also depends on text length.

**How the style score is calculated:** It equally averages three 0–1 components: `1 / (1 + sentence_length_CV)`, `1 - type_token_ratio`, and `min(punctuation_density / 0.10, 1)`. Sentence-length CV is standard deviation divided by mean word count; with fewer than two sentences its component is neutral (0.5). Punctuation density is Unicode punctuation characters divided by all characters.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Use a weighted average. When the signals disagree, the combined score stays between them instead of allowing either signal to decide alone; it leans somewhat more toward the model signal.

**The numbers:** `combined = 0.60 × model_score + 0.40 × style_score`. The weights sum to 1, so valid 0–1 inputs produce a 0–1 output.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**File and function:** `scoring.py::combine_signals`

**The three original test pieces:** Both signals score the short self-written text and the longer human-written text below 0.5. On the AI-generated piece, they split: the model score is **0.3640**, while the style score is **0.5745**.

| Test piece | Model signal | Style signal | Combined |
|---|---:|---:|---:|
| Short self-written | 0.0032 | 0.1667 | 0.06860 |
| Human-written | 0.3858 | 0.4677 | 0.41856 |
| AI-generated | 0.3640 | 0.5745 | 0.44820 |

**What my rule does with that split:** It gives the model 60% and style 40%, producing **0.44820** for the AI-generated piece. That moves the result toward the style signal without letting it decide alone. These three samples are too few to establish accuracy or justify retuning the weights.

The AI-generated sample is 15,823 characters, above the route's 10,000-character limit. These three comparisons call the signals directly; `/submit` would reject that oversized sample with HTTP 413.

**Four-input calibration check:** The labels below describe how each paragraph was constructed; they are not independently verified authorship labels. Scores came from the local GPT-2 model and `stylometry.style_signal`.

| Calibration input | Model signal | Style signal | Combined |
|---|---:|---:|---:|
| Clearly AI-style | 0.7682 | 0.4098 | 0.62484 |
| Human-style anecdote | 0.6593 | 0.4198 | 0.56350 |
| Formal human-style | 0.3981 | 0.3490 | 0.37846 |
| Lightly edited AI-style | 0.4813 | 0.3761 | 0.43922 |

**Lightly edited AI-style input:**

> I have taken a look at your idea and thank you again for your openness.
>
> One question came to mind while reading your experimental design. I found the comparison between predictable and unpredictable pings particularly interesting, especially how increasing the frequency of tasks across both conditions could help distinguish an aversion to overwork from the constraints imposed by unexpected demands. If the gender difference in earnings growth disappears under predictable schedules but persists under unpredictable ones, that would suggest the timing of work demands matters more than the additional workload itself.
>
> However, since earnings are determined by how quickly participants complete tasks, I wonder whether the experiment is primarily measuring accessibility, willingness to accommodate additional work, or productivity. In other words, could a difference in earnings reflect the cost of being constantly available rather than a difference in productive ability? I want to understand how you think about this distinction when connecting the experimental outcomes to gender wage inequality in real workplaces.

**What surprised me:** The style scores are close together, so these three simple features did not separate the four examples well. The model also gave the human-style anecdote a relatively high score (0.6593). These small examples are a diagnostic check, not proof that either signal can identify authorship.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 to 0.35, including 0.35 | We think this was probably written by a person. |
| unsure | Greater than 0.35 and less than 0.65 | We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation. |
| high-confidence AI | 0.65 to 1.00, including 0.65 | This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong. |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

I chose this wording because it states the system's uncertainty without treating the score as proof or blaming the writer.

**Reachability check:** I submitted these inputs to `/submit`; each produced its listed label:

| Input | Result |
|---|---|
| My short text, `some writing here` | `human`, combined score 0.06860 |
| The lightly edited AI-style experimental-design paragraph above | `unsure`, combined score 0.43922 |
| `People have a day.` repeated eight times | `ai`, combined score 0.91356 |

These are examples showing that all three route branches can be reached, not evidence that the scores prove authorship.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```powershell
$submitBody = '{"text":"People have a day. People have a day. People have a day. People have a day. People have a day. People have a day. People have a day. People have a day.","creator_id":"readme-sample"}'
$submitBody | curl.exe -sS -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" --data-binary "@-"
```

```json
{
  "combined_score": 0.91356,
  "confidence": 0.0,
  "content_id": "a31e8a2a-2edc-4ea1-b144-1789dbe1b239",
  "guess": "ai",
  "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
  "model_score": 0.9882,
  "style_score": 0.8016
}
```

**An appeal**

```powershell
$appealBody = '{"content_id":"a31e8a2a-2edc-4ea1-b144-1789dbe1b239","reasoning":"I wrote this text myself and would like the decision reviewed."}'
$appealBody | curl.exe -sS -X POST http://127.0.0.1:5000/appeal -H "Content-Type: application/json" --data-binary "@-"
```

```json
{
  "content_id": "a31e8a2a-2edc-4ea1-b144-1789dbe1b239",
  "message": "Your appeal has been recorded for review.",
  "ok": true,
  "status": "under_review"
}
```

**What the log shows afterwards**

```powershell
curl.exe -sS "http://127.0.0.1:5000/log?limit=2"
```

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.91356,
      "content_id": "a31e8a2a-2edc-4ea1-b144-1789dbe1b239",
      "creator_id": "readme-sample",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9882,
      "status": "decided",
      "style_score": 0.8016,
      "timestamp": "2026-11-03T02:07:32+00:00"
    },
    {
      "content_id": "a31e8a2a-2edc-4ea1-b144-1789dbe1b239",
      "creator_id": "readme-sample",
      "event": "appeal",
      "reasoning": "I wrote this text myself and would like the decision reviewed.",
      "status": "under_review",
      "timestamp": "2026-11-03T02:07:32+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* Why my multi-line `curl -X POST` command failed in PowerShell and how to send the same JSON request.
- *What came back:* The explanation was that PowerShell's `curl` name resolves to `Invoke-WebRequest`, which does not accept curl's `-X`, `-H`, and `-d` flags; PowerShell also uses a backtick rather than a backslash for line continuation.
- *What I changed:* I switched the project examples to call `curl.exe` explicitly and used PowerShell-compatible quoting and input piping, so the commands exercise the HTTP endpoint instead of the PowerShell alias.

**Moment 2**

- *What I asked for:* How to combine the model and stylometry signals, and how to present the three score outcomes without treating a score as proof of authorship.
- *What came back:* A weighted average was suggested so both signals contribute when they disagree, along with a middle unsure band and reader-facing wording that makes uncertainty explicit.
- *What I changed:* I used a 60% model / 40% style weighted average and the 0.35 / 0.65 label cutoffs in the code, then documented the exact formula, ranges, and an unsure message that says the result is not an accusation. I also kept both individual signal scores in the response and audit log so disagreements can be inspected.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 10 per minute, 200 per day

**Why those numbers and not others:**
Ten submissions in a minute leaves room for a writer correcting and resubmitting
their work, while stopping a burst of variations from quickly mapping the
thresholds. The daily cap still allows a writer to work across several pieces
without giving a script an unlimited number of attempts.

**What a caller counts as:** `creator_id` (falling back to the caller's address
when it is missing), so changing network addresses does not bypass the limit
when a script keeps the same creator ID.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

---

## Attack Run — Before

I ran all 56 rows from [attack_set](./attack_set/) with
`python run_attacks.py --set attack_set`. The row-by-row results, including the
combined score and my verdict for each attack, are in
[attack_run_2026-11-04_1727.md](./results/attack_run_2026-11-04_1727.md).

**Verdicts:** 15 broke, 41 held.

| Family | Broke | Held |
|---|---:|---:|
| Evasion | 9 | 1 |
| False positive | 3 | 5 |
| Prompt injection | 0 | 6 |
| Malformed input | 3 | 17 |
| Same-creator flood | 0 | 12 |

I counted an evasion as broke if AI text received anything other than the AI
label; an unsure result avoids an accusation, but still lets that text evade
the detector. For known-human false-positive examples, only an AI label counts
as broke because unsure is explicitly not an accusation. The three malformed
inputs labeled AI were also marked broke because they were non-prose or
nonstandard-script inputs. Prompt-injection attempts were held: they returned
ordinary decisions and did not alter the route or log structure. The flood
reached the configured ten-request allowance, then the remaining two requests
were rate-limited.

**Ten audit log entries from the run**

The complete 56-entry extract is in
[audit_extract.json](./results/audit_extract.json). These examples show an
evasion, a correctly detected AI sample, false positives, unusual-input
decisions, and rejected requests:

```json
[
  {
    "timestamp": "2026-11-05T01:27:10+00:00",
    "content_id": "9678630e-23f6-4b6a-a40e-904b9889a872",
    "creator_id": "attacker_EV01",
    "guess": "human",
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.25254000000000004,
    "label": "We think this was probably written by a person.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:14+00:00",
    "content_id": "5f748b81-32af-4282-a93a-e89576a27b3e",
    "creator_id": "attacker_EV10",
    "guess": "ai",
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.7811199999999999,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:16+00:00",
    "content_id": "fda02124-6db2-45fe-988d-8bbf1a5ca0e1",
    "creator_id": "attacker_FP05",
    "guess": "ai",
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:17+00:00",
    "content_id": "21ec5ec4-4316-4fd7-b244-c790144477bb",
    "creator_id": "attacker_FP07",
    "guess": "ai",
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:23+00:00",
    "content_id": "448d51da-bc36-4f5d-9e1c-d83f528efef5",
    "creator_id": "attacker_MF06",
    "guess": "ai",
    "model_score": 0.9969,
    "style_score": 0.5,
    "combined_score": 0.7981400000000001,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:23+00:00",
    "content_id": "c4fea101-da8f-410a-8340-cac9210bf367",
    "creator_id": "attacker_MF07",
    "guess": "ai",
    "model_score": 0.9064,
    "style_score": 0.5,
    "combined_score": 0.7438400000000001,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:24+00:00",
    "content_id": "c4c368cb-643d-4ec7-8bea-d6b5a42a22c4",
    "creator_id": "attacker_flood",
    "guess": "human",
    "model_score": 0.0287,
    "style_score": 0.2273,
    "combined_score": 0.10814,
    "label": "We think this was probably written by a person.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-05T01:27:20+00:00",
    "creator_id": "attacker_MF01",
    "event": "rejected",
    "status": "rejected",
    "reason": "invalid_text",
    "status_code": 400
  },
  {
    "timestamp": "2026-11-05T01:27:23+00:00",
    "creator_id": "attacker_MF08",
    "event": "rejected",
    "status": "rejected",
    "reason": "text_too_long",
    "status_code": 413
  },
  {
    "timestamp": "2026-11-05T01:27:26+00:00",
    "creator_id": "attacker_flood",
    "event": "rejected",
    "status": "rejected",
    "reason": "rate_limited",
    "limit": "10 per 1 minute"
  }
]
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

FP07: deliberately repeated human phrasing received the AI label with a
combined score of 0.71412. The score clears the 0.65 AI threshold, so this is a
confident false positive rather than an uncertain result.

---

## Run Log and Verdicts

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Attack-set false-positive proxy | 0 of 8 known-human examples labeled AI | 3/8 AI | 3/8 AI | 3/8 AI | MISSED |
| 2. Human and AI score separation | ≥7/8 human ≤0.35 and ≥8/10 AI ≥0.65 | H 0/8; AI 1/10 | H 0/8; AI 1/10 | H 0/8; AI 1/10 | MISSED |
| 3. All three labels reachable | 3 of 3 labels | 3/3 | 3/3 | 3/3 | MET |
| 4. Appeals recorded exactly once | 10 of 10 appeals return under_review and log once | 10/10 | 10/10 | 10/10 | MET |
| 5. Invalid and boundary text handling | 5 of 5 expected responses and health checks | 5/5 | 5/5 | 5/5 | MET |

The first-person false-positive criterion is not verified: the attack set has
eight known-human challenge examples, not my own writing. I used those as an
explicit proxy; [criteria.md](./criteria.md) records the revision. The separate
[samples.zip](./samples.zip) includes demo examples, but its `formal_human.json`
is intentionally empty for a writer to fill in. The full three-trial output is
in [run_2026-11-04_1748_before.md](./results/run_2026-11-04_1748_before.md),
produced by `run_eval.py::main`. The JSON below is actual trial-one output
from that report.

**Criterion 1 — false-positive proxy** (`run_eval.py::main`):

```json
{
  "status": 200,
  "content_id": "41f43d5e-5e03-4605-be5a-8717ec74573a",
  "guess": "ai",
  "confidence": 0.0,
  "model_score": 0.8005,
  "style_score": 0.4755,
  "combined_score": 0.6705,
  "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
  "json_error": null,
  "group": null,
  "sent": "To configure the service, edit the settings file in the installation d"
}
```

**Criterion 2 — score separation** (`run_eval.py::main`):

```json
{
  "status": 200,
  "content_id": "d2c4428a-d03d-4fb7-94d1-ae8c5785fef1",
  "guess": "human",
  "confidence": 0.0,
  "model_score": 0.1635,
  "style_score": 0.3861,
  "combined_score": 0.25254000000000004,
  "label": "We think this was probably written by a person.",
  "json_error": null,
  "group": "ai",
  "sent": "The importance of effective communication in the workplace cannot be o"
}
```

**Criterion 3 — label coverage** (`run_eval.py::main`):

```json
[
  {
    "status": 200,
    "content_id": "ca78bf0c-97f3-41ea-b4b1-efd60e212592",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.25254000000000004,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "8d5740e5-d461-48ac-a5d4-52b7019e52df",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.48414,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "32e8f25c-a6e9-416b-af7c-e49c8e861d88",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.7811199999999999,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Criterion 4 — appeal and audit record** (`run_eval.py::run_appeals`):

```json
{
  "creator_id": "eval_appeal_t1_1",
  "submission_status": 200,
  "submission": {
    "combined_score": 0.5263,
    "confidence": 0.0,
    "content_id": "e8a0c8cb-cc03-4e00-8d56-70db07d421f7",
    "guess": "unsure",
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "model_score": 0.6175,
    "style_score": 0.3895
  },
  "submission_json_error": null,
  "content_id": "e8a0c8cb-cc03-4e00-8d56-70db07d421f7",
  "appeal_status": 200,
  "appeal": {
    "content_id": "e8a0c8cb-cc03-4e00-8d56-70db07d421f7",
    "message": "Your appeal has been recorded for review.",
    "ok": true,
    "status": "under_review"
  },
  "appeal_json_error": null,
  "audit_log_status": 200,
  "audit_log_json_error": null,
  "audit_appeal_records": 1,
  "audit_appeal_record": {
    "content_id": "e8a0c8cb-cc03-4e00-8d56-70db07d421f7",
    "creator_id": "eval_appeal_t1_1",
    "event": "appeal",
    "reasoning": "I wrote this work and request a review.",
    "status": "under_review",
    "timestamp": "2026-11-05T01:47:59+00:00"
  }
}
```

**Criterion 5 — bad input and service availability** (`run_eval.py::main`):

```json
{
  "status": 400,
  "response": {
    "error": "invalid_text",
    "message": "text must be a non-empty string."
  },
  "json_error": null,
  "health_status": 200,
  "sent": "(empty text)"
}
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
