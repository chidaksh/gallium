"""Heuristic channel-fit checks (rule-based, no LLM).

These are pattern-matching checks against published best-practice guides
for each channel. They are *flags*, not scores — a flag means "a human
should look at this," not "this variant loses points."

Why heuristic and not learned: with 0 historical data and a portfolio demo,
fake learned scores would mislead more than they'd inform. Honest flags are
better than dishonest numbers.
"""

from __future__ import annotations

import re
from typing import List, Dict

from creatives import Creative


def check_linkedin_organic_post(creative: Creative) -> List[Dict[str, str]]:
    """Returns a list of {severity, code, message, evidence} dicts. Empty = clean."""
    flags: List[Dict[str, str]] = []
    text = creative.full_text
    first_line = text.strip().splitlines()[0] if text.strip() else ""

    # Rule 1: First line should not start with "We"
    if re.match(r"^\s*We\s", first_line, re.IGNORECASE):
        flags.append({
            "severity": "warn",
            "code": "OPENS_WITH_WE",
            "message": "Opens with 'We' — company-centric, weak hook for passive_scroll attention mode",
            "evidence": first_line,
        })

    # Rule 2: First line word count
    fl_words = len(first_line.split())
    if fl_words > 12:
        flags.append({
            "severity": "warn",
            "code": "FIRST_LINE_TOO_LONG",
            "message": f"First line is {fl_words} words; target ≤12 for thumb-stop on mobile",
            "evidence": first_line,
        })

    # Rule 3: Word count overall (LinkedIn organic optimum is roughly 100-300 words)
    word_count = len(re.findall(r"\b\w+\b", text))
    if word_count < 50:
        flags.append({
            "severity": "warn",
            "code": "TOO_SHORT",
            "message": f"Body is {word_count} words; LinkedIn algorithm favors ≥50 for engagement",
            "evidence": "",
        })
    elif word_count > 350:
        flags.append({
            "severity": "warn",
            "code": "TOO_LONG",
            "message": f"Body is {word_count} words; engagement drops sharply >350",
            "evidence": "",
        })

    # Rule 4: Hashtag count (LinkedIn recommends 3-5; >5 looks spammy)
    hashtags = re.findall(r"#\w+", text)
    if len(hashtags) > 5:
        flags.append({
            "severity": "warn",
            "code": "TOO_MANY_HASHTAGS",
            "message": f"{len(hashtags)} hashtags; LinkedIn de-ranks posts with >5",
            "evidence": " ".join(hashtags),
        })

    # Rule 5: Hard CTAs (signup, demo, free trial click) underperform on cold passive scroll.
    # Soft CTAs (link in comments) outperform.
    hard_cta_patterns = [
        (r"\b(?:click|tap)\s+here\b", "hard_cta_click_here"),
        (r"\b(?:try)\b.*\b(?:free|today)\b.*(?:link|→)", "hard_cta_try_free_link"),
        (r"book a (?:demo|call)", "hard_cta_book_demo"),
        (r"sign up (?:now|today)", "hard_cta_signup_now"),
    ]
    for pattern, code in hard_cta_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({
                "severity": "info",
                "code": code.upper(),
                "message": (
                    "Hard CTA detected; for passive_scroll audiences, soft CTAs "
                    "('link in comments') typically have higher click-through"
                ),
                "evidence": pattern,
            })
            break  # Only flag once

    # Rule 6: Whitespace density — needs line breaks for scannability
    avg_line_len = sum(len(line) for line in text.splitlines()) / max(len(text.splitlines()), 1)
    if avg_line_len > 100:
        flags.append({
            "severity": "warn",
            "code": "WALL_OF_TEXT",
            "message": f"Average line length {avg_line_len:.0f} chars; break into shorter lines",
            "evidence": "",
        })

    return flags


CHANNEL_CHECKERS = {
    "linkedin_organic_post": check_linkedin_organic_post,
}


def evaluate_channel_fit(creative: Creative) -> List[Dict[str, str]]:
    """Dispatch to the right checker for this creative's channel."""
    checker = CHANNEL_CHECKERS.get(creative.channel)
    if checker is None:
        return [{
            "severity": "info",
            "code": "NO_CHECKER",
            "message": f"No channel-fit checker registered for channel '{creative.channel}'",
            "evidence": "",
        }]
    return checker(creative)
