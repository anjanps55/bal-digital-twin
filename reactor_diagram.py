"""Reactor cutaway diagram — interactive HTML/CSS visualization."""


def build_reactor_html(data_json, inlet_nh3, inlet_lido, v_cv1, v_cv2, a_m):
    """Return HTML for the interactive reactor cutaway diagram."""
    return f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;overflow:hidden}}
#root{{padding:14px 18px;height:100vh;display:flex;flex-direction:column;gap:8px}}

/* Header */
.hdr{{display:flex;justify-content:space-between;align-items:center;flex-shrink:0}}
.hdr h3{{font-size:14px;color:#94a3b8;font-weight:600}}
#tl2{{font-size:12px;color:#64748b}}

/* Main reactor area */
#reactor{{flex:1;display:flex;gap:0;min-height:0;position:relative}}

/* Inlet / Outlet columns */
.io-col{{width:70px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:6px;flex-shrink:0}}
.io-label{{font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.5px}}
.io-val{{font-size:11px;font-weight:600}}

/* Shell (bioreactor body) */
#shell{{flex:1;background:#1a1f2e;border:2px solid #334155;border-radius:16px;position:relative;overflow:hidden;display:flex;flex-direction:column}}
#shell-label{{position:absolute;top:8px;left:12px;font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:1px;z-index:5}}

/* Compartment bundle area */
#compartments{{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 16px;gap:4px;position:relative}}

/* Single disc-compartment row */
.disc-row{{display:flex;align-items:stretch;height:52px;position:relative}}
.disc-lumen{{flex:1;border-radius:8px;position:relative;overflow:hidden;border:1.5px solid #475569}}
.lumen-inner{{position:absolute;inset:2px;border-radius:6px;transition:background 0.4s}}
.lumen-label{{position:absolute;left:8px;top:4px;font-size:8px;color:#94a3b8;font-weight:600;z-index:2}}
.lumen-flow{{position:absolute;top:50%;transform:translateY(-50%);font-size:9px;color:#64748b;z-index:2}}

/* Membrane wall */
.membrane-wall{{width:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;flex-shrink:0;position:relative}}
.mw-dot{{width:4px;height:4px;border-radius:50%;background:#475569}}
.mw-label{{position:absolute;font-size:7px;color:#475569;writing-mode:vertical-rl;letter-spacing:0.5px;right:-2px}}

/* ECS (extra-capillary space / hepatocyte zone) */
.ecs{{flex:1;border-radius:8px;position:relative;overflow:hidden;border:1.5px solid #475569}}
.ecs-inner{{position:absolute;inset:2px;border-radius:6px;transition:background 0.4s}}
.ecs-label{{position:absolute;left:8px;top:4px;font-size:8px;color:#94a3b8;font-weight:600;z-index:2}}

/* Molecule icons */
.mol{{display:inline-flex;align-items:center;gap:2px;font-size:9px;padding:2px 5px;border-radius:4px;font-weight:600;white-space:nowrap}}
.mol-nh3{{background:rgba(239,68,68,0.2);color:#f87171}}
.mol-urea{{background:rgba(13,148,136,0.2);color:#5eead4}}
.mol-lido{{background:rgba(99,102,241,0.2);color:#a5b4fc}}
.mol-megx{{background:rgba(245,158,11,0.2);color:#fbbf24}}
.mol-gx{{background:rgba(16,185,129,0.2);color:#6ee7b7}}

/* Reaction annotations */
.rxn-row{{display:flex;align-items:center;justify-content:center;gap:6px;padding:3px 0;flex-shrink:0}}
.rxn{{font-size:10px;padding:4px 10px;border-radius:6px;display:flex;align-items:center;gap:4px}}
.rxn-urea{{background:rgba(13,148,136,0.12);color:#5eead4;border:1px solid rgba(13,148,136,0.25)}}
.rxn-cyp{{background:rgba(99,102,241,0.12);color:#a5b4fc;border:1px solid rgba(99,102,241,0.25)}}
.rxn-arrow{{font-size:12px}}

/* Flux arrows (animated) */
.flux-zone{{position:absolute;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;align-items:center;gap:1px;z-index:3}}
.flux-dot{{width:5px;height:5px;border-radius:50%;animation:pulse 1.5s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:0.3;transform:scale(0.8)}}50%{{opacity:1;transform:scale(1.2)}}}}

/* Concentration bars inside compartments */
.conc-row{{display:flex;align-items:center;gap:4px;font-size:9px;color:#94a3b8;padding:0 8px;z-index:2;position:relative}}
.conc-row b{{color:#e2e8f0;min-width:50px;text-align:right}}
.cbar{{height:4px;flex:1;background:#0f172a;border-radius:2px;overflow:hidden;max-width:80px}}
.cbar-f{{height:100%;border-radius:2px;transition:width 0.4s,background 0.4s}}

/* Hepatocyte cells in ECS */
.cells{{position:absolute;bottom:6px;right:8px;display:flex;gap:3px;z-index:2}}
.cell{{width:10px;height:10px;border-radius:50%;border:1px solid rgba(16,185,129,0.4);transition:background 0.4s}}

/* Bottom metrics */
#mets2{{display:flex;gap:8px;flex-shrink:0}}
.m2{{flex:1;background:#1e293b;border-radius:6px;padding:6px 10px;display:flex;justify-content:space-between;align-items:center}}
.m2-l{{font-size:9px;color:#64748b;text-transform:uppercase}}
.m2-v{{font-size:13px;font-weight:700}}

/* Controls */
#ctl2{{display:flex;align-items:center;gap:10px;flex-shrink:0}}
#pbtn2{{background:#6366f1;color:#fff;border:none;border-radius:6px;padding:5px 16px;cursor:pointer;font-size:11px;font-weight:600}}
#pbtn2:hover{{background:#4f46e5}}
#scr2{{flex:1;accent-color:#6366f1;height:4px;cursor:pointer}}
</style></head><body>
<div id="root">

<div class="hdr">
  <h3>Flat-Disc Bioreactor Cross-Section</h3>
  <span id="tl2">t = 0 min</span>
</div>

<div id="reactor">
  <!-- Inlet -->
  <div class="io-col">
    <div class="io-label">Plasma In</div>
    <div class="io-val mol mol-nh3" id="in_nh3">-</div>
    <div class="io-val mol mol-lido" id="in_lido">-</div>
    <svg width="20" height="60"><path d="M10 0 L10 45 L4 39 M10 45 L16 39" stroke="#475569" fill="none" stroke-width="1.5"/></svg>
    <div class="io-label" style="font-size:8px;color:#334155">Q = <span id="in_q">75</span></div>
  </div>

  <!-- Bioreactor shell -->
  <div id="shell">
    <div id="shell-label">Bioreactor Shell &mdash; Polysulfone Flat-Disc Membrane (35&times;20 cm cylindrical cartridge)</div>

    <div id="compartments">
      <!-- Disc 1 (NH3/Urea pathway) -->
      <div class="disc-row">
        <div class="disc-lumen">
          <div class="lumen-inner" id="lum1"></div>
          <div class="lumen-label">CV1 &mdash; Lumen (Plasma)</div>
          <div style="position:absolute;bottom:4px;left:8px;right:8px;display:flex;flex-direction:column;gap:2px;z-index:2">
            <div class="conc-row"><span class="mol mol-nh3" style="font-size:8px">NH\u2083</span><b id="f1_nh3">-</b></div>
            <div class="conc-row"><span class="mol mol-urea" style="font-size:8px">Urea</span><b id="f1_urea">-</b></div>
          </div>
        </div>
        <div class="membrane-wall">
          <div class="mw-dot"></div><div class="mw-dot"></div><div class="mw-dot"></div>
          <div class="mw-dot"></div><div class="mw-dot"></div><div class="mw-dot"></div>
          <div class="flux-zone" style="left:-2px">
            <div class="flux-dot" style="background:#f87171;animation-delay:0s"></div>
            <div class="flux-dot" style="background:#f87171;animation-delay:0.3s"></div>
            <div class="flux-dot" style="background:#5eead4;animation-delay:0.6s"></div>
          </div>
          <div class="mw-label">MEMBRANE</div>
        </div>
        <div class="ecs">
          <div class="ecs-inner" id="ecs1"></div>
          <div class="ecs-label">CV2 &mdash; ECS (Hepatocytes)</div>
          <div style="position:absolute;bottom:4px;left:8px;right:8px;display:flex;flex-direction:column;gap:2px;z-index:2">
            <div class="conc-row"><span class="mol mol-nh3" style="font-size:8px">NH\u2083</span><b id="f1_nh3_cv2">-</b></div>
            <div class="conc-row"><span class="mol mol-urea" style="font-size:8px">Urea</span><b id="f1_urea_cv2">-</b></div>
          </div>
          <div class="cells" id="cells1"></div>
        </div>
      </div>

      <!-- Reaction annotation row -->
      <div class="rxn-row">
        <div class="rxn rxn-urea">
          <span class="mol mol-nh3" style="font-size:9px">2 NH\u2083</span>
          <span class="rxn-arrow">\u2192</span>
          <span class="mol mol-urea" style="font-size:9px">1 Urea</span>
          <span style="font-size:8px;color:#475569;margin-left:4px">(urea cycle)</span>
        </div>
        <div class="rxn rxn-cyp">
          <span class="mol mol-lido" style="font-size:9px">Lido</span>
          <span class="rxn-arrow">\u2192</span>
          <span class="mol mol-megx" style="font-size:9px">MEGX</span>
          <span class="rxn-arrow">\u2192</span>
          <span class="mol mol-gx" style="font-size:9px">GX</span>
          <span style="font-size:8px;color:#475569;margin-left:4px">(CYP450)</span>
        </div>
      </div>

      <!-- Disc 2 (Lido/MEGX/GX pathway) -->
      <div class="disc-row">
        <div class="disc-lumen">
          <div class="lumen-inner" id="lum2"></div>
          <div class="lumen-label">CV1 &mdash; Lumen (Plasma)</div>
          <div style="position:absolute;bottom:4px;left:8px;right:8px;display:flex;flex-direction:column;gap:2px;z-index:2">
            <div class="conc-row"><span class="mol mol-lido" style="font-size:8px">Lido</span><b id="f2_lido">-</b></div>
            <div class="conc-row"><span class="mol mol-megx" style="font-size:8px">MEGX</span><b id="f2_megx">-</b><span class="mol mol-gx" style="font-size:8px;margin-left:4px">GX</span><b id="f2_gx">-</b></div>
          </div>
        </div>
        <div class="membrane-wall">
          <div class="mw-dot"></div><div class="mw-dot"></div><div class="mw-dot"></div>
          <div class="mw-dot"></div><div class="mw-dot"></div><div class="mw-dot"></div>
          <div class="flux-zone" style="left:-2px">
            <div class="flux-dot" style="background:#a5b4fc;animation-delay:0.2s"></div>
            <div class="flux-dot" style="background:#fbbf24;animation-delay:0.5s"></div>
            <div class="flux-dot" style="background:#6ee7b7;animation-delay:0.8s"></div>
          </div>
        </div>
        <div class="ecs">
          <div class="ecs-inner" id="ecs2"></div>
          <div class="ecs-label">CV2 &mdash; ECS (Hepatocytes)</div>
          <div style="position:absolute;bottom:4px;left:8px;right:8px;display:flex;flex-direction:column;gap:2px;z-index:2">
            <div class="conc-row"><span class="mol mol-lido" style="font-size:8px">Lido</span><b id="f2_lido_cv2">-</b></div>
            <div class="conc-row"><span class="mol mol-megx" style="font-size:8px">MEGX</span><b id="f2_megx_cv2">-</b><span class="mol mol-gx" style="font-size:8px;margin-left:4px">GX</span><b id="f2_gx_cv2">-</b></div>
          </div>
          <div class="cells" id="cells2"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Outlet -->
  <div class="io-col">
    <div class="io-label">Plasma Out</div>
    <div class="io-val mol mol-nh3" id="out_nh3">-</div>
    <div class="io-val mol mol-lido" id="out_lido">-</div>
    <svg width="20" height="60"><path d="M10 0 L10 45 L4 39 M10 45 L16 39" stroke="#475569" fill="none" stroke-width="1.5"/></svg>
    <div class="io-label" style="font-size:8px;color:#334155">to mixer</div>
  </div>
</div>

<!-- Metrics strip -->
<div id="mets2">
  <div class="m2"><span class="m2-l">Viability</span><span class="m2-v" id="xv2">-</span></div>
  <div class="m2"><span class="m2-l">NH\u2083 Clear.</span><span class="m2-v" id="xc2">-</span></div>
  <div class="m2"><span class="m2-l">Lido Clear.</span><span class="m2-v" id="xl2">-</span></div>
  <div class="m2"><span class="m2-l">MEGX (CV1)</span><span class="m2-v" id="xm2">-</span></div>
  <div class="m2"><span class="m2-l">GX (CV1)</span><span class="m2-v" id="xg2">-</span></div>
  <div class="m2"><span class="m2-l">A_m</span><span class="m2-v" style="color:#64748b">{a_m:,.0f} cm\u00b2</span></div>
</div>

<!-- Controls -->
<div id="ctl2">
  <button id="pbtn2">\u25b6 Play</button>
  <input id="scr2" type="range" min="0" max="1" step="1" value="0">
  <span id="tl2b" style="font-size:11px;color:#64748b;min-width:70px;text-align:right">t = 0 min</span>
</div>

</div>
<script>
(function(){{
  const D={data_json},N=D.length,INH3={inlet_nh3},ILIDO={inlet_lido};
  if(!N)return;
  const $=id=>document.getElementById(id);
  let fi=0,play=false,aid=null,lt=0;
  $('scr2').max=N-1;

  function bc(v,g,w){{return v>g?'#10b981':v>w?'#f59e0b':'#ef4444';}}

  // Generate cell dots
  function makeCells(id,count){{
    let el=$(id);el.innerHTML='';
    for(let i=0;i<count;i++){{
      let d=document.createElement('div');d.className='cell';el.appendChild(d);
    }}
  }}
  makeCells('cells1',6);makeCells('cells2',6);

  function render(){{
    let d=D[fi];

    // Inlet
    $('in_nh3').textContent='NH\u2083 '+INH3;
    $('in_lido').textContent='Lido '+ILIDO;
    $('in_q').textContent=d.pump_Q||75;

    // Outlet
    $('out_nh3').textContent='NH\u2083 '+d.bio_nh3;
    $('out_nh3').style.color=d.bio_nh3<50?'#10b981':'#f87171';
    $('out_lido').textContent='Lido '+d.bio_lido;
    $('out_lido').style.color=d.bio_lido<12?'#10b981':'#a5b4fc';

    // Disc 1 lumen color (NH3 intensity)
    let i1=Math.min(d.bio_nh3_cv1/Math.max(INH3,50),1);
    $('lum1').style.background='rgba(239,68,68,'+(0.04+i1*0.12).toFixed(3)+')';
    $('f1_nh3').textContent=d.bio_nh3_cv1;
    $('f1_urea').textContent=d.bio_urea_cv1;

    // Disc 1 ECS color
    let i2=Math.min(d.bio_nh3_cv2/Math.max(INH3,50),1);
    $('ecs1').style.background='rgba(13,148,136,'+(0.04+(1-i2)*0.12).toFixed(3)+')';
    $('f1_nh3_cv2').textContent=d.bio_nh3_cv2;
    $('f1_urea_cv2').textContent=d.bio_urea_cv2;

    // Disc 2 lumen (Lido)
    let li1=Math.min(d.bio_lido/Math.max(ILIDO,10),1);
    $('lum2').style.background='rgba(99,102,241,'+(0.04+li1*0.12).toFixed(3)+')';
    $('f2_lido').textContent=d.bio_lido;
    $('f2_megx').textContent=(d.bio_megx_cv1||0).toFixed(1);
    $('f2_gx').textContent=(d.bio_gx_cv1||0).toFixed(1);

    // Disc 2 ECS
    $('ecs2').style.background='rgba(99,102,241,'+(0.04+(1-li1)*0.08).toFixed(3)+')';
    $('f2_lido_cv2').textContent=(d.bio_lido_cv2||0).toFixed(1);
    $('f2_megx_cv2').textContent=(d.bio_megx_cv2||0).toFixed(1);
    $('f2_gx_cv2').textContent=(d.bio_gx_cv2||0).toFixed(1);

    // Cell viability coloring
    let vb=d.bio_viability;
    let cc=bc(vb,0.8,0.6);
    document.querySelectorAll('.cell').forEach(c=>{{
      c.style.background=cc+'30';c.style.borderColor=cc+'60';
    }});

    // Metrics
    $('xv2').textContent=(vb*100).toFixed(1)+'%';$('xv2').style.color=bc(vb,0.8,0.6);
    let cl=d.bio_clearance;
    $('xc2').textContent=(cl*100).toFixed(1)+'%';$('xc2').style.color=bc(cl,0.5,0.3);
    let lcl=d.bio_lido_cl||0;
    $('xl2').textContent=(lcl*100).toFixed(1)+'%';$('xl2').style.color=bc(lcl,0.5,0.3);
    $('xm2').textContent=(d.bio_megx_cv1||0).toFixed(1);$('xm2').style.color='#fbbf24';
    $('xg2').textContent=(d.bio_gx_cv1||0).toFixed(1);$('xg2').style.color='#6ee7b7';

    // Time
    $('tl2').textContent='t = '+d.t+' min';
    $('tl2b').textContent='t = '+d.t+' min';
  }}

  function tick(ts){{
    if(!play)return;
    if(ts-lt>100){{lt=ts;fi=Math.min(fi+1,N-1);$('scr2').value=fi;render();
      if(fi>=N-1){{play=false;$('pbtn2').textContent='\u21bb Replay';}}
    }}
    aid=requestAnimationFrame(tick);
  }}

  $('pbtn2').onclick=()=>{{
    if(play){{play=false;$('pbtn2').textContent='\u25b6 Play';cancelAnimationFrame(aid);}}
    else{{if(fi>=N-1)fi=0;play=true;$('pbtn2').textContent='\u23f8 Pause';lt=0;aid=requestAnimationFrame(tick);}}
  }};
  $('scr2').oninput=()=>{{fi=+$('scr2').value;render();}};
  render();
}})();
</script></body></html>
"""
