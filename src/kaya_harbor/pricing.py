"""Frontier model pricing tables matching kaya-utils official rates per million tokens."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPriceRate:
    prompt_usd_per_m: float
    completion_usd_per_m: float
    cache_read_usd_per_m: float

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        billable_prompt = max(0, prompt_tokens - cached_tokens)
        prompt_cost = (billable_prompt * self.prompt_usd_per_m) / 1_000_000.0
        cache_cost = (cached_tokens * self.cache_read_usd_per_m) / 1_000_000.0
        completion_cost = (completion_tokens * self.completion_usd_per_m) / 1_000_000.0
        return prompt_cost + cache_cost + completion_cost


MODEL_RATES: dict[str, ModelPriceRate] = {
    "google/gemini-2.5-pro": ModelPriceRate(1.25, 5.00, 0.3125),
    "gemini-2.5-pro": ModelPriceRate(1.25, 5.00, 0.3125),
    "google/gemini-2.5-flash": ModelPriceRate(0.075, 0.30, 0.01875),
    "gemini-2.5-flash": ModelPriceRate(0.075, 0.30, 0.01875),
    "google/gemini-2.0-flash": ModelPriceRate(0.10, 0.40, 0.025),
    "gemini-2.0-flash": ModelPriceRate(0.10, 0.40, 0.025),
    "anthropic/claude-3-7-sonnet": ModelPriceRate(3.00, 15.00, 0.30),
    "claude-3-7-sonnet": ModelPriceRate(3.00, 15.00, 0.30),
    "openai/gpt-4o": ModelPriceRate(2.50, 10.00, 1.25),
    "gpt-4o": ModelPriceRate(2.50, 10.00, 1.25),
    "openai/gpt-4o-mini": ModelPriceRate(0.15, 0.60, 0.075),
    "gpt-4o-mini": ModelPriceRate(0.15, 0.60, 0.075),
}


def calculate_cost_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Calculate the estimated USD cost based on token counts and model pricing."""
    rate = MODEL_RATES.get(model.lower())
    if not rate:
        # Fallback to standard Gemini 2.5 Pro pricing if unknown
        rate = MODEL_RATES["google/gemini-2.5-pro"]
    return rate.calculate_cost(prompt_tokens, completion_tokens, cached_tokens)
