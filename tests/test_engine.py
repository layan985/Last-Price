from lastprice.agents import PolicySpec
from lastprice.engine import NegotiationEngine
from lastprice.models import EconomicState

def test_agreed_price_respects_surplus_bounds():
    state=EconomicState(120,70,100,max_rounds=20); out=NegotiationEngine().run(state,PolicySpec("b"),PolicySpec("s"),seed=1); assert out.agreed; assert state.seller_cost<=out.price<=state.buyer_value; assert abs(out.total_surplus-(state.buyer_value-state.seller_cost))<1e-9

def test_reproducible_with_same_seed():
    state=EconomicState(120,70,100,max_rounds=20); b=PolicySpec("b",noise_sd=1.0); s=PolicySpec("s",noise_sd=1.0); e=NegotiationEngine(); a=e.run(state,b,s,seed=42,repetition=3); c=e.run(state,b,s,seed=42,repetition=3); assert a.price==c.price; assert a.transcript==c.transcript

def test_cost_shock_changes_only_cost():
    state=EconomicState(120,70,100); shocked=NegotiationEngine.shock_cost(state,0.10); assert shocked.seller_cost==77; assert shocked.buyer_value==state.buyer_value
