from __future__ import annotations
from dataclasses import asdict
from itertools import product
from pathlib import Path
import json, numpy as np, pandas as pd
from .agents import PolicySpec
from .engine import NegotiationEngine
from .models import EconomicState, NegotiationOutcome

def _event_json(outcome): return json.dumps([asdict(x) for x in outcome.transcript],separators=(",",":"))
def outcomes_to_frame(outcomes,include_transcripts=True):
    rows=[]
    for out in outcomes:
        row=out.flat_dict()
        if include_transcripts: row["transcript_json"]=_event_json(out)
        rows.append(row)
    return pd.DataFrame(rows)

def run_identity_swap(state:EconomicState,buyers:list[PolicySpec],sellers:list[PolicySpec],*,repetitions:int=100,master_seed:int=20260810)->pd.DataFrame:
    engine=NegotiationEngine(); cells=list(product(buyers,sellers,range(repetitions))); rng=np.random.default_rng(master_seed); rng.shuffle(cells); outcomes=[]
    for buyer,seller,rep in cells:
        outcomes.append(engine.run(state,buyer,seller,repetition=rep,seed=master_seed,treatment_id=f"B={buyer.name}|S={seller.name}|rep={rep}"))
    df=outcomes_to_frame(outcomes); df["experiment"]="identity_swap"; return df

def run_inflation_shock(state,buyers,sellers,*,shock_pct=0.10,repetitions=100,master_seed=20260810):
    engine=NegotiationEngine(); frames=[]
    for name,st in [("baseline",state),("cost_shock",engine.shock_cost(state,shock_pct))]:
        df=run_identity_swap(st,buyers,sellers,repetitions=repetitions,master_seed=master_seed); df["shock_state"]=name; df["cost_shock_pct"]=0.0 if name=="baseline" else shock_pct; frames.append(df)
    out=pd.concat(frames,ignore_index=True)
    paired=out[out["agreed"]].pivot_table(index=["buyer_model","seller_model","repetition"],columns="shock_state",values="price",aggfunc="first")
    if {"baseline","cost_shock"}.issubset(paired.columns):
        paired["experienced_inflation"]=paired["cost_shock"]/paired["baseline"]-1
        out=out.merge(paired[["experienced_inflation"]].reset_index(),on=["buyer_model","seller_model","repetition"],how="left")
    else: out["experienced_inflation"]=np.nan
    out["experiment"]="inflation_shock"; return out

def summarize_identity_swap(df,baseline_buyer=None):
    agreed=df[df["agreed"] & df["price"].notna()].copy()
    summary=df.groupby(["buyer_model","seller_model"],as_index=False).agg(negotiations=("treatment_id","size"),agreement_rate=("agreed","mean"),mean_price=("price","mean"),median_price=("price","median"),mean_buyer_surplus=("buyer_surplus","mean"),mean_seller_surplus=("seller_surplus","mean"),mean_rounds=("rounds","mean")).sort_values(["buyer_model","seller_model"])
    buyer_means=agreed.groupby("buyer_model",as_index=False)["price"].mean().rename(columns={"price":"mean_price"})
    if buyer_means.empty: return summary,pd.DataFrame(columns=["buyer_model","mean_price","abp_vs_baseline"])
    if baseline_buyer is None: baseline_buyer=str(buyer_means.sort_values("buyer_model").iloc[0]["buyer_model"])
    base=float(buyer_means.loc[buyer_means.buyer_model==baseline_buyer,"mean_price"].iloc[0]); buyer_means["abp_vs_baseline"]=buyer_means.mean_price-base; buyer_means["abp_pct_vs_baseline"]=buyer_means.mean_price/base-1
    return summary,buyer_means

def summarize_inflation(df):
    p=df[["buyer_model","seller_model","repetition","experienced_inflation"]].drop_duplicates()
    return p.groupby("buyer_model",as_index=False).agg(mean_experienced_inflation=("experienced_inflation","mean"),median_experienced_inflation=("experienced_inflation","median"),valid_pairs=("experienced_inflation","count")).sort_values("mean_experienced_inflation")

def write_results(df,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); df.to_csv(path,index=False); return path
