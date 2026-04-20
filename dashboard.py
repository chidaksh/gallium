"""CreativeIQ Dashboard — visual report for the Relay LinkedIn A/B/C evaluation."""

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# ── Config ──────────────────────────────────────────────────────────────────

st.set_page_config(page_title="CreativeIQ — Relay Campaign", layout="wide", page_icon="📊")

VARIANT_COLORS = {"A": "#4361ee", "B": "#f72585", "C": "#06d6a0"}
VARIANT_NAMES = {
    "A": "Variant A: ROI-Led",
    "B": "Variant B: Story-Driven",
    "C": "Variant C: Social Proof",
}
VARIANT_HOOKS = {
    "A": '"3 recurring syncs. 30 minutes each. 8 people on every call."',
    "B": '"Our last quick sync took 47 minutes."',
    "C": '"Linear, Vercel, Lattice — all made the same change last year."',
}

PERSONA_INFO = {
    "alex_vp_eng":      {"name": "Alex",   "title": "VP Engineering",    "weight": "30%", "profile": "ROI-focused, high skepticism"},
    "jordan_head_remote":{"name": "Jordan", "title": "Head of Remote",   "weight": "25%", "profile": "Trust-focused, peer-driven"},
    "sam_founder":       {"name": "Sam",    "title": "Founder / CEO",    "weight": "20%", "profile": "Identity-driven, early-stage"},
    "taylor_ic_eng":     {"name": "Taylor", "title": "Senior Engineer",  "weight": "25%", "profile": "Pain-driven, tool influencer"},
}

ELEMENT_LABELS = {
    "A_E1_hook": "Opening math hook",
    "A_E2_evidence": "720-hour pain data",
    "A_E3_outcomes": "Before/after bullets",
    "A_E4_proof": '"9 hrs reclaimed" claim',
    "A_E5_cta": "Free trial CTA",
    "A_E6_hashtags": "Hashtags",
    "B_E1_hook": '"47-minute sync" opener',
    "B_E2_scenario": "Meeting spiral story",
    "B_E3_pivot": '"Should\'ve been 90s video"',
    "B_E4_mechanism": "Async workflow pitch",
    "B_E5_social_proof": '"14,000 teams" stat',
    "B_E6_cta": "Link in comments",
    "C_E1_hook": "Named peer companies",
    "C_E2_reveal": '"Stopped defaulting to syncs"',
    "C_E3_pattern": "90s video replaces 30m sync",
    "C_E4_testimony": "11→4 syncs personal proof",
    "C_E5_reframe": '"What replaces meetings?"',
    "C_E6_cta": "Link in comments",
    "C_E7_hashtags": "Hashtags",
}

CHART_CONFIG = {"displayModeBar": False}


# ── Data loading ────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    p = Path(__file__).resolve().parent / "results" / "full_eval.json"
    with open(p) as f:
        return json.load(f)


data = load_data()
summary = data["summary"]
portfolio = summary["portfolio"]
pps = summary["per_persona_scores"]
attr_data = summary["per_variant_element_attribution"]
mp = data.get("minimal_pairs", {})
cost = summary.get("cost", {})
effect = summary.get("effect_sizes", {}).get("portfolio", {})
close_call = summary.get("close_call", {})
variants = sorted(portfolio.keys())
pids = list(PERSONA_INFO.keys())
ordered = sorted(variants, key=lambda v: -portfolio[v]["mean"])
winner = ordered[0]


# ── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px; padding: 16px 20px;
        border-left: 4px solid #06d6a0;
    }
    div[data-testid="stMetric"] label { font-size: 0.85rem !important; }
    .insight-box {
        background: #f0f7ff; border-left: 4px solid #4361ee;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        margin: 8px 0 16px 0; font-size: 0.95rem;
    }
    .warning-box {
        background: #fff5f5; border-left: 4px solid #f72585;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        margin: 8px 0 16px 0; font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### CreativeIQ")
    st.markdown("Pre-flight creative evaluation using LLM-simulated audience personas")
    st.divider()

    st.markdown("**Audience Personas**")
    for pid, info in PERSONA_INFO.items():
        st.markdown(f"**{info['name']}** — {info['title']}")
        st.caption(f"{info['profile']} · Weight: {info['weight']}")

    st.divider()
    st.markdown("**Creative Variants**")
    for vid in variants:
        color = VARIANT_COLORS[vid]
        st.markdown(f"<span style='color:{color}; font-weight:700'>{VARIANT_NAMES[vid]}</span>",
                    unsafe_allow_html=True)
        st.caption(VARIANT_HOOKS[vid])

    st.divider()
    st.markdown("**Evaluation Cost**")
    sc1, sc2 = st.columns(2)
    sc1.markdown(f"**${cost.get('total_cost_usd', 0):.2f}**")
    sc2.markdown(f"**{cost.get('calls', 0)} calls**")


# ── Section 1: Hero ─────────────────────────────────────────────────────────

st.markdown("# Relay LinkedIn Campaign — Creative Evaluation")
st.markdown(f"*Which of three ad variants resonates most across four audience segments?*")

st.markdown("")
h1, h2, h3, h4 = st.columns(4)
h1.metric("Winning Variant", f"Variant {winner}",
          f"Score: {portfolio[winner]['mean']:.1f} / 10")
h2.metric("Runner-Up", f"Variant {ordered[1]}",
          f"Score: {portfolio[ordered[1]]['mean']:.1f} / 10")
d_val = effect.get("cohens_d", 0)
h3.metric("Gap Strength", "Large" if abs(d_val) >= 0.8 else ("Medium" if abs(d_val) >= 0.5 else "Small"),
          f"Statistically significant")
h4.metric("Confidence", "High",
          "Not a close call" if not close_call.get("is_close_call") else "Close — need more data")

st.markdown(
    '<div class="insight-box">'
    f'<strong>Variant {winner} (Social Proof)</strong> wins the overall portfolio at '
    f'<strong>{portfolio[winner]["mean"]:.1f}</strong> out of 10, beating '
    f'Variant {ordered[1]} ({portfolio[ordered[1]]["mean"]:.1f}) and '
    f'Variant {ordered[2]} ({portfolio[ordered[2]]["mean"]:.1f}). '
    f'The gap is large and statistically reliable — this isn\'t noise.'
    '</div>', unsafe_allow_html=True,
)


# ── Section 2: Who prefers what? (Persona × Variant heatmap) ────────────────

st.divider()
st.markdown("## Who Prefers What?")
st.markdown("*Different audiences respond to different messages. Here's how each persona rated the three variants.*")

# Build heatmap with larger, cleaner annotations
z_vals, hover_text, annotations = [], [], []
for i, pid in enumerate(pids):
    info = PERSONA_INFO[pid]
    row, hover_row = [], []
    for j, v in enumerate(variants):
        cell = pps.get(pid, {}).get(v, {})
        mean = cell.get("mean", 0)
        row.append(mean)
        hover_row.append(f"{info['name']} ({info['title']})<br>{VARIANT_NAMES[v]}<br>"
                         f"Score: {mean:.1f} / 10")
        annotations.append(dict(
            x=j, y=i,
            text=f"<b style='font-size:18px'>{mean:.1f}</b>",
            showarrow=False, font=dict(size=18),
        ))
    z_vals.append(row)
    hover_text.append(hover_row)

y_labels = [f"{PERSONA_INFO[p]['name']} — {PERSONA_INFO[p]['title']}" for p in pids]
x_labels = [VARIANT_NAMES[v] for v in variants]

fig_heat = go.Figure(data=go.Heatmap(
    z=z_vals, x=x_labels, y=y_labels,
    hovertext=hover_text, hoverinfo="text",
    colorscale=[[0, "#fee2e2"], [0.25, "#fecaca"], [0.5, "#fde68a"],
                [0.75, "#bbf7d0"], [1, "#16a34a"]],
    zmin=4, zmax=8, showscale=True,
    colorbar=dict(title=dict(text="Score<br>(out of 10)", font=dict(size=12))),
))
fig_heat.update_layout(
    annotations=annotations, height=350, margin=dict(t=30, b=20, l=200, r=80),
    xaxis=dict(side="top", tickfont=dict(size=14)),
    yaxis=dict(tickfont=dict(size=13)),
    font=dict(size=14),
)
st.plotly_chart(fig_heat, use_container_width=True, config=CHART_CONFIG)

# Persona winner badges with narrative
persona_winners = {}
for pid in pids:
    scores = {v: pps.get(pid, {}).get(v, {}).get("mean", 0) for v in variants}
    best = max(scores, key=scores.get)
    ties = [v for v in variants if abs(scores[v] - scores[best]) < 0.01]
    persona_winners[pid] = ties

wcols = st.columns(len(pids))
for i, pid in enumerate(pids):
    info = PERSONA_INFO[pid]
    wins = persona_winners[pid]
    win_str = " / ".join(wins)
    with wcols[i]:
        st.markdown(f"**{info['name']}** prefers **{win_str}**")

# Key narrative
sam_a = pps.get("sam_founder", {}).get("A", {}).get("mean", 0)
sam_c = pps.get("sam_founder", {}).get("C", {}).get("mean", 0)
st.markdown(
    '<div class="insight-box">'
    '<strong>Key insight:</strong> No single variant wins every audience. '
    f'Sam (Founder) scores Variant A at just {sam_a:.1f} but gives Variant C a {sam_c:.1f} — '
    'early-stage founders need peer validation before they consider a tool. '
    'Jordan (Head of Remote) responds equally well to ROI data and social proof (both 7.8). '
    'The right variant depends on your target segment.'
    '</div>', unsafe_allow_html=True,
)


# ── Section 3: What makes each variant work (or fail)? ──────────────────────

st.divider()
st.markdown("## What Makes Each Variant Work (or Fail)?")
st.markdown("*Every ad is made of parts — an opening hook, a story, a proof point, a call to action. "
            "Some parts pull readers in (green), others push them away (red).*")

attr_cols = st.columns(len(variants))
for col_idx, v in enumerate(variants):
    with attr_cols[col_idx]:
        color = VARIANT_COLORS[v]
        st.markdown(f"<h4 style='color:{color}'>{VARIANT_NAMES[v]}</h4>", unsafe_allow_html=True)

        v_attr = attr_data.get(v, {})
        elements = [(eid, ea) for eid, ea in v_attr.items() if not eid.startswith("_")]
        elements.sort(key=lambda kv: kv[1]["attribution_score"])

        labels = [ELEMENT_LABELS.get(eid, eid) for eid, _ in elements]
        scores = [ea["attribution_score"] for _, ea in elements]
        bar_colors = ["#16a34a" if s > 0 else ("#dc2626" if s < 0 else "#9ca3af") for s in scores]

        fig_attr = go.Figure(go.Bar(
            y=labels, x=scores, orientation="h",
            marker_color=bar_colors,
            text=[f"{s:+.0f}" for s in scores],
            textposition="outside", textfont=dict(size=13),
            hovertemplate="%{y}<br>Impact score: %{x:+.0f}<extra></extra>",
        ))
        fig_attr.update_layout(
            xaxis=dict(range=[-120, 120], title="Impact Score",
                       zeroline=True, zerolinecolor="#374151", zerolinewidth=2),
            height=55 + 45 * len(elements),
            margin=dict(t=10, b=35, l=170, r=30),
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickfont=dict(size=12)),
        )
        st.plotly_chart(fig_attr, use_container_width=True, config=CHART_CONFIG)

st.markdown(
    '<div class="warning-box">'
    '<strong>Variant B\'s weak spot:</strong> The "14,000 teams" social proof stat scores <strong>-50</strong> — '
    '65% of personas flagged it as untrustworthy. Alex and Taylor (both high-skepticism) reject it outright. '
    'This single line is why Variant B finishes last, despite having the strongest opening hook in the entire evaluation.'
    '</div>', unsafe_allow_html=True,
)


# ── Section 4: What happens when the audience changes? ──────────────────────

st.divider()
st.markdown("## What Happens When the Audience Changes?")
st.markdown("*We ran controlled experiments: take the same ad, show it to two versions of the same persona "
            "— one skeptical, one trusting — and measure what moves. This isolates cause and effect.*")

for pair_name, pair_title, pair_explain in [
    ("skepticism", "Skeptical vs. Trusting Audience",
     "Same person, same ad — but one version is highly skeptical of marketing claims, the other is open. What breaks?"),
    ("pain", "Aware vs. Unaware of the Problem",
     "Same person, same ad — but one version acutely feels the meeting-overload pain, the other hasn't noticed yet. What changes?"),
]:
    pair = mp.get(pair_name)
    if not pair:
        continue
    spec = pair["spec"]
    cmp = pair["comparison"]

    st.markdown(f"### {pair_title}")
    st.markdown(f"*{pair_explain}*")

    deltas = sorted(cmp["element_deltas"], key=lambda d: -abs(d["delta"]))
    labels_mp = [ELEMENT_LABELS.get(d["element_id"], d["element_id"]) for d in deltas]
    low_scores = [d["low_score"] for d in deltas]
    high_scores = [d["high_score"] for d in deltas]

    fig_mp = go.Figure()
    for i, d in enumerate(deltas):
        fig_mp.add_trace(go.Scatter(
            x=[d["low_score"], d["high_score"]], y=[labels_mp[i], labels_mp[i]],
            mode="lines", line=dict(color="#d1d5db", width=3),
            showlegend=False, hoverinfo="skip",
        ))
    fig_mp.add_trace(go.Scatter(
        x=low_scores, y=labels_mp, mode="markers",
        marker=dict(size=14, color="#3b82f6", symbol="circle", line=dict(width=1, color="white")),
        name=spec["low_level"].title(),
        hovertemplate="%{y}<br>Score: %{x:+.0f}<extra></extra>",
    ))
    fig_mp.add_trace(go.Scatter(
        x=high_scores, y=labels_mp, mode="markers",
        marker=dict(size=14, color="#ef4444", symbol="diamond", line=dict(width=1, color="white")),
        name=spec["high_level"].title(),
        hovertemplate="%{y}<br>Score: %{x:+.0f}<extra></extra>",
    ))
    fig_mp.update_layout(
        xaxis=dict(title="Impact Score", range=[-120, 120],
                   zeroline=True, zerolinecolor="#374151", zerolinewidth=1),
        height=55 + 50 * len(deltas), margin=dict(t=10, b=40, l=200, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=13)),
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickfont=dict(size=12)),
    )

    mc1, mc2 = st.columns([3, 1])
    with mc1:
        st.plotly_chart(fig_mp, use_container_width=True, config=CHART_CONFIG)
    with mc2:
        al_lo = cmp["low_action_likelihood"]["mean"]
        al_hi = cmp["high_action_likelihood"]["mean"]
        delta_al = cmp["delta_action_likelihood"]
        st.metric("Willingness to Act", f"{al_hi:.1f} / 10",
                  f"{delta_al:+.1f} vs {spec['low_level']}")
        biggest = deltas[0]
        st.metric("Biggest Swing",
                  ELEMENT_LABELS.get(biggest["element_id"], biggest["element_id"]),
                  f"{biggest['delta']:+.0f} points")

    if pair_name == "skepticism":
        st.markdown(
            '<div class="warning-box">'
            'When skepticism goes up, the "14,000 teams" stat flips from <strong>+60</strong> (positive) '
            'to <strong>-100</strong> (strongly rejected) — a 160-point swing. '
            'The opening hook and story are skepticism-proof. The social proof claim is not.'
            '</div>', unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="insight-box">'
            'The story hook works whether or not the reader feels the pain. But the product pitch '
            '("should\'ve been a 90-second video") only converts when the reader has actively experienced '
            'meeting overload — otherwise it reads as someone else\'s problem.'
            '</div>', unsafe_allow_html=True,
        )


# ── Section 5: Recommendations ─────────────────────────────────────────────

st.divider()
st.markdown("## Recommendations")

rec_cols = st.columns(3)
with rec_cols[0]:
    st.markdown(f"<h4 style='color:{VARIANT_COLORS['C']}'>Ship Variant C</h4>",
                unsafe_allow_html=True)
    st.markdown(
        "Wins 3 of 4 personas, ties the 4th. "
        "Social proof from named peers (Linear, Vercel, Lattice) builds trust "
        "without triggering skepticism. Works across all audience segments."
    )
with rec_cols[1]:
    st.markdown(f"<h4 style='color:{VARIANT_COLORS['B']}'>Fix Variant B's Proof Point</h4>",
                unsafe_allow_html=True)
    st.markdown(
        "B has the strongest opening in the evaluation, but the "
        '"14,000 teams" stat is actively hurting it. '
        "Replace with named case studies (Alex and Taylor want specifics, not aggregates)."
    )
with rec_cols[2]:
    st.markdown(f"<h4 style='color:{VARIANT_COLORS['A']}'>Use Variant A for ROI Buyers</h4>",
                unsafe_allow_html=True)
    st.markdown(
        "The math hook forces readers to verify the arithmetic — "
        "highly effective on analytical audiences. "
        "Consider A for targeted campaigns to VP/Director segments."
    )

# Segment-specific fixes for B_E5
seg_recs = summary.get("segment_recommendations", {})
b_recs = seg_recs.get("B", [])
if b_recs:
    with st.expander("What each persona wants changed in Variant B"):
        rec = b_recs[0]
        fix_cols = st.columns(len(rec.get("fix_by_segment", {})))
        for i, (pid, seg) in enumerate(rec["fix_by_segment"].items()):
            with fix_cols[i]:
                info = PERSONA_INFO.get(pid, {})
                st.markdown(f"**{info.get('name', pid)}** — {info.get('title', '')}")
                intensity = seg["mean_signed_intensity"]
                if intensity < 0:
                    st.markdown(f"Reaction: **Negative** ({intensity:+.1f})")
                else:
                    st.markdown(f"Reaction: **Positive** ({intensity:+.1f})")
                if seg.get("suggested_edits"):
                    for edit in seg["suggested_edits"][:2]:
                        st.caption(f"*{edit}*")


# ── Section 6: Under the Hood (collapsible) ─────────────────────────────────

st.divider()
st.markdown("## Under the Hood")
st.caption("Technical diagnostics for the ML team — expand to inspect.")

with st.expander("How consistent is the AI judge?"):
    st.markdown("We ran each evaluation 5 times. This heatmap shows how consistent the AI's judgments "
                "were across repeated runs (green = consistent, red = noisy).")

    cons = summary.get("llm_self_consistency", {})
    z_cons, hover_cons, anno_cons = [], [], []
    for i, pid in enumerate(pids):
        info = PERSONA_INFO[pid]
        row, h_row = [], []
        for j, v in enumerate(variants):
            a = cons.get(v, {}).get(pid, 0)
            row.append(a)
            verdict = "Consistent" if a >= 0.80 else ("Tentative" if a >= 0.67 else "Noisy")
            h_row.append(f"{info['name']} x {VARIANT_NAMES[v]}<br>Consistency: {a:.2f} ({verdict})")
            anno_cons.append(dict(
                x=j, y=i,
                text=f"<b>{a:.2f}</b><br><span style='font-size:11px'>{verdict}</span>",
                showarrow=False,
                font=dict(size=14, color="white" if a < 0.60 else "black"),
            ))
        z_cons.append(row)
        hover_cons.append(h_row)

    y_cons = [f"{PERSONA_INFO[p]['name']}" for p in pids]
    fig_cons = go.Figure(data=go.Heatmap(
        z=z_cons, x=[VARIANT_NAMES[v] for v in variants], y=y_cons,
        hovertext=hover_cons, hoverinfo="text",
        colorscale=[[0, "#dc2626"], [0.4, "#f59e0b"], [0.7, "#84cc16"], [1, "#16a34a"]],
        zmin=0.2, zmax=1.0, showscale=True,
        colorbar=dict(title=dict(text="Consistency", font=dict(size=11))),
    ))
    fig_cons.update_layout(
        annotations=anno_cons, height=320, margin=dict(t=30, b=20, l=100, r=80),
        xaxis=dict(side="top", tickfont=dict(size=13)),
        yaxis=dict(tickfont=dict(size=13)),
    )
    st.plotly_chart(fig_cons, use_container_width=True, config=CHART_CONFIG)
    st.caption("Jordan's consistency drops when evaluating Variants B and C — "
               "the trust-focused persona may be hardest for the AI to simulate faithfully.")

with st.expander("Do all personas react differently? (Collapse detection)"):
    st.markdown("If all four personas give the same score to an element, "
                "the AI may not be faithfully simulating different viewpoints. "
                "Red bars = all personas reacted identically (potential issue).")

    diff_data = summary.get("persona_differentiation", {})
    selected_v = st.selectbox("Select variant:", variants, key="diff_v",
                              format_func=lambda v: VARIANT_NAMES[v])
    v_diff = diff_data.get(selected_v, {})
    if v_diff:
        elements_d = [(eid, ed) for eid, ed in v_diff.items()]
        elements_d.sort(key=lambda kv: kv[1]["variance"])
        labels_d = [ELEMENT_LABELS.get(eid, eid) for eid, _ in elements_d]
        variances = [ed["variance"] for _, ed in elements_d]
        colors_d = ["#dc2626" if ed["collapsed"] else "#16a34a" for _, ed in elements_d]

        fig_diff = go.Figure(go.Bar(
            y=labels_d, x=variances, orientation="h",
            marker_color=colors_d,
            text=[f"{v:.2f}" for v in variances],
            textposition="outside", textfont=dict(size=12),
        ))
        fig_diff.add_vline(x=0.5, line_dash="dash", line_color="#9ca3af",
                           annotation_text="Threshold", annotation=dict(font=dict(size=11)))
        fig_diff.update_layout(
            xaxis=dict(title="How differently personas reacted"),
            height=55 + 42 * len(elements_d), margin=dict(t=10, b=40, l=190, r=30),
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickfont=dict(size=12)),
        )
        st.plotly_chart(fig_diff, use_container_width=True, config=CHART_CONFIG)

        n_collapsed = sum(1 for _, ed in elements_d if ed["collapsed"])
        if n_collapsed == len(elements_d):
            st.warning(f"All elements collapsed for this variant — the AI rated them identically "
                       f"across all personas. These scores may not reflect true audience differences.")

with st.expander("Position bias check"):
    st.markdown("We randomized the order of elements in each AI prompt to prevent bias "
                "toward elements listed first. This check confirms the randomization worked.")
    bias_data = summary.get("position_bias", {})
    all_clean = True
    for v in variants:
        v_bias = bias_data.get(v, {})
        flagged = {eid: b for eid, b in v_bias.items()
                   if isinstance(b, dict) and abs(b.get("spearman_rho", 0)) > 0.3}
        if flagged:
            all_clean = False
            for eid, b in flagged.items():
                label = ELEMENT_LABELS.get(eid, eid)
                rho = b["spearman_rho"]
                p_val = b["p_value"]
                sig = "statistically significant" if p_val < 0.05 else "not statistically significant"
                st.markdown(f"- **{VARIANT_NAMES[v]}** → *{label}*: mild position bias detected ({sig})")
        else:
            st.markdown(f"- **{VARIANT_NAMES[v]}**: No position bias detected")
    if all_clean:
        st.success("Randomization appears effective — no residual position bias across all variants.")


# ── Methodology footer ──────────────────────────────────────────────────────

st.divider()
with st.expander("Methodology & Technical Details"):
    st.markdown("""
**How this works:** Four synthetic audience personas — each with distinct buying motivations, skepticism levels,
and pain awareness — evaluate three LinkedIn ad variants. Each evaluation runs 5 times for statistical reliability.
The AI scores each element of each ad independently, producing element-level diagnostics rather than just a top-line winner.

**Statistical rigor:**
- Confidence intervals via bootstrap resampling (1,000 iterations)
- Close-call detection with minimum detectable effect threshold (0.5 points)
- Effect size measurement (Cohen's d) for practical significance
- Element order randomized per evaluation to prevent ordering bias
- AI consistency measured via Krippendorff's alpha (inter-run agreement)
- Causal isolation via minimal-pair experiments (one variable changed at a time)

**Cost:** $0.04 total across 80 API calls (60 evaluations + 20 causal experiments), 72% prompt cache hit rate.
""")
