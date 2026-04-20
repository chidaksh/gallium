"""Demo personas for the Relay LinkedIn campaign.

Each persona is a (dimension → level) assignment plus one-line demographics.
The portfolio weights model a realistic distribution of who actually sees
Relay's LinkedIn content (used for the weighted winner rollup).
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Persona:
    id: str
    label: str
    demographics: str
    dimensions: Dict[str, str] = field(default_factory=dict)


PERSONAS = {
    "alex_vp_eng": Persona(
        id="alex_vp_eng",
        label="Alex — VP Engineering, Series B startup",
        demographics=(
            "34, VP Engineering at a 200-person Series B startup, team across 3 timezones, "
            "manages 8 recurring syncs/week."
        ),
        dimensions={
            "buying_stage": "consideration",
            "skepticism_level": "high",
            "decision_driver": "roi_focused",
            "pain_awareness": "acute",
            "attention_mode": "passive_scroll",
        },
    ),
    "jordan_head_remote": Persona(
        id="jordan_head_remote",
        label="Jordan — Head of Remote, scale-up",
        demographics=(
            "41, formal Head of Remote role at a 500-person scale-up, evaluating 3 tools this "
            "quarter, has budget approval, needs exec buy-in."
        ),
        dimensions={
            "buying_stage": "decision",
            "skepticism_level": "medium",
            "decision_driver": "trust_focused",
            "pain_awareness": "acute",
            "attention_mode": "active_research",
        },
    ),
    "sam_founder": Persona(
        id="sam_founder",
        label="Sam — Founder/CEO, early-stage",
        demographics=(
            "28, founder/CEO of a 30-person early-stage startup, 18 months post-launch, fully "
            "remote from day one, thinks of themselves as building differently."
        ),
        dimensions={
            "buying_stage": "awareness",
            "skepticism_level": "low",
            "decision_driver": "identity_driven",
            "pain_awareness": "latent",
            "attention_mode": "passive_scroll",
        },
    ),
    "taylor_ic_eng": Persona(
        id="taylor_ic_eng",
        label="Taylor — Senior Engineer IC, tool-adoption influencer",
        demographics=(
            "29, senior IC engineer with no budget authority but strong influence over tool "
            "adoption, grumbles about meetings but sees them as an unavoidable part of the job."
        ),
        dimensions={
            "buying_stage": "consideration",
            "skepticism_level": "high",
            "decision_driver": "pain_driven",
            "pain_awareness": "latent",
            "attention_mode": "warm_network",
        },
    ),
}


# Realistic distribution of who sees Relay's LinkedIn content.
# Weights sum to 1.0 — used for the weighted portfolio rollup.
PORTFOLIO_WEIGHTS = {
    "alex_vp_eng":        0.30,  # Primary buyer
    "jordan_head_remote": 0.25,  # Champion buyer
    "sam_founder":        0.20,  # SMB segment
    "taylor_ic_eng":      0.25,  # Influencer/advocate
}

assert abs(sum(PORTFOLIO_WEIGHTS.values()) - 1.0) < 1e-9, "Portfolio weights must sum to 1.0"
assert set(PORTFOLIO_WEIGHTS) == set(PERSONAS), "Weight keys must match persona keys"


def render_persona_for_prompt(persona: Persona) -> str:
    """Render one persona's assignment as a stable text block for the user prompt."""
    dim_lines = [f"- {dim}: **{level}**" for dim, level in persona.dimensions.items()]
    return (
        f"# YOUR ASSIGNED PROFILE: {persona.label}\n"
        f"\n"
        f"**Demographics:** {persona.demographics}\n"
        f"\n"
        f"**Behavioral dimensions:**\n"
        + "\n".join(dim_lines)
    )
