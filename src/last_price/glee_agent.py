"""Strategic GLEE competition agent derived from the Last Price research line.

The agent is deliberately hybrid:
1. economic rules choose reservation/acceptance boundaries,
2. lightweight opponent modelling learns from offers,
3. language is constrained to messages that do not change the economic action.

Two modes:
- leaderboard: use all disclosed information.
- research: randomize whether disclosed opponent identity is used, by game_id,
  creating an auditable identity-aware vs identity-blind comparison.

No opponent private fields are accessed; GLEE already filters game_state to the
information legally visible to the agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from typing import Any


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _progress(state: dict[str, Any]) -> float:
    round_no = float(state.get("round", 1) or 1)
    max_rounds = state.get("max_rounds")
    if not state.get("horizon_known", max_rounds is not None) or not max_rounds:
        return _clip((round_no - 1.0) / 10.0, 0.0, 0.65)
    if float(max_rounds) <= 1:
        return 1.0
    return _clip((round_no - 1.0) / (float(max_rounds) - 1.0), 0.0, 1.0)


def _research_arm(game_id: str) -> str:
    digest = sha256(game_id.encode("utf-8")).digest()
    return "identity_aware" if digest[0] < 128 else "identity_blind"


def _identity(game: dict[str, Any]) -> str:
    opponent = game.get("opponent") or {}
    return str(opponent.get("type") or "hidden").lower()


@dataclass
class GameMemory:
    game_id: str
    family: str
    arm: str
    opponent_type: str
    observed_opponent_offers: list[float] = field(default_factory=list)
    own_offers: list[float] = field(default_factory=list)
    last_round_seen: int = 0
    last_buyer_total_payoff: float | None = None
    last_seller_total_payoff: float | None = None
    persuasion_hits: int = 0
    persuasion_misses: int = 0


class LastPriceGleeAgent:
    def __init__(self, *, mode: str = "leaderboard", log_path: str | os.PathLike[str] | None = "artifacts/glee/games.jsonl") -> None:
        if mode not in {"leaderboard", "research"}:
            raise ValueError("mode must be 'leaderboard' or 'research'")
        self.mode = mode
        self.log_path = Path(log_path) if log_path else None
        self._memory: dict[str, GameMemory] = {}

    def strategy(self, game: dict[str, Any]) -> dict[str, Any]:
        game_id = str(game["game_id"])
        family = str(game["game_family"])
        mem = self._memory.get(game_id)
        if mem is None:
            mem = GameMemory(
                game_id=game_id,
                family=family,
                arm=_research_arm(game_id) if self.mode == "research" else "identity_aware",
                opponent_type=_identity(game),
            )
            self._memory[game_id] = mem

        state = game["game_state"]
        actions = game["valid_actions"]
        self._observe(game, mem)

        if family == "bargaining":
            action = self._bargaining(state, actions, mem)
        elif family == "negotiation":
            action = self._negotiation(state, actions, mem)
        elif family == "persuasion":
            action = self._persuasion(state, actions, mem)
        else:
            raise ValueError(f"Unknown GLEE family: {family}")

        self._log(game, action, mem)
        return action

    def _use_identity(self, mem: GameMemory) -> bool:
        return mem.arm == "identity_aware" and mem.opponent_type in {"human", "agent"}

    def _aggression_shift(self, mem: GameMemory) -> float:
        if not self._use_identity(mem):
            return 0.0
        if mem.opponent_type == "agent":
            return 0.025
        if mem.opponent_type == "human":
            return -0.015
        return 0.0

    def _observe(self, game: dict[str, Any], mem: GameMemory) -> None:
        state = game["game_state"]
        current_round = int(state.get("round", 0) or 0)
        last_offer = state.get("last_offer")
        if last_offer and current_round >= mem.last_round_seen:
            raw = last_offer.get("price")
            if raw is None:
                me = state.get("current_player")
                if me and f"{me}_gain" in last_offer:
                    raw = last_offer[f"{me}_gain"]
            if isinstance(raw, (int, float)):
                value = float(raw)
                if not mem.observed_opponent_offers or not math.isclose(mem.observed_opponent_offers[-1], value, rel_tol=1e-12, abs_tol=1e-12):
                    mem.observed_opponent_offers.append(value)

        buyer_total = state.get("buyer_total_payoff")
        seller_total = state.get("seller_total_payoff")
        if isinstance(buyer_total, (int, float)) and mem.last_buyer_total_payoff is not None:
            delta = float(buyer_total) - mem.last_buyer_total_payoff
            if delta > 0:
                mem.persuasion_hits += 1
            elif delta < 0:
                mem.persuasion_misses += 1
        if isinstance(buyer_total, (int, float)):
            mem.last_buyer_total_payoff = float(buyer_total)
        if isinstance(seller_total, (int, float)):
            mem.last_seller_total_payoff = float(seller_total)
        mem.last_round_seen = max(mem.last_round_seen, current_round)

    def _bargaining(self, state: dict[str, Any], actions: dict[str, Any], mem: GameMemory) -> dict[str, Any]:
        money = float(state["money_to_divide"])
        progress = _progress(state)
        shift = self._aggression_shift(mem)
        if actions["type"] == "offer":
            me = str(state["current_player"])
            own_share = _clip(0.58 + shift - 0.07 * progress, 0.50, 0.62)
            own_gain = money * own_share
            other_gain = money - own_gain
            if me == "alice":
                action = {"alice_gain": own_gain, "bob_gain": other_gain}
            elif me == "bob":
                action = {"alice_gain": other_gain, "bob_gain": own_gain}
            else:
                action = {"alice_gain": money / 2.0, "bob_gain": money / 2.0}
            if state.get("messages_allowed"):
                action["message"] = "This leaves both sides positive and moves us toward agreement." if progress < 0.7 else "We are close enough that closing now beats another costly round."
            mem.own_offers.append(own_gain)
            return action

        if actions["type"] == "decision":
            offer = state["last_offer"]
            me = str(state["current_player"])
            my_gain = float(offer[f"{me}_gain"])
            my_share = my_gain / money if money else 0.0
            threshold = _clip(0.455 + shift - 0.105 * progress, 0.34, 0.48)
            if my_share >= threshold or my_share >= 0.50:
                return {"decision": "accept"}
            if progress >= 0.98:
                return {"decision": "accept"} if my_gain > 0 else {"decision": "walkaway"}
            return {"decision": "reject"}
        return {}

    def _negotiation(self, state: dict[str, Any], actions: dict[str, Any], mem: GameMemory) -> dict[str, Any]:
        me = str(state["current_player"])
        role = str(state[f"{me}_role"])
        my_value = float(state[f"{me}_value"])
        progress = _progress(state)
        shift = self._aggression_shift(mem)

        if actions["type"] == "offer":
            price = self._negotiation_counter(role, my_value, progress, shift, mem)
            out: dict[str, Any] = {"product_price": price}
            if state.get("messages_allowed"):
                out["message"] = self._negotiation_message(role, progress)
            mem.own_offers.append(price)
            return out

        if actions["type"] == "decision":
            price = float(state["last_offer"]["price"])
            profitable = price <= my_value if role == "buyer" else price >= my_value
            if profitable and self._accept_negotiation(role, my_value, price, progress, shift, mem):
                return {"decision": "AcceptOffer"}
            if progress >= 0.98:
                return {"decision": "AcceptOffer"} if profitable else {"decision": "WalkAway"}
            counter = self._negotiation_counter(role, my_value, progress, shift, mem)
            out = {"decision": "RejectOffer", "product_price": counter}
            if state.get("messages_allowed"):
                out["message"] = self._negotiation_message(role, progress)
            mem.own_offers.append(counter)
            return out
        return {}

    def _negotiation_counter(self, role: str, my_value: float, progress: float, shift: float, mem: GameMemory) -> float:
        if role == "buyer":
            ratio = _clip(0.72 - shift + 0.24 * progress, 0.62, 0.98)
            target = my_value * ratio
            if mem.observed_opponent_offers:
                latest = mem.observed_opponent_offers[-1]
                if latest <= my_value:
                    target = min(target, (latest + my_value) / 2.0)
            return round(max(0.0, target), 6)
        ratio = _clip(1.34 + shift - 0.30 * progress, 1.02, 1.50)
        target = my_value * ratio
        if mem.observed_opponent_offers:
            latest = mem.observed_opponent_offers[-1]
            if latest >= my_value:
                target = max(target, (latest + my_value) / 2.0)
        return round(max(0.0, target), 6)

    def _accept_negotiation(self, role: str, my_value: float, price: float, progress: float, shift: float, mem: GameMemory) -> bool:
        if role == "buyer":
            max_ratio = _clip(0.91 - shift + 0.09 * progress, 0.84, 1.0)
            if price <= my_value * max_ratio:
                return True
            if len(mem.observed_opponent_offers) >= 2:
                first, latest = mem.observed_opponent_offers[0], mem.observed_opponent_offers[-1]
                if latest < first and price <= my_value * 0.97:
                    return True
            return False
        min_ratio = _clip(1.09 + shift - 0.09 * progress, 1.0, 1.16)
        if price >= my_value * min_ratio:
            return True
        if len(mem.observed_opponent_offers) >= 2:
            first, latest = mem.observed_opponent_offers[0], mem.observed_opponent_offers[-1]
            if latest > first and price >= my_value * 1.03:
                return True
        return False

    @staticmethod
    def _negotiation_message(role: str, progress: float) -> str:
        if role == "buyer":
            return "I can close at this number now." if progress > 0.65 else "This is a serious offer that keeps the deal inside my value."
        return "I can close at this number now." if progress > 0.65 else "This price keeps the trade viable on my side."

    def _persuasion(self, state: dict[str, Any], actions: dict[str, Any], mem: GameMemory) -> dict[str, Any]:
        action_type = actions["type"]
        if action_type == "seller_recommendation":
            quality = str(state.get("current_quality", "")).lower()
            return {"decision": "yes" if quality == "high" else "no"}
        if action_type == "seller_message":
            quality = str(state.get("current_quality", "")).lower()
            if quality == "high":
                return {"message": "I recommend buying this round; the product quality supports the price."}
            return {"message": "I would pass this round. Preserving a reliable recommendation is worth more than forcing one sale."}
        if action_type == "buyer_decision":
            price = float(state["product_price"])
            p = float(state["p"])
            v = float(state["v"])
            u = float(state["u"])
            prior_ev = p * v + (1.0 - p) * u
            evidence_n = mem.persuasion_hits + mem.persuasion_misses
            trust = 0.5 if not evidence_n else (mem.persuasion_hits + 1.0) / (evidence_n + 2.0)
            recommendation = str(state.get("seller_message") or state.get("seller_recommendation") or "").lower()
            positive_signal = any(token in recommendation for token in ("yes", "recommend", "buy", "high", "great", "worth"))
            negative_signal = any(token in recommendation for token in ("no", "pass", "low", "don't", "do not", "avoid"))
            posterior_ev = prior_ev
            if positive_signal:
                posterior_ev = prior_ev + trust * 0.25 * max(v - prior_ev, 0.0)
            if negative_signal:
                posterior_ev = prior_ev - trust * 0.25 * max(prior_ev - u, 0.0)
            return {"decision": "yes" if posterior_ev >= price else "no"}
        return {}

    def _log(self, game: dict[str, Any], action: dict[str, Any], mem: GameMemory) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "game_id": game.get("game_id"),
            "family": game.get("game_family"),
            "phase": game.get("phase"),
            "opponent_type": mem.opponent_type,
            "identity_arm": mem.arm,
            "round": game.get("game_state", {}).get("round"),
            "action": action,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


_default_agent: LastPriceGleeAgent | None = None


def strategy(game: dict[str, Any]) -> dict[str, Any]:
    global _default_agent
    if _default_agent is None:
        _default_agent = LastPriceGleeAgent(mode=os.getenv("GLEE_MODE", "leaderboard").strip().lower() or "leaderboard")
    return _default_agent.strategy(game)
