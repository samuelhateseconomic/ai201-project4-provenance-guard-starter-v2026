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
5. `scoring.combine_signals` combines the two 0–1 scores using 40% model signal and 60% style signal.
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

**The rule:** Use a weighted average. When the signals disagree, the combined score stays between them instead of allowing either signal to decide alone; it leans somewhat more toward the style signal.

**The numbers:** `combined = 0.40 × model_score + 0.60 × style_score`. The weights sum to 1, so valid 0–1 inputs produce a 0–1 output.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**File and function:** `scoring.py::combine_signals`

**The three original test pieces:** Both signals score the short self-written text and the longer human-written text below 0.5. On the AI-generated piece, they split: the model score is **0.3640**, while the style score is **0.5745**. The combined values in this original table use the previous 60% model / 40% style weights.

| Test piece | Model signal | Style signal | Combined |
|---|---:|---:|---:|
| Short self-written | 0.0032 | 0.1667 | 0.06860 |
| Human-written | 0.3858 | 0.4677 | 0.41856 |
| AI-generated | 0.3640 | 0.5745 | 0.44820 |

**What my rule does with that split:** Under the original 60% model / 40% style weighting, the AI-generated piece scored **0.44820**. The current 40% model / 60% style weighting yields **0.49030** for the same signal scores. These three samples are too few to establish accuracy or justify the new weights; the after-run below measures the change on the full supplied set.

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
- *What I changed:* I initially used a 60% model / 40% style weighted average and the 0.35 / 0.65 label cutoffs in the code, then documented the exact formula, ranges, and an unsure message that says the result is not an accusation. I also kept both individual signal scores in the response and audit log so disagreements can be inspected. The later reweighting experiment is documented below.

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
produced by `run_eval.py::main`. Each JSON block below is actual output from its corresponding trial in that report.

All three trials produced identical measured outputs for each criterion. Submission content IDs and appeal timestamps are unique per run; the scores, labels, statuses, and criterion results stayed the same.

**Criterion 1 — false-positive proxy** (`run_eval.py::main`):

**Trial 1 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "01a11d26-ea25-4d49-8d3a-d9317cdb671b",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "33cc9177-87d0-4c50-9e9f-d3d5043e39f6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "c37e0d37-e0f5-40a6-908e-926b2cad9d74",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "3f23d579-982d-43cb-b5d2-7f4726cd55ca",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
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
  },
  {
    "status": 200,
    "content_id": "b4015135-dc75-4e1b-9c59-ca3deee2ebc3",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "c44b2602-4d88-4a97-b6e2-f4d6fa752137",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "ddc142dc-93de-41e4-bf4d-8a936316bcc6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

**Trial 2 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "7b0b225f-a4e2-4382-94f8-f8159e0314d3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "85c7a887-9538-42c5-b7ec-da6c3d0683ac",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "4812420c-a9be-4697-ac93-96824aa62e81",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "395f69bb-6c61-4136-91bc-0e8b7b8d9d7e",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "29c035b6-6b26-49a7-8e9e-2188263599ab",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "46dd77bd-92c3-451a-b502-aa907a3d691b",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "9f3cecc5-cd80-487e-a01e-1cac2bf56f9b",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "80335ef6-cbe7-4214-b3bc-cc8f5ed8318d",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

**Trial 3 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "64868320-852b-4d26-bf6c-c60214bc797f",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "41ae7506-d8d4-4fa0-8b0a-7722cf969b48",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "547b46ee-5070-45ed-861d-aff4d8e704f6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "f835a19f-b16b-4b85-b4f0-e7e8d36034a6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "03a7194e-05c3-4853-9d06-59f5b21dbb79",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "8078aa29-0f3b-4b52-83d5-29095a9b224f",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "c1650962-28aa-48c9-9982-fa442e589371",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "1829f6a7-81c9-4ab6-82f3-53febc07141b",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

**Criterion 2 — score separation** (`run_eval.py::main`):

**Trial 1 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "2f1eb4e4-4225-4880-b700-0276b1916083",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "9ecb3b4d-3cfc-49e1-a0e1-3afcbd72a559",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "f0759a9e-00ec-4ee6-8961-81b6bf560f0a",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "92cb69d1-a301-40a8-9f8f-6e41c96f75f9",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "892fda88-de49-4ec7-8637-bb54a80abb26",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "c767702b-8578-43e3-9a45-2b81603c2e36",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "c7dda4bb-5b1b-40b6-b974-a79d961f591a",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "767b7fd4-893b-4d5b-bc03-622efb513fa4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
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
  },
  {
    "status": 200,
    "content_id": "77a621be-073d-4522-af48-cd7881d8b5f3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.48414,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "4bb022f3-fd0a-497b-904a-6041b20be2ea",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.54788,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "e7cf20d2-9bc8-4f7a-be4d-dd79d161ebdd",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.52176,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "6896d5e4-f287-4367-9576-c4f31249203c",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.3438,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "70c0bb9f-f8fe-4af8-a74d-c45de0536e9c",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.45462,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "2d13d1e6-b083-4f11-8bf6-ce18e08ef0d4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.48956000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "c7e41fb9-ef32-46b8-a361-6fe7f438ba63",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.29208,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "160ea10e-1b84-41d6-ac28-1f7cfcaf002d",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.56528,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "1bbb6c2c-aa89-4bdf-b9d2-960c6a883124",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.7811199999999999,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 2 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "1bf50c37-c1b0-4d00-b087-01906bcc862f",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "584ed07b-2c8c-4ac2-8728-d7d1df55391e",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "4e69c717-55fe-433e-aef9-596e3e6e20c6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "9d355596-a519-4cea-a545-7780818b786d",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "584edc2a-e06c-4322-9e4e-04a331b9ab0f",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "c118b587-9c3f-4180-9599-11e0c4dcaccd",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "a1d5438e-0425-476e-b890-b859ca7e5042",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "29df631b-6797-44d0-8341-28433ecbabe4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
  {
    "status": 200,
    "content_id": "d623106a-a206-4c6c-9f09-083b0bada00b",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.25254000000000004,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "b435a822-6c4f-40b1-8241-8845b814557e",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.48414,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "b07c7405-cf0c-40ac-bee1-30fb215d875a",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.54788,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "c1f04a5b-f234-4403-a8d9-0e4ab7659946",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.52176,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "bb4e71cb-1dc1-4b86-8580-3690e4263606",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.3438,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "9f74e08c-65a5-4a4b-bf34-e2ae7683e6e2",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.45462,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "e980ecff-bb73-4dc3-b06b-b03e2acb60da",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.48956000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "8f9fc7fb-7db4-42c0-9e88-c00330755cb5",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.29208,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "42505008-29b8-4639-9ff0-70b1a4d4044c",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.56528,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "d8c0c89a-18c7-4e52-a683-eb1ea6915e5f",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.7811199999999999,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 3 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "bfda7828-9cd2-43ec-bc7d-1b444b93cdd9",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.5263,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "543fc0bc-9d2f-4d38-b4b0-26bb8f94cfc2",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.61166,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "22da134f-5e93-47a5-8931-c28de13a8ffb",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.64274,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "713f89a7-4afa-4e77-ba1f-7369a160234e",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.64986,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "14bcd781-e2d2-4dae-9780-d267673f764e",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6705,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "78e94fdd-77d0-47f5-bb7e-d81a28df0772",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.67848,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "cb936010-39fe-4fd5-ac14-223bf9c8fbc2",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.71412,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "53bf963c-5e1e-4fb5-a9bb-5361ca6229fe",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.39754,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
  {
    "status": 200,
    "content_id": "df71b09a-3d7b-4bf1-9011-1c5c86049d0a",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.25254000000000004,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "38002be9-4c42-40f0-b333-34a92e744173",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.48414,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "c263cbc7-f36e-496f-816e-2cd2a6a77765",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.54788,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "aba9dfc9-0132-4c3e-a318-d60963280931",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.52176,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "c95985e2-f6c0-447c-9e11-192f205eceb4",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.3438,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "48c419a6-4483-48ea-b9cf-bce1548dec28",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.45462,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "7ddde056-132e-4725-9404-ffe94d80b420",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.48956000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "6fae41e8-5a3b-46f7-9274-50a21442c61b",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.29208,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "63e89f38-e2fc-44f3-869d-2ae28bb4079f",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.56528,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "9c48d163-611c-4504-aa3a-8dd32b6835c3",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.7811199999999999,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Criterion 3 — label coverage** (`run_eval.py::main`):

**Trial 1 output from `run_eval.py::main`**

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

**Trial 2 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "24e57bc2-edf4-4cc5-97a5-50e853ec5b33",
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
    "content_id": "5a13c3d9-3171-455d-8852-ef22482a94fd",
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
    "content_id": "4e1109e2-3273-4eea-a58c-d196eb1034c7",
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

**Trial 3 output from `run_eval.py::main`**

```json
[
  {
    "status": 200,
    "content_id": "23e98e76-b5e1-4734-b745-930bf2465eb4",
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
    "content_id": "e9aea0c7-ad63-434e-b948-21f7f18c98c9",
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
    "content_id": "68296db0-2e2b-4d7c-999c-fec8c1d549f1",
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

**Trial 1 output from `run_eval.py::main`**

```json
[
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
  },
  {
    "creator_id": "eval_appeal_t1_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.61166,
      "confidence": 0.0,
      "content_id": "8c2b60c7-02ef-45dd-8ec6-58a60e381906",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "8c2b60c7-02ef-45dd-8ec6-58a60e381906",
    "appeal_status": 200,
    "appeal": {
      "content_id": "8c2b60c7-02ef-45dd-8ec6-58a60e381906",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "8c2b60c7-02ef-45dd-8ec6-58a60e381906",
      "creator_id": "eval_appeal_t1_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:47:59+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64274,
      "confidence": 0.0,
      "content_id": "60099b08-4000-43f1-b3c0-9d7bf4128462",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "60099b08-4000-43f1-b3c0-9d7bf4128462",
    "appeal_status": 200,
    "appeal": {
      "content_id": "60099b08-4000-43f1-b3c0-9d7bf4128462",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "60099b08-4000-43f1-b3c0-9d7bf4128462",
      "creator_id": "eval_appeal_t1_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64986,
      "confidence": 0.0,
      "content_id": "e2cc38ab-6b55-47b8-8027-9440ddef8f52",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "e2cc38ab-6b55-47b8-8027-9440ddef8f52",
    "appeal_status": 200,
    "appeal": {
      "content_id": "e2cc38ab-6b55-47b8-8027-9440ddef8f52",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "e2cc38ab-6b55-47b8-8027-9440ddef8f52",
      "creator_id": "eval_appeal_t1_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6705,
      "confidence": 0.0,
      "content_id": "6659de85-97c4-4610-8d40-89a8d4b2cfee",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "6659de85-97c4-4610-8d40-89a8d4b2cfee",
    "appeal_status": 200,
    "appeal": {
      "content_id": "6659de85-97c4-4610-8d40-89a8d4b2cfee",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "6659de85-97c4-4610-8d40-89a8d4b2cfee",
      "creator_id": "eval_appeal_t1_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.67848,
      "confidence": 0.0,
      "content_id": "369912bb-3106-4284-9318-28f248831cc8",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "369912bb-3106-4284-9318-28f248831cc8",
    "appeal_status": 200,
    "appeal": {
      "content_id": "369912bb-3106-4284-9318-28f248831cc8",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "369912bb-3106-4284-9318-28f248831cc8",
      "creator_id": "eval_appeal_t1_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.71412,
      "confidence": 0.0,
      "content_id": "0a324748-a9bb-43b5-b83e-2465550fdf00",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "0a324748-a9bb-43b5-b83e-2465550fdf00",
    "appeal_status": 200,
    "appeal": {
      "content_id": "0a324748-a9bb-43b5-b83e-2465550fdf00",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "0a324748-a9bb-43b5-b83e-2465550fdf00",
      "creator_id": "eval_appeal_t1_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:01+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.25254000000000004,
      "confidence": 0.0,
      "content_id": "e53197d4-99bb-4d6f-8303-dbc5c23bf46b",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "e53197d4-99bb-4d6f-8303-dbc5c23bf46b",
    "appeal_status": 200,
    "appeal": {
      "content_id": "e53197d4-99bb-4d6f-8303-dbc5c23bf46b",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "e53197d4-99bb-4d6f-8303-dbc5c23bf46b",
      "creator_id": "eval_appeal_t1_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:01+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.48414,
      "confidence": 0.0,
      "content_id": "2959b2ad-257f-40c3-bded-bc6e4f95d996",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "2959b2ad-257f-40c3-bded-bc6e4f95d996",
    "appeal_status": 200,
    "appeal": {
      "content_id": "2959b2ad-257f-40c3-bded-bc6e4f95d996",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "2959b2ad-257f-40c3-bded-bc6e4f95d996",
      "creator_id": "eval_appeal_t1_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:01+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.7811199999999999,
      "confidence": 0.0,
      "content_id": "ce94d22c-ba02-4616-abc8-6f0fc2700716",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "ce94d22c-ba02-4616-abc8-6f0fc2700716",
    "appeal_status": 200,
    "appeal": {
      "content_id": "ce94d22c-ba02-4616-abc8-6f0fc2700716",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "ce94d22c-ba02-4616-abc8-6f0fc2700716",
      "creator_id": "eval_appeal_t1_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:02+00:00"
    }
  }
]
```

**Trial 2 output from `run_eval.py::main`**

```json
[
  {
    "creator_id": "eval_appeal_t2_1",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5263,
      "confidence": 0.0,
      "content_id": "1ea32811-aabf-4465-85bb-be93324f4ad3",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.6175,
      "style_score": 0.3895
    },
    "submission_json_error": null,
    "content_id": "1ea32811-aabf-4465-85bb-be93324f4ad3",
    "appeal_status": 200,
    "appeal": {
      "content_id": "1ea32811-aabf-4465-85bb-be93324f4ad3",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "1ea32811-aabf-4465-85bb-be93324f4ad3",
      "creator_id": "eval_appeal_t2_1",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.61166,
      "confidence": 0.0,
      "content_id": "20bd5e8c-fcd6-49ac-b2db-86372894e3b3",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "20bd5e8c-fcd6-49ac-b2db-86372894e3b3",
    "appeal_status": 200,
    "appeal": {
      "content_id": "20bd5e8c-fcd6-49ac-b2db-86372894e3b3",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "20bd5e8c-fcd6-49ac-b2db-86372894e3b3",
      "creator_id": "eval_appeal_t2_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64274,
      "confidence": 0.0,
      "content_id": "c258c083-3d6e-4496-aba7-a55c43c8de87",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "c258c083-3d6e-4496-aba7-a55c43c8de87",
    "appeal_status": 200,
    "appeal": {
      "content_id": "c258c083-3d6e-4496-aba7-a55c43c8de87",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "c258c083-3d6e-4496-aba7-a55c43c8de87",
      "creator_id": "eval_appeal_t2_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64986,
      "confidence": 0.0,
      "content_id": "6ec7ea26-301f-4c5a-91f4-171b7eb15220",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "6ec7ea26-301f-4c5a-91f4-171b7eb15220",
    "appeal_status": 200,
    "appeal": {
      "content_id": "6ec7ea26-301f-4c5a-91f4-171b7eb15220",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "6ec7ea26-301f-4c5a-91f4-171b7eb15220",
      "creator_id": "eval_appeal_t2_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6705,
      "confidence": 0.0,
      "content_id": "8c05deac-8ddb-401c-af5a-5971aee43a48",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "8c05deac-8ddb-401c-af5a-5971aee43a48",
    "appeal_status": 200,
    "appeal": {
      "content_id": "8c05deac-8ddb-401c-af5a-5971aee43a48",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "8c05deac-8ddb-401c-af5a-5971aee43a48",
      "creator_id": "eval_appeal_t2_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.67848,
      "confidence": 0.0,
      "content_id": "ef51beba-d2d5-4b8b-8688-6fc4f9228693",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "ef51beba-d2d5-4b8b-8688-6fc4f9228693",
    "appeal_status": 200,
    "appeal": {
      "content_id": "ef51beba-d2d5-4b8b-8688-6fc4f9228693",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "ef51beba-d2d5-4b8b-8688-6fc4f9228693",
      "creator_id": "eval_appeal_t2_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.71412,
      "confidence": 0.0,
      "content_id": "1c8cd5ce-6c51-45b2-aa05-47cf1886dc77",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "1c8cd5ce-6c51-45b2-aa05-47cf1886dc77",
    "appeal_status": 200,
    "appeal": {
      "content_id": "1c8cd5ce-6c51-45b2-aa05-47cf1886dc77",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "1c8cd5ce-6c51-45b2-aa05-47cf1886dc77",
      "creator_id": "eval_appeal_t2_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.25254000000000004,
      "confidence": 0.0,
      "content_id": "fb8b30b0-9867-46ac-959f-4ef19878ff74",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "fb8b30b0-9867-46ac-959f-4ef19878ff74",
    "appeal_status": 200,
    "appeal": {
      "content_id": "fb8b30b0-9867-46ac-959f-4ef19878ff74",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "fb8b30b0-9867-46ac-959f-4ef19878ff74",
      "creator_id": "eval_appeal_t2_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:04+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.48414,
      "confidence": 0.0,
      "content_id": "a989f2c5-1b5c-41eb-88e3-965c781e93d5",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "a989f2c5-1b5c-41eb-88e3-965c781e93d5",
    "appeal_status": 200,
    "appeal": {
      "content_id": "a989f2c5-1b5c-41eb-88e3-965c781e93d5",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "a989f2c5-1b5c-41eb-88e3-965c781e93d5",
      "creator_id": "eval_appeal_t2_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:04+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.7811199999999999,
      "confidence": 0.0,
      "content_id": "fac177fe-546c-45d2-806e-3835d31fd4a7",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "fac177fe-546c-45d2-806e-3835d31fd4a7",
    "appeal_status": 200,
    "appeal": {
      "content_id": "fac177fe-546c-45d2-806e-3835d31fd4a7",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "fac177fe-546c-45d2-806e-3835d31fd4a7",
      "creator_id": "eval_appeal_t2_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:04+00:00"
    }
  }
]
```

**Trial 3 output from `run_eval.py::main`**

```json
[
  {
    "creator_id": "eval_appeal_t3_1",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5263,
      "confidence": 0.0,
      "content_id": "b14aa4f7-c06c-4e83-8f60-e54bf2923b31",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.6175,
      "style_score": 0.3895
    },
    "submission_json_error": null,
    "content_id": "b14aa4f7-c06c-4e83-8f60-e54bf2923b31",
    "appeal_status": 200,
    "appeal": {
      "content_id": "b14aa4f7-c06c-4e83-8f60-e54bf2923b31",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "b14aa4f7-c06c-4e83-8f60-e54bf2923b31",
      "creator_id": "eval_appeal_t3_1",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.61166,
      "confidence": 0.0,
      "content_id": "bfc27ca9-290f-47f4-bcce-5c0815b9d83a",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "bfc27ca9-290f-47f4-bcce-5c0815b9d83a",
    "appeal_status": 200,
    "appeal": {
      "content_id": "bfc27ca9-290f-47f4-bcce-5c0815b9d83a",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "bfc27ca9-290f-47f4-bcce-5c0815b9d83a",
      "creator_id": "eval_appeal_t3_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64274,
      "confidence": 0.0,
      "content_id": "4026a4cd-06f0-4a11-9689-a87909dfd9fe",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "4026a4cd-06f0-4a11-9689-a87909dfd9fe",
    "appeal_status": 200,
    "appeal": {
      "content_id": "4026a4cd-06f0-4a11-9689-a87909dfd9fe",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "4026a4cd-06f0-4a11-9689-a87909dfd9fe",
      "creator_id": "eval_appeal_t3_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.64986,
      "confidence": 0.0,
      "content_id": "18fba46f-2396-41c5-ac98-a4ac67ff1b38",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "18fba46f-2396-41c5-ac98-a4ac67ff1b38",
    "appeal_status": 200,
    "appeal": {
      "content_id": "18fba46f-2396-41c5-ac98-a4ac67ff1b38",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "18fba46f-2396-41c5-ac98-a4ac67ff1b38",
      "creator_id": "eval_appeal_t3_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6705,
      "confidence": 0.0,
      "content_id": "815dca1a-9a55-42eb-85ac-ff9a627bfd1b",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "815dca1a-9a55-42eb-85ac-ff9a627bfd1b",
    "appeal_status": 200,
    "appeal": {
      "content_id": "815dca1a-9a55-42eb-85ac-ff9a627bfd1b",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "815dca1a-9a55-42eb-85ac-ff9a627bfd1b",
      "creator_id": "eval_appeal_t3_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.67848,
      "confidence": 0.0,
      "content_id": "72eebd75-b0bc-4a4a-96bf-1b2aa7a7a0ad",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "72eebd75-b0bc-4a4a-96bf-1b2aa7a7a0ad",
    "appeal_status": 200,
    "appeal": {
      "content_id": "72eebd75-b0bc-4a4a-96bf-1b2aa7a7a0ad",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "72eebd75-b0bc-4a4a-96bf-1b2aa7a7a0ad",
      "creator_id": "eval_appeal_t3_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.71412,
      "confidence": 0.0,
      "content_id": "724989c8-0c9b-4b89-9056-43c8c4466718",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "724989c8-0c9b-4b89-9056-43c8c4466718",
    "appeal_status": 200,
    "appeal": {
      "content_id": "724989c8-0c9b-4b89-9056-43c8c4466718",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "724989c8-0c9b-4b89-9056-43c8c4466718",
      "creator_id": "eval_appeal_t3_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.25254000000000004,
      "confidence": 0.0,
      "content_id": "8388a052-c9a7-4bed-952c-a4b1bd6384a8",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "8388a052-c9a7-4bed-952c-a4b1bd6384a8",
    "appeal_status": 200,
    "appeal": {
      "content_id": "8388a052-c9a7-4bed-952c-a4b1bd6384a8",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "8388a052-c9a7-4bed-952c-a4b1bd6384a8",
      "creator_id": "eval_appeal_t3_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.48414,
      "confidence": 0.0,
      "content_id": "ecd3e899-08e8-463b-b9e3-90e2da682fc5",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "ecd3e899-08e8-463b-b9e3-90e2da682fc5",
    "appeal_status": 200,
    "appeal": {
      "content_id": "ecd3e899-08e8-463b-b9e3-90e2da682fc5",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "ecd3e899-08e8-463b-b9e3-90e2da682fc5",
      "creator_id": "eval_appeal_t3_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:07+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.7811199999999999,
      "confidence": 0.0,
      "content_id": "4117f0da-e60a-42b5-ab31-0d27279c73d8",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "4117f0da-e60a-42b5-ab31-0d27279c73d8",
    "appeal_status": 200,
    "appeal": {
      "content_id": "4117f0da-e60a-42b5-ab31-0d27279c73d8",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "4117f0da-e60a-42b5-ab31-0d27279c73d8",
      "creator_id": "eval_appeal_t3_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T01:48:07+00:00"
    }
  }
]
```

**Criterion 5 — bad input and service availability** (`run_eval.py::main`):

**Trial 1 output from `run_eval.py::main`**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.88236,
      "confidence": 0.0,
      "content_id": "bed0e1c9-659d-4b70-89b2-62ebdbde3636",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```

**Trial 2 output from `run_eval.py::main`**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.88236,
      "confidence": 0.0,
      "content_id": "2d23728f-d96a-40f0-a1e3-77696e5f6857",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```

**Trial 3 output from `run_eval.py::main`**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.88236,
      "confidence": 0.0,
      "content_id": "232c5f1c-9ce2-413a-9d91-3556fdfefab3",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```


**Diagnoses**

The evaluation was stable: the scores, labels, and per-criterion counts were
identical in all three trials. Only generated IDs and appeal timestamps
changed. This points to repeatable scoring behavior, not run-to-run
instability.

**Criterion misses**

- **Criterion 1 — MISSED:** 3 of 8 known-human proxy examples were labeled AI
  in every run, against a target of 0. The misses were FP05, FP06, and FP07.
  The original target about my own writing is still unverified because these
  supplied examples are not mine.
- **Criterion 2 — MISSED:** The human side scored 0/8 at or below 0.35, and
  the AI side scored only 1/10 at or above 0.65 in every run, against revised
  targets of 7/8 and 8/10. Stage: **signal one** is poorly calibrated for these
  classes: conventional human prose gets high AI scores, while edited/varied
  AI text often gets low or middle scores. Stage: **combining rule** then
  averages that weak separation (60% model, 40% style); it cannot recover
  class separation the signals did not provide.
- **Criteria 3–5 — MET:** All labels were reachable, all 10 appeal records
  were correct in each trial, and all five invalid/boundary requests returned
  the expected JSON status while `/health` stayed available.

**Broken attacks (15 total; stage and mechanism)**

- **Evasion, EV01–EV09 (9):** The detector did not label any of these AI-targeted
  samples AI; EV10 was held. Stage: **signal one** is directly evaded by
  unusual vocabulary (EV04, model score 0.6114) and by staying below its token
  window (EV08, 0.2452, then a confident human label). Typos (EV01) and heavy
  editing (EV05) also make AI text less predictable to the model (EV01 model
  score 0.1635; EV05 0.3212). Stage: **signal two** measures surface form, not
  authorship: sentence breaks, quotations, sentence-length extremes, and
  punctuation padding (EV02, EV03, EV06, EV07) can move its measures without
  changing who wrote the text. Stages: **signal one and signal two** are both
  affected by the pasted human opening in EV09. The results were 0.25254
  (EV01), 0.3438 (EV05), and 0.29208 (EV08), labeled human. EV02, EV03, EV04,
  EV06, EV07, and EV09 landed between 0.45462 and 0.56528, labeled unsure.
  Stage: **combining rule** left EV09 at 0.56528 despite its 0.7042 model
  score because its style score was 0.3569. The label mapping followed the configured
  thresholds; the problem is that these upstream scores never reached the AI
  band.
- **False positives, FP05–FP07 (3):** A person’s technical documentation,
  formal template, and deliberately repeated phrasing were all labeled AI.
  Stage: **signal one** assigns these conventional or repetitive human samples
  high model scores (0.8005, 0.8814, 0.8816). Stage: **signal two** also leans
  AI-like when sentence lengths are even, vocabulary repeats, or punctuation
  is dense (0.4755, 0.3741, 0.4629). Stage: **combining rule** averages
  those signals to 0.6705, 0.67848, and 0.71412, above the 0.65 threshold;
  **label mapping** therefore emits AI. This same pattern explains criterion
  1’s 3/8 false positives and why criterion 2’s human score target failed.
- **Malformed text, MF05–MF07 (3):** The very long single word, emoji-only
  text, and right-to-left script all received confident AI labels. Stage:
  **route** accepts any non-empty string as prose instead of identifying
  unsupported/non-prose input. Stage: **signal one** then produces extreme
  scores on input outside its useful text domain (0.9976 for the long word,
  0.9969 for emoji, and 0.9064 for RTL text). For emoji and RTL text, the
  ASCII-only word tokenizer yields no words and the style signal falls back to
  0.5. Stage: **combining rule** gives signal one enough weight to push
  them over the AI threshold (combined scores 0.66524, 0.79814, and 0.74384),
  so the **label mapping** turns non-prose into an authorship accusation.

No route crash was auto-marked in the attack run. Prompt-injection attempts
were held; their text did not change the response format or inject log fields.

---

## The Improvement

**What changed:** In `config.py`, I changed the model/style weights from
60%/40% to **40%/60%**. I changed no signal, threshold, route, or test input.

**Which diagnosis pointed at it:** Before the change, FP05–FP07 were false
positives: their model scores were 0.8005–0.8816 and the 60% model-weighted
combination put all three above the 0.65 AI threshold. Giving more weight to
the lower style scores should reduce those false accusations. The diagnosis
also warned that the style signal is a weak proxy for authorship, so the
attack and evaluation runs check whether this helps without hiding a cost.

### Attack Run — After

I ran all 56 rows with
`python run_attacks.py --set attack_set --label after`. The complete,
row-by-row report is
[attack_run_2026-11-04_1811_after.md](./results/attack_run_2026-11-04_1811_after.md).
The same verdict convention as the before run gives **11 BROKE and 45 HELD**:
EV01–EV09 and MF06–MF07 broke; the other 45 held.

| Family | Before BROKE / HELD | After BROKE / HELD |
|---|---:|---:|
| Evasion | 9 / 1 | 9 / 1 |
| False positive | 3 / 5 | 0 / 8 |
| Prompt injection | 0 / 6 | 0 / 6 |
| Malformed input | 3 / 17 | 2 / 18 |
| Same-creator flood | 0 / 12 | 0 / 12 |
| **Total** | **15 / 41** | **11 / 45** |

The three known-human examples previously labeled AI (FP05–FP07) are now
unsure. MF05, the long single word, also moved from AI to unsure; emoji-only
MF06 and RTL MF07 remain incorrectly labeled AI. Nine of ten AI evasion
examples still avoid an AI label, so reweighting did not improve that attack
family.

### Five Criteria — After

I ran `python run_eval.py --label after`. Its saved output is
[run_2026-11-04_1812_after.md](./results/run_2026-11-04_1812_after.md),
produced by `run_eval.py::main`. The complete output, including the actual
JSON from all three trials of each criterion, is included below.

| Criterion | Before (three trials) | After (three trials) | After verdict |
|---|---|---|---|
| 1. Known-human false-positive proxy | 3/8 AI in each run | 0/8 AI in each run | MET |
| 2. Human/AI score separation | H 0/8; AI 1/10 in each run | H 0/8; AI 1/10 in each run | MISSED |
| 3. All three labels reachable | 3/3 in each run | 3/3 in each run | MET |
| 4. Appeals recorded exactly once | 10/10 in each run | 10/10 in each run | MET |
| 5. Invalid and boundary input handling | 5/5 in each run | 5/5 in each run | MET |

All after-run criterion counts matched across the three trials. The request
IDs and appeal timestamps differ, but the measured scores, labels, statuses,
and verdict counts were stable.

**Did it help?** Yes, for the narrow false-positive measure: known-human AI
labels fell from 3/8 to 0/8, and total broken attacks fell from 15 to 11.
But the human examples did not become confidently human; all eight remained
above the 0.35 human cutoff, so criterion 2 still fails. AI score separation
also stayed at 1/10, and nine evasion attacks still broke. The change traded
false AI accusations for more unsure results, not better overall authorship
detection.



---


## Full Trial Output - After

### Run log — after

- Produced by: `run_eval.py::main`
- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`
- 3 trials per criterion · 2026-11-04 18:12

Each run cell reports the measured result for its criterion. A criterion
is MET only when its target holds in all three trials.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. attack-set false-positive proxy | 0 of 8 known-human examples labeled AI in each run | 0/8 AI | 0/8 AI | 0/8 AI | MET |
| 2. human and AI score separation | at least 7/8 human ≤0.35 and 8/10 AI ≥0.65 per run | H 0/8; AI 1/10 | H 0/8; AI 1/10 | H 0/8; AI 1/10 | MISSED |
| 3. all three labels reachable | 3 of 3 labels in each run | 3/3 labels | 3/3 labels | 3/3 labels | MET |
| 4. appeals recorded exactly once | 10 of 10 appeals return under_review and log once | 10/10 | 10/10 | 10/10 | MET |
| 5. invalid and boundary text handling | 5 of 5 expected responses and health checks | 5/5 | 5/5 | 5/5 | MET |

---

## What actually came back

Real output. Paste the relevant parts into your README — the rubric
asks for the actual JSON, not a description of it.

### attack-set false-positive proxy

**Trial 1**

```json
[
  {
    "status": 200,
    "content_id": "33e7f666-edd6-4faf-bc91-87c65d2039cf",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "67cfd669-c8fa-43d1-a65e-4deb023eb723",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "a3ca340d-85f7-4186-84fb-61c6b0bf4a39",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "36a72389-1bbe-4118-986b-c407a599cc24",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "f7a293c0-9406-4b63-ab4f-d764dc6255f0",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "c8b46d41-e560-48da-97a1-53efcc7e8005",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "65f802c8-c29c-4ed8-a8d2-09fe2bc9b8c6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "dbd398fc-d56a-48e1-a12a-a3935c1bf5a0",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

**Trial 2**

```json
[
  {
    "status": 200,
    "content_id": "799c7675-7da9-4766-8215-cb50e92fd9ea",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "610a4dea-3720-409a-ac59-1878d923d0d7",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "703c945e-94f4-4f3c-93af-d792f8de0c40",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "c53c19fa-bddf-46b1-bf2b-f25c32eeb3f9",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "2b81e8b9-07fb-4b31-a281-dd149e81b4a4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "a658fcb2-92ff-422c-90f6-5547d22781f1",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "1c5146bb-841c-4b2d-adbc-67e9ae02f9ba",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "1581cdd7-0977-40a3-b99a-09b39855f3d3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

**Trial 3**

```json
[
  {
    "status": 200,
    "content_id": "5f65d8d5-f151-4d5e-986a-140c16d6875c",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "8dc5f8a0-db50-4305-b42f-bcf0de43e05c",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "75bc037e-a04e-41a7-8604-17a5d801af72",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "8ac0c729-9a2f-4c77-b554-a69ce5ef0a36",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "7f48ea5a-ef92-4cf7-ae06-1da8a3bd4fb7",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "64dcf73c-d653-4bc6-a858-5d275a8a33b5",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "20c20041-03b0-4e6f-80d8-0d42f7cb3ca4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "a0ce73f7-eefa-4dab-9fd7-fd2d934455f3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "Went for a run. Legs hurt. Worth it."
  }
]
```

### human and AI score separation

**Trial 1**

```json
[
  {
    "status": 200,
    "content_id": "d702a064-e86c-4685-bf32-a287c6f27b5d",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "fc2e818d-97f0-4770-8c91-df5e15b84a2d",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "f18cab2a-90c6-4efd-b20e-948a5b163d3b",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "5b9dc064-c595-415a-96bd-b8431b81fce4",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "2fd0a3db-5541-47d8-ad08-6d37b6eaa338",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "243e9482-c33a-498c-8b5b-b5103ce7da47",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "2417e11d-dc89-4d35-854e-547e5c37b5f7",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "d7f164fe-a8db-487a-9bbb-640d98e965eb",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
  {
    "status": 200,
    "content_id": "d156306b-9e03-4559-a8d5-69850fbd494a",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "f17cdaf1-1dc0-457d-989e-ea55e4f2d1a2",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "84226805-a54e-4ab4-8670-2d63266cf06c",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.48872,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "a55d2514-a840-49de-be57-6b3104230762",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.47694000000000003,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "49eb04ef-1ba0-4cae-a5f3-2164a011dd73",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.35509999999999997,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "3c6a4ab0-2fd6-4c0d-905b-600af5a17b14",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.39558000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "832d8f55-5407-47e3-873d-0bd55474f992",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.44124,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "438da9a8-8bdc-4456-81b0-9dccf2764686",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.31552,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "1aefd8b2-47f1-47fe-bba4-dbeed12f3208",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.49582000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "b7b47a0b-df16-4248-b872-5aaca00f3720",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 2**

```json
[
  {
    "status": 200,
    "content_id": "5936ab17-b185-4b9f-8da7-1cfb15caddb6",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "b3c03a1f-6891-4a4f-b606-716345b47c88",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "e6853389-a47e-46cb-92d5-b0da0cc14b41",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "f67325f6-c71a-48a8-b719-f347c21712e3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "02288519-ad3a-404d-8401-4c514f412587",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "f02d9963-bc12-4f3c-bad3-b247f7510375",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "e310b11b-56c5-4e4d-9f0a-7875fe334515",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "78325b5e-af4e-49fe-a3a5-4a8c5b84e5e3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
  {
    "status": 200,
    "content_id": "4a7ef0c7-6184-4ad5-be06-2cc57e5a4cd8",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "01865d6f-e751-42d5-9a58-43fa42dcbe21",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "a686fe8e-c63d-420b-a10c-214f0522a21e",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.48872,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "764cf4e8-ef9f-41b5-a229-e1643612cc60",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.47694000000000003,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "b85d1d81-df18-4012-a335-b57a807006ab",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.35509999999999997,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "221cf2f4-7544-4588-a089-0457362ed0a5",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.39558000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "77bf7fd8-5a7b-4378-ab7c-214b2756ad60",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.44124,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "404f41a3-b6e7-4c4a-b9d4-3bbe2f199186",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.31552,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "719adb14-c8e1-475f-850c-d045507ea503",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.49582000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "0bb68e6c-6a33-4fe5-9a86-1760d11b5899",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 3**

```json
[
  {
    "status": 200,
    "content_id": "24aaef0b-a10f-456c-83f0-01d45f991213",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6175,
    "style_score": 0.3895,
    "combined_score": 0.4807,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"
  },
  {
    "status": 200,
    "content_id": "3921d7a1-0787-4819-bab6-39832ddb76dd",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7387,
    "style_score": 0.4211,
    "combined_score": 0.5481400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "This report sets out the findings of the working group. The group met "
  },
  {
    "status": 200,
    "content_id": "ba2e1eee-d2a3-48a2-b738-2688fabf3e86",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8051,
    "style_score": 0.3992,
    "combined_score": 0.5615600000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "I want to describe my experience of the first month in this country. T"
  },
  {
    "status": 200,
    "content_id": "778de734-ccb8-400c-bee6-3ca34c218a59",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8329,
    "style_score": 0.3753,
    "combined_score": 0.5583400000000001,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "There are three main causes of the conflict. The first cause is econom"
  },
  {
    "status": 200,
    "content_id": "9a3a8c78-ce0b-477e-9c76-474753cdc3a3",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8005,
    "style_score": 0.4755,
    "combined_score": 0.6055,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "To configure the service, edit the settings file in the installation d"
  },
  {
    "status": 200,
    "content_id": "7445189d-faae-4817-add2-73625af077d2",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8814,
    "style_score": 0.3741,
    "combined_score": 0.57702,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Dear Sir or Madam, I am writing to enquire about the position advertis"
  },
  {
    "status": 200,
    "content_id": "5b92130d-619b-46bb-b98e-5bfeb3f1228f",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.8816,
    "style_score": 0.4629,
    "combined_score": 0.63038,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "It rained on Monday. It rained on Tuesday. It rained on Wednesday and "
  },
  {
    "status": 200,
    "content_id": "24029a6d-8e1c-4d7f-8d9a-7bad86dc93bc",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3223,
    "style_score": 0.5104,
    "combined_score": 0.43516,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "human",
    "sent": "Went for a run. Legs hurt. Worth it."
  },
  {
    "status": 200,
    "content_id": "398d3ba6-a828-422f-8555-b92c5016e9a4",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "37d4bdb3-90af-45ee-84ba-036fde8121c1",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "c3155f7b-7425-46fb-b87e-3e6836033f88",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6662,
    "style_score": 0.3704,
    "combined_score": 0.48872,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "9c10bf6a-2587-4e83-960f-3358fa802bed",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.6114,
    "style_score": 0.3873,
    "combined_score": 0.47694000000000003,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of efficacious communication in the workplace cannot be"
  },
  {
    "status": 200,
    "content_id": "fe4a8606-2185-4c13-943d-8b227c2fb788",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.3212,
    "style_score": 0.3777,
    "combined_score": 0.35509999999999997,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Communication at work matters more than people say it does \u2014 and I mea"
  },
  {
    "status": 200,
    "content_id": "adaef63b-9908-4b5c-8f83-314d16add8e9",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5727,
    "style_score": 0.2775,
    "combined_score": 0.39558000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "It is worth noting that the importance of effective communication in t"
  },
  {
    "status": 200,
    "content_id": "23cca401-bfa0-4f74-ad0d-cf4dbe2362f5",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5862,
    "style_score": 0.3446,
    "combined_score": 0.44124,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "c0e0e152-bebe-4e82-8f39-6d8f367f7a3e",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.2452,
    "style_score": 0.3624,
    "combined_score": 0.31552,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": "ai",
    "sent": "Teams that communicate well do better. This is widely understood."
  },
  {
    "status": 200,
    "content_id": "639daf38-0017-435f-9c05-4eda7e82b556",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.7042,
    "style_score": 0.3569,
    "combined_score": 0.49582000000000004,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": "ai",
    "sent": "Right, so. I've been thinking about this since the meeting on Thursday"
  },
  {
    "status": 200,
    "content_id": "6bae6ab4-6364-4348-9762-322ebf1be894",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": "ai",
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

### all three labels reachable

**Trial 1**

```json
[
  {
    "status": 200,
    "content_id": "19cc584c-8a0d-4ee5-8aca-fba0bbad2573",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "d9db9de2-e374-47a0-a377-73f8369330e1",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "73d9aba4-b171-4d3f-8053-913295de693c",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 2**

```json
[
  {
    "status": 200,
    "content_id": "6184bcf3-ef59-4af7-91ee-fa0a2425147a",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "58f680f0-da95-4318-bf1a-d768466939cd",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "8651af59-3350-44c6-b29d-15f0417c52b4",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

**Trial 3**

```json
[
  {
    "status": 200,
    "content_id": "647e2b90-6061-410c-a264-ab30610df0fc",
    "guess": "human",
    "confidence": 0.0,
    "model_score": 0.1635,
    "style_score": 0.3861,
    "combined_score": 0.29706,
    "label": "We think this was probably written by a person.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "3b8e8006-0eac-4df2-b8ab-fee65775cd83",
    "guess": "unsure",
    "confidence": 0.0,
    "model_score": 0.5943,
    "style_score": 0.3189,
    "combined_score": 0.42906000000000005,
    "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  },
  {
    "status": 200,
    "content_id": "b995daa9-62c4-43a4-bdb0-1110546be19b",
    "guess": "ai",
    "confidence": 0.0,
    "model_score": 0.9792,
    "style_score": 0.484,
    "combined_score": 0.68208,
    "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
    "json_error": null,
    "group": null,
    "sent": "The importance of effective communication in the workplace cannot be o"
  }
]
```

### appeals recorded exactly once

**Trial 1**

```json
[
  {
    "creator_id": "eval_appeal_t1_1",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.4807,
      "confidence": 0.0,
      "content_id": "9fbbc006-47fb-4f67-81e3-9cc0b341bb07",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.6175,
      "style_score": 0.3895
    },
    "submission_json_error": null,
    "content_id": "9fbbc006-47fb-4f67-81e3-9cc0b341bb07",
    "appeal_status": 200,
    "appeal": {
      "content_id": "9fbbc006-47fb-4f67-81e3-9cc0b341bb07",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "9fbbc006-47fb-4f67-81e3-9cc0b341bb07",
      "creator_id": "eval_appeal_t1_1",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:57+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5481400000000001,
      "confidence": 0.0,
      "content_id": "9b50e976-1c3d-404e-8d39-1fc6e9b63784",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "9b50e976-1c3d-404e-8d39-1fc6e9b63784",
    "appeal_status": 200,
    "appeal": {
      "content_id": "9b50e976-1c3d-404e-8d39-1fc6e9b63784",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "9b50e976-1c3d-404e-8d39-1fc6e9b63784",
      "creator_id": "eval_appeal_t1_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:58+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5615600000000001,
      "confidence": 0.0,
      "content_id": "53bed9fb-25be-4264-9b2d-e2152a05f33a",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "53bed9fb-25be-4264-9b2d-e2152a05f33a",
    "appeal_status": 200,
    "appeal": {
      "content_id": "53bed9fb-25be-4264-9b2d-e2152a05f33a",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "53bed9fb-25be-4264-9b2d-e2152a05f33a",
      "creator_id": "eval_appeal_t1_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:58+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5583400000000001,
      "confidence": 0.0,
      "content_id": "b8c4355c-1b12-43e2-beaf-ddb9ca1868ea",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "b8c4355c-1b12-43e2-beaf-ddb9ca1868ea",
    "appeal_status": 200,
    "appeal": {
      "content_id": "b8c4355c-1b12-43e2-beaf-ddb9ca1868ea",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "b8c4355c-1b12-43e2-beaf-ddb9ca1868ea",
      "creator_id": "eval_appeal_t1_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:58+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6055,
      "confidence": 0.0,
      "content_id": "be97a433-2364-4d79-9ff5-e5463c2ae550",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "be97a433-2364-4d79-9ff5-e5463c2ae550",
    "appeal_status": 200,
    "appeal": {
      "content_id": "be97a433-2364-4d79-9ff5-e5463c2ae550",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "be97a433-2364-4d79-9ff5-e5463c2ae550",
      "creator_id": "eval_appeal_t1_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:59+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.57702,
      "confidence": 0.0,
      "content_id": "acf1f3f2-b173-4633-9ff3-d4f553c2ffbc",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "acf1f3f2-b173-4633-9ff3-d4f553c2ffbc",
    "appeal_status": 200,
    "appeal": {
      "content_id": "acf1f3f2-b173-4633-9ff3-d4f553c2ffbc",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "acf1f3f2-b173-4633-9ff3-d4f553c2ffbc",
      "creator_id": "eval_appeal_t1_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:59+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.63038,
      "confidence": 0.0,
      "content_id": "af935a30-c047-44f9-abd8-4ba42ff344b6",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "af935a30-c047-44f9-abd8-4ba42ff344b6",
    "appeal_status": 200,
    "appeal": {
      "content_id": "af935a30-c047-44f9-abd8-4ba42ff344b6",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "af935a30-c047-44f9-abd8-4ba42ff344b6",
      "creator_id": "eval_appeal_t1_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:11:59+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.29706,
      "confidence": 0.0,
      "content_id": "9696eeb0-afa1-4699-a797-c6106f216056",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "9696eeb0-afa1-4699-a797-c6106f216056",
    "appeal_status": 200,
    "appeal": {
      "content_id": "9696eeb0-afa1-4699-a797-c6106f216056",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "9696eeb0-afa1-4699-a797-c6106f216056",
      "creator_id": "eval_appeal_t1_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.42906000000000005,
      "confidence": 0.0,
      "content_id": "a38fc600-4f90-41c7-a474-6f0f723ae32a",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "a38fc600-4f90-41c7-a474-6f0f723ae32a",
    "appeal_status": 200,
    "appeal": {
      "content_id": "a38fc600-4f90-41c7-a474-6f0f723ae32a",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "a38fc600-4f90-41c7-a474-6f0f723ae32a",
      "creator_id": "eval_appeal_t1_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:00+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t1_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.68208,
      "confidence": 0.0,
      "content_id": "832736a2-4acb-4033-af06-f059e22e2118",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "832736a2-4acb-4033-af06-f059e22e2118",
    "appeal_status": 200,
    "appeal": {
      "content_id": "832736a2-4acb-4033-af06-f059e22e2118",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "832736a2-4acb-4033-af06-f059e22e2118",
      "creator_id": "eval_appeal_t1_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:00+00:00"
    }
  }
]
```

**Trial 2**

```json
[
  {
    "creator_id": "eval_appeal_t2_1",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.4807,
      "confidence": 0.0,
      "content_id": "1dc0ba20-88dc-4f95-a29b-9ab26438fa93",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.6175,
      "style_score": 0.3895
    },
    "submission_json_error": null,
    "content_id": "1dc0ba20-88dc-4f95-a29b-9ab26438fa93",
    "appeal_status": 200,
    "appeal": {
      "content_id": "1dc0ba20-88dc-4f95-a29b-9ab26438fa93",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "1dc0ba20-88dc-4f95-a29b-9ab26438fa93",
      "creator_id": "eval_appeal_t2_1",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:01+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5481400000000001,
      "confidence": 0.0,
      "content_id": "e2d7b74c-edf1-4362-90ec-cc684130134d",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "e2d7b74c-edf1-4362-90ec-cc684130134d",
    "appeal_status": 200,
    "appeal": {
      "content_id": "e2d7b74c-edf1-4362-90ec-cc684130134d",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "e2d7b74c-edf1-4362-90ec-cc684130134d",
      "creator_id": "eval_appeal_t2_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:01+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5615600000000001,
      "confidence": 0.0,
      "content_id": "ec480377-6726-4740-a9ab-e23995c4a6e9",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "ec480377-6726-4740-a9ab-e23995c4a6e9",
    "appeal_status": 200,
    "appeal": {
      "content_id": "ec480377-6726-4740-a9ab-e23995c4a6e9",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "ec480377-6726-4740-a9ab-e23995c4a6e9",
      "creator_id": "eval_appeal_t2_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5583400000000001,
      "confidence": 0.0,
      "content_id": "9260d59b-c102-4e5e-a0e6-371c1dfcbd01",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "9260d59b-c102-4e5e-a0e6-371c1dfcbd01",
    "appeal_status": 200,
    "appeal": {
      "content_id": "9260d59b-c102-4e5e-a0e6-371c1dfcbd01",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "9260d59b-c102-4e5e-a0e6-371c1dfcbd01",
      "creator_id": "eval_appeal_t2_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6055,
      "confidence": 0.0,
      "content_id": "99f6866f-69fc-44bf-a901-889a05a0129a",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "99f6866f-69fc-44bf-a901-889a05a0129a",
    "appeal_status": 200,
    "appeal": {
      "content_id": "99f6866f-69fc-44bf-a901-889a05a0129a",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "99f6866f-69fc-44bf-a901-889a05a0129a",
      "creator_id": "eval_appeal_t2_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.57702,
      "confidence": 0.0,
      "content_id": "1a2c303e-da63-411d-b594-7cb337bc9d70",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "1a2c303e-da63-411d-b594-7cb337bc9d70",
    "appeal_status": 200,
    "appeal": {
      "content_id": "1a2c303e-da63-411d-b594-7cb337bc9d70",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "1a2c303e-da63-411d-b594-7cb337bc9d70",
      "creator_id": "eval_appeal_t2_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:02+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.63038,
      "confidence": 0.0,
      "content_id": "00399d16-2b5f-4222-af3d-7b637ada7672",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "00399d16-2b5f-4222-af3d-7b637ada7672",
    "appeal_status": 200,
    "appeal": {
      "content_id": "00399d16-2b5f-4222-af3d-7b637ada7672",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "00399d16-2b5f-4222-af3d-7b637ada7672",
      "creator_id": "eval_appeal_t2_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.29706,
      "confidence": 0.0,
      "content_id": "98bef607-c3eb-4d6b-95f6-89abd422259a",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "98bef607-c3eb-4d6b-95f6-89abd422259a",
    "appeal_status": 200,
    "appeal": {
      "content_id": "98bef607-c3eb-4d6b-95f6-89abd422259a",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "98bef607-c3eb-4d6b-95f6-89abd422259a",
      "creator_id": "eval_appeal_t2_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:03+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.42906000000000005,
      "confidence": 0.0,
      "content_id": "6396739f-0dc0-42f8-ba4f-2b0f9e0a0a1b",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "6396739f-0dc0-42f8-ba4f-2b0f9e0a0a1b",
    "appeal_status": 200,
    "appeal": {
      "content_id": "6396739f-0dc0-42f8-ba4f-2b0f9e0a0a1b",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "6396739f-0dc0-42f8-ba4f-2b0f9e0a0a1b",
      "creator_id": "eval_appeal_t2_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:04+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t2_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.68208,
      "confidence": 0.0,
      "content_id": "f5aa9de0-1fbf-41cc-ad7c-0dc703c3d21b",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "f5aa9de0-1fbf-41cc-ad7c-0dc703c3d21b",
    "appeal_status": 200,
    "appeal": {
      "content_id": "f5aa9de0-1fbf-41cc-ad7c-0dc703c3d21b",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "f5aa9de0-1fbf-41cc-ad7c-0dc703c3d21b",
      "creator_id": "eval_appeal_t2_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:04+00:00"
    }
  }
]
```

**Trial 3**

```json
[
  {
    "creator_id": "eval_appeal_t3_1",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.4807,
      "confidence": 0.0,
      "content_id": "29cdfca6-59ab-42d4-9923-3805942aa951",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.6175,
      "style_score": 0.3895
    },
    "submission_json_error": null,
    "content_id": "29cdfca6-59ab-42d4-9923-3805942aa951",
    "appeal_status": 200,
    "appeal": {
      "content_id": "29cdfca6-59ab-42d4-9923-3805942aa951",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "29cdfca6-59ab-42d4-9923-3805942aa951",
      "creator_id": "eval_appeal_t3_1",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:04+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_2",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5481400000000001,
      "confidence": 0.0,
      "content_id": "8b0ec8e1-4fbc-488c-8f3f-9e053d5ed05f",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.7387,
      "style_score": 0.4211
    },
    "submission_json_error": null,
    "content_id": "8b0ec8e1-4fbc-488c-8f3f-9e053d5ed05f",
    "appeal_status": 200,
    "appeal": {
      "content_id": "8b0ec8e1-4fbc-488c-8f3f-9e053d5ed05f",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "8b0ec8e1-4fbc-488c-8f3f-9e053d5ed05f",
      "creator_id": "eval_appeal_t3_2",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_3",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5615600000000001,
      "confidence": 0.0,
      "content_id": "7838f426-2736-4051-a5e9-f761baea1967",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8051,
      "style_score": 0.3992
    },
    "submission_json_error": null,
    "content_id": "7838f426-2736-4051-a5e9-f761baea1967",
    "appeal_status": 200,
    "appeal": {
      "content_id": "7838f426-2736-4051-a5e9-f761baea1967",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "7838f426-2736-4051-a5e9-f761baea1967",
      "creator_id": "eval_appeal_t3_3",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_4",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.5583400000000001,
      "confidence": 0.0,
      "content_id": "6c4d8542-4dfb-4481-b935-9949711ecff0",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8329,
      "style_score": 0.3753
    },
    "submission_json_error": null,
    "content_id": "6c4d8542-4dfb-4481-b935-9949711ecff0",
    "appeal_status": 200,
    "appeal": {
      "content_id": "6c4d8542-4dfb-4481-b935-9949711ecff0",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "6c4d8542-4dfb-4481-b935-9949711ecff0",
      "creator_id": "eval_appeal_t3_4",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_5",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.6055,
      "confidence": 0.0,
      "content_id": "4118780e-ebd9-476b-ba06-fa043813e535",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8005,
      "style_score": 0.4755
    },
    "submission_json_error": null,
    "content_id": "4118780e-ebd9-476b-ba06-fa043813e535",
    "appeal_status": 200,
    "appeal": {
      "content_id": "4118780e-ebd9-476b-ba06-fa043813e535",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "4118780e-ebd9-476b-ba06-fa043813e535",
      "creator_id": "eval_appeal_t3_5",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:05+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_6",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.57702,
      "confidence": 0.0,
      "content_id": "d3e707e6-0b8b-426c-80cb-63fa4ff22c96",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8814,
      "style_score": 0.3741
    },
    "submission_json_error": null,
    "content_id": "d3e707e6-0b8b-426c-80cb-63fa4ff22c96",
    "appeal_status": 200,
    "appeal": {
      "content_id": "d3e707e6-0b8b-426c-80cb-63fa4ff22c96",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "d3e707e6-0b8b-426c-80cb-63fa4ff22c96",
      "creator_id": "eval_appeal_t3_6",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_7",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.63038,
      "confidence": 0.0,
      "content_id": "976f2d38-0168-4e59-9316-a275a55d1df8",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.8816,
      "style_score": 0.4629
    },
    "submission_json_error": null,
    "content_id": "976f2d38-0168-4e59-9316-a275a55d1df8",
    "appeal_status": 200,
    "appeal": {
      "content_id": "976f2d38-0168-4e59-9316-a275a55d1df8",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "976f2d38-0168-4e59-9316-a275a55d1df8",
      "creator_id": "eval_appeal_t3_7",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:06+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_8",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.29706,
      "confidence": 0.0,
      "content_id": "60abddb6-7e02-4a42-b4c5-ee2117e77ea0",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.1635,
      "style_score": 0.3861
    },
    "submission_json_error": null,
    "content_id": "60abddb6-7e02-4a42-b4c5-ee2117e77ea0",
    "appeal_status": 200,
    "appeal": {
      "content_id": "60abddb6-7e02-4a42-b4c5-ee2117e77ea0",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "60abddb6-7e02-4a42-b4c5-ee2117e77ea0",
      "creator_id": "eval_appeal_t3_8",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:07+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_9",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.42906000000000005,
      "confidence": 0.0,
      "content_id": "d4731e0d-c814-4232-9a75-1cc9d8285502",
      "guess": "unsure",
      "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
      "model_score": 0.5943,
      "style_score": 0.3189
    },
    "submission_json_error": null,
    "content_id": "d4731e0d-c814-4232-9a75-1cc9d8285502",
    "appeal_status": 200,
    "appeal": {
      "content_id": "d4731e0d-c814-4232-9a75-1cc9d8285502",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "d4731e0d-c814-4232-9a75-1cc9d8285502",
      "creator_id": "eval_appeal_t3_9",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:07+00:00"
    }
  },
  {
    "creator_id": "eval_appeal_t3_10",
    "submission_status": 200,
    "submission": {
      "combined_score": 0.68208,
      "confidence": 0.0,
      "content_id": "54fe4916-0a52-4275-a2e3-1e6bb776796c",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.9792,
      "style_score": 0.484
    },
    "submission_json_error": null,
    "content_id": "54fe4916-0a52-4275-a2e3-1e6bb776796c",
    "appeal_status": 200,
    "appeal": {
      "content_id": "54fe4916-0a52-4275-a2e3-1e6bb776796c",
      "message": "Your appeal has been recorded for review.",
      "ok": true,
      "status": "under_review"
    },
    "appeal_json_error": null,
    "audit_log_status": 200,
    "audit_log_json_error": null,
    "audit_appeal_records": 1,
    "audit_appeal_record": {
      "content_id": "54fe4916-0a52-4275-a2e3-1e6bb776796c",
      "creator_id": "eval_appeal_t3_10",
      "event": "appeal",
      "reasoning": "I wrote this work and request a review.",
      "status": "under_review",
      "timestamp": "2026-11-05T02:12:07+00:00"
    }
  }
]
```

### invalid and boundary text handling

**Trial 1**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.82504,
      "confidence": 0.0,
      "content_id": "2d807c41-e1d9-473e-b18b-a33898e38666",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```

**Trial 2**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.82504,
      "confidence": 0.0,
      "content_id": "b67ab429-1696-400c-ba34-773d7986ebf4",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```

**Trial 3**

```json
[
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "   "
  },
  {
    "status": 400,
    "response": {
      "error": "invalid_text",
      "message": "text must be a non-empty string."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 200,
    "response": {
      "combined_score": 0.82504,
      "confidence": 0.0,
      "content_id": "0534b56a-1d35-476f-a947-a11eda09c2e5",
      "guess": "ai",
      "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
      "model_score": 0.997,
      "style_score": 0.7104
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  },
  {
    "status": 413,
    "response": {
      "error": "text_too_long",
      "message": "text must be at most 10000 characters. Please shorten it."
    },
    "json_error": null,
    "health_status": 200,
    "sent": "A writer submits a complete piece of original work for review. A write"
  }
]
```


## What's Still Broken

Criterion 2 remains missed, and criterion 1's personal-writing target remains
unverified because the eight supplied examples are not my own writing. All
eight known-human examples are now unsure rather than confidently human, and
most AI-targeted evasion examples remain unsure or human. Unsupported inputs
also remain a risk: emoji-only and RTL text still get AI labels because the
signals are not calibrated for them. The 40%/60% split is a single measured
experiment, not a validated production setting.

**The trade I'd make if this ran for real:**

I would keep an unsure result out of automatic enforcement and send it for
human review, even though that means more AI-written text avoids a confident
AI label. A heuristic score is not proof of authorship, and a real writer
should not bear the cost of a false accusation.



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
