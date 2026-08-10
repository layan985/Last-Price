from __future__ import annotations
import numpy as np, pandas as pd

def paired_buyer_effects(df:pd.DataFrame,baseline_buyer:str,*,n_boot:int=2000,seed:int=20260810)->pd.DataFrame:
    agreed=df[df["agreed"] & df["price"].notna()].copy(); wide=agreed.pivot_table(index=["seller_model","repetition"],columns="buyer_model",values="price",aggfunc="first")
    if baseline_buyer not in wide.columns: raise ValueError(f"baseline buyer {baseline_buyer!r} is absent")
    rng=np.random.default_rng(seed); rows=[]
    for model in sorted(map(str,wide.columns)):
        pair=wide[[baseline_buyer,model]].dropna(); diff=pair[model].to_numpy()-pair[baseline_buyer].to_numpy()
        if len(diff)==0: rows.append({"buyer_model":model,"n_pairs":0,"effect":np.nan,"ci_low":np.nan,"ci_high":np.nan}); continue
        effect=float(np.mean(diff))
        if len(diff)==1 or np.allclose(diff,diff[0]): lo=hi=effect
        else:
            idx=rng.integers(0,len(diff),size=(n_boot,len(diff))); boots=diff[idx].mean(axis=1); lo,hi=np.quantile(boots,[0.025,0.975])
        rows.append({"buyer_model":model,"n_pairs":int(len(diff)),"effect":effect,"ci_low":float(lo),"ci_high":float(hi)})
    return pd.DataFrame(rows)

def two_way_price_variance(df:pd.DataFrame)->pd.DataFrame:
    x=df[df["agreed"] & df["price"].notna()][["buyer_model","seller_model","price"]].copy()
    if x.empty:return pd.DataFrame(columns=["component","sum_squares","share"])
    grand=x.price.mean(); n=len(x); ss_total=float(((x.price-grand)**2).sum()); b=x.groupby("buyer_model").price.agg(["mean","size"]); s=x.groupby("seller_model").price.agg(["mean","size"]); cell=x.groupby(["buyer_model","seller_model"]).price.agg(["mean","size"])
    ss_b=float(((b["mean"]-grand)**2*b["size"]).sum()); ss_s=float(((s["mean"]-grand)**2*s["size"]).sum()); ss_i=0.0
    for (bm,sm),row in cell.iterrows(): ss_i+=float(row["size"]*(row["mean"]-(b.loc[bm,"mean"]+s.loc[sm,"mean"]-grand))**2)
    cm=x.join(cell["mean"].rename("cell_mean"),on=["buyer_model","seller_model"]); ss_r=float(((cm.price-cm.cell_mean)**2).sum()); denom=ss_total if ss_total>0 else 1.0
    return pd.DataFrame([{"component":name,"sum_squares":ss,"share":ss/denom,"n":n} for name,ss in [("buyer_model",ss_b),("seller_model",ss_s),("buyer_x_seller",ss_i),("within_cell",ss_r)]])
