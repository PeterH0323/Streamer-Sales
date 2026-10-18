"""Resolve the network tool without replacing a configured delivery service."""

from ....web_configs import WEB_CONFIGS


def get_search_provider(config=WEB_CONFIGS):
    if not config.ENABLE_AGENT:
        return None
    provider = config.AGENT_SEARCH_PROVIDER
    if provider not in ("auto", "parallel", "delivery", "none"):
        raise ValueError("AGENT_SEARCH_PROVIDER must be auto, parallel, delivery or none")
    if provider == "none":
        return None
    if provider == "auto":
        # Even partial credentials express a choice; do not silently switch it.
        configured = config.AGENT_WEATHER_API_KEY is not None or config.AGENT_DELIVERY_TIME_API_KEY is not None
        provider = "delivery" if configured else "parallel"
    if provider == "delivery" and not (config.AGENT_WEATHER_API_KEY and config.AGENT_DELIVERY_TIME_API_KEY):
        return None
    return provider
