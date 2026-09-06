"""Tests for model pricing and cost calculations in kaya-harbor."""

import pytest
from kaya_harbor.pricing import calculate_cost_usd, MODEL_RATES


def test_gemini_pro_cost_calculation():
    # 50,000 prompt tokens, 5,000 completion tokens on gemini-2.5-pro
    # Prompt: 50,000 / 1,000,000 * 1.25 = 0.0625
    # Completion: 5,000 / 1,000,000 * 5.00 = 0.025
    # Total = 0.0875
    cost = calculate_cost_usd("google/gemini-2.5-pro", 50000, 5000)
    assert pytest.approx(cost, 1e-6) == 0.0875


def test_gemini_flash_cost_calculation():
    # 100,000 prompt, 10,000 completion on gemini-2.5-flash
    # Prompt: 100,000 / 1,000,000 * 0.075 = 0.0075
    # Completion: 10,000 / 1,000,000 * 0.30 = 0.003
    # Total = 0.0105
    cost = calculate_cost_usd("google/gemini-2.5-flash", 100000, 10000)
    assert pytest.approx(cost, 1e-6) == 0.0105


def test_cached_prompt_discount():
    # 50,000 prompt with 20,000 cached on gemini-2.5-pro
    # Billable prompt: 30,000 * 1.25 / 1M = 0.0375
    # Cached prompt: 20,000 * 0.3125 / 1M = 0.00625
    # Completion: 1,000 * 5.00 / 1M = 0.005
    # Total = 0.04875
    cost = calculate_cost_usd("google/gemini-2.5-pro", 50000, 1000, cached_tokens=20000)
    assert pytest.approx(cost, 1e-6) == 0.04875


def test_claude_sonnet_cost():
    cost = calculate_cost_usd("anthropic/claude-3-7-sonnet", 10000, 1000)
    # 10,000 * 3.00 / 1M = 0.03
    # 1,000 * 15.00 / 1M = 0.015
    assert pytest.approx(cost, 1e-6) == 0.045
