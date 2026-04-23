from alfred.config import Config


def pick_model(task: str) -> str:
    """Route tasks to the cheapest model that can handle them."""
    cheap = {
        "classify", "acknowledge", "greet", "confirm",
    }
    medium = {
        "summarize", "briefing", "research_light", "idea_score",
        "plan", "document", "link_summary", "chat",
    }
    # Everything else defaults to expensive (opus)
    if task in cheap:
        return Config.MODEL_HAIKU
    if task in medium:
        return Config.MODEL_SONNET
    return Config.MODEL_OPUS
