/* global React */
const { useState } = React;

// ───────── Attribution ─────────
function Attribution({ data }) {
  const { variants, attribution } = data;
  const max = 100;
  return (
    <section style={at.root}>
      <div style={at.head}>
        <h2 style={at.h2}>What makes each variant work — or fail?</h2>
        <p style={at.p}>Every ad is made of parts. Some pull readers in (green), others push them away (red). This is where we learn <em>why</em> a variant wins.</p>
      </div>
      <div style={at.cols}>
        {['A','B','C'].map(vid => {
          const v = variants[vid];
          const rows = [...attribution[vid]].sort((a,b) => b.score - a.score);
          return (
            <div key={vid} style={at.col}>
              <div style={at.colHead}>
                <div style={{...at.tag, background: v.colorSoft, color: v.colorInk}}>
                  <span style={{...at.tagDot, background: v.color}} />
                  Variant {vid}
                </div>
                <div style={at.colName}>{v.name}</div>
              </div>
              <div style={at.list}>
                {rows.map(r => {
                  const pct = Math.abs(r.score) / max;
                  const positive = r.score > 0;
                  const neutral = r.score === 0;
                  return (
                    <div key={r.id} style={at.row}>
                      <div style={at.rowLabel}>{r.label}</div>
                      <div style={at.rowBar}>
                        <div style={at.center} />
                        <div style={{
                          ...at.fill,
                          left: positive ? '50%' : `${50 - pct*50}%`,
                          width: `${pct*50}%`,
                          background: neutral ? '#cbd5e1' : positive ? '#16a34a' : '#dc2626',
                        }} />
                      </div>
                      <div style={{
                        ...at.rowVal,
                        color: neutral ? 'var(--fg-3)' : positive ? '#16a34a' : '#dc2626',
                      }}>{r.score > 0 ? '+' : ''}{r.score}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <div style={at.warning}>
        <strong>Variant B's weak spot.</strong> The <span style={at.code}>"14,000 teams"</span> social proof stat scores
        <span style={{...at.num, color:'#dc2626'}}> −50</span> — 65% of personas flagged it as untrustworthy.
        Alex and Taylor (both high-skepticism) reject it outright. This single line is why B finishes last,
        despite having the strongest opening hook in the entire evaluation.
      </div>
    </section>
  );
}
const at = {
  root: { padding:'32px 36px', borderBottom:'1px solid var(--border)' },
  head: { marginBottom:20 },
  h2: { fontSize:26, fontWeight:700, letterSpacing:'-0.01em', margin:'0 0 6px', color:'var(--fg-1)' },
  p: { fontSize:14, color:'var(--fg-3)', margin:0, maxWidth:720 },
  cols: { display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:20, marginBottom:18 },
  col: { border:'1px solid var(--border)', borderRadius:10, padding:16, background:'white' },
  colHead: { display:'flex', alignItems:'center', gap:10, marginBottom:14, paddingBottom:12, borderBottom:'1px solid var(--bg-3)' },
  tag: { display:'inline-flex', alignItems:'center', gap:6, padding:'3px 10px', borderRadius:999, fontSize:11, fontWeight:700 },
  tagDot: { width:6, height:6, borderRadius:'50%' },
  colName: { fontSize:13, fontWeight:600, color:'var(--fg-2)' },
  list: { display:'flex', flexDirection:'column', gap:10 },
  row: { display:'grid', gridTemplateColumns:'1fr 100px 34px', alignItems:'center', gap:10 },
  rowLabel: { fontSize:12, color:'var(--fg-2)', lineHeight:1.35 },
  rowBar: { position:'relative', height:18, background:'var(--bg-2)', borderRadius:4 },
  center: { position:'absolute', left:'50%', top:0, bottom:0, width:1, background:'var(--border-strong)' },
  fill: { position:'absolute', top:3, bottom:3, borderRadius:3, transition:'width 300ms' },
  rowVal: { fontFamily:'var(--font-mono)', fontSize:12, fontWeight:600, textAlign:'right', fontVariantNumeric:'tabular-nums' },
  warning: { padding:'14px 16px', background:'#fef2f2', borderLeft:'4px solid #dc2626', borderRadius:'0 8px 8px 0', fontSize:13.5, lineHeight:1.55, color:'var(--fg-2)' },
  code: { fontFamily:'var(--font-mono)', fontSize:12, background:'white', padding:'1px 6px', borderRadius:3, border:'1px solid var(--border)' },
  num: { fontFamily:'var(--font-mono)', fontWeight:700, fontVariantNumeric:'tabular-nums' },
};

// ───────── Minimal pairs ─────────
function MinimalPair({ data }) {
  const [pair, setPair] = useState('skepticism');
  const mp = data.minimalPairs[pair];
  const maxAbs = 120;
  return (
    <section style={mp2.root}>
      <div style={mp2.head}>
        <div>
          <h2 style={mp2.h2}>What happens when the audience changes?</h2>
          <p style={mp2.p}>Same persona, same ad — we flip one psychological dimension and measure what moves. This isolates cause from correlation.</p>
        </div>
        <div style={mp2.tabs}>
          <button onClick={() => setPair('skepticism')} style={{...mp2.tab, ...(pair==='skepticism'?mp2.tabActive:{})}}>Skepticism</button>
          <button onClick={() => setPair('pain')} style={{...mp2.tab, ...(pair==='pain'?mp2.tabActive:{})}}>Pain awareness</button>
        </div>
      </div>
      <div style={mp2.titleRow}>
        <div>
          <div style={mp2.expTitle}>{mp.title}</div>
          <div style={mp2.expSub}>{mp.explain}</div>
        </div>
        <div style={mp2.metricBlock}>
          <div style={mp2.metricL}>Willingness to act</div>
          <div style={mp2.metricV}>
            <span style={{color:'#3b82f6'}}>{mp.actionLow.toFixed(1)}</span>
            <span style={mp2.arrow}>→</span>
            <span style={{color:'#ef4444'}}>{mp.actionHigh.toFixed(1)}</span>
          </div>
          <div style={mp2.metricDelta}>
            {(mp.actionHigh - mp.actionLow > 0 ? '+' : '')}
            {(mp.actionHigh - mp.actionLow).toFixed(1)} pts · {mp.low.toLowerCase()} → {mp.high.toLowerCase()}
          </div>
        </div>
      </div>
      <div style={mp2.chart}>
        <div style={mp2.legend}>
          <span style={mp2.legItem}><span style={{...mp2.legDot, background:'#3b82f6'}} />{mp.low}</span>
          <span style={mp2.legItem}><span style={{...mp2.legDot, background:'#ef4444', borderRadius:0, transform:'rotate(45deg)'}} />{mp.high}</span>
          <span style={mp2.axisLabel}>Impact score — negative (hurts) to positive (helps)</span>
        </div>
        {mp.elements.map((el, i) => {
          const lowPct = 50 + (el.low / maxAbs) * 50;
          const highPct = 50 + (el.high / maxAbs) * 50;
          const minPct = Math.min(lowPct, highPct);
          const maxPct = Math.max(lowPct, highPct);
          return (
            <div key={i} style={mp2.elRow}>
              <div style={mp2.elLabel}>{el.label}</div>
              <div style={mp2.track}>
                <div style={mp2.center} />
                <div style={{...mp2.bridge, left: `${minPct}%`, width: `${maxPct - minPct}%`}} />
                <div style={{...mp2.dot, left: `${lowPct}%`, background:'#3b82f6'}} />
                <div style={{...mp2.diamond, left: `${highPct}%`, background:'#ef4444'}} />
              </div>
              <div style={mp2.elDelta}>
                <span style={{color:'#3b82f6'}}>{el.low>0?'+':''}{el.low}</span>
                <span style={{color:'var(--fg-muted)', margin:'0 4px'}}>→</span>
                <span style={{color:'#ef4444'}}>{el.high>0?'+':''}{el.high}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{...mp2.insight, borderLeftColor: '#dc2626', background: '#fef2f2'}}>
        {mp.insight}
      </div>
    </section>
  );
}
const mp2 = {
  root: { padding:'32px 36px', borderBottom:'1px solid var(--border)' },
  head: { display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:22 },
  h2: { fontSize:26, fontWeight:700, letterSpacing:'-0.01em', margin:'0 0 6px', color:'var(--fg-1)' },
  p: { fontSize:14, color:'var(--fg-3)', margin:0, maxWidth:620 },
  tabs: { display:'flex', gap:4, padding:4, borderRadius:10, background:'var(--bg-2)', border:'1px solid var(--border)' },
  tab: { fontFamily:'inherit', fontSize:13, fontWeight:600, padding:'6px 14px', borderRadius:7, border:'none', background:'transparent', color:'var(--fg-3)', cursor:'pointer' },
  tabActive: { background:'white', color:'var(--fg-1)', boxShadow:'0 1px 2px rgba(15,23,42,0.08)' },
  titleRow: { display:'flex', justifyContent:'space-between', alignItems:'flex-end', gap:24, marginBottom:20, padding:'16px 20px', background:'var(--bg-2)', borderRadius:10, border:'1px solid var(--border)' },
  expTitle: { fontSize:17, fontWeight:600, color:'var(--fg-1)' },
  expSub: { fontSize:13, color:'var(--fg-3)', marginTop:4, maxWidth:520, lineHeight:1.5 },
  metricBlock: { textAlign:'right', flexShrink:0 },
  metricL: { fontSize:10, fontWeight:600, color:'var(--fg-3)', textTransform:'uppercase', letterSpacing:'0.04em' },
  metricV: { display:'flex', alignItems:'baseline', gap:10, justifyContent:'flex-end', fontWeight:700, fontSize:28, fontVariantNumeric:'tabular-nums', marginTop:4 },
  arrow: { color:'var(--fg-muted)', fontSize:18 },
  metricDelta: { fontSize:11, color:'var(--fg-3)', fontFamily:'var(--font-mono)', marginTop:2 },
  chart: { padding:'20px 24px', border:'1px solid var(--border)', borderRadius:10, marginBottom:16, background:'white' },
  legend: { display:'flex', alignItems:'center', gap:18, marginBottom:14, paddingBottom:12, borderBottom:'1px solid var(--bg-3)', fontSize:12, color:'var(--fg-2)' },
  legItem: { display:'inline-flex', alignItems:'center', gap:6, fontWeight:500 },
  legDot: { width:10, height:10, borderRadius:'50%' },
  axisLabel: { marginLeft:'auto', fontSize:11, color:'var(--fg-3)', fontFamily:'var(--font-mono)' },
  elRow: { display:'grid', gridTemplateColumns:'200px 1fr 110px', alignItems:'center', gap:14, padding:'6px 0' },
  elLabel: { fontSize:12, color:'var(--fg-2)' },
  track: { position:'relative', height:18 },
  center: { position:'absolute', left:'50%', top:0, bottom:0, width:1, background:'var(--border-strong)' },
  bridge: { position:'absolute', top:'50%', height:2, background:'var(--ink-200)', transform:'translateY(-50%)' },
  dot: { position:'absolute', top:'50%', width:12, height:12, borderRadius:'50%', border:'2px solid white', transform:'translate(-50%, -50%)', boxShadow:'0 1px 3px rgba(0,0,0,0.15)' },
  diamond: { position:'absolute', top:'50%', width:12, height:12, border:'2px solid white', transform:'translate(-50%, -50%) rotate(45deg)', boxShadow:'0 1px 3px rgba(0,0,0,0.15)' },
  elDelta: { fontFamily:'var(--font-mono)', fontSize:11, textAlign:'right', fontVariantNumeric:'tabular-nums', fontWeight:600 },
  insight: { padding:'14px 16px', borderLeft:'4px solid', borderRadius:'0 8px 8px 0', fontSize:13.5, lineHeight:1.55, color:'var(--fg-2)' },
};

// ───────── Recommendations ─────────
function Recommendations({ data }) {
  const { variants } = data;
  const recs = [
    { v: 'C', title: 'Ship Variant C', body: "Wins 3 of 4 personas, ties the 4th. Peer-validation (Linear, Vercel, Lattice) builds trust without triggering skepticism. Works across all audience segments.", action: 'Recommended' },
    { v: 'B', title: "Fix Variant B's proof point", body: 'B has the strongest opening in the evaluation, but the "14,000 teams" stat is actively hurting it. Replace with named case studies — Alex and Taylor want specifics, not aggregates.', action: 'Revise' },
    { v: 'A', title: 'Use Variant A for ROI buyers', body: 'The math hook forces readers to verify the arithmetic — highly effective on analytical audiences. Consider A for targeted campaigns to VP/Director segments.', action: 'Segment' },
  ];
  return (
    <section style={rc.root}>
      <h2 style={rc.h2}>Recommendations</h2>
      <div style={rc.grid}>
        {recs.map(r => {
          const v = variants[r.v];
          return (
            <div key={r.v} style={{...rc.card, borderTopColor:v.color}}>
              <div style={rc.cardHead}>
                <div style={{...rc.chip, background:v.colorSoft, color:v.colorInk}}>Variant {r.v}</div>
                <div style={rc.action}>{r.action}</div>
              </div>
              <div style={rc.title}>{r.title}</div>
              <div style={rc.body}>{r.body}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
const rc = {
  root: { padding:'32px 36px', borderBottom:'1px solid var(--border)' },
  h2: { fontSize:26, fontWeight:700, letterSpacing:'-0.01em', margin:'0 0 20px', color:'var(--fg-1)' },
  grid: { display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:16 },
  card: { padding:'18px 20px', borderRadius:12, background:'white', border:'1px solid var(--border)', borderTop:'3px solid', boxShadow:'0 1px 2px rgba(15,23,42,0.04)' },
  cardHead: { display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 },
  chip: { padding:'3px 10px', borderRadius:999, fontSize:11, fontWeight:700 },
  action: { fontSize:10, fontWeight:700, color:'var(--fg-3)', textTransform:'uppercase', letterSpacing:'0.06em' },
  title: { fontSize:16, fontWeight:700, color:'var(--fg-1)', marginBottom:8, letterSpacing:'-0.01em' },
  body: { fontSize:13, color:'var(--fg-2)', lineHeight:1.55 },
};

// ───────── Diagnostics ─────────
function Diagnostics() {
  const [open, setOpen] = useState(false);
  return (
    <section style={dg.root}>
      <button onClick={() => setOpen(!open)} style={dg.toggle}>
        <span style={dg.caret}>{open ? '▾' : '▸'}</span>
        <span style={dg.toggleT}>Under the hood — diagnostics for the ML team</span>
        <span style={dg.toggleS}>Krippendorff's α · position bias · persona collapse</span>
      </button>
      {open && (
        <div style={dg.body}>
          <div style={dg.stat}>
            <div style={dg.statL}>LLM self-consistency</div>
            <div style={dg.statV}>0.87</div>
            <div style={dg.statSub}>Krippendorff's α · ordinal</div>
          </div>
          <div style={dg.stat}>
            <div style={dg.statL}>Persona differentiation</div>
            <div style={dg.statV}>0.62</div>
            <div style={dg.statSub}>mean between-persona variance</div>
          </div>
          <div style={dg.stat}>
            <div style={dg.statL}>Position bias</div>
            <div style={dg.statV}>—</div>
            <div style={dg.statSub}>no elements flagged (ρ &lt; 0.3)</div>
          </div>
          <div style={dg.stat}>
            <div style={dg.statL}>Close-call detection</div>
            <div style={dg.statV}>False</div>
            <div style={dg.statSub}>MDE = 0.5, Kohavi et al. 2020</div>
          </div>
        </div>
      )}
    </section>
  );
}
const dg = {
  root: { padding:'24px 36px 48px' },
  toggle: { display:'flex', alignItems:'center', gap:12, padding:'14px 18px', width:'100%', background:'var(--bg-2)', border:'1px solid var(--border)', borderRadius:10, fontFamily:'inherit', cursor:'pointer', textAlign:'left' },
  caret: { fontFamily:'var(--font-mono)', color:'var(--fg-3)', fontSize:14 },
  toggleT: { fontSize:14, fontWeight:600, color:'var(--fg-1)' },
  toggleS: { fontSize:12, color:'var(--fg-3)', marginLeft:'auto', fontFamily:'var(--font-mono)' },
  body: { display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:12, marginTop:12 },
  stat: { padding:'16px 18px', borderRadius:10, background:'white', border:'1px solid var(--border)' },
  statL: { fontSize:11, fontWeight:600, color:'var(--fg-3)', textTransform:'uppercase', letterSpacing:'0.04em' },
  statV: { fontSize:28, fontWeight:700, fontVariantNumeric:'tabular-nums', color:'var(--fg-1)', letterSpacing:'-0.02em', margin:'6px 0 4px' },
  statSub: { fontSize:11, color:'var(--fg-3)', fontFamily:'var(--font-mono)' },
};

Object.assign(window, { Attribution, MinimalPair, Recommendations, Diagnostics });
