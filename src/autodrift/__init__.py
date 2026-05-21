"""AutoDrift simulation package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autodrift.env import AutoDriftEnv

__all__ = ["AutoDriftEnv"]


def __getattr__(name: str):
    if name == "AutoDriftEnv":
        from autodrift.env import AutoDriftEnv

        return AutoDriftEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
