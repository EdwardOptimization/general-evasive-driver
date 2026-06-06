from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_response_prediction_trace_instrumentation_repair as m2859,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class _FakeModel(torch.nn.Module):
    obs_dim = 72
    act_dim = 3
    actor_encoder = "human_view_online_gru"
    response_prediction_dim = 2
    response_prediction_horizon = 2
    is_online_recurrent = True

    def __init__(self) -> None:
        super().__init__()
        self.param = torch.nn.Parameter(torch.zeros(()))
        self.response_prediction_head = object()

    def initial_hidden(self, batch_size: int, device: torch.device | None = None) -> torch.Tensor:
        return torch.zeros((batch_size, 1), device=device)

    def predict_response_recurrent_sequence(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        dones: torch.Tensor,
    ) -> torch.Tensor:
        del actions, initial_hidden, dones
        output = torch.zeros((obs.shape[0], obs.shape[1], self.response_prediction_horizon, self.response_prediction_dim))
        output[..., 0] = 1.0
        output[..., 1] = 2.0
        return output.to(obs.device)


def _subject_registry(baseline: Path, candidate: Path) -> dict[str, dict[str, object]]:
    return {
        "baseline": {
            "subject": "baseline",
            "checkpoint_path": baseline,
            "checkpoint_hash": "baseline-hash",
            "model_state_hash": "baseline-state",
            "actor_encoder": "human_view_online_gru",
            "model": _FakeModel(),
        },
        "candidate": {
            "subject": "candidate",
            "checkpoint_path": candidate,
            "checkpoint_hash": "candidate-hash",
            "model_state_hash": "candidate-state",
            "actor_encoder": "human_view_online_gru",
            "model": _FakeModel(),
        },
    }


def _source_artifacts(root: Path) -> dict[str, Path]:
    audit = root / "m2858.md"
    audit.write_text("M2858 accepts M2857\n", encoding="utf-8")
    summary = root / "m2857-summary.json"
    write_json(
        summary,
        {
            "status_pass": True,
            "response_prediction_available_count": 0,
            "per_step_localization_bucket_counts": {"response_prediction_timing_unresolved": 2},
        },
    )
    surfaces = root / "surface.csv"
    write_csv_rows(
        surfaces,
        [
            {
                "surface_id": "m2850_explanatory",
                "pair_id": "m2850-pair-0001-m1680-spec-0000",
                "task_source_id": "m1680-spec-0000",
                "profile_name": "L3_online_gru",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "ordinary_success_denominator_allowed": False,
            },
            {
                "surface_id": "m2850_explanatory",
                "pair_id": "m2850-pair-0002-m1680-spec-0001",
                "task_source_id": "m1680-spec-0001",
                "profile_name": "L3_online_gru",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "ordinary_success_denominator_allowed": False,
            },
        ],
    )
    workload = root / "m1690.csv"
    rows = []
    specs = []
    for index in range(2):
        task_source_id = f"m1680-spec-000{index}"
        config = root / f"{task_source_id}.json"
        write_json(config, {"env": {"history_length": 1}, "runtime": {}})
        rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": f"source_family_{index}|role_{index}",
                "window_tag": "mapping_window_unspecified",
                "strata": "all_72_specs",
                "executable_source_family": f"source_family_{index}",
                "env_template_family": "template",
                "profile_config_path": str(config),
                "config_exists": True,
                "profile_specific_tuning": False,
            }
        )
        specs.append({"task_source_id": task_source_id, "env_config": {"history_length": 1, "max_steps": 12}})
    write_csv_rows(workload, rows)
    executable_specs = root / "specs.json"
    write_json(executable_specs, {"executable_task_specs": specs})
    baseline = root / "baseline.pt"
    candidate = root / "candidate.pt"
    baseline.write_text("baseline", encoding="utf-8")
    candidate.write_text("candidate", encoding="utf-8")
    return {
        "audit": audit,
        "summary": summary,
        "surfaces": surfaces,
        "workload": workload,
        "specs": executable_specs,
        "baseline": baseline,
        "candidate": candidate,
    }


def test_prediction_rows_from_episode_writes_valid_and_gap_rows() -> None:
    model = _FakeModel()
    subject = {
        "subject": "candidate",
        "checkpoint_path": Path("candidate.pt"),
        "model": model,
    }
    surface = {
        "surface_id": "m2850_explanatory",
        "pair_id": "pair-1",
        "task_source_id": "task-1",
        "profile_name": "L3_online_gru",
    }
    observations = [np.full(72, float(index), dtype=np.float32) for index in range(4)]
    actions = [np.zeros(3, dtype=np.float32) for _ in observations]
    dones = [False, False, False, True]

    trace_rows, gap_rows = m2859.prediction_rows_from_episode(
        surface_row=surface,
        subject_entry=subject,
        eval_seed=1,
        observations=observations,
        actions=actions,
        dones=dones,
    )

    assert len(trace_rows) == 8
    assert any(row["target_available"] is True for row in trace_rows)
    assert any(row["target_available"] is False for row in trace_rows)
    assert gap_rows
    assert all(row["future_label_actor_visible"] is False for row in trace_rows)
    assert all(row["actor_visible_allowed"] is False for row in trace_rows)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in trace_rows)


def test_m2859_runner_writes_artifacts_and_blocks_overclaims(monkeypatch, tmp_path: Path) -> None:
    paths = _source_artifacts(tmp_path)
    output_dir = tmp_path / "m2859"
    doc_path = tmp_path / "m2859.md"
    follow_up = tmp_path / "m2860.json"

    def fake_load_subject_registry(*, baseline_checkpoint: Path, candidate_checkpoint: Path, device: str):
        del device
        return _subject_registry(baseline_checkpoint, candidate_checkpoint)

    def fake_collect_prediction_artifacts(**kwargs: object):
        selected = kwargs["selected_rows"]
        subject_registry = kwargs["subject_registry"]
        trace_rows = []
        episode_rows = []
        gap_rows = []
        for surface in selected:
            for subject_name in ("baseline", "candidate"):
                subject = subject_registry[subject_name]
                traces = [
                    {
                        field: ""
                        for field in m2859.TRACE_FIELDNAMES
                    }
                    for _ in range(2)
                ]
                for index, row in enumerate(traces):
                    row.update(
                        {
                            "trace_id": f"{surface['pair_id']}-{subject_name}-{index}",
                            "surface_id": surface["surface_id"],
                            "pair_id": surface["pair_id"],
                            "task_source_id": surface["task_source_id"],
                            "profile_name": surface["profile_name"],
                            "checkpoint_subject": subject_name,
                            "checkpoint_path": str(subject["checkpoint_path"]),
                            "eval_seed": 285900,
                            "step_index": index,
                            "horizon_index": 1,
                            "target_step_index": index + 1 if index == 0 else "",
                            "response_prediction_available": True,
                            "target_available": index == 0,
                            "response_prediction_dim": 2,
                            "response_prediction_horizon": 2,
                            "prediction_error_norm": 0.5 if index == 0 else "",
                            "prediction_error_mean_abs": 0.25 if index == 0 else "",
                            "prediction_error_max_abs": 0.4 if index == 0 else "",
                            "done_before_target": index != 0,
                            "gap_reason": "" if index == 0 else "future_target_unavailable_due_to_terminal_or_horizon_end",
                            "predicted_values": "[1,2]",
                            "target_values": "[1,2]" if index == 0 else "",
                            "diagnostic_only": True,
                            "actor_visible_allowed": False,
                            "future_label_actor_visible": False,
                            "hidden_oracle_actor_input_required": False,
                            "ranking_admissible": False,
                            "ordinary_success_denominator_allowed": False,
                        }
                    )
                trace_rows.extend(traces)
                gap_rows.append(
                    m2859.gap_row(
                        surface,
                        subject=subject_name,
                        step_index=1,
                        horizon_index=1,
                        reason="future_target_unavailable_due_to_terminal_or_horizon_end",
                    )
                )
                episode_rows.append(m2859.episode_row_from_prediction_rows(surface, subject, traces, gap_rows[-1:]))
        return trace_rows, episode_rows, gap_rows

    monkeypatch.setattr(m2859, "load_subject_registry", fake_load_subject_registry)
    monkeypatch.setattr(m2859, "collect_prediction_artifacts", fake_collect_prediction_artifacts)

    summary = m2859.run_response_prediction_trace_instrumentation_repair(
        m2858_audit=paths["audit"],
        m2857_summary=paths["summary"],
        m2857_surface_rows=paths["surfaces"],
        m1690_workload=paths["workload"],
        executable_specs=paths["specs"],
        baseline_checkpoint=paths["baseline"],
        candidate_checkpoint=paths["candidate"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        eval_seed_base=285900,
        row_count=2,
        horizon_steps=3,
        device="cpu",
    )

    assert summary["status_pass"] is True
    assert summary["selected_surface_row_count"] == 2
    assert summary["episode_row_count"] == 4
    assert summary["response_prediction_trace_row_count"] == 8
    assert summary["valid_prediction_row_count"] == 4
    assert summary["instrumentation_gap_row_count"] == 4
    assert summary["future_label_actor_visible"] is False
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    trace_rows = _read_csv(output_dir / "response_prediction_trace_rows.csv")
    gap_rows = _read_csv(output_dir / "instrumentation_gap_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert trace_rows
    assert gap_rows
    assert all(row["future_label_actor_visible"] == "False" for row in trace_rows)
    assert any(row["claim_id"] == "m2859-claim-follow_up_result_audit_registered" for row in claim_rows)
    assert all(row["status_pass"] == "True" for row in gate_rows)
    assert follow_up.exists()
    assert doc_path.exists()
