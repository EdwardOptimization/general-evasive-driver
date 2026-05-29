from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.capability_step_sequence_intervention_probe import TracePoint
from autodrift.forward_geometry_source_miner import prepare_source_geometry_frame as prepare_m1438_source_frame
from autodrift.source_action_divergence_enrichment import (
    build_source_step_variant_hiddens,
    enrich_source_geometry_row,
    evaluate_source_step_variant_actions,
    prepare_source_geometry_frame,
    run_source_action_divergence_enrichment_from_rows,
    select_enriched_source_rows,
    trace_prefix_to_step,
    write_enrichment_outputs,
)


class _FakeEnv:
    def __init__(self):
        self.config = SimpleNamespace(max_steps=64)
        self.step_count = 0
        self.last_obs = np.zeros(72, dtype=np.float32)

    def step(self, action):
        self.step_count += 1
        obs = np.zeros(72, dtype=np.float32)
        obs[:3] = np.asarray(action, dtype=np.float32)
        self.last_obs = obs
        return obs, 0.0, False, False, {"step": self.step_count}


class _FakeModel:
    def initial_hidden(self, batch_size: int, device: torch.device):
        return torch.zeros((batch_size, 3), dtype=torch.float32, device=device)

    def recurrent_features_tensor(self, obs_t: torch.Tensor, hidden_t: torch.Tensor):
        obs_part = obs_t[:, :3].to(dtype=torch.float32)
        features = hidden_t + 0.05 * obs_part
        next_hidden = hidden_t + 0.01 * obs_part
        return features, next_hidden

    def actor_mean(self, features: torch.Tensor):
        return features[:, :3]


def _point(step: int, hidden_values: tuple[float, float, float]) -> TracePoint:
    obs = np.zeros(72, dtype=np.float32)
    obs[:3] = np.array([0.2, -0.1, 0.05], dtype=np.float32)
    return TracePoint(
        seed=101,
        fault=SimpleNamespace(name="fault"),
        step=step,
        observation=obs,
        hidden=torch.tensor([hidden_values], dtype=torch.float32),
        env=_FakeEnv(),
        info={"step": step},
    )


def _trace(hidden_base: float) -> list[TracePoint]:
    return [
        _point(8, (hidden_base, 0.0, 0.0)),
        _point(16, (hidden_base + 0.1, -0.1, 0.0)),
        _point(24, (hidden_base + 0.2, -0.2, 0.1)),
    ]


def _source_row(**updates):
    row = {
        "source_geometry_index": 3,
        "upstream_source_index": 8,
        "seed": 101,
        "reveal_step": 32,
        "source_step": 24,
        "preferred_fault": "preferred",
        "preferred_fault_family": "pref_family",
        "wrong_fault": "wrong",
        "wrong_fault_family": "wrong_family",
        "capability_pair": "pref_family->wrong_family",
        "preferred_reveal_bucket": "bucket-a",
        "wrong_reveal_bucket": "bucket-b",
        "matched_current_pass": False,
        "bucketed_current_pass": True,
        "source_body_x": 8.0,
        "source_body_y": 0.2,
        "source_half_width": 0.6,
    }
    row.update(updates)
    return row


def test_prepare_source_geometry_frame_requires_m1440_schema():
    with pytest.raises(ValueError, match="missing required columns"):
        prepare_source_geometry_frame(pd.DataFrame([{"seed": 101}]))

    prepared = prepare_source_geometry_frame(pd.DataFrame([_source_row()]))
    assert int(prepared.loc[0, "source_step"]) == 24
    assert bool(prepared.loc[0, "bucketed_current_pass"]) is True


def test_source_step_variant_hiddens_are_anchored_at_source_step():
    model = _FakeModel()
    device = torch.device("cpu")
    preferred = _trace(0.3)
    wrong = _trace(-0.4)

    hiddens = build_source_step_variant_hiddens(
        model=model,
        preferred_trace=preferred,
        wrong_trace=wrong,
        source_step=24,
        recent_window_length=8,
        device=device,
    )

    assert torch.allclose(hiddens["normal"], preferred[-1].hidden)
    assert torch.allclose(hiddens["wrong_warmup_history_same_reveal"], wrong[-1].hidden)
    assert torch.allclose(hiddens["reset_hidden"], torch.zeros_like(hiddens["reset_hidden"]))
    assert trace_prefix_to_step(preferred, 24)[-1].step == 24


def test_evaluate_source_step_variant_actions_measures_first_and_sequence_distance():
    model = _FakeModel()
    device = torch.device("cpu")
    source = _trace(0.3)[-1]
    normal_metrics, normal_actions = evaluate_source_step_variant_actions(
        model=model,
        source_snapshot=source,
        variant="normal",
        variant_hidden=source.hidden,
        normal_first_action=None,
        normal_actions=None,
        sequence_horizon=4,
        response_dim=12,
        device=device,
    )
    reset_metrics, _ = evaluate_source_step_variant_actions(
        model=model,
        source_snapshot=source,
        variant="warmup_removed",
        variant_hidden=model.initial_hidden(1, device),
        normal_first_action=normal_actions[0],
        normal_actions=normal_actions,
        sequence_horizon=4,
        response_dim=12,
        device=device,
    )

    assert normal_metrics["first_action_l2"] == 0.0
    assert reset_metrics["first_action_l2"] > 0.014
    assert reset_metrics["sequence_action_l2_mean"] > 0.025
    assert reset_metrics["sequence_steps"] == 4


def test_enrich_source_geometry_row_emits_source_step_variants():
    rows, rejected = enrich_source_geometry_row(
        _source_row(),
        model=_FakeModel(),
        preferred_trace=_trace(0.3),
        wrong_trace=_trace(-0.4),
        variants=("normal", "warmup_removed", "wrong_warmup_history_same_reveal"),
        recent_window_length=8,
        sequence_horizon=4,
        response_dim=12,
        device=torch.device("cpu"),
    )

    assert rejected == []
    by_variant = {row["variant"]: row for row in rows}
    assert by_variant["normal"]["variant_time_anchor"] == "source_step"
    assert by_variant["warmup_removed"]["history_variant"] is True
    assert by_variant["warmup_removed"]["action_divergent"] is True
    assert by_variant["wrong_warmup_history_same_reveal"]["first_action_l2"] > 0.014


def test_select_enriched_rows_are_m1438_compatible():
    rows, _ = enrich_source_geometry_row(
        _source_row(),
        model=_FakeModel(),
        preferred_trace=_trace(0.3),
        wrong_trace=_trace(-0.4),
        variants=("normal", "warmup_removed", "reset_hidden"),
        sequence_horizon=4,
        response_dim=12,
        device=torch.device("cpu"),
    )
    selected = select_enriched_source_rows(
        pd.DataFrame(rows),
        max_candidates=8,
        per_seed_cap=4,
        per_capability_pair_cap=4,
        per_reveal_bucket_cap=4,
        per_source_step_cap=4,
        per_variant_cap=4,
    )

    assert set(selected["variant"]) == {"warmup_removed"}
    prepared = prepare_m1438_source_frame(selected)
    assert "source_body_x" in prepared.columns
    assert float(prepared.iloc[0]["sequence_action_l2_mean"]) > 0.025


def test_runner_writes_outputs_without_public_run_guardrail(tmp_path: Path):
    source_csv = tmp_path / "source_geometry_rows.csv"
    pd.DataFrame([_source_row()]).to_csv(source_csv, index=False)

    def trace_for(seed: int, fault_name: str, reveal_step: int):
        assert seed == 101
        assert reveal_step == 32
        return _trace(0.3 if fault_name == "preferred" else -0.4)

    summary = run_source_action_divergence_enrichment_from_rows(
        source_geometry_rows_path=source_csv,
        model=_FakeModel(),
        trace_for=trace_for,
        run_dir=tmp_path / "run",
        device=torch.device("cpu"),
        variants=("normal", "warmup_removed"),
        sequence_horizon=4,
        source_enrichment_started=False,
    )

    assert summary["enriched_source_geometry_rows"] == 2
    assert summary["selected_enriched_rows"] == 1
    assert summary["source_enrichment_started"] is False
    assert summary["replay_started"] is False
    assert (tmp_path / "run" / "selected_enriched_rows.csv").exists()


def test_write_outputs_keeps_guardrails_false(tmp_path: Path):
    enriched = pd.DataFrame([{**_source_row(), "variant": "warmup_removed", "history_variant": True, "action_divergent": True, "first_action_l2": 0.1, "sequence_action_l2_mean": 0.2}])
    selected = enriched.copy()
    rejected = pd.DataFrame()

    summary = write_enrichment_outputs(
        run_dir=tmp_path,
        enriched=enriched,
        selected=selected,
        rejected=rejected,
        source_enrichment_started=False,
    )

    assert summary["source_enrichment_started"] is False
    assert summary["source_preflight_started"] is False
    assert (tmp_path / "summary.json").exists()
