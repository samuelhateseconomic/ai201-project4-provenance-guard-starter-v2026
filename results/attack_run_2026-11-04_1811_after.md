# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-04 18:11
- Auto-marked BROKE (5xx, crash, no response): **0**
- Manual verdicts: **11 BROKE, 45 HELD**

The script cannot decide attacks that depend on intended outcome; I judged
them against their targets. Evasions that did not receive an AI label are
BROKE; a known-human example is BROKE only if it received an AI label. The
malformed non-prose cases labeled AI are BROKE. Prompt-injection attempts and
rate-limited flood rows are HELD because they did not achieve their stated goal.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Combined score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `060ea6df-915b-4ac7-a779-080e4bb84f73` | human | 0.297 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `7bc0c295-63ad-4963-8461-eebb8759fc11` | unsure | 0.429 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `dc4cc77b-7ead-4ce9-9251-b6de0dd08e89` | unsure | 0.489 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `01222e94-afba-4f39-bc1b-e7a30b7428d3` | unsure | 0.477 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `1b07371e-3dfe-4b29-8c8d-f63c274874c4` | unsure | 0.355 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `766831c8-9a01-4198-adb6-65a59f9220d8` | unsure | 0.396 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `b46efa7a-bf58-453c-90e0-48006e54a945` | unsure | 0.441 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `58a9ae7b-336b-4906-aecf-9249fb1726d4` | human | 0.316 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `24ae7d91-8fed-45b6-a1ef-7c82e83ff74e` | unsure | 0.496 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `7a339b8f-2d2c-45f5-a267-a93ea52fb18b` | ai | 0.682 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `86274b48-bfe7-470c-8a09-127160b25bbd` | unsure | 0.481 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `8499cc08-5045-44a3-a931-5d4c8374696a` | unsure | 0.548 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `f5486398-b57f-4c5c-b8c3-4da99a8d248a` | unsure | 0.562 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | `83076b34-0448-44f9-95ff-97c7564195c1` | unsure | 0.558 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | `b8b38e5e-037c-433d-9265-48dbbbb55d4a` | unsure | 0.606 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | `4c49f980-b4c1-4460-a718-2a96b2322a3b` | unsure | 0.577 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `1d35177c-8f6a-40c5-85f8-6f29720e2ea5` | unsure | 0.630 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | `e6b7b22a-1b72-4393-b903-433c823ef49f` | unsure | 0.435 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `1d094e5d-81e4-48d6-8143-a32b93941dd3` | human | 0.350 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `9299ef30-76b5-4736-b497-b658d052fa35` | human | 0.261 | HELD |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `6532336e-5512-49a4-a4d6-8473590fd1ef` | unsure | 0.442 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `afda8b8a-4d04-4ec6-b6c4-fa13334b153f` | unsure | 0.451 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `9f000c70-9b07-4a53-b1e5-14551f9ccd50` | unsure | 0.586 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `294c19c1-0d43-4a82-9167-fb95214b59ec` | unsure | 0.457 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 200 | `4fdf2646-fbd0-4385-b573-9f1f91c5886d` | human | 0.290 | HELD |
| MF04 | malformed | text is only punctuation | 200 | `d966b883-f506-45ef-9a8c-b8265c5038a5` | human | 0.304 | HELD |
| MF05 | malformed | text is a very long single word | 200 | `b43a331e-5d50-492e-913f-f44b61ed82ec` | unsure | 0.499 | HELD |
| MF06 | malformed | text is emoji only | 200 | `22f5a445-7bfc-4aee-8f57-71c216182ee9` | ai | 0.699 | BROKE |
| MF07 | malformed | text is right-to-left script | 200 | `4341ce8a-e74f-4908-b9a0-275d966aeab6` | ai | 0.663 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `3a0b7181-c330-4bca-a90c-fc17ff290b9e` | human | 0.148 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `cecafceb-ce82-4947-a9b9-e6047fef893f` | human | 0.148 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `103162a2-aeaa-4248-95c1-864669f7bf95` | human | 0.148 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c8757dfa-8f31-4197-b93d-e7781c942ea5` | human | 0.148 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `0b4747b4-ce85-4a64-8460-8092ca2d966e` | human | 0.148 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `bdf97e9b-1102-4f9c-8f7f-ca92a2908cf0` | human | 0.148 | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `930d5a4b-626d-4adf-a559-2f4363ca8c19` | human | 0.148 | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `fbf620d3-c8fc-4fd4-884e-74cbb1bc1b7f` | human | 0.148 | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `661788ee-c843-4508-9de3-0a602e82e3be` | human | 0.148 | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `4e7d2393-33fe-427e-bc9d-450ca3d804e5` | human | 0.148 | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

---

## By family

| Family | Attacks | BROKE | HELD |
|---|---|---|---|
| `evasion` | 10 | 9 | 1 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 2 | 18 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "060ea6df-915b-4ac7-a779-080e4bb84f73",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.29706,
  "model_score": 0.1635,
  "style_score": 0.3861,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "7bc0c295-63ad-4963-8461-eebb8759fc11",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.42906000000000005,
  "model_score": 0.5943,
  "style_score": 0.3189,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "dc4cc77b-7ead-4ce9-9251-b6de0dd08e89",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.48872,
  "model_score": 0.6662,
  "style_score": 0.3704,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "01222e94-afba-4f39-bc1b-e7a30b7428d3",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.47694000000000003,
  "model_score": 0.6114,
  "style_score": 0.3873,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "1b07371e-3dfe-4b29-8c8d-f63c274874c4",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.35509999999999997,
  "model_score": 0.3212,
  "style_score": 0.3777,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "766831c8-9a01-4198-adb6-65a59f9220d8",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.39558000000000004,
  "model_score": 0.5727,
  "style_score": 0.2775,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "b46efa7a-bf58-453c-90e0-48006e54a945",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.44124,
  "model_score": 0.5862,
  "style_score": 0.3446,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "58a9ae7b-336b-4906-aecf-9249fb1726d4",
  "creator_id": "attacker_EV08",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.31552,
  "model_score": 0.2452,
  "style_score": 0.3624,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "24ae7d91-8fed-45b6-a1ef-7c82e83ff74e",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.49582000000000004,
  "model_score": 0.7042,
  "style_score": 0.3569,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "7a339b8f-2d2c-45f5-a267-a93ea52fb18b",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.0,
  "combined_score": 0.68208,
  "model_score": 0.9792,
  "style_score": 0.484,
  "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "86274b48-bfe7-470c-8a09-127160b25bbd",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.4807,
  "model_score": 0.6175,
  "style_score": 0.3895,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "8499cc08-5045-44a3-a931-5d4c8374696a",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.5481400000000001,
  "model_score": 0.7387,
  "style_score": 0.4211,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "f5486398-b57f-4c5c-b8c3-4da99a8d248a",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.5615600000000001,
  "model_score": 0.8051,
  "style_score": 0.3992,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "83076b34-0448-44f9-95ff-97c7564195c1",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.5583400000000001,
  "model_score": 0.8329,
  "style_score": 0.3753,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "b8b38e5e-037c-433d-9265-48dbbbb55d4a",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.6055,
  "model_score": 0.8005,
  "style_score": 0.4755,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "4c49f980-b4c1-4460-a718-2a96b2322a3b",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.57702,
  "model_score": 0.8814,
  "style_score": 0.3741,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "1d35177c-8f6a-40c5-85f8-6f29720e2ea5",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.63038,
  "model_score": 0.8816,
  "style_score": 0.4629,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "e6b7b22a-1b72-4393-b903-433c823ef49f",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.43516,
  "model_score": 0.3223,
  "style_score": 0.5104,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "1d094e5d-81e4-48d6-8143-a32b93941dd3",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.34988,
  "model_score": 0.4625,
  "style_score": 0.2748,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "9299ef30-76b5-4736-b497-b658d052fa35",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.26139999999999997,
  "model_score": 0.2044,
  "style_score": 0.2994,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "6532336e-5512-49a4-a4d6-8473590fd1ef",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.44196,
  "model_score": 0.5943,
  "style_score": 0.3404,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "afda8b8a-4d04-4ec6-b6c4-fa13334b153f",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.45054000000000005,
  "model_score": 0.4998,
  "style_score": 0.4177,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "9f000c70-9b07-4a53-b1e5-14551f9ccd50",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.5864,
  "model_score": 0.6401,
  "style_score": 0.5506,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "294c19c1-0d43-4a82-9167-fb95214b59ec",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.4572,
  "model_score": 0.5583,
  "style_score": 0.3898,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "4fdf2646-fbd0-4385-b573-9f1f91c5886d",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.29046,
  "model_score": 0.0,
  "style_score": 0.4841,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "d966b883-f506-45ef-9a8c-b8265c5038a5",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.30448,
  "model_score": 0.0112,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "b43a331e-5d50-492e-913f-f44b61ed82ec",
  "creator_id": "attacker_MF05",
  "guess": "unsure",
  "confidence": 0.0,
  "combined_score": 0.49906000000000006,
  "model_score": 0.9976,
  "style_score": 0.1667,
  "label": "We can't confidently tell whether this was written by a person or generated by AI. This result is uncertain, not an accusation.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "22f5a445-7bfc-4aee-8f57-71c216182ee9",
  "creator_id": "attacker_MF06",
  "guess": "ai",
  "confidence": 0.0,
  "combined_score": 0.69876,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "4341ce8a-e74f-4908-b9a0-275d966aeab6",
  "creator_id": "attacker_MF07",
  "guess": "ai",
  "confidence": 0.0,
  "combined_score": 0.66256,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "This text has features often associated with AI writing, but this result is not proof of who wrote it. You can appeal if you think we got it wrong.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "3a0b7181-c330-4bca-a90c-fc17ff290b9e",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "cecafceb-ce82-4947-a9b9-e6047fef893f",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "103162a2-aeaa-4248-95c1-864669f7bf95",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "c8757dfa-8f31-4197-b93d-e7781c942ea5",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "0b4747b4-ce85-4a64-8460-8092ca2d966e",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 200,
  "content_id": "bdf97e9b-1102-4f9c-8f7f-ca92a2908cf0",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 200,
  "content_id": "930d5a4b-626d-4adf-a559-2f4363ca8c19",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 200,
  "content_id": "fbf620d3-c8fc-4fd4-884e-74cbb1bc1b7f",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 200,
  "content_id": "661788ee-c843-4508-9de3-0a602e82e3be",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 200,
  "content_id": "4e7d2393-33fe-427e-bc9d-450ca3d804e5",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.0,
  "combined_score": 0.14786,
  "model_score": 0.0287,
  "style_score": 0.2273,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "combined_score": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
