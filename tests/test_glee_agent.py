from last_price.glee_agent import LastPriceGleeAgent


def test_bargaining_offer_sums_to_pot():
    agent = LastPriceGleeAgent(log_path=None)
    game = {
        "game_id": "b1",
        "game_family": "bargaining",
        "phase": "offer",
        "opponent": {"type": "human", "name": "x"},
        "valid_actions": {"type": "offer", "fields": {}},
        "game_state": {
            "money_to_divide": 100,
            "current_player": "alice",
            "round": 1,
            "max_rounds": 5,
            "horizon_known": True,
            "messages_allowed": True,
        },
    }
    action = agent.strategy(game)
    assert abs(action["alice_gain"] + action["bob_gain"] - 100) < 1e-9


def test_negotiation_buyer_offer_is_below_value_initially():
    agent = LastPriceGleeAgent(log_path=None)
    game = {
        "game_id": "n1",
        "game_family": "negotiation",
        "phase": "offer",
        "opponent": {"type": "agent", "name": "x"},
        "valid_actions": {"type": "offer", "fields": {}},
        "game_state": {
            "current_player": "player_2",
            "player_2_role": "buyer",
            "player_2_value": 100,
            "round": 1,
            "max_rounds": 5,
            "horizon_known": True,
            "messages_allowed": True,
        },
    }
    action = agent.strategy(game)
    assert 0 < action["product_price"] < 100


def test_persuasion_seller_does_not_recommend_low_quality():
    agent = LastPriceGleeAgent(log_path=None)
    game = {
        "game_id": "p1",
        "game_family": "persuasion",
        "phase": "seller_recommendation",
        "opponent": {"type": "hidden", "name": None},
        "valid_actions": {"type": "seller_recommendation", "fields": {}},
        "game_state": {"current_quality": "low", "product_price": 10, "p": 0.5, "round": 1, "total_rounds": 5},
    }
    assert agent.strategy(game) == {"decision": "no"}
