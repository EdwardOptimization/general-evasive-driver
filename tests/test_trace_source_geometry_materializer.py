from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.capability_step_sequence_intervention_probe import TracePoint
from autodrift.trace_source_geometry_materializer import (
    active_obstacle_diagnostics,
    emergency_obstacle_geometry_from_trace_point,
    materialize_source_geometry_for_row,
    materialize_trace_source_geometry_from_rows,
    prepare_reveal_source_frame,
    run_trace_source_geometry_materializer_from_rows,
    trace_point_at_step,
    write_trace_source_geometry_outputs,
)


class _FakeEnv:
    def __init__(self, *, obstacle_body_x: float, obstacle_body_y: float, half_width: float):
        self.obstacle_position = np.array([obstacle_body_x, obstacle_body_y], dtype=np.float64)
        self.obstacle_scenario = SimpleNamespace(obstacle_half_width=half_width)

    def _body_point(self, position):
        return np.asarray(position, dtype=np.float64)


def _point(
    *,
    step: int,
    obstacle_body_x: float,
    obstacle_body_y: float = 0.25,
    half_width: float = 0.6,
    active_body_x: float = 1.5,
) -> TracePoint:
    return TracePoint(
        seed=123,
        fault=SimpleNamespace(name="fault"),
        step=step,
        observation=np.zeros(72, dtype=np.float32),
        hidden=torch.zeros((1, 8), dtype=torch.float32),
        env=_FakeEnv(obstacle_body_x=obstacle_body_x, obstacle_body_y=obstacle_body_y, half_width=half_width),
        info={
            "active_obstacle_kind": "warmup_gate",
            "active_obstacle_body_x": active_body_x,
            "active_obstacle_body_y": -0.4,
            "active_obstacle_half_width": 0.3,
        },
    )


def _trace(*steps: int, base_x: float = 8.0) -> list[TracePoint]:
    return [_point(step=step, obstacle_body_x=base_x + 0.1 * step) for step in steps]


def _row(**updates):
    row = {
        "source_index": 7,
        "seed": 123,
        "reveal_step": 32,
        "preferred_fault": "preferred",
        "preferred_fault_family": "pref_family",
        "wrong_fault": "wrong",
        "wrong_fault_family": "wrong_family",
        "capability_pair": "pref_family->wrong_family",
        "preferred_reveal_bucket": "bucket-a",
        "wrong_reveal_bucket": "bucket-b",
        "matched_current_pass": False,
        "bucketed_current_pass": True,
    }
    row.update(updates)
    return row


def test_emergency_geometry_uses_emergency_obstacle_not_active_obstacle():
    point = _point(step=16, obstacle_body_x=9.0, obstacle_body_y=0.7, half_width=0.8, active_body_x=1.0)

    source_x, source_y, half_width = emergency_obstacle_geometry_from_trace_point(point)
    active = active_obstacle_diagnostics(point)

    assert source_x == pytest.approx(9.0)
    assert source_y == pytest.approx(0.7)
    assert half_width == pytest.approx(0.8)
    assert active["preferred_active_obstacle_body_x"] == pytest.approx(1.0)


def test_prepare_reveal_source_frame_requires_schema():
    with pytest.raises(ValueError, match="missing required columns"):
        prepare_reveal_source_frame(pd.DataFrame([{"seed": 1}]))

    prepared = prepare_reveal_source_frame(pd.DataFrame([_row()]))
    assert bool(prepared.loc[0, "matched_or_bucketed_reveal_pass"]) is True


def test_materialize_source_geometry_for_row_offsets_and_diagnostics():
    preferred_trace = _trace(0, 24, 32, base_x=6.0)
    wrong_trace = _trace(0, 24, 32, base_x=7.0)

    rows, rejected = materialize_source_geometry_for_row(
        _row(),
        preferred_trace=preferred_trace,
        wrong_trace=wrong_trace,
        source_step_offsets=(-8, 0),
    )

    assert rejected == []
    assert [row["source_step"] for row in rows] == [24, 32]
    assert rows[0]["source_body_x"] == pytest.approx(8.4)
    assert rows[0]["wrong_source_body_x"] == pytest.approx(9.4)
    assert rows[0]["preferred_active_obstacle_kind"] == "warmup_gate"
    assert rows[0]["matched_or_bucketed_reveal_pass"] is True


def test_materialize_source_geometry_rejects_missing_trace_step():
    rows, rejected = materialize_source_geometry_for_row(
        _row(),
        preferred_trace=_trace(32),
        wrong_trace=_trace(32),
        source_step_offsets=(-8, 0),
    )

    assert len(rows) == 1
    assert len(rejected) == 1
    assert rejected[0]["source_step"] == 24
    assert rejected[0]["rejection_reason"] == "trace_or_geometry_materialization_failed"


def test_materialize_trace_source_geometry_from_rows_uses_trace_callback():
    def trace_for(seed: int, fault_name: str, reveal_step: int):
        assert seed == 123
        assert reveal_step == 32
        base_x = 6.0 if fault_name == "preferred" else 7.0
        return _trace(24, 32, base_x=base_x)

    source_rows, rejected_rows = materialize_trace_source_geometry_from_rows(
        pd.DataFrame([_row()]),
        trace_for=trace_for,
        source_step_offsets=(-8, 0),
    )

    assert len(source_rows) == 2
    assert rejected_rows.empty
    assert list(source_rows["source_geometry_index"]) == [0, 1]
    assert list(source_rows["source_to_reveal_steps"]) == [8, 0]


def test_write_outputs_keep_implementation_guardrail_false(tmp_path: Path):
    source_rows = pd.DataFrame([_row(source_geometry_index=0, source_step=32, source_body_x=8.0)])
    rejected_rows = pd.DataFrame()

    summary = write_trace_source_geometry_outputs(
        run_dir=tmp_path,
        source_rows=source_rows,
        rejected_rows=rejected_rows,
        source_materialization_started=False,
    )

    assert summary["source_materialization_started"] is False
    assert summary["replay_started"] is False
    assert (tmp_path / "source_geometry_rows.csv").exists()
    assert (tmp_path / "summary.json").exists()


def test_runner_writes_synthetic_rows(tmp_path: Path):
    source_csv = tmp_path / "source_rows.csv"
    pd.DataFrame([_row()]).to_csv(source_csv, index=False)

    def trace_for(seed: int, fault_name: str, reveal_step: int):
        base_x = 6.0 if fault_name == "preferred" else 7.0
        return _trace(24, 32, base_x=base_x)

    summary = run_trace_source_geometry_materializer_from_rows(
        source_rows_path=source_csv,
        trace_for=trace_for,
        run_dir=tmp_path / "run",
        source_step_offsets=(-8, 0),
        source_materialization_started=False,
    )

    assert summary["source_geometry_rows"] == 2
    assert summary["rejected_rows"] == 0
    assert trace_point_at_step(_trace(24), 24).step == 24
