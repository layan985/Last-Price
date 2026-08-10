from __future__ import annotations
import argparse
from pathlib import Path
from .agents import PolicySpec
from .analysis import paired_buyer_effects,two_way_price_variance
from .experiments import run_identity_swap,run_inflation_shock,summarize_identity_swap,summarize_inflation,write_results
from .models import EconomicState

def demo_policies():
    return ([PolicySpec("buyer_A",0.60,0.15),PolicySpec("buyer_B",0.35,0.22),PolicySpec("buyer_C",0.15,0.35)],[PolicySpec("seller_A",0.55,0.16),PolicySpec("seller_B",0.25,0.30)])

def main():
    p=argparse.ArgumentParser(); p.add_argument("experiment",choices=["identity","inflation"],nargs="?",default="identity"); p.add_argument("--repetitions",type=int,default=200); p.add_argument("--seed",type=int,default=20260810); p.add_argument("--shock",type=float,default=0.10); p.add_argument("--out",default="results"); a=p.parse_args(); out=Path(a.out)
    state=EconomicState(120.0,70.0,100.0,max_rounds=12); buyers,sellers=demo_policies()
    if a.experiment=="identity":
        df=run_identity_swap(state,buyers,sellers,repetitions=a.repetitions,master_seed=a.seed); summary,effects=summarize_identity_swap(df,"buyer_A"); write_results(df,out/"identity_swap_raw.csv"); write_results(summary,out/"identity_swap_summary.csv"); write_results(effects,out/"buyer_model_effects.csv"); write_results(paired_buyer_effects(df,"buyer_A"),out/"buyer_model_paired_effects.csv"); write_results(two_way_price_variance(df),out/"price_variance_decomposition.csv"); print(summary.to_string(index=False))
    else:
        df=run_inflation_shock(state,buyers,sellers,shock_pct=a.shock,repetitions=a.repetitions,master_seed=a.seed); summary=summarize_inflation(df); write_results(df,out/"inflation_shock_raw.csv"); write_results(summary,out/"experienced_inflation_by_buyer.csv"); print(summary.to_string(index=False))

if __name__=="__main__": main()
