# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1.

On a test set of at least 100 pieces known to be human-written, no more than 1 piece (1%) may receive the AI label in each of the three runs.

**Why this target:**
An AI label can unfairly harm a real writer, so I would rather miss some AI-written text than falsely accuse more than 1 in 100 human writers. The minimum sample size makes the 1% target measurable; I will count only the AI label as a false positive, not the uncertain label.


---

## 2.
For each of three runs, at least 8 of 10 clearly human-written examples must score at or below 0.35, and at least 8 of 10 clearly AI-written examples must score at or above 0.65.

**Why this target:**
The 0–1 score should leave a visible gap between clear examples instead of forcing a confident label when the signals overlap. The 0.35 and 0.65 cutoffs leave a middle band for uncertain cases; requiring 8 of 10 in each class allows some difficult examples without hiding poor separation.


---

## 3.

Every run must produce all three intended labels—human, uncertain, and AI—when tested with labeled examples: at least one example for each label in each of the three runs.

**Why this target:**
The middle label is useful only if it can actually be reached, and the other labels must not be made unreachable by the thresholds. Testing all three labels in every run catches threshold or scoring changes that collapse the system into one or two outcomes.


---

## 4.
For every valid appeal in a test of 10 submissions, the response must report `under_review` and the audit log must contain exactly one new appeal record with its `content_id`, `reasoning`, and timestamp.

**Why this target:**
Writers need confirmation that their appeal was received, and reviewers need a reliable record to investigate it. Recording an appeal does not automatically teach or update the detector; any future model changes should be separately reviewed and tested.

---

## 5.

If `text` is missing, empty, or whitespace-only, the endpoint must return HTTP 400 with a JSON error. It must accept text up to 10,000 characters; text longer than that must return HTTP 413 with a JSON error asking the writer to shorten it. The service must remain available after each rejected request.

**Why this target:**
Writers get a clear, actionable response instead of a confusing server error. A fixed 10,000-character limit makes the boundary testable and protects the service from unexpectedly large requests; accepting a text file is outside this endpoint's contract.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
