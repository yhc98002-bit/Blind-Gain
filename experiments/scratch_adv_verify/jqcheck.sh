#!/usr/bin/env bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
D=data/track4_premise_v2_dev_v1
S="$D/manifest_causal_pairs.jsonl"
R="$D/caption_qa_inputs/manifest.jsonl"
K="$D/caption_qa_inputs/key.jsonl"

echo "=== jq: full-set field diff (all 160 pairs), release ==="
jq -s --slurpfile src "$S" '
  ($src | map({key:.pair_id, value:.}) | from_entries) as $S
  | map(. as $r
      | $S[$r.pair_id] as $s
      | {pair_id: $r.pair_id,
         q:      ($r.question == $s.question),
         sha_a:  (($r.members[]|select(.member_id==($r.pair_id+"_a"))|.image_sha256) == $s.image_a_sha256),
         sha_b:  (($r.members[]|select(.member_id==($r.pair_id+"_b"))|.image_sha256) == $s.image_b_sha256),
         pa:     (($r.members[]|select(.member_id==($r.pair_id+"_a"))|.image_path) == ("../" + ($s.image_a_path | sub("^data/track4_premise_v2_dev_v1/";"")))),
         pb:     (($r.members[]|select(.member_id==($r.pair_id+"_b"))|.image_path) == ("../" + ($s.image_b_path | sub("^data/track4_premise_v2_dev_v1/";"")))),
         sv:     ($r.schema_version)})
  | {n: length,
     q_ok: (map(select(.q))|length),
     sha_a_ok: (map(select(.sha_a))|length),
     sha_b_ok: (map(select(.sha_b))|length),
     pa_ok: (map(select(.pa))|length),
     pb_ok: (map(select(.pb))|length),
     schema_versions: (map(.sv)|unique)}
' "$R"

echo "=== jq: full-set field diff (all 160 pairs), key ==="
jq -s --slurpfile src "$S" '
  ($src | map({key:.pair_id, value:.}) | from_entries) as $S
  | map(. as $k
      | $S[$k.pair_id] as $s
      | {tid: ($k.template_id == $s.template_id),
         cat: ($k.category == $s.category),
         ctw: ($k.catch_twin_id == $s.catch_twin_id),
         spid_eq_pid: ($k.source_pair_id == $k.pair_id),
         ans_a: (($k.members[]|select(.member_id==($k.pair_id+"_a"))|.answer) == ($s.answer_a|tostring)),
         ans_b: (($k.members[]|select(.member_id==($k.pair_id+"_b"))|.answer) == ($s.answer_b|tostring)),
         side_a: (($k.members[]|select(.member_id==($k.pair_id+"_a"))|.source_side) == "a"),
         side_b: (($k.members[]|select(.member_id==($k.pair_id+"_b"))|.source_side) == "b"),
         sv: $k.schema_version})
  | {n: length,
     tid_ok:(map(select(.tid))|length), cat_ok:(map(select(.cat))|length), ctw_ok:(map(select(.ctw))|length),
     spid_eq_pid:(map(select(.spid_eq_pid))|length),
     ans_a_ok:(map(select(.ans_a))|length), ans_b_ok:(map(select(.ans_b))|length),
     side_a_ok:(map(select(.side_a))|length), side_b_ok:(map(select(.side_b))|length),
     schema_versions:(map(.sv)|unique)}
' "$K"

