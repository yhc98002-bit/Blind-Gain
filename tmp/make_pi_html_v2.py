#!/usr/bin/env python3
import json, os

OUT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/review_packages/pi_review_v2_20260811"
d = json.load(open(os.path.join(OUT, "examples.json")))

FAM_ORDER = [
 ("r19",      "R19 &mdash; FlipTrack v02r19 (frozen primary benchmark)"),
 ("r20",      "R20 &mdash; private twin (one-shot confirmatory)"),
 ("cue",      "Cue ladder &mdash; nine-series, 6 rungs (incl. unannotated)"),
 ("chart",    "Chart v08 calibration &mdash; legend-to-series"),
 ("chartnec", "Chart v08 necessity &mdash; annotation ablation (incl. unannotated)"),
 ("doc",      "Document vNext &mdash; dense table"),
 ("pv2probe", "premise-v2 &mdash; premise probe"),
 ("pv2causal","premise-v2 &mdash; causal pairs"),
 ("pv2inv",   "premise-v2 &mdash; invariance pairs"),
 ("b1",       "B1 premise probe v1 (frozen anchor)"),
 ("catch",    "Catch / distractor eval (mini-A5 catch-stability)"),
 ("legacy",   "Superseded FlipTrack lineage &mdash; not part of frozen R19/R20"),
 ("train",    "mini-A5 training corpus &mdash; not a benchmark"),
]
payload = json.dumps({"meta": d["meta"], "inventory": d["inventory"],
                      "examples": d["examples"], "famOrder": FAM_ORDER})

tpl = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BlindGain &mdash; benchmark review package (rebuild)</title>
<style>
:root{--bg:#fbfbfa;--fg:#1c1c1a;--mut:#6b6b66;--line:#dedcd6;--card:#fff;--accent:#3a5a8c;--code:#f4f3ef;--warn:#8a5a20}
@media(prefers-color-scheme:dark){:root{--bg:#141413;--fg:#e8e6e1;--mut:#9a9a93;--line:#33322e;--card:#1c1c1a;--accent:#8fb0dd;--code:#232320;--warn:#d9a760}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 20px}
h1{margin:0 0 3px;font-size:17px;font-weight:600}
.sub{color:var(--mut);font-size:12.5px}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:9px}
button.tab{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:5px 11px;border-radius:20px;cursor:pointer;font-size:12.5px}
button.tab[aria-pressed=true]{background:var(--accent);color:#fff;border-color:var(--accent)}
input[type=search]{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:5px 9px;border-radius:6px;font-size:12.5px;min-width:210px}
label.tg{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:5px;cursor:pointer}
main{padding:18px 20px 70px;max-width:1300px;margin:0 auto}
h2.sec{margin:26px 0 10px;font-size:15px;font-weight:600}
.gh{margin:30px 0 12px;font-size:14px;font-weight:600;padding-bottom:6px;border-bottom:1px solid var(--line)}
.gh .n{color:var(--mut);font-weight:400}
.vh{margin:18px 0 9px;font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent);font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:15px 17px;margin-bottom:16px}
.mrow{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:11px}
.m{font:11.5px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);border:1px solid var(--line);border-radius:4px;padding:2px 6px;color:var(--mut)}
.m b{color:var(--fg);font-weight:600}
.imgs{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:11px 0}
.imgs figure{margin:0}
.imgs figcaption{font:11.5px ui-monospace,monospace;color:var(--mut);margin-bottom:4px}
.imgs img{width:100%;height:auto;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:zoom-in;display:block}
.masks img{max-width:190px}
.q{margin:10px 0 4px}
.q .lab{font:11.5px ui-monospace,monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.q .txt{font-size:14.5px}
.gold{font:12.5px ui-monospace,monospace;color:var(--mut);margin-top:3px}
.gold b{color:var(--fg)}
table{width:100%;border-collapse:collapse;margin-top:11px;font-size:13px}
th,td{border:1px solid var(--line);padding:7px 9px;vertical-align:top;text-align:left}
th{background:var(--code);font-size:11.5px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0}
td.arm{white-space:nowrap;font-weight:600;font-size:12.5px}
pre{margin:0;font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;word-break:break-word;max-height:210px;overflow:auto}
.flags{margin-top:5px;display:flex;flex-wrap:wrap;gap:4px}
.f{font:11px ui-monospace,monospace;border:1px solid var(--line);border-radius:3px;padding:1px 5px;color:var(--mut);background:var(--code)}
.f.t{background:rgba(60,140,90,.13);border-color:rgba(60,140,90,.35)}
.f.f{background:rgba(180,70,60,.12);border-color:rgba(180,70,60,.32)}
.hidef .flags{display:none}
.none{color:var(--warn);font-size:12.5px;font-style:italic}
details{margin-top:10px}
details summary{cursor:pointer;font:11.5px ui-monospace,monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
details pre{margin-top:7px;max-height:340px;background:var(--code);padding:9px;border-radius:5px;border:1px solid var(--line);font-size:11.5px}
#invwrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
#inv{margin:0;font-size:12.5px;min-width:1050px}
#inv td{vertical-align:top}
#inv td.v{font:11.5px ui-monospace,monospace}
#inv td.st{font-size:12px}
#inv .src{display:block;color:var(--mut);font-size:10.5px;margin-top:3px;font-style:italic}
#inv tr.famstart td{border-top:2px solid var(--accent)}
.pill{font:10.5px ui-monospace,monospace;border-radius:3px;padding:1px 5px;border:1px solid var(--line);background:var(--code);color:var(--mut);white-space:nowrap}
.pill.no{color:var(--warn);border-color:var(--warn)}
dialog{border:none;background:transparent;max-width:96vw;max-height:96vh;padding:0}
dialog::backdrop{background:rgba(0,0,0,.82)}
dialog img{max-width:96vw;max-height:96vh;border-radius:6px;background:#fff}
.note{color:var(--mut);font-size:12.5px}
@media(max-width:760px){.imgs{grid-template-columns:1fr}}
</style></head><body>
<header>
  <h1>BlindGain &mdash; benchmark review package (rebuild)</h1>
  <div class="sub" id="sub"></div>
  <div class="bar" id="tabs"></div>
  <div class="bar">
    <input type="search" id="q" placeholder="filter by pair_id, template, question, answer&hellip;">
    <label class="tg"><input type="checkbox" id="fl" checked> scoring fields</label>
    <label class="tg"><input type="checkbox" id="im" checked> images</label>
    <span class="sub" id="count"></span>
  </div>
</header>
<main>
  <h2 class="sec" id="inventory">Inventory &mdash; task variants and the capability stage each covers</h2>
  <p class="note" id="invnote"></p>
  <div id="invwrap"><table id="inv"></table></div>
  <h2 class="sec">Examples</h2>
  <div id="main"></div>
</main>
<dialog id="lb"><img id="lbi" alt=""></dialog>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const esc=s=>(s==null?'':String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const flag=(k,v)=>v===undefined||v===null?'':`<span class="f ${v===true?'t':v===false?'f':''}">${k}=${esc(v)}</span>`;
const famLabel=k=>(D.famOrder.find(f=>f[0]===k)||[k,k])[1];

document.getElementById('sub').innerHTML=
 `${D.meta.n_examples} examples across ${D.meta.n_variants} task variants in ${D.famOrder.length} families &middot; `+
 `selection: ${esc(D.meta.selection_rule)}`;
document.getElementById('invnote').innerHTML=
 `Every distinct <code>template_id</code> found by scanning all <code>data/**.jsonl</code> manifests is listed &mdash; `+
 `including superseded lineage and training templates, and variants with no cached model outputs. `+
 `<b>cached outputs</b> names the arms that have predictions joined to this variant; `+
 `<b>n bench</b> is the full variant size, <b>n pkg</b> how many are shown below. `+
 `Capability-stage wording is quoted from the registered docs cited beneath it.`;

// ---- inventory table
(function(){
  let h='<thead><tr><th>family</th><th>variant</th><th>category</th><th>n bench</th><th>n pkg</th>'+
        '<th>cached outputs</th><th>capability stage covered</th></tr></thead><tbody>';
  let lastFam=null;
  D.famOrder.forEach(([fk,fl])=>{
    D.inventory.filter(i=>i.family===fk).forEach((i,idx)=>{
      const arms=i.arms_available.length
        ? i.arms_available.map(a=>`<span class="pill">${esc(a)}</span>`).join(' ')
        : '<span class="pill no">none</span>';
      h+=`<tr class="${idx===0?'famstart':''}">`+
         `<td>${idx===0?fl:''}</td>`+
         `<td class="v">${esc(i.variant_label)}${i.note?`<span class="src">${esc(i.note)}</span>`:''}</td>`+
         `<td class="v">${esc(i.category||'&mdash;')}</td>`+
         `<td>${i.n_in_benchmark}</td><td>${i.n_in_package}</td>`+
         `<td>${arms}</td>`+
         `<td class="st">${esc(i.capability_stage)}<span class="src">source: ${esc(i.stage_source)}</span></td></tr>`;
    });
  });
  document.getElementById('inv').innerHTML=h+'</tbody>';
})();

let group='all', term='', imgs=true;
const tabs=document.getElementById('tabs');
const cnt=k=>D.examples.filter(e=>k==='all'||e.family===k).length;
const mk=(k,l)=>`<button class="tab" data-g="${k}" aria-pressed="${group===k}">${l} <span style="opacity:.65">${cnt(k)}</span></button>`;
const tabsHtml=()=>mk('all','all')+D.famOrder.map(([k,l])=>mk(k,l.replace(/&mdash;.*/,'').trim())).join('');
tabs.innerHTML=tabsHtml();
tabs.addEventListener('click',e=>{const b=e.target.closest('button.tab');if(!b)return;group=b.dataset.g;tabs.innerHTML=tabsHtml();render()});
document.getElementById('q').addEventListener('input',e=>{term=e.target.value.toLowerCase();render()});
document.getElementById('fl').addEventListener('change',e=>document.body.classList.toggle('hidef',!e.target.checked));
document.getElementById('im').addEventListener('change',e=>{imgs=e.target.checked;render()});

function armTable(e){
  const names=Object.keys(e.arms);
  if(!names.length) return '<p class="none">no cached model outputs exist for this variant &mdash; benchmark item shown as-is</p>';
  const cell=(a,s)=>`<td><pre>${esc(a['prediction_'+s])}</pre>`+
    `<div class="flags">${flag('extracted_answer_'+s,a['extracted_answer_'+s])}${flag('correct_'+s,a['correct_'+s])}</div></td>`;
  return `<table><thead><tr><th>arm / condition</th><th>image A output</th><th>image B output</th></tr></thead><tbody>`+
    names.map(n=>{const a=e.arms[n];return `<tr><td class="arm">${esc(n)}`+
      `<div class="flags" style="margin-top:6px">${flag('pair_correct',a.pair_correct)}${flag('strict_pair_correct',a.strict_pair_correct)}${flag('contract_valid',a.contract_valid)}${flag('collapsed',a.collapsed)}</div>`+
      `</td>${cell(a,'a')}${cell(a,'b')}</tr>`}).join('')+`</tbody></table>`;
}
function card(e){
  const m=[['pair_id',e.pair_id],['template_id',e.template_id],['category',e.category],
           ['rung',e.rung],['intervention_type',e.intervention_type]]
    .filter(([,v])=>v!=null&&v!=='')
    .map(([k,v])=>`<span class="m">${k}=<b>${esc(v)}</b></span>`).join('');
  const im=imgs&&(e.image_a||e.image_b)?`<div class="imgs">
      ${e.image_a?`<figure><figcaption>image A</figcaption><img loading="lazy" src="${e.image_a}" alt="A"></figure>`:''}
      ${e.image_b?`<figure><figcaption>image B</figcaption><img loading="lazy" src="${e.image_b}" alt="B"></figure>`:''}</div>`:'';
  const mk_=imgs&&(e.mask_a||e.mask_b)?`<div class="imgs masks">
      ${e.mask_a?`<figure><figcaption>changed_region_mask_a</figcaption><img loading="lazy" src="${e.mask_a}" alt="mask A"></figure>`:''}
      ${e.mask_b?`<figure><figcaption>changed_region_mask_b</figcaption><img loading="lazy" src="${e.mask_b}" alt="mask B"></figure>`:''}</div>`:'';
  const prem=e.premise_question?`<div class="q"><span class="lab">premise question</span><div class="txt">${esc(e.premise_question)}</div>`+
      `<div class="gold">premise_answer_a=<b>${esc(e.premise_gold_a)}</b>${e.premise_gold_b!=null?` &nbsp; premise_answer_b=<b>${esc(e.premise_gold_b)}</b>`:''}</div></div>`:'';
  return `<div class="card"><div class="mrow">${m}</div>${im}${mk_}${prem}`+
    `<div class="q"><span class="lab">question</span><div class="txt">${esc(e.question)}</div>`+
    `<div class="gold">answer_a=<b>${esc(e.gold_a)}</b> &nbsp; answer_b=<b>${esc(e.gold_b)}</b></div></div>`+
    armTable(e)+
    `<details><summary>full manifest record (${esc(e.manifest)})</summary><pre>${esc(JSON.stringify(e.record,null,1))}</pre></details>`+
    `</div>`;
}
function render(){
  const sel=D.examples.filter(e=>(group==='all'||e.family===group)&&(!term||JSON.stringify(e).toLowerCase().includes(term)));
  document.getElementById('count').textContent=`showing ${sel.length}`;
  let h='';
  D.famOrder.forEach(([fk,fl])=>{
    const inFam=sel.filter(e=>e.family===fk);
    if(!inFam.length)return;
    h+=`<div class="gh">${fl} <span class="n">&mdash; ${inFam.length}</span></div>`;
    const vs=[];inFam.forEach(e=>{if(!vs.includes(e.variant))vs.push(e.variant)});
    vs.forEach(v=>{
      const items=inFam.filter(e=>e.variant===v);
      h+=`<div class="vh">${esc(items[0].variant_label)}</div>`+items.map(card).join('');
    });
  });
  document.getElementById('main').innerHTML=h||'<p class="note">no examples match.</p>';
}
document.getElementById('main').addEventListener('click',e=>{
  const i=e.target.closest('.imgs img');if(!i)return;
  document.getElementById('lbi').src=i.src;document.getElementById('lb').showModal();
});
document.getElementById('lb').addEventListener('click',()=>document.getElementById('lb').close());
render();
</script></body></html>"""

open(os.path.join(OUT, "index.html"), "w").write(tpl.replace("__PAYLOAD__", payload))
print("wrote index.html", os.path.getsize(os.path.join(OUT, "index.html")), "bytes")
