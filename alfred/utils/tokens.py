"""Token budget tracking and cost estimation."""

# Approximate costs per 1M tokens (input)
MODEL_COSTS = {
    "claude-haiku-4-5-20251001": 0.25,
    "claude-sonnet-4-6-20260414": 3.00,
    "claude-opus-4-6-20260414": 15.00,
}


def estimate_cost(tokens: int, model: str) -> float:
    """Estimate cost in USD for a given number of tokens."""
    cost_per_million = MODEL_COSTS.get(model, 3.00)
    return (tokens / 1_000_000) * cost_per_million


def format_cost(usd: float) -> str:
    """Format cost for display."""
    if usd < 0.01:
        return f"${usd:.4f}"
    return f"${usd:.2f}"
