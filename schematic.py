"""Standalone module for the BAL schematic HTML generation."""


def build_schematic_html(data_json, inlet_nh3, v_cv1, v_cv2):
    """Return the full HTML string for the animated BAL schematic."""
    return f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;overflow:hidden}}
#root{{padding:16px 20px 12px;height:100vh;display:flex;flex-direction:column;gap:10px}}

/* Pipeline row */
#pipeline{{display:flex;align-items:center;gap:0;flex-shrink:0}}
.pipe{{width:32px;height:6px;border-radius:3px;transition:background .4s}}
.pipe-main{{background:#334155}}
.arrow-txt{{font-size:10px;color:#64748b;white-space:nowrap;padding:0 4px}}
.mod{{border-radius:10px;background:#1e293b;border:2px solid #10b981;padding:8px 10px;
     text-align:center;min-width:90px;transition:border-color .4s,box-shadow .4s;flex-shrink:0}}
.mod.a0{{border-color:#10b981;box-shadow:0 0 8px rgba(16,185,129,.25)}}
.mod.a1{{border-color:#f59e0b;box-shadow:0 0 8px rgba(245,158,11,.3)}}
.mod.a2,.mod.a3{{border-color:#ef4444;box-shadow:0 0 8px rgba(239,68,68,.3)}}
.ml{{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px}}
.mv{{font-size:12px;color:#e2e8f0;margin-top:3px;line-height:1.4}}
.bar-t{{height:4px;background:#0f172a;border-radius:2px;margin-top:4px;overflow:hidden}}
.bar-f{{height:100%;border-radius:2px;transition:width .4s,background .4s}}
.mchk{{font-size:20px;font-weight:bold;margin-top:2px}}

/* Bypass */
.byp{{display:flex;align-items:center;margin:-4px 0 0 0}}
.byp-lbl{{font-size:9px;color:#475569;margin-left:6px}}
.byp-pipe{{flex:1;height:4px;background:rgba(239,68,68,.15);border-radius:2px;margin:0 4px}}

/* Bioreactor inset */
#bio{{flex:1;display:flex;gap:12px;min-height:0}}
.ch{{flex:1;border-radius:10px;padding:14px 16px;border:1.5px solid #334155;transition:background .4s;display:flex;flex-direction:column}}
.ch-t{{font-size:11px;font-weight:700;margin-bottom:8px}}
.ch-r{{display:flex;justify-content:space-between;font-size:12px;color:#94a3b8;line-height:1.7}}
.ch-r b{{color:#e2e8f0;font-weight:600}}
#mem{{width:50px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;flex-shrink:0}}
.mb{{width:6px;height:8px;background:#475569;border-radius:1px}}
.mem-l{{font-size:8px;color:#475569;writing-mode:vertical-rl;letter-spacing:1px;text-transform:uppercase}}
.fx{{display:flex;align-items:center;gap:4px;font-size:10px;margin:4px 0}}

/* Metrics */
#mets{{display:flex;gap:10px;flex-shrink:0}}
.mc{{flex:1;background:#1e293b;border-radius:8px;padding:8px 12px}}
.mc-l{{font-size:9px;color:#64748b;text-transform:uppercase}}
.mc-v{{font-size:16px;font-weight:700;margin-top:2px}}
.mc-bt{{height:5px;background:#0f172a;border-radius:3px;margin-top:4px;overflow:hidden}}
.mc-bf{{height:100%;border-radius:3px;transition:width .4s,background .4s}}

/* Controls */
#ctl{{display:flex;align-items:center;gap:10px;flex-shrink:0;padding-top:2px}}
#pbtn{{background:#6366f1;color:#fff;border:none;border-radius:6px;padding:6px 18px;cursor:pointer;font-size:12px;font-weight:600}}
#pbtn:hover{{background:#4f46e5}}
#scr{{flex:1;accent-color:#6366f1;height:5px;cursor:pointer}}
#tl{{font-size:12px;color:#94a3b8;min-width:80px;text-align:right}}
.eq{{font-size:10px;color:#475569;font-style:italic;text-align:center;flex-shrink:0}}
</style></head><body>
<div id="root">

<div id="pipeline">
  <span class="arrow-txt">Blood In</span>
  <div class="pipe pipe-main" id="p0"></div>
  <div class="mod a0" id="m0"><div class="ml">Separator</div><div class="mv" id="v0"></div></div>
  <div class="pipe pipe-main" id="p1"></div>
  <div class="mod a0" id="m1"><div class="ml">Pump</div><div class="mv" id="v1"></div></div>
  <div class="pipe pipe-main" id="p2"></div>
  <div class="mod a0" id="m2" style="min-width:130px"><div class="ml">Bioreactor</div><div class="mv" id="v2"></div>
    <div class="bar-t"><div class="bar-f" id="bv" style="width:100%;background:#10b981"></div></div></div>
  <div class="pipe pipe-main" id="p3"></div>
  <div class="mod a0" id="m3"><div class="ml">Sampler</div><div class="mv" id="v3">\u25cb</div></div>
  <div class="pipe pipe-main" id="p4"></div>
  <div class="mod a0" id="m4"><div class="ml">Mixer</div><div class="mv" id="v4"></div></div>
  <div class="pipe pipe-main" id="p5"></div>
  <div class="mod a0" id="m5" style="min-width:60px"><div class="ml">Return</div><div class="mchk" id="v5"></div></div>
  <div class="pipe pipe-main" id="p6"></div>
  <span class="arrow-txt">Return</span>
</div>

<div class="byp"><div style="width:148px"></div><div class="byp-pipe"></div>
  <span class="byp-lbl">Cellular bypass (RBCs, WBCs, platelets)</span>
  <div class="byp-pipe"></div><div style="width:100px"></div></div>

<div id="bio">
  <div class="ch" id="c1">
    <div class="ch-t" style="color:#ef4444">CV1 \u2014 Plasma Compartment</div>
    <div class="ch-r"><span>NH\u2083</span><b id="c1n">-</b></div>
    <div class="ch-r"><span>Urea</span><b id="c1u">-</b></div>
    <div class="ch-r"><span>Volume</span><b>{v_cv1:.0f} mL</b></div>
    <div style="flex:1"></div>
    <div class="fx" style="color:#ef4444"><span>NH\u2083</span><span style="font-size:14px">\u2192</span><span>diffuses to CV2</span></div>
    <div class="fx" style="color:#0d9488"><span>Urea</span><span style="font-size:14px">\u2190</span><span>received from CV2</span></div>
  </div>
  <div id="mem">
    <div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div>
    <div class="mem-l">Membrane</div>
    <div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div><div class="mb"></div>
  </div>
  <div class="ch" id="c2">
    <div class="ch-t" style="color:#0d9488">CV2 \u2014 Hepatocyte Compartment</div>
    <div class="ch-r"><span>NH\u2083</span><b id="c2n">-</b></div>
    <div class="ch-r"><span>Urea</span><b id="c2u">-</b></div>
    <div class="ch-r"><span>Volume</span><b>{v_cv2:.0f} mL</b></div>
    <div style="flex:1"></div>
    <div class="fx" style="color:#10b981"><span>\u2699 Metabolism:</span><span style="margin-left:4px">2 NH\u2083 \u2192 1 Urea</span></div>
    <div class="fx" style="color:#6366f1"><span>\u2699 CYP450:</span><span style="margin-left:4px">1 Lido \u2192 1 MEGX</span></div>
  </div>
</div>

<div id="mets">
  <div class="mc"><div class="mc-l">Cell Viability</div><div class="mc-v" id="xv">-</div>
    <div class="mc-bt"><div class="mc-bf" id="xvb"></div></div></div>
  <div class="mc"><div class="mc-l">NH\u2083 Clearance</div><div class="mc-v" id="xc">-</div>
    <div class="mc-bt"><div class="mc-bf" id="xcb"></div></div></div>
  <div class="mc"><div class="mc-l">Outlet NH\u2083</div><div class="mc-v" id="xn">-</div></div>
  <div class="mc"><div class="mc-l">Outlet Lido</div><div class="mc-v" id="xl">-</div></div>
  <div class="mc"><div class="mc-l">Return Status</div><div class="mc-v" id="xr">-</div></div>
</div>

<div class="eq">dC/dt = (Q/V)(C_in \u2212 C) \u2212 (P_m \u00b7 A_m / V)\u0394C &nbsp;|&nbsp; 2 NH\u2083 \u2192 1 Urea &nbsp;|&nbsp; 1 Lido \u2192 1 MEGX</div>

<div id="ctl">
  <button id="pbtn">\u25b6 Play</button>
  <input id="scr" type="range" min="0" max="1" step="1" value="0">
  <span id="tl">t = 0 min</span>
</div>

</div>
<script>
(function(){{
  const D={data_json},N=D.length,INH3={inlet_nh3};
  if(!N)return;
  const $=id=>document.getElementById(id);
  let fi=0,play=false,aid=null,lt=0;
  $('scr').max=N-1;

  const AC=['a0','a1','a2','a3'];
  function sa(el,c){{AC.forEach(a=>el.classList.remove(a));el.classList.add(AC[Math.min(c,3)]);}}
  function tc(v,mx){{let r=Math.min(v/Math.max(mx,50),1);return`rgb(${{Math.round(239*r+16*(1-r))}},${{Math.round(68*r+185*(1-r))}},${{Math.round(68*r+129*(1-r))}})`;}}
  function bc(v,g,w){{return v>g?'#10b981':v>w?'#f59e0b':'#ef4444';}}

  function render(){{
    let d=D[fi];
    sa($('m0'),d.sep_state);$('v0').innerHTML='Q<sub>p</sub> '+d.sep_Q_plasma+'<br>Q<sub>c</sub> '+d.sep_Q_cells;
    sa($('m1'),d.pump_state);$('v1').textContent=d.pump_Q+' mL/min';
    sa($('m2'),d.bio_state);$('v2').innerHTML='NH\u2083 '+d.bio_nh3+' &nbsp; Lido '+d.bio_lido;
    let vb=d.bio_viability;$('bv').style.width=(vb*100)+'%';$('bv').style.background=bc(vb,.8,.6);
    sa($('m4'),d.mix_state);$('v4').innerHTML='Q '+d.mix_Q+'<br>Hct '+d.mix_Hct.toFixed(2);
    sa($('m5'),d.mon_state);$('v5').innerHTML=d.mon_approved?'<span style="color:#10b981">\u2713</span>':'<span style="color:#ef4444">\u2717</span>';
    for(let i=0;i<7;i++)$('p'+i).style.background=tc(i<3?INH3:d.bio_nh3,INH3);

    let i1=Math.min(d.bio_nh3_cv1/Math.max(INH3,50),1);
    $('c1').style.background='rgba(239,68,68,'+(0.05+i1*0.15).toFixed(2)+')';
    $('c1n').textContent=d.bio_nh3_cv1+' \u00b5mol/L';$('c1u').textContent=d.bio_urea_cv1+' mmol/L';
    let i2=Math.min(d.bio_nh3_cv2/Math.max(INH3,50),1);
    $('c2').style.background='rgba(13,148,136,'+(0.05+(1-i2)*0.15).toFixed(2)+')';
    $('c2n').textContent=d.bio_nh3_cv2+' \u00b5mol/L';$('c2u').textContent=d.bio_urea_cv2+' mmol/L';

    $('xv').textContent=(vb*100).toFixed(1)+'%';$('xv').style.color=bc(vb,.8,.6);
    $('xvb').style.width=(vb*100)+'%';$('xvb').style.background=bc(vb,.8,.6);
    let cl=d.bio_clearance;
    $('xc').textContent=(cl*100).toFixed(1)+'%';$('xc').style.color=bc(cl,.5,.3);
    $('xcb').style.width=(Math.min(cl,1)*100)+'%';$('xcb').style.background=bc(cl,.5,.3);
    $('xn').textContent=d.bio_nh3+' \u00b5mol/L';$('xn').style.color=d.bio_nh3<50?'#10b981':'#ef4444';
    $('xl').textContent=d.bio_lido+' \u00b5mol/L';$('xl').style.color=d.bio_lido<10?'#10b981':'#ef4444';
    $('xr').textContent=d.mon_approved?'APPROVED':'PENDING';$('xr').style.color=d.mon_approved?'#10b981':'#f59e0b';
  }}

  function tick(ts){{
    if(!play)return;
    if(ts-lt>100){{lt=ts;fi=Math.min(fi+1,N-1);$('scr').value=fi;$('tl').textContent='t = '+D[fi].t+' min';render();
      if(fi>=N-1){{play=false;$('pbtn').textContent='\u21bb Replay';}}
    }}
    aid=requestAnimationFrame(tick);
  }}

  $('pbtn').onclick=()=>{{
    if(play){{play=false;$('pbtn').textContent='\u25b6 Play';cancelAnimationFrame(aid);}}
    else{{if(fi>=N-1)fi=0;play=true;$('pbtn').textContent='\u23f8 Pause';lt=0;aid=requestAnimationFrame(tick);}}
  }};
  $('scr').oninput=()=>{{fi=+$('scr').value;$('tl').textContent='t = '+D[fi].t+' min';render();}};
  render();
}})();
</script></body></html>
"""
