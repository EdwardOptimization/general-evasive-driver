"""Path definitions for drift tracking tasks."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from autodrift.math_utils import wrap_pi


@dataclass(frozen=True)
class PathFrame:
    lateral_error: float
    heading_error: float
    curvature: float
    progress: float
    tangent_heading: float
    tangent: np.ndarray


class CircleTrack:
    """Closed circular path, useful for steady drift and friction sweeps."""

    def __init__(self, radius: float = 18.0, clockwise: bool = False):
        if radius <= 1.0:
            raise ValueError("radius must be greater than 1 m")
        self.radius = float(radius)
        self.clockwise = bool(clockwise)

    def frame(self, x: float, y: float, psi: float) -> PathFrame:
        angle = math.atan2(y, x)
        distance = max(math.hypot(x, y), 1e-6)
        lateral_error = distance - self.radius
        tangent_heading = angle + (-math.pi / 2.0 if self.clockwise else math.pi / 2.0)
        heading_error = wrap_pi(psi - tangent_heading)
        sign = -1.0 if self.clockwise else 1.0
        tangent = np.array([math.cos(tangent_heading), math.sin(tangent_heading)], dtype=np.float64)
        progress_angle = -angle if self.clockwise else angle
        progress = self.radius * (progress_angle % (2.0 * math.pi))
        return PathFrame(
            lateral_error=lateral_error,
            heading_error=heading_error,
            curvature=sign / self.radius,
            progress=progress,
            tangent_heading=tangent_heading,
            tangent=tangent,
        )

    def reset_pose(self, rng: np.random.Generator, speed: float, beta: float = 0.0) -> tuple[float, float, float, float, float]:
        angle = rng.uniform(-math.pi, math.pi)
        radial_noise = rng.normal(0.0, 0.3)
        x = (self.radius + radial_noise) * math.cos(angle)
        y = (self.radius + radial_noise) * math.sin(angle)
        tangent_heading = angle + (-math.pi / 2.0 if self.clockwise else math.pi / 2.0)
        psi = tangent_heading - beta + rng.normal(0.0, 0.03)
        vx = speed * math.cos(beta)
        vy = speed * math.sin(beta)
        return x, y, psi, vx, vy
