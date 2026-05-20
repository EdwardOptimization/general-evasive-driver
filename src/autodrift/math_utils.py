"""Small numerical helpers used by the simulator."""

from __future__ import annotations

import math


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def move_towards(current: float, target: float, max_delta: float) -> float:
    delta = clamp(target - current, -max_delta, max_delta)
    return current + delta


def wrap_pi(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi
