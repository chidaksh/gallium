"""Creative variants for the Relay LinkedIn campaign.

Each creative is decomposed into labeled elements so the LLM evaluates them
individually — element-level attribution is the core analytical output.

Three variants, each designed to activate a different primary decision_driver:
  Variant A: ROI-led, analytical — activates roi_focused (Alex)
  Variant B: Story-driven, tension-first — activates pain_driven (Taylor) + identity_driven (Sam)
  Variant C: Social proof-led, peer-validation — activates trust_focused (Jordan)

This creates segment-dependent winners: the pipeline doesn't just pick a
global winner, it shows which variant wins for which audience segment.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Element:
    id: str
    text: str
    element_type: str         # hook | scenario | feature_list | claim | mechanism | social_proof | cta | hashtags | intro
    semantic_properties: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Creative:
    id: str
    name: str
    channel: str
    full_text: str
    elements: List[Element]


CREATIVE_A = Creative(
    id="A",
    name="Variant A — ROI-led, analytical",
    channel="linkedin_organic_post",
    full_text=(
        "3 recurring syncs. 30 minutes each. 8 people on every call.\n\n"
        "That's 12 hours of engineering time. Every week. Before anyone opens an IDE.\n\n"
        "We tracked it across our 40-person eng org last quarter: 720 hours spent in "
        "syncs that could have been async. Not just the meetings — the scheduling, "
        "the context-switching, the \"let me share my screen\" dance, the Slack thread "
        "afterward because nobody wrote down the decision.\n\n"
        "We replaced them with Relay:\n"
        "→ A 2-min video walkthrough instead of a 30-min sync — same decision, no calendar hold\n"
        "→ Timezone-proof: Tokyo watches at 9am, Denver watches at 9am\n"
        "→ Threaded replies in video, voice, or text — decisions stay next to the content, "
        "not lost in Slack\n"
        "→ Searchable transcript with every decision indexed — \"what did we decide about X?\" "
        "has an answer\n\n"
        "6 weeks in, we measured: 9 hours/week reclaimed. Not projected — tracked.\n\n"
        "Try it free for 14 days — long enough to run your own before/after → [link]\n\n"
        "#engineeringops #remotework #asyncfirst"
    ),
    elements=[
        Element(
            id="A_E1_hook",
            text=(
                "3 recurring syncs. 30 minutes each. 8 people on every call.\n\n"
                "That's 12 hours of engineering time. Every week. Before anyone opens an IDE."
            ),
            element_type="hook",
            semantic_properties={
                "tone": "analytical",
                "voice": "declarative — forces reader to verify the math",
                "evidence_type": "quantified_pain",
                "specificity": "high (exact arithmetic, verifiable)",
                "pattern_interrupt": "cognitive — involuntary calculation",
            },
        ),
        Element(
            id="A_E2_evidence",
            text=(
                "We tracked it across our 40-person eng org last quarter: 720 hours spent in "
                "syncs that could have been async. Not just the meetings — the scheduling, "
                "the context-switching, the \"let me share my screen\" dance, the Slack thread "
                "afterward because nobody wrote down the decision."
            ),
            element_type="quantified_pain",
            semantic_properties={
                "tone": "first-party data",
                "evidence_type": "measured_observation",
                "specificity": "high (40-person org, 720 hours, named waste categories)",
                "authenticity_signals": "\"let me share my screen\" and lost Slack decisions are details only someone who lived it would write",
            },
        ),
        Element(
            id="A_E3_outcomes",
            text=(
                "We replaced them with Relay:\n"
                "→ A 2-min video walkthrough instead of a 30-min sync — same decision, no calendar hold\n"
                "→ Timezone-proof: Tokyo watches at 9am, Denver watches at 9am\n"
                "→ Threaded replies in video, voice, or text — decisions stay next to the content, "
                "not lost in Slack\n"
                "→ Searchable transcript with every decision indexed — \"what did we decide about X?\" "
                "has an answer"
            ),
            element_type="outcome_list",
            semantic_properties={
                "tone": "outcome-driven (each bullet is a before/after, not a feature name)",
                "evidence_type": "outcome_claims",
                "specificity": "high (time delta per bullet, named pain per bullet)",
            },
        ),
        Element(
            id="A_E4_proof",
            text="6 weeks in, we measured: 9 hours/week reclaimed. Not projected — tracked.",
            element_type="proof_claim",
            semantic_properties={
                "tone": "anti-skeptic (\"not projected — tracked\")",
                "evidence_type": "first_party_measurement",
                "specificity": "high (6 weeks, 9 hours, methodology framing)",
                "skeptic_risk": "medium — first-party, no third-party verification",
            },
        ),
        Element(
            id="A_E5_cta",
            text="Try it free for 14 days — long enough to run your own before/after → [link]",
            element_type="cta",
            semantic_properties={
                "friction_level": "high (requires signup)",
                "framing": "experiment — appeals to analytical readers",
                "specificity": "explicit (14 days, implies measurable outcome)",
            },
        ),
        Element(
            id="A_E6_hashtags",
            text="#engineeringops #remotework #asyncfirst",
            element_type="hashtags",
            semantic_properties={
                "count": "3",
                "discoverability": "niche + broad mix (engineeringops is targeted, remotework is broad)",
            },
        ),
    ],
)


CREATIVE_B = Creative(
    id="B",
    name="Variant B — Story-driven, tension-first",
    channel="linkedin_organic_post",
    full_text=(
        "Our last \"quick sync\" took 47 minutes.\n\n"
        "It started as: \"Can we hop on for 5?\"\n\n"
        "Then 3 people joined who didn't need to be there.\n"
        "Then someone needed context from a doc nobody could find.\n"
        "Then we rescheduled the actual decision for next week.\n\n"
        "We built Relay because that meeting should have been a 90-second video "
        "— we'd have saved 46 minutes and made the decision the same day.\n\n"
        "Send it when you're ready. Watch it when you can. Decide asynchronously.\n\n"
        "14,000 teams including Linear, Vercel, and Lattice run async-first on Relay. "
        "In self-reported usage data, most have cut sync meetings by 60%.\n\n"
        "Link to try it free in comments."
    ),
    elements=[
        Element(
            id="B_E1_hook",
            text="Our last \"quick sync\" took 47 minutes.",
            element_type="hook",
            semantic_properties={
                "tone": "confessional",
                "evidence_type": "specific_anecdote",
                "specificity": "high (47 minutes — precise enough to be believed)",
                "pattern_interrupt": "emotional — names a universal frustration with a specific number",
            },
        ),
        Element(
            id="B_E2_scenario",
            text=(
                "It started as: \"Can we hop on for 5?\"\n\n"
                "Then 3 people joined who didn't need to be there.\n"
                "Then someone needed context from a doc nobody could find.\n"
                "Then we rescheduled the actual decision for next week."
            ),
            element_type="scenario",
            semantic_properties={
                "tone": "narrative escalation — each line adds one more way the decision got deferred",
                "evidence_type": "lived_experience",
                "relatability": "high (every line is a recognizable micro-frustration)",
                "structure": "decision-deferral arc: ask → bloat → missing context → postpone",
            },
        ),
        Element(
            id="B_E3_pivot",
            text=(
                "We built Relay because that meeting should have been a 90-second video "
                "— we'd have saved 46 minutes and made the decision the same day."
            ),
            element_type="pivot",
            semantic_properties={
                "tone": "founder voice with embedded ROI",
                "evidence_type": "product_origin_story + implicit ROI",
                "specificity": "high (90-second video, 46 minutes saved, same-day decision)",
                "dual_signal": "pain_driven personas hear the origin story; roi_focused personas hear the math",
            },
        ),
        Element(
            id="B_E4_mechanism",
            text="Send it when you're ready. Watch it when you can. Decide asynchronously.",
            element_type="mechanism",
            semantic_properties={
                "tone": "rhythmic triplet — three short imperatives",
                "evidence_type": "workflow_description",
                "specificity": "medium (describes the flow, not the features)",
                "identity_signal": "frames async as a philosophy, not just a feature",
            },
        ),
        Element(
            id="B_E5_social_proof",
            text=(
                "14,000 teams including Linear, Vercel, and Lattice run async-first on Relay. "
                "In self-reported usage data, most have cut sync meetings by 60%."
            ),
            element_type="social_proof",
            semantic_properties={
                "tone": "aggregate stat + named peers + methodology nod",
                "evidence_type": "attributed_aggregate_with_methodology",
                "specificity": "high (14K teams, 3 named companies, 60% reduction)",
                "skeptic_risk": "medium — named companies and methodology framing reduce risk vs. unsourced",
            },
        ),
        Element(
            id="B_E6_cta",
            text="Link to try it free in comments.",
            element_type="cta",
            semantic_properties={
                "friction_level": "low (no immediate signup, soft CTA)",
                "specificity": "low",
                "attention_mode_fit": "optimal for passive_scroll — zero activation energy",
            },
        ),
    ],
)


CREATIVE_C = Creative(
    id="C",
    name="Variant C — Social proof-led, peer-validation",
    channel="linkedin_organic_post",
    full_text=(
        "Linear, Vercel, Lattice — all made the same change last year.\n\n"
        "They stopped defaulting to synchronous meetings.\n\n"
        "Not \"banned meetings.\" Not \"replaced them with email.\" They made async video "
        "the default for anything that doesn't require real-time debate.\n\n"
        "The pattern is the same everywhere: a 90-second video replaces a 30-minute sync. "
        "The sender records when the thinking is fresh. The team responds when they have "
        "context, not when the calendar says so. Decisions happen faster because they're made "
        "when people are ready, not when people are available.\n\n"
        "I tried it with my own team using Relay — the tool all three use. We went from "
        "11 recurring syncs/week to 4. The ones we kept are the ones that genuinely need "
        "real-time presence. The rest were just habit wearing a calendar invite.\n\n"
        "The question isn't \"should we have fewer meetings?\" Everyone agrees on that. "
        "The question is \"what replaces them?\" Async video with threaded decisions is "
        "the most concrete answer I've seen.\n\n"
        "Link in comments if you want to try it.\n\n"
        "#futureofwork #asyncfirst #engineeringleadership"
    ),
    elements=[
        Element(
            id="C_E1_hook",
            text=(
                "Linear, Vercel, Lattice — all made the same change last year."
            ),
            element_type="hook",
            semantic_properties={
                "tone": "insider observation — named peers signal author is in the same league",
                "evidence_type": "peer_signal",
                "specificity": "high (3 named companies, specific timeframe)",
                "pattern_interrupt": "curiosity gap — what change? reader must continue to find out",
                "trust_signal": "naming Linear/Vercel/Lattice upfront implies peer familiarity without claiming it",
            },
        ),
        Element(
            id="C_E2_reveal",
            text=(
                "They stopped defaulting to synchronous meetings.\n\n"
                "Not \"banned meetings.\" Not \"replaced them with email.\" They made async video "
                "the default for anything that doesn't require real-time debate."
            ),
            element_type="reveal",
            semantic_properties={
                "tone": "nuanced — immediately addresses the two most common misreadings",
                "evidence_type": "observed_pattern",
                "specificity": "medium (names the change, preempts objections)",
                "objection_handling": "\"not banned\" and \"not email\" neutralize the two reflexive dismissals",
            },
        ),
        Element(
            id="C_E3_pattern",
            text=(
                "The pattern is the same everywhere: a 90-second video replaces a 30-minute sync. "
                "The sender records when the thinking is fresh. The team responds when they have "
                "context, not when the calendar says so. Decisions happen faster because they're made "
                "when people are ready, not when people are available."
            ),
            element_type="mechanism",
            semantic_properties={
                "tone": "analytical observation — describes the workflow without naming the product",
                "evidence_type": "workflow_description",
                "specificity": "high (90-second vs 30-minute, named workflow steps)",
                "product_mention": "none — builds credibility by explaining the pattern before the pitch",
            },
        ),
        Element(
            id="C_E4_testimony",
            text=(
                "I tried it with my own team using Relay — the tool all three use. We went from "
                "11 recurring syncs/week to 4. The ones we kept are the ones that genuinely need "
                "real-time presence. The rest were just habit wearing a calendar invite."
            ),
            element_type="testimony",
            semantic_properties={
                "tone": "first-person proof with specific numbers",
                "evidence_type": "first_party_testimony",
                "specificity": "high (11 to 4 syncs, names the product for the first time here)",
                "authenticity_signals": "\"habit wearing a calendar invite\" is a detail only someone who lived it would write",
                "roi_signal": "implicit — 11 to 4 is a 64% reduction the reader can compute",
            },
        ),
        Element(
            id="C_E5_reframe",
            text=(
                "The question isn't \"should we have fewer meetings?\" Everyone agrees on that. "
                "The question is \"what replaces them?\" Async video with threaded decisions is "
                "the most concrete answer I've seen."
            ),
            element_type="reframe",
            semantic_properties={
                "tone": "intellectual move — reframes the problem space",
                "evidence_type": "opinion_with_reasoning",
                "identity_signal": "high — positions reader as someone asking the harder question",
                "product_mention": "indirect (\"async video with threaded decisions\" describes Relay without naming it)",
            },
        ),
        Element(
            id="C_E6_cta",
            text="Link in comments if you want to try it.",
            element_type="cta",
            semantic_properties={
                "friction_level": "low (soft CTA, conditional phrasing)",
                "specificity": "low",
                "attention_mode_fit": "optimal for warm_network — matches the trust-based frame",
            },
        ),
        Element(
            id="C_E7_hashtags",
            text="#futureofwork #asyncfirst #engineeringleadership",
            element_type="hashtags",
            semantic_properties={
                "count": "3",
                "discoverability": "thought-leader mix (futureofwork is broad, engineeringleadership is niche)",
            },
        ),
    ],
)


CREATIVES = {"A": CREATIVE_A, "B": CREATIVE_B, "C": CREATIVE_C}


def render_creative_for_prompt(
    creative: Creative,
    shuffle_seed: Optional[int] = None,
    return_order: bool = False,
) -> str | tuple[str, List[str]]:
    """Render a creative as a labeled element block for the user prompt.

    `full_text` is always shown in the natural reading order so the persona sees
    the creative as a real reader would. The element decomposition list, however,
    is order-permuted when `shuffle_seed` is provided — this defends against the
    LLM anchoring on the first listed element when emitting reactions. Element
    attribution downstream is keyed by element_id, so it is robust to order.

    If `return_order` is True, returns (text, element_id_order) for position
    bias verification downstream.
    """
    elements = list(creative.elements)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(elements)
    lines = [
        f"# CREATIVE TO EVALUATE: {creative.name}",
        f"**Channel:** {creative.channel}",
        f"**Variant ID:** {creative.id}",
        "",
        "## Full creative as it appears to the reader:",
        "```",
        creative.full_text,
        "```",
        "",
        "## Element decomposition (use these IDs in your element_reactions; order below is randomized):",
    ]
    for el in elements:
        lines.append(f"\n### {el.id}  ({el.element_type})")
        lines.append(f"```\n{el.text}\n```")
    text = "\n".join(lines)
    if return_order:
        return text, [el.id for el in elements]
    return text
