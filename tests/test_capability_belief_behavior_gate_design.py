import json

from autodrift.capability_belief_behavior_gate_design import (
    PROTECTED_CRITICAL_KEY,
    REQUIRED_INTERVENTIONS,
    build_gate_spec,
    gate_checklist_rows,
    write_gate_design_artifacts,
)


def test_build_gate_spec_contains_required_behavior_and_intervention_stages():
    spec = build_gate_spec(
        candidate_name="cand",
        candidate_checkpoint="runs/candidate.pt",
        behavior_seeds=(9503, 9504),
        strict_surface_seeds=(9900, 9920),
    )

    stage_ids = {stage["id"] for stage in spec["stages"]}

    assert "actor_input_contract" in stage_ids
    assert "behavior_retention" in stage_ids
    assert "response_history_interventions" in stage_ids
    assert "critical_key_replay" in stage_ids
    assert "matched_history_action_gate" in stage_ids
    assert "matched_history_outcome_gate" in stage_ids
    assert "strict_proof_surface" in stage_ids
    assert "promotion_boundary" in stage_ids
    assert spec["required_interventions"] == list(REQUIRED_INTERVENTIONS)


def test_gate_spec_preserves_p0_contract_and_forbidden_fields():
    spec = build_gate_spec(candidate_name="cand", candidate_checkpoint="runs/candidate.pt")
    contract_stage = next(stage for stage in spec["stages"] if stage["id"] == "actor_input_contract")

    assert contract_stage["pass_thresholds"]["actor_obs_dim"] == 72
    assert contract_stage["pass_thresholds"]["actor_encoder"] == "human_view_online_gru"
    assert "mu" in contract_stage["pass_thresholds"]["forbidden_actor_fields"]
    assert "oracle_feasibility" in contract_stage["pass_thresholds"]["forbidden_actor_fields"]
    assert "TTC" in contract_stage["pass_thresholds"]["forbidden_actor_fields"]


def test_gate_spec_includes_all_candidate_ablation_commands():
    spec = build_gate_spec(candidate_name="cand", candidate_checkpoint="runs/candidate.pt")
    behavior_stage = next(stage for stage in spec["stages"] if stage["id"] == "behavior_retention")
    commands = "\n".join(behavior_stage["commands"])

    assert "cand=runs/candidate.pt" in commands
    assert "cand_reset=runs/candidate.pt@reset_recurrent_state" in commands
    assert "cand_zero_current=runs/candidate.pt@zero_current_response" in commands
    assert "cand_zero_all=runs/candidate.pt@zero_all_response" in commands
    assert "cand_noact=runs/candidate.pt@zero_action_history" in commands


def test_gate_spec_critical_key_and_strict_thresholds_are_preregistered():
    spec = build_gate_spec(candidate_name="cand", candidate_checkpoint="runs/candidate.pt")
    critical = next(stage for stage in spec["stages"] if stage["id"] == "critical_key_replay")
    strict = next(stage for stage in spec["stages"] if stage["id"] == "strict_proof_surface")

    assert critical["pass_thresholds"]["protected_key"] == PROTECTED_CRITICAL_KEY
    assert critical["pass_thresholds"]["margin_gap_min"] == 0.005
    assert strict["pass_thresholds"]["seed_9900_selected_physical_pairs_min"] == 10
    assert strict["pass_thresholds"]["seed_9920_selected_seeds_min"] == 8


def test_gate_checklist_rows_and_artifacts(tmp_path):
    spec = build_gate_spec(candidate_name="cand", candidate_checkpoint="runs/candidate.pt")
    rows = gate_checklist_rows(spec)

    assert len(rows) == spec["gate_stage_count"]
    assert all(row["required"] for row in rows)

    write_gate_design_artifacts(tmp_path, spec)

    written = json.loads((tmp_path / "gate_spec.json").read_text(encoding="utf-8"))
    assert written["candidate_name"] == "cand"
    assert (tmp_path / "gate_checklist.csv").exists()
    assert (tmp_path / "command_plan.csv").exists()
    assert (tmp_path / "summary.json").exists()
