import sys
sys.path.insert(0,"/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
from src.eval.fliptrack_metrics import pair_score
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT as PC

# A catch-shaped row: shared gold (answer_a == answer_b), as in data/mini_a5_catch_v1.
base = {"pair_id":"m6catch_probe","answer_a":"B9U","answer_b":"B9U"}

cases = {
 "both sides agree AND both right":      ("<answer>B9U</answer>","<answer>B9U</answer>"),
 "both sides agree BUT both wrong":      ("<answer>C1X</answer>","<answer>C1X</answer>"),
 "sides DISAGREE (invariance failure)":  ("<answer>B9U</answer>","<answer>C1X</answer>"),
}
for name,(pa,pb) in cases.items():
    r = dict(base); r["prediction_a"]=pa; r["prediction_b"]=pb
    s = pair_score(r, prompt_contract=PC)
    print(f"{name:38} pair_correct={s['pair_correct']!s:5} strict={s['strict_pair_correct']!s:5} "
          f"collapsed={s['collapsed']!s:5} equal_gold_a={s['equal_gold_a']!s:5} "
          f"extracted=({s['extracted_answer_a']!r},{s['extracted_answer_b']!r})")
print()
print("NOTE: no field equals the invariance criterion (extracted_a == extracted_b).")
print("'collapsed' is the only agreement field and it is gated on answer_a != answer_b,")
print("so it is identically False on every catch pair.")
