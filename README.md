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

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

Criteria 1 and 2 remain missed, and criterion 1's personal-writing target
remains unverified. I would collect a real set of my own writing and
recalibrate signal one on human and AI examples before changing thresholds;
otherwise I could hide the false positives only by letting more AI samples
through. I would also add deliberate handling for text outside the tokenizer's
language/length assumptions rather than treating an extreme score as evidence
of AI authorship. Those are follow-up changes, not fixes validated by this
before-run.

**The trade I'd make if this ran for real:**

I would widen the unsure band or require human review before an AI label when
signals disagree, even if more AI-written text consequently avoids a confident
label. The site and its detection goal would pay that cost; a real writer should
not pay for a heuristic false accusation.



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
