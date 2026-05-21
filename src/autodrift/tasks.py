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
        self.reference_radius = self.radius

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

    def lookahead_centerline(self, x: float, y: float, distances: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        angle = math.atan2(y, x)
        sign = -1.0 if self.clockwise else 1.0
        points = []
        tangents = []
        for distance in distances:
            point_angle = angle + sign * float(distance) / self.radius
            tangent_heading = point_angle + (-math.pi / 2.0 if self.clockwise else math.pi / 2.0)
            points.append([self.radius * math.cos(point_angle), self.radius * math.sin(point_angle)])
            tangents.append([math.cos(tangent_heading), math.sin(tangent_heading)])
        return np.asarray(points, dtype=np.float64), np.asarray(tangents, dtype=np.float64)


class FigureEightTrack:
    """Closed figure-eight path for drift transition and varying curvature."""

    def __init__(self, radius: float = 18.0, samples: int = 1024):
        if radius <= 1.0:
            raise ValueError("radius must be greater than 1 m")
        if samples < 64:
            raise ValueError("samples must be at least 64")
        self.radius = float(radius)
        self.samples = int(samples)
        t = np.linspace(0.0, 2.0 * math.pi, self.samples, endpoint=False)
        x = self.radius * np.sin(t)
        y = self.radius * np.sin(t) * np.cos(t)
        dx = self.radius * np.cos(t)
        dy = self.radius * np.cos(2.0 * t)
        ddx = -self.radius * np.sin(t)
        ddy = -2.0 * self.radius * np.sin(2.0 * t)
        speed = np.maximum(np.hypot(dx, dy), 1e-9)
        self.points = np.column_stack([x, y]).astype(np.float64)
        self.tangents = np.column_stack([dx / speed, dy / speed]).astype(np.float64)
        self.tangent_headings = np.arctan2(self.tangents[:, 1], self.tangents[:, 0])
        self.curvatures = ((dx * ddy - dy * ddx) / np.maximum(speed**3, 1e-9)).astype(np.float64)
        next_points = np.roll(self.points, -1, axis=0)
        segment_lengths = np.linalg.norm(next_points - self.points, axis=1)
        self.progress = np.concatenate([[0.0], np.cumsum(segment_lengths[:-1])]).astype(np.float64)
        self.length = float(np.sum(segment_lengths))
        max_curvature = float(np.max(np.abs(self.curvatures)))
        self.reference_radius = 1.0 / max(max_curvature, 1e-6)

    def _nearest_index(self, x: float, y: float) -> int:
        point = np.array([x, y], dtype=np.float64)
        distances = np.sum(np.square(self.points - point), axis=1)
        return int(np.argmin(distances))

    def frame(self, x: float, y: float, psi: float) -> PathFrame:
        index = self._nearest_index(x, y)
        point = self.points[index]
        tangent = self.tangents[index]
        delta = np.array([x, y], dtype=np.float64) - point
        lateral_error = float(tangent[0] * delta[1] - tangent[1] * delta[0])
        tangent_heading = float(self.tangent_headings[index])
        heading_error = wrap_pi(psi - tangent_heading)
        return PathFrame(
            lateral_error=lateral_error,
            heading_error=heading_error,
            curvature=float(self.curvatures[index]),
            progress=float(self.progress[index]),
            tangent_heading=tangent_heading,
            tangent=tangent.copy(),
        )

    def reset_pose(self, rng: np.random.Generator, speed: float, beta: float = 0.0) -> tuple[float, float, float, float, float]:
        index = int(rng.integers(0, self.samples))
        point = self.points[index]
        tangent = self.tangents[index]
        normal_left = np.array([-tangent[1], tangent[0]], dtype=np.float64)
        lateral_noise = rng.normal(0.0, 0.3)
        x, y = point + lateral_noise * normal_left
        tangent_heading = float(self.tangent_headings[index])
        psi = tangent_heading - beta + rng.normal(0.0, 0.03)
        vx = speed * math.cos(beta)
        vy = speed * math.sin(beta)
        return float(x), float(y), psi, vx, vy

    def lookahead_centerline(self, x: float, y: float, distances: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        index = self._nearest_index(x, y)
        current_progress = float(self.progress[index])
        targets = (current_progress + distances.astype(np.float64)) % self.length
        indices = np.searchsorted(self.progress, targets, side="left") % self.samples
        return self.points[indices].copy(), self.tangents[indices].copy()


def make_track(kind: str, radius: float) -> CircleTrack | FigureEightTrack:
    if kind == "circle":
        return CircleTrack(radius=radius)
    if kind == "figure_eight":
        return FigureEightTrack(radius=radius)
    raise ValueError(f"unknown track_kind: {kind}")
