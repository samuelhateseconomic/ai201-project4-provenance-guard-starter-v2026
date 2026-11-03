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
| Lightly edited AI-style | 0.6153 | 0.3925 | 0.52618 |

**What surprised me:** The style scores are close together, so these three simple features did not separate the four examples well. The model also gave the human-style anecdote a relatively high score (0.6593). These small examples are a diagnostic check, not proof that either signal can identify authorship.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



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
$submitBody = '{"text":"The project service accepts a writer submission and returns a score. A reviewer can inspect the audit record later. This example is for checking the route and log, not for judging authorship.","creator_id":"readme-sample"}'
$submitBody | curl.exe -sS -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" --data-binary "@-"
```

```json
{
  "combined_score": 0.23994000000000001,
  "confidence": 0.0,
  "content_id": "2c432a65-68bf-439b-9c94-09fb027a4831",
  "guess": "pending",
  "label": "Classification is not implemented yet.",
  "model_score": 0.1319,
  "style_score": 0.402
}
```

**An appeal**

```powershell
$appealBody = '{"content_id":"...","reasoning":"..."}'
$appealBody | curl.exe -sS -X POST http://127.0.0.1:5000/appeal -H "Content-Type: application/json" --data-binary "@-"
```

```json

```

**What the log shows afterwards**

```powershell
curl.exe -sS "http://127.0.0.1:5000/log?limit=3"
```

```json
{
  "count": 1,
  "entries": [
    {
      "combined_score": 0.23994000000000001,
      "content_id": "2c432a65-68bf-439b-9c94-09fb027a4831",
      "creator_id": "readme-sample",
      "guess": "pending",
      "label": "Classification is not implemented yet.",
      "model_score": 0.1319,
      "status": "decided",
      "style_score": 0.402,
      "timestamp": "2026-11-03T01:28:37+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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
