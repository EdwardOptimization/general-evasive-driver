from pathlib import Path

from autodrift.artifacts import write_json
from autodrift import metric_specific_bounded_panel_materialization_preflight as panel


def _spec_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    semantics: list[dict[str, object]] = []
    repaired: list[dict[str, object]] = []
    for role_index, role in enumerate(panel.ROLE_PANEL_SELECTIONS, start=1):
        for source_index, source_id in enumerate(role["source_scenario_spec_ids"]):
            source = str(source_id)
            row = {
                "scenario_spec_id": source,
                "m1728_scenario_spec_id": source,
                "scenario_family_id": f"S{role_index}",
                "scenario_family": f"family_{role_index}",
                "scenario_role": f"role_{role_index}",
                "allowed_labels_metadata_only": "aes_feasible",
                "evaluation_role": role["panel_evaluation_role"],
                "primary_metric_family": role["panel_primary_metric_family"],
                "hidden_dynamics_bucket": f"hidden_{source_index % 2}",
                "road_boundary_bucket": f"road_{source_index % 2}",
                "obstacle_timing_bucket": f"timing_{source_index % 3}",
                "obstacle_lateral_bucket": f"lateral_{source_index % 2}",
                "ranking_eligible_after_audit": False,
                "diagnostic_only_no_ranking_claim": True,
            }
            semantics.append(row)
            repaired.append(
                {
                    **row,
                    "sampling_repair_source": "synthetic",
                    "sampling_repair_variant_id": "none",
                    "sampling_repair_applied": False,
                    "env_config": {"include_privileged_params": False},
                }
            )
    return semantics, repaired


def test_metric_specific_bounded_panel_materialization_smoke(tmp_path: Path, monkeypatch) -> None:
    semantics, repaired = _spec_rows()
    semantics_path = tmp_path / "semantics.json"
    repaired_path = tmp_path / "repaired.json"
    write_json(semantics_path, {"semantics_scenario_specs": semantics})
    write_json(repaired_path, {"repaired_scenario_specs": repaired})

    monkeypatch.setattr(
        panel,
        "profile_artifact_rows",
        lambda m1674_run_dir: [
            {
                "profile_name": "L1_one_step",
                "config_path": "config-a.json",
                "checkpoint_path": "checkpoint-a.pt",
                "config_exists": True,
                "checkpoint_exists": True,
            },
            {
                "profile_name": "L3_online_gru",
                "config_path": "config-b.json",
                "checkpoint_path": "checkpoint-b.pt",
                "config_exists": True,
                "checkpoint_exists": True,
            },
        ],
    )
    monkeypatch.setattr(panel, "contract_violation_rows", lambda panel_specs: [])
    monkeypatch.setattr(
        panel,
        "unsupported_scenario_feature_rows",
        lambda: [{"feature": "wheel_specific_grip_loss", "covered_by_current_preflight": False}],
    )

    summary = panel.run_metric_specific_bounded_panel_materialization_preflight(
        semantics_scenario_specs_path=semantics_path,
        repaired_scenario_specs_path=repaired_path,
        output_dir=tmp_path / "out",
        target_profile_count=2,
    )

    assert summary["result_class"] == "metric_specific_bounded_panel_materialization_preflight_pass"
    assert summary["panel_spec_count"] == 24
    assert summary["role_panel_count"] == 4
    assert set(summary["specs_per_role"].values()) == {6}
    assert summary["profile_count"] == 2
    assert summary["panel_cell_count"] == 48
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "bounded_panel_specs.json").exists()
    assert (tmp_path / "out" / "bounded_panel_matrix.csv").exists()
    assert (tmp_path / "out" / "bounded_panel_metric_contract.json").exists()
