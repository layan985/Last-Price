from lastprice.agents import PolicySpec
from lastprice.experiments import run_identity_swap,run_inflation_shock,summarize_identity_swap
from lastprice.models import EconomicState

def policies(): return [PolicySpec("b1",0.6,0.15),PolicySpec("b2",0.2,0.35)],[PolicySpec("s1",0.5,0.18),PolicySpec("s2",0.2,0.3)]
def test_identity_swap_is_fully_crossed():
    b,s=policies(); df=run_identity_swap(EconomicState(120,70,100,max_rounds=20),b,s,repetitions=7); assert len(df)==28; assert set(df.buyer_model)=={"b1","b2"}; assert set(df.seller_model)=={"s1","s2"}
def test_summary_produces_buyer_effects():
    b,s=policies(); df=run_identity_swap(EconomicState(120,70,100,max_rounds=20),b,s,repetitions=5); summary,effects=summarize_identity_swap(df,"b1"); assert len(summary)==4; assert effects.loc[effects.buyer_model=="b1","abp_vs_baseline"].iloc[0]==0
def test_inflation_pairs_are_constructed():
    b,s=policies(); df=run_inflation_shock(EconomicState(120,70,100,max_rounds=20),b,s,shock_pct=0.05,repetitions=5); assert set(df.shock_state)=={"baseline","cost_shock"}; assert "experienced_inflation" in df.columns
