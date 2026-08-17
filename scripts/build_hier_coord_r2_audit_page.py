#!/usr/bin/env python3
"""Build the hier_coord_v1 r2 human-audit page: ONE self-contained HTML file
(images embedded as data URIs, all CSS/JS inline, no folder picker, no
network) for the HB.8 human audit of the re-rendered coordinate family.

Sample rule (no RNG, R19/R20 discipline): the first N mother-items per
(cell, role) in frozen L3 manifest order. Target-switch mothers carry L3 +
probe only (Amendment A2), so their cards show the L3 pair alone.

The page is a DESIGN audit instrument: legibility, cue visibility and
placement, in-image text neutrality, layer semantics, and counterfactual
minimality. Golds sit behind a per-item reveal so the reviewer can attempt
the item first. Findings export as JSON from the page itself.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "hier_coord_v1"
CELLS = ("n8", "n12", "n20")
ROLES = ("target_switch", "target_stable", "invariance")
LAYERS = ("l3", "l2", "l1", "probe")

CHECKS = [
    ("labels_legible", "Every point label is legible and unoccluded at 100% zoom"),
    ("cue_visible", "L1 cue is clearly visible and unambiguously indicates ONE point"),
    ("cue_disjoint", "L1 cue touches/overlaps no point, label, gridline or axis"),
    ("text_neutral", "In-image text states no task procedure and names no target"),
    ("layer_semantics", "L3 withholds the target identity; L2/L1 name it"),
    ("counterfactual_minimal", "The two sides differ only by the intended scene edit"),
]


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def scene_diff(scene_a: list, scene_b: list) -> list[str]:
    a = {row[0]: (row[1], row[2]) for row in scene_a}
    b = {row[0]: (row[1], row[2]) for row in scene_b}
    out = []
    for label in sorted(set(a) | set(b)):
        if label not in a:
            out.append(f"{label}: absent on A, {b[label]} on B")
        elif label not in b:
            out.append(f"{label}: {a[label]} on A, absent on B")
        elif a[label] != b[label]:
            out.append(f"{label}: {a[label]} on A -> {b[label]} on B")
    return out


def build_items(data_dir: Path, per_cell_role: int) -> list[dict]:
    items = []
    for cell in CELLS:
        rows = {}
        for layer in LAYERS:
            path = data_dir / f"manifest_{FAMILY}_{cell}_{layer}.jsonl"
            rows[layer] = [json.loads(l) for l in path.read_text().splitlines()
                           if l.strip()]
        by_mother = {layer: {r["mother_item_id"]: r for r in rows[layer]}
                     for layer in LAYERS}
        picked: dict[str, list] = {}
        for row in rows["l3"]:
            bucket = picked.setdefault(row["role"], [])
            if len(bucket) < per_cell_role:
                bucket.append(row)
        for role in ROLES:
            for l3 in picked.get(role, []):
                mid = l3["mother_item_id"]
                l1 = by_mother["l1"].get(mid)
                l2 = by_mother["l2"].get(mid)
                probe = by_mother["probe"].get(mid)
                item = {
                    "mother_item_id": mid,
                    "cell": cell,
                    "role": role,
                    "l3_question": l3["question"],
                    "l2_question": l2["question"] if l2 else None,
                    "l1_question": l1["question"] if l1 else None,
                    "probe_question": probe["question"] if probe else None,
                    "l3_a": data_uri(Path(l3["image_a_path"])),
                    "l3_b": data_uri(Path(l3["image_b_path"])),
                    "l1_a": data_uri(Path(l1["image_a_path"])) if l1 else None,
                    "l1_b": data_uri(Path(l1["image_b_path"])) if l1 else None,
                    "gold": {
                        "answer_a": l3["answer_a"],
                        "answer_b": l3["answer_b"],
                        "target_a": l3["verifier_results"]["target_label_a"],
                        "target_b": l3["verifier_results"]["target_label_b"],
                        "extremum_kind": l3["verifier_results"]["extremum_kind"],
                        "probe_gold_a": probe["answer_a"] if probe else None,
                        "probe_gold_b": probe["answer_b"] if probe else None,
                        "semantic_side_swapped":
                            l3["provenance"]["semantic_side_assignment_swapped"],
                        "scene_diff": scene_diff(l3["scene_a"], l3["scene_b"]),
                        "cue": (l1["verifier_results"].get("cue") if l1 else None),
                        "l2_identical_to_l3": bool(
                            l2 and l2["image_a_sha256"] == l3["image_a_sha256"]
                            and l2["image_b_sha256"] == l3["image_b_sha256"]),
                    },
                }
                items.append(item)
    return items


PAGE_CSS = """
:root{color-scheme:light;--ink:#1b241f;--muted:#5d6b64;--line:#ccd4cf;
--surface:#fff;--canvas:#f2f5f3;--accent:#0b6b4f;--warn:#8a5a00;--flag:#b42318}
*{box-sizing:border-box}
body{margin:0;background:var(--canvas);color:var(--ink);
font:15px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:#16211d;color:#eef4f0;padding:18px 24px;position:sticky;top:0;z-index:20;
box-shadow:0 1px 0 rgba(0,0,0,.2)}
header h1{margin:0 0 4px;font-size:19px}
header p{margin:2px 0;font-size:13px;color:#b9c8c1;max-width:1100px}
.bar{display:flex;gap:12px;align-items:center;margin-top:10px;flex-wrap:wrap}
button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:4px;
background:var(--surface);color:var(--ink);cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button:hover{filter:brightness(.97)}
main{padding:20px 24px 80px;max-width:1500px;margin:0 auto}
.intro{background:var(--surface);border:1px solid var(--line);border-radius:6px;
padding:16px 20px;margin-bottom:20px}
.intro h2{margin:0 0 8px;font-size:16px}
.intro ul{margin:6px 0;padding-left:20px}
.intro code{background:var(--canvas);padding:1px 5px;border-radius:3px;font-size:13px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:6px;
margin-bottom:22px;overflow:hidden}
.card.flagged{border-color:var(--flag);box-shadow:0 0 0 2px #fdecea}
.card>h3{margin:0;padding:12px 18px;background:#eef2f0;font-size:15px;
display:flex;gap:12px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line)}
.tag{font-size:12px;padding:2px 8px;border-radius:10px;background:#dde6e1;color:#31463d}
.tag.role{background:#dbe7f5;color:#22405e}
.body{padding:16px 18px}
.layer{margin-bottom:18px}
.layer h4{margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;
color:var(--muted)}
.q{font-size:14px;margin:0 0 8px;padding:8px 10px;background:var(--canvas);
border-left:3px solid var(--accent);border-radius:0 4px 4px 0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.pane{border:1px solid var(--line);border-radius:4px;overflow:hidden;background:#fbfcfb}
.pane figcaption{font-size:12px;color:var(--muted);padding:4px 8px;border-bottom:1px solid var(--line)}
.pane img{width:100%;display:block;cursor:zoom-in}
.note{font-size:12.5px;color:var(--muted);margin:6px 0 0}
.checks{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.checks label{display:flex;gap:8px;align-items:flex-start;margin:4px 0;font-size:13.5px}
.checks input{margin-top:3px}
textarea{width:100%;min-height:52px;margin-top:8px;padding:8px;border:1px solid var(--line);
border-radius:4px;font:inherit;resize:vertical}
.gold{margin-top:12px;font-size:13.5px}
.gold pre{background:#f7faf8;border:1px solid var(--line);border-radius:4px;padding:10px;
overflow:auto;font-size:12.5px;margin:6px 0 0}
#zoom{position:fixed;inset:0;background:rgba(12,18,15,.92);display:none;z-index:50;
overflow:auto;cursor:zoom-out}
#zoom img{display:block;margin:20px auto;image-rendering:pixelated}
#zoom .hint{position:fixed;top:10px;left:50%;transform:translateX(-50%);color:#dfe9e4;
font-size:13px;background:rgba(0,0,0,.5);padding:4px 12px;border-radius:12px}
footer{position:fixed;bottom:0;left:0;right:0;background:#16211d;color:#dfe9e4;
padding:8px 24px;font-size:13px;display:flex;gap:16px;align-items:center;z-index:20}
"""

PAGE_JS = """
const ITEMS = window.__AUDIT_ITEMS__;
const CHECKS = window.__AUDIT_CHECKS__;
const KEY = 'hier_coord_r2_audit_v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { state = {}; }

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  render();
}
function render() {
  let done = 0;
  ITEMS.forEach(it => {
    const s = state[it.mother_item_id] || {};
    const all = CHECKS.every(c => s[c[0]] === true);
    if (all) done++;
    const card = document.getElementById('card-' + it.mother_item_id);
    if (card) card.classList.toggle('flagged', !!s.flag);
  });
  document.getElementById('progress').textContent =
    done + ' / ' + ITEMS.length + ' items fully checked';
  const flagged = Object.values(state).filter(s => s && s.flag).length;
  document.getElementById('flagcount').textContent = flagged + ' flagged';
}
function toggle(mid, key, value) {
  state[mid] = state[mid] || {};
  state[mid][key] = value;
  save();
}
function note(mid, value) {
  state[mid] = state[mid] || {};
  state[mid].note = value;
  save();
}
function revealAll() {
  document.querySelectorAll('.gold').forEach(g => { g.style.display = 'block'; });
}
function exportFindings() {
  const rows = ITEMS.map(it => {
    const s = state[it.mother_item_id] || {};
    const checks = {};
    CHECKS.forEach(c => { checks[c[0]] = s[c[0]] === true; });
    return {
      mother_item_id: it.mother_item_id, cell: it.cell, role: it.role,
      checks: checks, all_pass: CHECKS.every(c => s[c[0]] === true),
      flagged: !!s.flag, note: s.note || ''
    };
  });
  const payload = {
    schema_version: 'blind-gains.hier-coord-r2-human-audit-findings.v1',
    instrument: window.__AUDIT_META__,
    reviewed_utc: new Date().toISOString(),
    reviewer: document.getElementById('reviewer').value || '(unnamed)',
    n_items: rows.length,
    n_all_pass: rows.filter(r => r.all_pass).length,
    n_flagged: rows.filter(r => r.flagged).length,
    items: rows
  };
  // data: URI rather than blob: — a page served from file:// under
  // default-src 'none' can have blob: navigation blocked in some browsers.
  const a = document.createElement('a');
  a.href = 'data:application/json;charset=utf-8,' +
           encodeURIComponent(JSON.stringify(payload, null, 2));
  a.download = 'hier_coord_r2_audit_findings.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
}
function zoomImage(src) {
  const z = document.getElementById('zoom');
  z.querySelector('img').src = src;
  z.style.display = 'block';
  z.scrollTop = 0;
}
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('zoom').addEventListener('click', e => {
    e.currentTarget.style.display = 'none';
  });
  document.querySelectorAll('.pane img').forEach(img => {
    img.addEventListener('click', () => zoomImage(img.src));
  });
  document.querySelectorAll('[data-reveal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const g = document.getElementById('gold-' + btn.dataset.reveal);
      g.style.display = g.style.display === 'block' ? 'none' : 'block';
    });
  });
  document.querySelectorAll('[data-check]').forEach(box => {
    const [mid, key] = box.dataset.check.split('|');
    const s = state[mid] || {};
    box.checked = s[key] === true;
    box.addEventListener('change', () => toggle(mid, key, box.checked));
  });
  document.querySelectorAll('[data-flag]').forEach(box => {
    const mid = box.dataset.flag;
    box.checked = (state[mid] || {}).flag === true;
    box.addEventListener('change', () => toggle(mid, 'flag', box.checked));
  });
  document.querySelectorAll('[data-note]').forEach(area => {
    const mid = area.dataset.note;
    area.value = (state[mid] || {}).note || '';
    area.addEventListener('input', () => note(mid, area.value));
  });
  document.getElementById('revealall').addEventListener('click', revealAll);
  document.getElementById('export').addEventListener('click', exportFindings);
  render();
});
"""


def render_card(item: dict) -> str:
    mid = item["mother_item_id"]
    esc = html.escape
    parts = [f'<section class="card" id="card-{esc(mid)}">',
             f'<h3><span class="tag">{esc(item["cell"])}</span>'
             f'<span class="tag role">{esc(item["role"])}</span>'
             f'<code>{esc(mid)}</code></h3>', '<div class="body">']
    parts += ['<div class="layer"><h4>L3 — discovery (identity withheld)</h4>',
              f'<p class="q">{esc(item["l3_question"])}</p>',
              '<div class="pair">',
              f'<figure class="pane"><figcaption>side A</figcaption>'
              f'<img src="{item["l3_a"]}" alt="L3 side A"></figure>',
              f'<figure class="pane"><figcaption>side B</figcaption>'
              f'<img src="{item["l3_b"]}" alt="L3 side B"></figure>',
              '</div>']
    if item["l2_question"]:
        parts.append(f'<p class="note"><b>L2 — grounding</b> (same images, byte-identical): '
                     f'{esc(item["l2_question"])}</p>')
    if item["probe_question"]:
        parts.append(f'<p class="note"><b>Discovery probe</b> (same images): '
                     f'{esc(item["probe_question"])}</p>')
    parts.append('</div>')
    if item["l1_a"]:
        parts += ['<div class="layer"><h4>L1 — readout (location cue added)</h4>',
                  f'<p class="q">{esc(item["l1_question"] or "")}</p>',
                  '<div class="pair">',
                  f'<figure class="pane"><figcaption>side A + cue</figcaption>'
                  f'<img src="{item["l1_a"]}" alt="L1 side A"></figure>',
                  f'<figure class="pane"><figcaption>side B + cue</figcaption>'
                  f'<img src="{item["l1_b"]}" alt="L1 side B"></figure>',
                  '</div></div>']
    else:
        parts.append('<p class="note"><b>No L1/L2 rows by design</b> — a target-switch '
                     'pair admits no single truthful identity-given question, so it '
                     'derives at L3 only (Amendment A2). Please confirm this is the '
                     'right call for this item.</p>')
    parts.append('<div class="checks">')
    for key, label in CHECKS:
        parts.append(f'<label><input type="checkbox" data-check="{esc(mid)}|{key}">'
                     f'<span>{esc(label)}</span></label>')
    parts.append(f'<label><input type="checkbox" data-flag="{esc(mid)}">'
                 f'<span><b>Flag this item for the PI</b></span></label>')
    parts.append(f'<textarea data-note="{esc(mid)}" placeholder="Notes on this item '
                 '(what is wrong, what to change)"></textarea>')
    parts.append(f'<p><button data-reveal="{esc(mid)}">Reveal gold / construction</button></p>')
    gold = json.dumps(item["gold"], indent=2, sort_keys=True)
    parts.append(f'<div class="gold" id="gold-{esc(mid)}" style="display:none">'
                 f'<pre>{esc(gold)}</pre></div>')
    parts.append('</div></div></section>')
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_v1_dev_r2")
    parser.add_argument("--per-cell-role", type=int, default=3)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/review_packages/"
                                       "hier_coord_r2_human_audit_20260817.html")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/hier_coord_r2_audit_page_v1.json")
    args = parser.parse_args()
    for path in (args.output, args.report):
        if path.exists():
            raise FileExistsError(path)

    items = build_items(args.data_dir, args.per_cell_role)
    meta = {
        "instrument": "hier_coord_r2_human_audit",
        "render_rev": "r2-footer-neutral",
        "data_dir": str(args.data_dir),
        "family": FAMILY,
        "selection_rule": f"first {args.per_cell_role} mother-items per (cell, role) "
                          "in frozen L3 manifest order (no RNG)",
        "n_items": len(items),
        "registered_in_image_text": {
            "title": "Coordinate Survey Register",
            "footer": "Each point is identified by its printed label."},
        "retired_v1_footer": "Locate the requested label, then read its coordinate "
                             "from the numbered axes.",
    }
    body = "".join(render_card(item) for item in items)
    stripped = [{k: v for k, v in item.items()
                 if k not in ("l3_a", "l3_b", "l1_a", "l1_b")} for item in items]
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>hier_coord_v1 r2 — human audit (HB.8)</title>
<style>{PAGE_CSS}</style></head><body>
<header>
<h1>hier_coord_v1 — human audit of the r2 render (HB.8 freeze prerequisite)</h1>
<p>Sample: {meta['selection_rule']} — {len(items)} mother-items across n8 / n12 / n20.
Images are the <b>r2</b> re-render (footer corrected); scenes, questions, answers and
cues are unchanged from v1.</p>
<p>Click any image to inspect it at 100% natural size (1400&times;1240) — judge legibility there, not in the fitted view.</p>
<div class="bar">
<label>Reviewer: <input id="reviewer" placeholder="name" style="padding:5px 8px;border-radius:4px;border:1px solid #4a5b54;background:#0f1815;color:#eef4f0"></label>
<button id="revealall">Reveal all golds</button>
<button id="export" class="primary">Export findings JSON</button>
</div></header>
<main>
<section class="intro">
<h2>What to check, and why this audit exists</h2>
<p>The intended capability hierarchy: <b>L1 readout</b> (target <i>location</i> given) &middot;
<b>L2 grounding</b> (target <i>identity</i> given, model must find it) &middot;
<b>L3 discovery</b> (model must determine <i>which</i> target is relevant). The discovery
probe isolates the L3 selection step.</p>
<ul>
<li>The v1 images carried the footer <code>{html.escape(meta['retired_v1_footer'])}</code> — the L2
procedure printed inside every image, including L3 and probe images that withhold the
label. It is retired. The registered footer is now
<code>{html.escape(meta['registered_in_image_text']['footer'])}</code>; please confirm it states no
task procedure and gives away no target.</li>
<li><b>Legibility</b>: every point label readable, no overlaps, at 100% zoom (n20 is the
crowded cell).</li>
<li><b>Cue</b> (L1 only): visible, unambiguous about which point it marks, and touching
no ink (it must not occlude points, labels, gridlines or axes).</li>
<li><b>Layer semantics</b>: the L3 question must not name the target; L2/L1 must.</li>
<li><b>Counterfactual</b>: the two sides should differ only by the intended scene edit —
reveal the gold to see the exact recorded difference.</li>
</ul>
<p>Golds are hidden per item so you can attempt the item first. Your checkboxes and notes
are kept in this browser; <b>Export findings JSON</b> writes them to a file for the record.</p>
</section>
{body}
</main>
<div id="zoom"><span class="hint">100% natural size — click anywhere to close</span><img alt="zoomed"></div>
<footer><span id="progress">0 / 0</span><span id="flagcount">0 flagged</span>
<span style="color:#9fb3aa">hier_coord_v1 &middot; r2-footer-neutral &middot; {len(items)} items</span></footer>
<script>window.__AUDIT_ITEMS__={json.dumps(stripped)};
window.__AUDIT_CHECKS__={json.dumps(CHECKS)};
window.__AUDIT_META__={json.dumps(meta)};</script>
<script>{PAGE_JS}</script>
</body></html>
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    report = {"schema_version": "blind-gains.hier-coord-r2-audit-page.v1",
              **meta,
              "output": str(args.output),
              "output_sha256": digest,
              "output_bytes": args.output.stat().st_size,
              "items": [{"mother_item_id": i["mother_item_id"], "cell": i["cell"],
                         "role": i["role"]} for i in items]}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"n_items": len(items), "bytes": report["output_bytes"],
                      "sha256": digest, "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
