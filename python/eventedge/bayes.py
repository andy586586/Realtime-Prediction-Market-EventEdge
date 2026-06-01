from __future__ import annotations

import math


def clamp(x: float, lo: float = 0.01, hi: float = 0.99) -> float:
    return max(lo, min(hi, x))


def prob_to_logit(p: float) -> float:
    p = clamp(p)
    return math.log(p / (1.0 - p))


def logit_to_prob(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def bayesian_logit_update(prior: float, evidence_score: float, strength: float = 0.25) -> float:
    """Update a binary-event probability.

    evidence_score is a signed standardized signal. Positive means event is more likely.
    strength controls how aggressively evidence moves log-odds.
    """
    posterior_logit = prob_to_logit(prior) + strength * evidence_score
    return clamp(logit_to_prob(posterior_logit))


def blend_market_and_model(market_mid: float, news_posterior: float, weight_news: float) -> float:
    weight_news = max(0.0, min(1.0, weight_news))
    return clamp((1.0 - weight_news) * market_mid + weight_news * news_posterior)
