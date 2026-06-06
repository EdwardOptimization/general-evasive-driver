from __future__ import annotations

import csv
from pathlib import Path

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel as m2850,
)
from autodrift import engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight as m2838


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class _FakeModel:
    obs_dim = 72
    act_dim = 3
    actor_encoder = "human_view_online_gru"


def _write_checkpoint(path: Path, offset: float) -> None:
    state = {
        "actor_mean.weight": torch.full((3, 2), offset),
        "actor_mean.bias": torch.full((3,), offset),
    }
    write_json(path.with_suffix(".meta.json"), {"offset": offset})
    torch.save({"model_state": state}, path)


def _write_source_artifacts(root: Path, row_count: int = 3) -> dict[str, Path]:
    m1690 = root / "m1690.csv"
    workload_rows = []
    spec_rows = []
    for selected in m2838.SELECTED_TASK_SOURCES[:row_count]:
        task_source_id, task_family, source_edge, window_tag, *_rest = selected
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": task_family,
                "source_edge": source_edge,
                "window_tag": window_tag,
                "executable_source_family": "source_family",
                "env_template_family": "template",
                "strata": "all_72_specs",
                "profile_config_path": str(root / f"{task_source_id}.json"),
                "checkpoint_path": "unused-old-checkpoint.pt",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
        write_json(root / f"{task_source_id}.json", {"env": {"history_length": 1}, "runtime": {}})
        spec_rows.append(
            {
                "task_source_id": task_source_id,
                "env_config": {"history_length": 1, "max_steps": 480},
            }
        )
    write_csv_rows(m1690, workload_rows)
    specs = root / "specs.json"
    write_json(specs, {"executable_task_specs": spec_rows})

    m2849 = root / "m2849.md"
    m2849.write_text("M2849 audit accepts M2848\n", encoding="utf-8")
    m2848_summary = root / "m2848-summary.json"
    write_json(m2848_summary, {"status_pass": True, "gate_matrix_pass": True})
    m2838_summary = root / "m2838-summary.json"
    write_json(
        m2838_summary,
        {
            "status_pass": True,
            "candidate_execution_row_count": 16,
            "diagnostic_success_count": 1,
            "diagnostic_collision_count": 2,
            "diagnostic_offtrack_count": 13,
            "ordinary_success_denominator_allowed": False,
        },
    )
    baseline = root / "baseline.pt"
    candidate = root / "candidate.pt"
    _write_checkpoint(baseline, 0.0)
    _write_checkpoint(candidate, 1.0)
    return {
        "m1690": m1690,
        "specs": specs,
        "m2849": m2849,
        "m2848_summary": m2848_summary,
        "m2838_summary": m2838_summary,
        "baseline": baseline,
        "candidate": candidate,
    }


def test_m2850_writes_paired_delta_artifacts_and_blocks_overclaims(monkeypatch, tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path, row_count=3)
    output_dir = tmp_path / "m2850"
    doc_path = tmp_path / "m2850.md"
    follow_up = tmp_path / "m2851.json"

    def fake_load(path: Path, device: str):
        del path, device
        return _FakeModel(), {"model_state": {"actor_mean.weight": torch.zeros((3, 2))}}

    def fake_hash(path: Path) -> str:
        return Path(path).stem + "-hash"

    def fake_state_hash(state: dict[str, torch.Tensor]) -> str:
        return "state-" + str(len(state))

    def fake_run_workload_cell(**kwargs: object) -> dict[str, object]:
        workload_row = kwargs["workload_row"]
        profile_row = kwargs["profile_row"]
        subject = "candidate" if "candidate" in str(profile_row["checkpoint_path"]) else "baseline"
        task_index = int(str(workload_row["task_source_id"]).split("-")[-1])
        base_margin = float(task_index) / 100.0
        subject_offset = 0.05 if subject == "candidate" else 0.0
        return {
            "workload_id": workload_row["workload_id"],
            "task_source_id": workload_row["task_source_id"],
            "profile_name": workload_row["profile_name"],
            "task_family": workload_row["task_family"],
            "source_edge": workload_row["source_edge"],
            "window_tag": workload_row["window_tag"],
            "strata": workload_row["strata"],
            "executable_source_family": workload_row["executable_source_family"],
            "env_template_family": workload_row["env_template_family"],
            "profile_config_path": profile_row["config_path"],
            "checkpoint_path": profile_row["checkpoint_path"],
            "seed": kwargs["eval_seed"],
            "policy": "checkpoint",
            "steps": 12,
            "terminated": True,
            "truncated": False,
            "success": subject == "candidate",
            "collision": False,
            "obstacle_completed": subject == "candidate",
            "termination_reason": "obstacle_completed" if subject == "candidate" else "off_track",
            "outcome_bucket": "diagnostic",
            "min_clearance_margin": base_margin + subject_offset,
            "min_obstacle_clearance": base_margin + 1.0,
            "return": 1.0 + subject_offset,
            "speed_mean": 7.0,
            "high_sideslip_fraction": 0.0,
            "action_rate_mean": 0.1,
            "previous_command_norm_mean": 0.2,
            "current_action_norm_mean": 0.3,
            "action_trace_delta_mean": 0.4,
            "plan_horizon": 1,
        }

    monkeypatch.setattr(m2850, "load_actor_critic_checkpoint", fake_load)
    monkeypatch.setattr(m2850, "_file_sha256", fake_hash)
    monkeypatch.setattr(m2850, "model_state_sha256", fake_state_hash)
    monkeypatch.setattr(m2850, "run_workload_cell", fake_run_workload_cell)

    summary = m2850.run_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel(
        m1690_workload=paths["m1690"],
        executable_specs=paths["specs"],
        m2849_audit=paths["m2849"],
        m2848_summary=paths["m2848_summary"],
        m2838_summary=paths["m2838_summary"],
        baseline_checkpoint=paths["baseline"],
        candidate_checkpoint=paths["candidate"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        eval_seed_base=285000,
        row_count=3,
        horizon_steps=12,
        device="cpu",
    )

    assert summary["status_pass"] is True
    assert summary["selected_pair_count"] == 3
    assert summary["paired_execution_row_count"] == 6
    assert summary["paired_delta_row_count"] == 3
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    execution_rows = _read_csv(output_dir / "paired_execution_rows.csv")
    delta_rows = _read_csv(output_dir / "paired_delta_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    assert len(execution_rows) == 6
    assert len(delta_rows) == 3
    assert all(row["ordinary_success_denominator_allowed"] == "False" for row in execution_rows)
    assert all(row["diagnostic_only"] == "True" for row in delta_rows)
    assert all(row["ranking_admissible"] == "False" for row in delta_rows)
    assert any(row["claim_id"] == "m2850-claim-follow_up_result_audit_registered" for row in claim_rows)
    assert follow_up.exists()


def test_m2850_delta_rows_do_not_create_ranking_or_success_rate_verdict() -> None:
    subject_registry = {
        "baseline": {"checkpoint_path": Path("baseline.pt"), "checkpoint_hash": "baseline-hash"},
        "candidate": {"checkpoint_path": Path("candidate.pt"), "checkpoint_hash": "candidate-hash"},
    }
    base = {
        "pair_id": "pair-1",
        "pair_index": 1,
        "execution_row_id": "pair-1-baseline",
        "checkpoint_subject": "baseline",
        "task_source_id": "task",
        "workload_id": "task::L3_online_gru",
        "profile_name": "L3_online_gru",
        "task_family": "T4",
        "source_edge": "edge",
        "window_tag": "window",
        "source_family_tag": "source",
        "scenario_role_primary": "role",
        "diagnostic_tags": "diag",
        "eval_seed": 285000,
        "execution_status": "completed",
        "steps": 10,
        "success": False,
        "collision": False,
        "termination_reason": "off_track",
        "min_clearance_margin": 0.1,
        "return": 1.0,
        "speed_mean": 7.0,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.2,
        "previous_command_norm_mean": 0.3,
        "current_action_norm_mean": 0.4,
        "action_trace_delta_mean": 0.5,
    }
    candidate = dict(base)
    candidate.update(
        {
            "execution_row_id": "pair-1-candidate",
            "checkpoint_subject": "candidate",
            "success": True,
            "termination_reason": "obstacle_completed",
            "min_clearance_margin": 0.2,
        }
    )

    rows = m2850.build_paired_delta_rows([base, candidate], subject_registry)

    assert len(rows) == 1
    assert rows[0]["paired_execution_complete"] is True
    assert rows[0]["finite_delta"] is True
    assert rows[0]["ordinary_success_denominator_allowed"] is False
    assert rows[0]["ranking_admissible"] is False
    assert rows[0]["winner_selected"] is False
    assert rows[0]["success_rate_verdict_computed"] is False
