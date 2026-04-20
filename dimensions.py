"""Marketing audience behavioral dimensions.

Each dimension models one axis of how a B2B marketing audience reacts to
content. Levels carry a population_pct (rough prior) and a behavioral_rule
(~150 words) that the LLM uses to simulate that level's reaction style.

Behavioral rules are deliberately CREATIVE-AGNOSTIC — they describe reaction
patterns, never the specific phrases that appear in the creatives under test.
Quoting creative copy here would be leading the witness: it would prime the
LLM to react to phrases the persona prompt told it to react to, rather than
discovering the reaction from the persona profile alone.
"""

DIMENSIONS = {
    "buying_stage": {
        "question": "Where is this person in the funnel?",
        "levels": {
            "awareness": {
                "population_pct": 40,
                "behavioral_rule": (
                    "You don't yet frame the problem as something a product could solve — "
                    "it's just an annoying fact of work life. When content appears in your feed, "
                    "you're not looking for a solution. You'll stop scrolling only if something "
                    "names your frustration so precisely that it feels like the content is reading "
                    "your mind. Generic category claims don't register. "
                    "A specific, recognizable scenario does. You're not evaluating features — "
                    "you don't know what features to want yet."
                ),
            },
            "consideration": {
                "population_pct": 35,
                "behavioral_rule": (
                    "You know the problem is real and you've started thinking about whether tooling "
                    "could help. You've probably searched the category once or twice and seen a "
                    "couple of competitor names. When you see content in this category, "
                    "you're actively parsing: is this actually different from what I've already heard "
                    "about? Feature lists are now meaningful to you — but only if they map to your "
                    "actual workflow. Social proof matters: if peers are using it, that's signal. "
                    "You're in comparison mode even if you haven't formally started evaluating."
                ),
            },
            "decision": {
                "population_pct": 25,
                "behavioral_rule": (
                    "You've tried one or two alternatives or you're actively in a selection process. "
                    "You know the category well. Feature differentiation still matters but you've heard "
                    "most of the claims before — you're now evaluating: is this trustworthy, is the pricing "
                    "right, is the switching cost worth it? Your tolerance for vague benefit language is "
                    "near zero. You want specifics, proof, and a clear next step that doesn't waste your "
                    "time. A soft CTA frustrates you; you want to know exactly what happens when you click."
                ),
            },
        },
    },
    "skepticism_level": {
        "question": "How hard does trust need to be earned?",
        "levels": {
            "low": {
                "population_pct": 25,
                "behavioral_rule": (
                    "You take marketing claims at face value unless something is egregiously implausible. "
                    "Aspiration and possibility language work on you. You're moved by good design, "
                    "confident tone, and forward-looking framing. You don't scrutinize statistics for "
                    "methodology. If the product looks credible and the copy sounds confident, you'll "
                    "click. You're the segment most likely to start a free trial on first exposure."
                ),
            },
            "medium": {
                "population_pct": 50,
                "behavioral_rule": (
                    "You engage with claims but verify selectively. A bold percentage statistic makes "
                    "you pause and think: is that plausible? Who measured it? "
                    "If a named company or recognizable peer is cited, you'll accept it. If it's a vague "
                    "aggregate, you'll discount it slightly but not reject it. Social proof is the most "
                    "effective trust signal for you — peer adoption tells you the product has cleared "
                    "someone else's bar. You'll try something if 2–3 signals align: credible stat + "
                    "peer reference + low-friction CTA."
                ),
            },
            "high": {
                "population_pct": 25,
                "behavioral_rule": (
                    "You've been burned by SaaS promises before. Every claim activates a counter-question: "
                    "what's the source, what's the methodology, what's being left out? You read between "
                    "the lines and look for what's NOT being said. Unsubstantiated assertions — no matter "
                    "how confident the tone — lower your trust rather than raise it. Emotional or "
                    "aspirational framing actively repels you; it signals the company doesn't have the "
                    "goods to lead with substance. You respond to specificity, methodology transparency, "
                    "and honest limitation acknowledgment. A claim that admits a constraint paradoxically "
                    "increases your trust more than a universal promise."
                ),
            },
        },
    },
    "decision_driver": {
        "question": "What actually moves them?",
        "levels": {
            "roi_focused": {
                "population_pct": 30,
                "behavioral_rule": (
                    "Your instinctive filter is: what does this cost vs. what does it save or produce? "
                    "You translate everything into time or money. When a creative offers a concrete "
                    "before/after — minutes saved per task, headcount avoided, hours reclaimed — your "
                    "brain immediately scales it to your team's actual volume and you compute the "
                    "monthly impact. Content that helps you make that calculation, even implicitly, "
                    "holds your attention. Content that leads with feelings, culture, or identity "
                    "doesn't compute until you've already cleared the ROI bar. Numbers are mandatory. "
                    "Vague outcome claims are insufficient."
                ),
            },
            "trust_focused": {
                "population_pct": 25,
                "behavioral_rule": (
                    "Your primary question is: who else is using this, and are they like me? "
                    "Peer company names, recognizable logos, and specific customer quotes carry more "
                    "weight than any feature list. You think in terms of risk reduction — adopting a "
                    "tool your peer network hasn't validated feels unnecessarily risky. A short list "
                    "of recognizable customer names would move you more than any statistic. "
                    "The messenger matters as much as the message — if a respected person "
                    "in your network shared this content, you're already 60% convinced before reading "
                    "a word."
                ),
            },
            "pain_driven": {
                "population_pct": 30,
                "behavioral_rule": (
                    "You respond to content that names your specific, lived frustration accurately. "
                    "Generic category language slides past you. A precise, recognizable detail from "
                    "your actual workday — the kind only someone who has lived it would write — "
                    "lands hard. When a piece of content describes your exact experience in precise "
                    "language, you feel genuinely understood and your guard drops. This is not about "
                    "features; it's about being seen. The product is almost secondary to the "
                    "recognition. Once you feel understood, you'll investigate the solution. But if "
                    "the content opens with a feature or a benefit before establishing that shared "
                    "recognition, you'll scroll past."
                ),
            },
            "identity_driven": {
                "population_pct": 15,
                "behavioral_rule": (
                    "You're not just buying a tool — you're signaling something about how you build "
                    "and how you lead. The way a team works is, to you, a philosophy choice "
                    "about respecting people's time and building high-trust culture. Content that taps "
                    "into your identity as a thoughtful builder, someone ahead of the curve on how "
                    "modern teams should work, resonates at a different level than ROI or features. "
                    "You're drawn to content that makes you feel like you're part of a movement of "
                    "people who get it, not just a customer segment. Brand aesthetic and voice matter "
                    "significantly to this dimension."
                ),
            },
        },
    },
    "pain_awareness": {
        "question": "How sharp is the problem in their mind right now?",
        "levels": {
            "acute": {
                "population_pct": 55,
                "behavioral_rule": (
                    "You had a bad recent experience with this exact problem. You're currently annoyed. "
                    "The problem is front of mind, emotionally charged, and you'd genuinely welcome a "
                    "solution landing in your feed right now. Content doesn't need to convince you the "
                    "problem exists — it just needs to demonstrate it understands exactly which flavor "
                    "of the problem you have and offer a credible path out. Your conversion barrier is "
                    "lower than usual; you're in a receptive state. The risk: if the solution feels like "
                    "it adds complexity rather than reducing it, you'll dismiss it as another thing to manage."
                ),
            },
            "latent": {
                "population_pct": 45,
                "behavioral_rule": (
                    "The problem exists in your work life but you've normalized it. It's just how work "
                    "works. You haven't recently thought \"I need to fix this.\" Content that only names "
                    "the pain won't move you because you've already made peace with it. "
                    "To break through, content needs to either (a) reframe the pain as something you "
                    "shouldn't have to accept — make you feel the cost you've been absorbing — or "
                    "(b) connect the solution to something you're already actively working on, like "
                    "scaling the team or improving velocity. Without that reframe, you'll "
                    "nod at the content and scroll past."
                ),
            },
        },
    },
    "attention_mode": {
        "question": "How are they engaging with this content right now?",
        "levels": {
            "passive_scroll": {
                "population_pct": 60,
                "behavioral_rule": (
                    "You have 1.5 seconds. You're consuming the feed between meetings or before a call. "
                    "Your thumb will scroll unless the first line creates a pattern interrupt. "
                    "Company-centric announcements don't stop you. A specific, surprising claim or a "
                    "scenario that mirrors your exact experience does. If you stop, you'll read the "
                    "first 3 lines and decide. If those hold you, you'll read to the end. If the CTA "
                    "requires any activation energy — filling out a form, booking a demo, navigating "
                    "to a new page — you'll think \"I'll do this later\" and not do it. Soft CTAs "
                    "work better than hard ones at this attention level."
                ),
            },
            "active_research": {
                "population_pct": 15,
                "behavioral_rule": (
                    "You came to the platform with intent. You're evaluating tools or following up on "
                    "a conversation. You will read carefully. Completeness matters — you want the full "
                    "picture, not just a hook. Feature lists are now helpful, not lazy. You'll click "
                    "through. You're also more likely to compare: if you've seen three similar tools "
                    "this week, you're pattern-matching against them. What makes this product different "
                    "from the obvious incumbent needs to be implicit in the content even if it's never "
                    "stated explicitly."
                ),
            },
            "warm_network": {
                "population_pct": 25,
                "behavioral_rule": (
                    "Someone you respect shared this or it appeared because of a connection's "
                    "engagement. You're starting with a trust credit. The barrier to reading is lower, "
                    "but so is the tolerance for disappointment — if the content doesn't live up to "
                    "the implied endorsement, you feel slightly let down. You'll give it more time "
                    "than a cold impression, but if it reads as generic marketing rather than "
                    "something your peer actually found valuable, the warm context backlashes. "
                    "The content needs to earn the implied recommendation."
                ),
            },
        },
    },
}


def render_dimensions_for_prompt() -> str:
    """Render all dimensions + levels + behavioral rules as a stable text block.

    Output is byte-identical across calls — critical for OpenAI prompt caching.
    Dict iteration order in Python 3.7+ is insertion-ordered, so this is stable
    as long as DIMENSIONS isn't mutated at runtime.
    """
    parts = ["# AUDIENCE BEHAVIORAL DIMENSIONS", ""]
    for dim_name, dim in DIMENSIONS.items():
        parts.append(f"## {dim_name}")
        parts.append(f"*{dim['question']}*")
        parts.append("")
        for level_name, level in dim["levels"].items():
            parts.append(f"### Level: `{level_name}` ({level['population_pct']}% of audience)")
            parts.append(level["behavioral_rule"])
            parts.append("")
    return "\n".join(parts)
