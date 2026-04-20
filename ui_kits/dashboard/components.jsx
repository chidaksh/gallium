/* global React */
const { useState, useMemo } = React;

// ───────── Header ─────────
function Header() {
  return (
    <header style={hdr.root}>
      <div style={hdr.brand}>
        <div style={hdr.mark}>
          <div style={hdr.markInner} />
          <div style={hdr.dotA} />
          <div style={hdr.dotB} />
        </div>
        <div>
          <div style={hdr.word}>creative<span style={{color:'#06d6a0'}}>IQ</span></div>
          <div style={hdr.sub}>Pre-flight creative evaluation · built for Gallium</div>
        </div>
      </div>
      <div style={hdr.right}>
        <div style={hdr.pill}>
          <span style={{...hdr.dot, background:'#06d6a0'}} />
          <span>Run complete · 5 iterations · $0.04</span>
        </div>
        <button style={hdr.btn}>New evaluation</button>
      </div>
    </header>
  );
}
const hdr = {
  root: { display:'flex', justifyContent:'space-between', alignItems:'center', padding:'16px 28px', borderBottom:'1px solid var(--border)', background:'white' },
  brand: { display:'flex', gap:12, alignItems:'center' },
  mark: { width:36, height:36, borderRadius:8, background:'#0f172a', position:'relative', flexShrink:0 },
  markInner: { position:'absolute', inset:7, border:'2px solid #06d6a0', borderRadius:4 },
  dotA: { position:'absolute', width:6, height:6, borderRadius:'50%', background:'#f72585', top:12, right:12 },
  dotB: { position:'absolute', width:6, height:6, borderRadius:'50%', background:'#4361ee', bottom:12, left:12 },
  word: { fontWeight:700, fontSize:18, letterSpacing:'-0.02em' },
  sub: { fontSize:12, color:'var(--fg-3)' },
  right: { display:'flex', alignItems:'center', gap:12 },
  pill: { display:'inline-flex', alignItems:'center', gap:8, padding:'6px 12px', borderRadius:999, background:'var(--bg-2)', border:'1px solid var(--border)', fontSize:12, color:'var(--fg-2)', fontVariantNumeric:'tabular-nums' },
  dot: { width:8, height:8, borderRadius:'50%' },
  btn: { fontFamily:'inherit', fontWeight:600, fontSize:13, padding:'8px 14px', borderRadius:8, background:'#0f172a', color:'white', border:'none', cursor:'pointer' },
};

// ───────── Sidebar ─────────
function Sidebar({ data, activePersona, onPersonaClick }) {
  const { variants, personas, cost } = data;
  return (
    <aside style={sb.root}>
      <div style={sb.section}>
        <div className="ds-eyebrow" style={{marginBottom:10}}>Campaign</div>
        <div style={sb.campaign}>Relay — LinkedIn organic</div>
        <div style={sb.meta}>Async video messaging for distributed teams</div>
      </div>

      <div style={sb.section}>
        <div className="ds-eyebrow" style={{marginBottom:10}}>Audience personas</div>
        {personas.map(p => (
          <button key={p.id} onClick={() => onPersonaClick(p.id)}
            style={{...sb.persona, ...(activePersona===p.id ? sb.personaActive : {})}}>
            <div style={{...sb.avatar, background:p.accent}}>{p.name[0]}</div>
            <div style={{flex:1, textAlign:'left'}}>
              <div style={sb.pName}>{p.name} <span style={sb.pTitle}>· {p.title}</span></div>
              <div style={sb.pProfile}>{p.profile}</div>
            </div>
            <div style={sb.weight}>{p.weight}%</div>
          </button>
        ))}
      </div>

      <div style={sb.section}>
        <div className="ds-eyebrow" style={{marginBottom:10}}>Creative variants</div>
        {Object.values(variants).map(v => (
          <div key={v.id} style={sb.variant}>
            <div style={{...sb.variantBar, background:v.color}} />
            <div style={{flex:1, minWidth:0}}>
              <div style={{...sb.vName, color:v.colorInk}}>Variant {v.id} · {v.name}</div>
              <div style={sb.vHook}>{v.hook}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={sb.cost}>
        <div>
          <div style={sb.costN}>${cost.total.toFixed(2)}</div>
          <div style={sb.costL}>Total cost</div>
        </div>
        <div>
          <div style={sb.costN}>{cost.calls}</div>
          <div style={sb.costL}>API calls</div>
        </div>
        <div>
          <div style={sb.costN}>{Math.round(cost.cacheHit*100)}%</div>
          <div style={sb.costL}>Cache hit</div>
        </div>
      </div>
    </aside>
  );
}
const sb = {
  root: { width:320, flexShrink:0, borderRight:'1px solid var(--border)', padding:'24px 20px', background:'var(--bg-2)', display:'flex', flexDirection:'column', gap:28, overflow:'auto' },
  section: {},
  campaign: { fontSize:15, fontWeight:600, color:'var(--fg-1)' },
  meta: { fontSize:12, color:'var(--fg-3)', marginTop:2 },
  persona: { display:'flex', alignItems:'center', gap:10, padding:'9px 10px', width:'100%', borderRadius:8, background:'transparent', border:'1px solid transparent', marginBottom:2, cursor:'pointer', fontFamily:'inherit', transition:'all 120ms' },
  personaActive: { background:'white', borderColor:'#0f172a', boxShadow:'0 1px 2px rgba(15,23,42,0.06)' },
  avatar: { width:28, height:28, borderRadius:'50%', color:'white', fontWeight:700, fontSize:12, display:'flex', alignItems:'center', justifyContent:'center' },
  pName: { fontSize:13, fontWeight:600, color:'var(--fg-1)' },
  pTitle: { fontWeight:400, color:'var(--fg-3)' },
  pProfile: { fontSize:12, color:'var(--fg-2)', marginTop:2, lineHeight:1.4 },
  weight: { fontFamily:'var(--font-mono)', fontSize:11, color:'var(--fg-3)', flexShrink:0, whiteSpace:'nowrap' },
  variant: { display:'flex', gap:10, padding:'8px 0', borderBottom:'1px solid var(--bg-3)' },
  variantBar: { width:3, borderRadius:2, flexShrink:0 },
  vName: { fontSize:12, fontWeight:600 },
  vHook: { fontSize:11, color:'var(--fg-3)', fontStyle:'italic', marginTop:3, lineHeight:1.45 },
  cost: { display:'flex', gap:16, padding:'12px 14px', borderRadius:10, background:'white', border:'1px solid var(--border)' },
  costN: { fontSize:16, fontWeight:700, fontVariantNumeric:'tabular-nums', color:'var(--fg-1)' },
  costL: { fontSize:10, color:'var(--fg-3)', textTransform:'uppercase', letterSpacing:'0.04em', marginTop:2 },
};

// ───────── Hero ─────────
function Hero({ data }) {
  const { variants, effect } = data;
  const ranked = ['A','B','C'].sort((x,y) => variants[y].mean - variants[x].mean);
  const w = variants[ranked[0]], r = variants[ranked[1]];
  return (
    <section style={hero.root}>
      <div>
        <div className="ds-eyebrow" style={{color:'var(--fg-3)', marginBottom:10}}>Relay LinkedIn campaign · pre-flight</div>
        <h1 style={hero.h}>
          Variant <span style={{color:w.color}}>{w.id}</span> wins —
          <span style={hero.hSub}> but only if you target Jordan or Sam.</span>
        </h1>
        <p style={hero.p}>
          Social proof-led copy scores <span style={hero.num}>{w.mean.toFixed(1)} / 10</span> across
          the weighted portfolio, beating ROI-led by
          <span style={hero.num}> +{(w.mean - r.mean).toFixed(2)}</span>
          {' '}(<span style={{fontFamily:'var(--font-mono)'}}>d = +{effect.cohensD.toFixed(2)}</span>, {effect.label.toLowerCase()} effect).
          The gap is statistically reliable — this isn't noise.
        </p>
      </div>
      <div>
        <div style={hero.metricsHead}>
          <span style={hero.metricsTitle}>Weighted portfolio score</span>
          <span style={hero.metricsHint}>Average persona rating · higher = more likely to convert</span>
        </div>
        <div style={hero.metrics}>
        {ranked.map((id, i) => {
          const v = variants[id];
          const rankLabel = i===0?'Winner':i===1?'Runner-up':'Third';
          return (
            <div key={id} style={{...hero.metric, borderLeftColor:v.color}}>
              <div style={hero.metricLeft}>
                <div style={hero.metricLabel}>{rankLabel}</div>
                <div style={hero.metricName}>
                  <span style={{color:v.color, fontWeight:700}}>Variant {v.id}</span>
                  <span style={hero.metricSub}> · {v.name}</span>
                </div>
                <div style={hero.metricCi}>95% CI [{v.ci[0].toFixed(2)}, {v.ci[1].toFixed(2)}]</div>
              </div>
              <div style={hero.metricRight}>
                <div style={hero.metricValue}>{v.mean.toFixed(2)}</div>
                <div style={hero.metricUnit}>/ 10</div>
              </div>
            </div>
          );
        })}
      </div>
      </div>
    </section>
  );
}
const hero = {
  root: { display:'grid', gridTemplateColumns:'1.4fr 1fr', gap:32, alignItems:'start', padding:'32px 36px', borderBottom:'1px solid var(--border)' },
  h: { fontSize:36, fontWeight:700, letterSpacing:'-0.02em', lineHeight:1.1, margin:'0 0 14px', color:'var(--fg-1)', textWrap:'balance' },
  hSub: { color:'var(--fg-3)', fontWeight:600 },
  p: { fontSize:15, lineHeight:1.55, color:'var(--fg-2)', margin:0, maxWidth:600 },
  num: { fontFamily:'var(--font-mono)', color:'var(--fg-1)', fontWeight:600, fontVariantNumeric:'tabular-nums' },
  metrics: { display:'grid', gridTemplateColumns:'1fr', gap:8 },
  metricsHead: { display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom:10, paddingBottom:8, borderBottom:'1px solid var(--border)' },
  metricsTitle: { fontSize:11, fontWeight:700, color:'var(--fg-1)', textTransform:'uppercase', letterSpacing:'0.06em' },
  metricsHint: { fontSize:11, color:'var(--fg-3)' },
  metric: { background:'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)', padding:'14px 18px', borderRadius:10, borderLeft:'4px solid #06d6a0', display:'flex', alignItems:'center', justifyContent:'space-between', gap:16 },
  metricLeft: { flex:1, minWidth:0 },
  metricLabel: { fontSize:10, fontWeight:700, color:'var(--fg-3)', textTransform:'uppercase', letterSpacing:'0.06em' },
  metricName: { fontSize:15, marginTop:4, letterSpacing:'-0.01em' },
  metricSub: { color:'var(--fg-2)', fontWeight:500 },
  metricCi: { fontFamily:'var(--font-mono)', fontSize:11, color:'var(--fg-3)', marginTop:4, fontVariantNumeric:'tabular-nums' },
  metricRight: { display:'flex', alignItems:'baseline', gap:4, flexShrink:0 },
  metricValue: { fontSize:34, fontWeight:700, letterSpacing:'-0.02em', color:'var(--fg-1)', fontVariantNumeric:'tabular-nums', lineHeight:1 },
  metricUnit: { fontFamily:'var(--font-mono)', fontSize:12, color:'var(--fg-3)' },
};

// ───────── Heatmap ─────────
function Heatmap({ data, activePersona, onPersonaClick }) {
  const { personas, variants, scores } = data;
  const vids = ['A','B','C'];
  const colorFor = (v) => {
    const t = Math.max(0, Math.min(1, (v - 4) / 4));
    // red -> amber -> green
    if (t < 0.5) {
      const k = t*2;
      return `rgb(${254 - 20*k}, ${226 + 12*k}, ${194 - 20*k})`;
    } else {
      const k = (t-0.5)*2;
      return `rgb(${242 - 154*k}, ${230 - 63*k}, ${138 + 2*k})`;
    }
  };
  const personaWinners = personas.reduce((acc, p) => {
    const s = scores[p.id];
    const best = vids.reduce((a,b) => s[a] >= s[b] ? a : b);
    acc[p.id] = vids.filter(v => Math.abs(s[v] - s[best]) < 0.05);
    return acc;
  }, {});

  return (
    <section style={hm.root}>
      <div style={hm.head}>
        <div>
          <h2 style={hm.h2}>Who prefers what?</h2>
          <p style={hm.p}>Different audiences respond to different messages. Click a row to drill in.</p>
        </div>
        <div style={hm.legend}>
          <span style={hm.legText}>Low</span>
          <div style={hm.bar} />
          <span style={hm.legText}>High</span>
        </div>
      </div>
      <div style={hm.grid}>
        <div />
        {vids.map(v => (
          <div key={v} style={{...hm.col, color: variants[v].colorInk}}>
            <span style={{...hm.chip, background: variants[v].colorSoft}}>
              <span style={{...hm.chipDot, background: variants[v].color}} />
              {v} · {variants[v].name}
            </span>
          </div>
        ))}
        {personas.map(p => {
          const active = activePersona===p.id;
          return (
            <React.Fragment key={p.id}>
              <button onClick={() => onPersonaClick(p.id)} style={{...hm.rowLabel, ...(active?hm.rowLabelActive:{})}}>
                <div style={{...hm.av, background:p.accent}}>{p.name[0]}</div>
                <div style={{flex:1, textAlign:'left'}}>
                  <div style={hm.rowName}>{p.name}</div>
                  <div style={hm.rowTitle}>{p.title} · {p.weight}%</div>
                </div>
                <div style={hm.rowPrefers}>
                  prefers <span style={{fontWeight:700, color:'var(--fg-1)'}}>{personaWinners[p.id].join('/')}</span>
                </div>
              </button>
              {vids.map(v => {
                const s = scores[p.id][v];
                const isWinner = personaWinners[p.id].includes(v);
                return (
                  <div key={v} style={{...hm.cell, background: colorFor(s), ...(active && !isWinner ? {opacity:0.45} : {})}}>
                    <span style={hm.cellV}>{s.toFixed(1)}</span>
                    {isWinner && <span style={hm.star}>★</span>}
                  </div>
                );
              })}
            </React.Fragment>
          );
        })}
      </div>
      <div style={hm.insight}>
        <strong>Key insight.</strong> No single variant wins every audience. Sam (Founder) scores Variant A at just
        <span style={hm.num}> 4.8</span> but gives Variant C a
        <span style={hm.num}> 7.0</span> — early-stage founders need peer validation before they consider a tool.
        Jordan responds equally well to ROI data and social proof (both 7.8).
      </div>
    </section>
  );
}
const hm = {
  root: { padding:'32px 36px', borderBottom:'1px solid var(--border)' },
  head: { display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:20 },
  h2: { fontSize:26, fontWeight:700, letterSpacing:'-0.01em', margin:'0 0 6px', color:'var(--fg-1)' },
  p: { fontSize:14, color:'var(--fg-3)', margin:0 },
  legend: { display:'flex', alignItems:'center', gap:8 },
  bar: { width:140, height:8, borderRadius:4, background:'linear-gradient(90deg, #fee2e2 0%, #fde68a 50%, #bbf7d0 75%, #16a34a 100%)' },
  legText: { fontSize:11, color:'var(--fg-3)', fontFamily:'var(--font-mono)' },
  grid: { display:'grid', gridTemplateColumns:'260px 1fr 1fr 1fr', gap:6, marginBottom:18 },
  col: { padding:'6px 4px', textAlign:'center' },
  chip: { display:'inline-flex', alignItems:'center', gap:6, padding:'4px 10px', borderRadius:999, fontSize:12, fontWeight:600 },
  chipDot: { width:6, height:6, borderRadius:'50%' },
  rowLabel: { display:'flex', alignItems:'center', gap:10, padding:'10px 12px', border:'1px solid transparent', borderRadius:8, background:'transparent', cursor:'pointer', fontFamily:'inherit', transition:'all 120ms' },
  rowLabelActive: { borderColor:'#0f172a', background:'white', boxShadow:'0 1px 2px rgba(15,23,42,0.06)' },
  av: { width:28, height:28, borderRadius:'50%', color:'white', fontWeight:700, fontSize:12, display:'flex', alignItems:'center', justifyContent:'center' },
  rowName: { fontSize:13, fontWeight:600, color:'var(--fg-1)' },
  rowTitle: { fontSize:11, color:'var(--fg-3)' },
  rowPrefers: { fontSize:11, color:'var(--fg-3)', fontFamily:'var(--font-mono)' },
  cell: { borderRadius:8, display:'flex', alignItems:'center', justifyContent:'center', gap:6, padding:'12px 8px', position:'relative', transition:'opacity 200ms' },
  cellV: { fontSize:22, fontWeight:700, color:'#0f172a', fontVariantNumeric:'tabular-nums' },
  star: { fontSize:12, color:'#0f172a' },
  insight: { padding:'14px 16px', background:'#f0f7ff', borderLeft:'4px solid #4361ee', borderRadius:'0 8px 8px 0', fontSize:13.5, lineHeight:1.55, color:'var(--fg-2)' },
  num: { fontFamily:'var(--font-mono)', fontWeight:600, color:'var(--fg-1)', fontVariantNumeric:'tabular-nums' },
};

Object.assign(window, { Header, Sidebar, Hero, Heatmap });
