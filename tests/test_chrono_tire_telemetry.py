from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from autodrift.chrono_vehicle_backend import _collect_tire_telemetry_from_vehicle


@dataclass
class Vec3:
    x: Any
    y: Any
    z: Any


@dataclass
class ForceReport:
    force: Vec3


class Rot:
    def __init__(self, local_force: Vec3):
        self.local_force = local_force

    def RotateBack(self, _force: Vec3) -> Vec3:
        return self.local_force


class Tire:
    def __init__(
        self,
        *,
        slip_angle: Any,
        longitudinal_slip: Any,
        camber_angle: Any,
        radius: Any,
        force: Vec3,
        expected_terrain: object,
    ):
        self.slip_angle = slip_angle
        self.longitudinal_slip = longitudinal_slip
        self.camber_angle = camber_angle
        self.radius = radius
        self.force = force
        self.expected_terrain = expected_terrain

    def GetSlipAngle(self) -> Any:
        return self.slip_angle

    def GetLongitudinalSlip(self) -> Any:
        return self.longitudinal_slip

    def GetCamberAngle(self) -> Any:
        return self.camber_angle

    def GetRadius(self) -> Any:
        return self.radius

    def ReportTireForce(self, terrain: object) -> ForceReport:
        assert terrain is self.expected_terrain
        return ForceReport(self.force)


@dataclass
class WheelState:
    omega: Any
    rot: Rot


class Wheel:
    def __init__(self, state: WheelState):
        self.state = state

    def GetState(self) -> WheelState:
        return self.state


class FakeVehModule:
    LEFT = 0
    RIGHT = 1


class FakeVehicle:
    def __init__(self, tires: dict[tuple[int, int], Tire], wheels: dict[tuple[int, int], Wheel]):
        self.tires = tires
        self.wheels = wheels

    def GetAxles(self) -> list[object]:
        return [object(), object()]

    def GetTire(self, axle: int, side: int) -> Tire:
        return self.tires[(axle, side)]

    def GetWheel(self, axle: int, side: int) -> Wheel:
        return self.wheels[(axle, side)]


def _make_vehicle() -> tuple[FakeVehicle, object]:
    terrain = object()
    specs = {
        (0, FakeVehModule.LEFT): {
            "slip_angle": -0.10,
            "longitudinal_slip": 0.05,
            "camber_angle": 0.01,
            "radius": 0.31,
            "omega": 10.0,
            "force": Vec3(100.0, -20.0, -3000.0),
            "local": Vec3(110.0, -30.0, -3200.0),
        },
        (0, FakeVehModule.RIGHT): {
            "slip_angle": 0.20,
            "longitudinal_slip": -0.10,
            "camber_angle": float("inf"),
            "radius": 0.31,
            "omega": 11.0,
            "force": Vec3(-200.0, 40.0, 3500.0),
            "local": Vec3(-210.0, 50.0, 3400.0),
        },
        (1, FakeVehModule.LEFT): {
            "slip_angle": 0.15,
            "longitudinal_slip": 0.20,
            "camber_angle": 0.03,
            "radius": 0.32,
            "omega": 12.0,
            "force": Vec3(50.0, -70.0, -3300.0),
            "local": Vec3(50.0, -80.0, -3300.0),
        },
        (1, FakeVehModule.RIGHT): {
            "slip_angle": -0.05,
            "longitudinal_slip": 0.12,
            "camber_angle": 0.01,
            "radius": "not-a-radius",
            "omega": 13.0,
            "force": Vec3(-250.0, 60.0, 3100.0),
            "local": Vec3(-300.0, 20.0, 3100.0),
        },
    }
    tires: dict[tuple[int, int], Tire] = {}
    wheels: dict[tuple[int, int], Wheel] = {}
    for key, spec in specs.items():
        tires[key] = Tire(
            slip_angle=spec["slip_angle"],
            longitudinal_slip=spec["longitudinal_slip"],
            camber_angle=spec["camber_angle"],
            radius=spec["radius"],
            force=spec["force"],
            expected_terrain=terrain,
        )
        wheels[key] = Wheel(WheelState(omega=spec["omega"], rot=Rot(spec["local"])))
    return FakeVehicle(tires, wheels), terrain


def test_collect_tire_telemetry_from_vehicle_returns_four_wheel_truth_rows() -> None:
    vehicle, terrain = _make_vehicle()

    rows, aggregate = _collect_tire_telemetry_from_vehicle(vehicle, FakeVehModule, terrain)

    assert [row["axle"] for row in rows] == ["front", "front", "rear", "rear"]
    assert [row["side"] for row in rows] == ["left", "right", "left", "right"]
    assert [row["side_index"] for row in rows] == [FakeVehModule.LEFT, FakeVehModule.RIGHT] * 2
    assert rows[0]["force_x_n"] == 100.0
    assert rows[0]["local_force_y_n"] == -30.0
    assert rows[0]["normal_load_n"] == 3000.0
    assert math.isnan(rows[1]["camber_angle_rad"])
    assert math.isnan(rows[3]["tire_radius_m"])

    assert aggregate["tire_telemetry_available"] is True
    assert aggregate["tire_telemetry_wheel_count"] == 4
    assert aggregate["tire_telemetry_force_frame"] == "global_report_force_plus_wheel_state_local_projection"
    assert math.isclose(aggregate["max_abs_tire_slip_angle_rad"], 0.20)
    assert math.isclose(aggregate["max_abs_tire_longitudinal_slip"], 0.20)
    assert math.isclose(aggregate["max_abs_tire_camber_angle_rad"], 0.03)
    assert math.isclose(aggregate["max_abs_tire_longitudinal_force_n"], 300.0)
    assert math.isclose(aggregate["max_abs_tire_lateral_force_n"], 80.0)
    assert math.isclose(aggregate["max_tire_normal_load_n"], 3500.0)
    assert math.isclose(aggregate["min_tire_normal_load_n"], 3000.0)
