"""Shared schema constants for the AutoDrift research harness."""

from __future__ import annotations


SCOREBOARD_FIELDS = [
    "milestone",
    "type",
    "checkpoint",
    "success_rate",
    "termination_rate",
    "clearance_margin_mean",
    "reset_success",
    "zero_wheel_success",
    "zero_all_success",
    "wheel_gain_mu",
    "decision",
    "reason",
]
