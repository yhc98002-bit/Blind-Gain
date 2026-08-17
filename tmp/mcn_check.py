import math, sys
sys.path.insert(0,"/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
def mcnemar(b01,b10):
    n=b01+b10
    if n==0: return 1.0
    k=min(b01,b10)
    return min(1.0, 2*sum(math.comb(n,i) for i in range(k+1))/(2**n))
try:
    from scipy.stats import binomtest
    ok=True
except Exception as e:
    ok=False; print("scipy unavailable:",e)
cases=[(6,3),(20,18),(21,15),(17,59),(16,4),(3,3),(5,10),(12,26),(16,39),(17,46),(0,284),(2,20),(0,0)]
worst=0.0
for b01,b10 in cases:
    mine=mcnemar(b01,b10)
    if ok:
        n=b01+b10
        ref=1.0 if n==0 else binomtest(min(b01,b10),n,0.5,alternative="two-sided").pvalue
        worst=max(worst,abs(mine-ref))
        print(f"b01={b01:4d} b10={b10:4d} mine={mine:.12g} scipy={ref:.12g} absdiff={abs(mine-ref):.3g}")
    else:
        print(f"b01={b01:4d} b10={b10:4d} mine={mine:.12g}")
if ok: print("max abs diff:",worst)
