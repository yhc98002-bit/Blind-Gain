#!/usr/bin/env python3
import json, os, html

OUT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/review_packages/pi_review_20260811"
d = json.load(open(os.path.join(OUT, "examples.json")))
meta, examples = d["meta"], d["examples"]

GROUPS = [
    ("r19_primary", "R19 &mdash; primary visual anchor (search + binding)"),
    ("r19_oracle",  "R19 &mdash; oracle-localized readout control"),
    ("r20_coord",   "R20 private twin &mdash; coordinate register"),
    ("r20_starred", "R20 private twin &mdash; starred series"),
    ("r20_header",  "R20 private twin &mdash; header-cued table"),
    ("premise_v2",  "premise-v2 (track4 dev)"),
]
ARMS = [("base", "base"), ("standard_grpo", "standard GRPO"), ("cp", "CP")]

payload = json.dumps({"meta": meta, "examples": examples, "groups": GROUPS, "arms": ARMS})

tpl = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BlindGain &mdash; PI review package</title>
<style>
:root{--bg:#fbfbfa;--fg:#1c1c1a;--mut:#6b6b66;--line:#dedcd6;--card:#fff;--accent:#3a5a8c;--code:#f4f3ef}
@media(prefers-color-scheme:dark){:root{--bg:#141413;--fg:#e8e6e1;--mut:#9a9a93;--line:#33322e;--card:#1c1c1a;--accent:#8fb0dd;--code:#232320}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 20px}
h1{margin:0 0 3px;font-size:17px;font-weight:600}
.sub{color:var(--mut);font-size:12.5px}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:10px}
button.tab{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:5px 11px;border-radius:20px;cursor:pointer;font-size:12.5px}
button.tab[aria-pressed=true]{background:var(--accent);color:#fff;border-color:var(--accent)}
input[type=search]{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:5px 9px;border-radius:6px;font-size:12.5px;min-width:200px}
label.tg{font-size:12.5px;color:var(--mut);display:flex;align-items:center;gap:5px;cursor:pointer}
main{padding:18px 20px 60px;max-width:1250px;margin:0 auto}
.gh{margin:30px 0 12px;font-size:14px;font-weight:600;letter-spacing:.02em;padding-bottom:6px;border-bottom:1px solid var(--line)}
.gh .n{color:var(--mut);font-weight:400}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:15px 17px;margin-bottom:16px}
.mrow{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:11px}
.m{font:11.5px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);border:1px solid var(--line);border-radius:4px;padding:2px 6px;color:var(--mut)}
.m b{color:var(--fg);font-weight:600}
.imgs{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:11px 0}
.imgs figure{margin:0}
.imgs figcaption{font:11.5px ui-monospace,monospace;color:var(--mut);margin-bottom:4px}
.imgs img{width:100%;height:auto;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:zoom-in;display:block}
.q{margin:10px 0 4px}
.q .lab{font:11.5px ui-monospace,monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.q .txt{font-size:14.5px}
.gold{font:12.5px ui-monospace,monospace;color:var(--mut);margin-top:3px}
.gold b{color:var(--fg)}
table{width:100%;border-collapse:collapse;margin-top:11px;font-size:13px}
th,td{border:1px solid var(--line);padding:7px 9px;vertical-align:top;text-align:left}
th{background:var(--code);font-size:11.5px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
td.arm{white-space:nowrap;font-weight:600;font-size:12.5px}
pre{margin:0;font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;word-break:break-word;max-height:220px;overflow:auto}
.flags{margin-top:5px;display:flex;flex-wrap:wrap;gap:4px}
.f{font:11px ui-monospace,monospace;border:1px solid var(--line);border-radius:3px;padding:1px 5px;color:var(--mut);background:var(--code)}
.f.t{background:rgba(60,140,90,.13);border-color:rgba(60,140,90,.35)}
.f.f{background:rgba(180,70,60,.12);border-color:rgba(180,70,60,.32)}
.hidef .flags{display:none}
.probe{margin-top:13px;border-top:1px dashed var(--line);padding-top:10px}
.probe h4{margin:0 0 5px;font:11.5px ui-monospace,monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
dialog{border:none;background:transparent;max-width:96vw;max-height:96vh;padding:0}
dialog::backdrop{background:rgba(0,0,0,.82)}
dialog img{max-width:96vw;max-height:96vh;border-radius:6px;background:#fff}
.note{color:var(--mut);font-size:12.5px;margin:0 0 6px}
@media(max-width:760px){.imgs{grid-template-columns:1fr}table,thead,tbody,th,td,tr{display:block}th{display:none}td{border-top:none}td.arm{border-top:1px solid var(--line);background:var(--code)}}
</style></head><body>
<header>
  <h1>BlindGain &mdash; PI review package</h1>
  <div class="sub" id="sub"></div>
  <div class="bar" id="tabs"></div>
  <div class="bar">
    <input type="search" id="q" placeholder="filter by pair_id, question, answer text&hellip;">
    <label class="tg"><input type="checkbox" id="fl" checked> show scoring fields</label>
    <label class="tg"><input type="checkbox" id="im" checked> show images</label>
    <span class="sub" id="count"></span>
  </div>
</header>
<main id="main"></main>
<dialog id="lb"><img id="lbi" alt=""></dialog>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const esc=s=>(s==null?'':String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const flag=(k,v)=>v===undefined||v===null?'':`<span class="f ${v===true?'t':v===false?'f':''}">${k}=${esc(v)}</span>`;
document.getElementById('sub').innerHTML=
 `${D.meta.n_examples} examples &middot; arms: base &middot; standard GRPO &middot; CP &middot; `+
 `selection: ${esc(D.meta.selection_rule)}`;

let group='all', term='';
const tabs=document.getElementById('tabs');
const mk=(k,l,n)=>`<button class="tab" data-g="${k}" aria-pressed="${group===k}">${l}${n!==undefined?` <span style="opacity:.65">${n}</span>`:''}</button>`;
function counts(k){return D.examples.filter(e=>k==='all'||e.group===k).length}
function tabsHtml(){return mk('all','all',counts('all'))+D.groups.map(([k,l])=>mk(k,l,counts(k))).join('')}
tabs.innerHTML=tabsHtml();
tabs.addEventListener('click',e=>{const b=e.target.closest('button.tab');if(!b)return;group=b.dataset.g;tabs.innerHTML=tabsHtml();render()});
document.getElementById('q').addEventListener('input',e=>{term=e.target.value.toLowerCase();render()});
document.getElementById('fl').addEventListener('change',e=>document.body.classList.toggle('hidef',!e.target.checked));
document.getElementById('im').addEventListener('change',e=>{imgs=e.target.checked;render()});
let imgs=true;

function armRow(name,a){
  if(!a)return `<tr><td class="arm">${name}</td><td colspan="2" style="color:var(--mut)">no record</td></tr>`;
  const cell=(s)=>`<td><pre>${esc(a['prediction_'+s])}</pre>`+
    `<div class="flags">${flag('extracted_answer_'+s,a['extracted_answer_'+s])}${flag('correct_'+s,a['correct_'+s])}</div></td>`;
  return `<tr><td class="arm">${name}`+
    `<div class="flags" style="margin-top:6px">${flag('pair_correct',a.pair_correct)}${flag('strict_pair_correct',a.strict_pair_correct)}${flag('contract_valid',a.contract_valid)}${flag('collapsed',a.collapsed)}${flag('extraction_level',a.extraction_level)}</div>`+
    `</td>${cell('a')}${cell('b')}</tr>`;
}
function probeTable(p){
  const cell=(s)=>`<td><pre>${esc(p['prediction_'+s])}</pre>`+
    `<div class="flags">${flag('extracted_answer_'+s,p['extracted_answer_'+s])}${flag('correct_'+s,p['correct_'+s])}</div></td>`;
  return `<div class="q"><span class="lab">question</span><div class="txt">${esc(p.question)}</div>`+
   `<div class="gold">gold_a=<b>${esc(p.gold_a)}</b> &nbsp; gold_b=<b>${esc(p.gold_b)}</b></div></div>`+
   `<table><thead><tr><th>arm</th><th>image A output</th><th>image B output</th></tr></thead><tbody>`+
   `<tr><td class="arm">base<div class="flags" style="margin-top:6px">${flag('pair_correct',p.pair_correct)}${flag('strict_pair_correct',p.strict_pair_correct)}${flag('contract_valid',p.contract_valid)}${flag('collapsed',p.collapsed)}</div></td>${cell('a')}${cell('b')}</tr>`+
   `</tbody></table>`;
}
function card(e){
  const m=[['pair_id',e.pair_id],['template_id',e.template_id],['category',e.category],
           ['intervention_type',e.intervention_type],['split',e.split],
           ['scene_program_id',e.scene_program_id],['source_pair_id',e.source_pair_id],
           ['eval_image_mode',e.eval_image_mode],['prompt_contract_id',e.prompt_contract_id]]
    .filter(([,v])=>v!=null&&v!=='')
    .map(([k,v])=>`<span class="m">${k}=<b>${esc(v)}</b></span>`).join('');
  const role=e.task_role?`<span class="m">task_role=<b>${esc(e.task_role)}</b></span>`:'';
  const im=imgs&&(e.image_a||e.image_b)?`<div class="imgs">
      ${e.image_a?`<figure><figcaption>image A</figcaption><img loading="lazy" src="${e.image_a}" alt="image A"></figure>`:''}
      ${e.image_b?`<figure><figcaption>image B</figcaption><img loading="lazy" src="${e.image_b}" alt="image B"></figure>`:''}
    </div>`:'';
  let body;
  if(e.group==='premise_v2'){
    body=`<div class="probe"><h4>probe: premise_probe</h4>${probeTable(e.probes.premise_probe)}</div>`+
         `<div class="probe"><h4>probe: final</h4>${probeTable(e.probes.final)}</div>`;
  }else{
    body=`<div class="q"><span class="lab">question</span><div class="txt">${esc(e.question)}</div>`+
      `<div class="gold">gold_a=<b>${esc(e.gold_a)}</b> &nbsp; gold_b=<b>${esc(e.gold_b)}</b></div></div>`+
      `<table><thead><tr><th>arm</th><th>image A output</th><th>image B output</th></tr></thead><tbody>`+
      D.arms.map(([k,l])=>armRow(l,e.arms[k])).join('')+`</tbody></table>`;
  }
  return `<div class="card"><div class="mrow">${role}${m}</div>${im}${body}</div>`;
}
function render(){
  const sel=D.examples.filter(e=>(group==='all'||e.group===group)&&(!term||JSON.stringify(e).toLowerCase().includes(term)));
  const byG={};sel.forEach(e=>(byG[e.group]=byG[e.group]||[]).push(e));
  document.getElementById('count').textContent=`showing ${sel.length}`;
  document.getElementById('main').innerHTML=D.groups.filter(([k])=>byG[k])
    .map(([k,l])=>`<div class="gh">${l} <span class="n">&mdash; ${byG[k].length}</span></div>`+byG[k].map(card).join(''))
    .join('')||'<p class="note">no examples match.</p>';
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
