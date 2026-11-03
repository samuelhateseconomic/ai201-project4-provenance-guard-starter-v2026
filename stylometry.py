"""
Signal two: the style signal.

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are implemented below. Their scaling and direction are simple
heuristics, so calibration—not intuition—is needed before relying on them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics
import unicodedata


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    The coefficient of variation of sentence word counts.

    Returns:
        A non-negative float. Fewer than two sentences return 0.0.
    """
    lengths = [len(words(sentence)) for sentence in sentences(text)]
    if len(lengths) < 2:
        return 0.0

    mean_length = statistics.mean(lengths)
    if mean_length == 0:
        return 0.0
    return statistics.stdev(lengths) / mean_length


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    The proportion of characters that are Unicode punctuation.

    Returns:
        A float between 0 and 1.
    """
    if not text:
        return 0.0
    punctuation_count = sum(
        unicodedata.category(character).startswith("P") for character in text
    )
    return punctuation_count / len(text)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    Combine the measures into one number. Low sentence-length variation,
    repeated vocabulary, and high punctuation density each add to the
    AI-leaning score. These are simple heuristics, not authorship evidence.

    Heuristic conventions:

      1. Low sentence-length spread and low type-token ratio are treated as
         more AI-like; punctuation density is scaled to 0–1 at 10% of the
         characters.
      2. Each component is scaled to 0–1 and given equal weight.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.
    """
    tokens = words(text)
    if not tokens:
        return 0.5

    sentence_list = sentences(text)
    spread = sentence_length_spread(text)
    spread_score = 0.5 if len(sentence_list) < 2 else 1.0 / (1.0 + spread)
    repetition_score = 1.0 - type_token_ratio(text)
    punctuation_score = min(punctuation_density(text) / 0.10, 1.0)

    return round(
        (spread_score + repetition_score + punctuation_score) / 3.0,
        4,
    )


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nThe style score is a heuristic, not proof of authorship.")
