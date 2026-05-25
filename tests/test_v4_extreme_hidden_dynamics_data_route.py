import numpy as np
import torch

from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.v4_extreme_hidden_dynamics_data_route import (
    IdentityResidualGate,
    accepted_history_rows_for_candidate,
    build_matched_action_divergent_rows,
    classify_extreme_hidden_dynamics_route,
    fault_onset_bucket,
    matched_pair_diversity_metrics,
    source_diversity_metrics,
)


def _fault(activation_step: int, *, fidelity_class: str = "current_model_fault") -> FaultSpec:
    return FaultSpec(
        name=f"fault_{activation_step}",
        family="global_mu_drop",
        severity="extreme",
        activation_step=activation_step,
        params={"mu_scale": 0.3},
        fidelity_class=fidelity_class,
    )


def test_identity_residual_gate_returns_three_ones():
    gate = IdentityResidualGate()
    features = torch.zeros((4, 7), dtype=torch.float32)
    values = gate(features)
    assert values.shape == (4, 3)
    assert torch.allclose(values, torch.ones((4, 3), dtype=torch.float32))


def test_fault_onset_bucket_covers_expected_ranges():
    assert fault_onset_bucket(_fault(0), snapshot_step=50, warmup_steps=24) == "preexisting"
    assert fault_onset_bucket(_fault(20), snapshot_step=50, warmup_steps=24) == "warmup"
    assert fault_onset_bucket(_fault(30), snapshot_step=50, warmup_steps=24) == "pre_emergency"
    assert fault_onset_bucket(_fault(48), snapshot_step=50, warmup_steps=24) == "emergency_entry"
    assert fault_onset_bucket(_fault(60), snapshot_step=50, warmup_steps=24) == "mid_maneuver"
    assert fault_onset_bucket(_fault(90), snapshot_step=50, warmup_steps=24) == "recovery"


def test_acceptance_rows_distinguish_self_id_and_mitigation():
    normal = {
        "candidate_id": 1,
        "source_group_id": 2,
        "snapshot_uid": "2:3:40",
        "source_index": 3,
        "seed": 10,
        "step": 40,
        "warmup_mode": "brake_tap",
        "preferred_fault": "mu_drop",
        "preferred_fault_family": "global_mu_drop",
        "preferred_fidelity_class": "current_model_fault",
        "wrong_fault": "nominal",
        "wrong_fault_family": "nominal",
        "wrong_fidelity_class": "current_model_fault",
        "fault_family_pair": "global_mu_drop->nominal",
        "fault_onset_bucket": "emergency_entry",
        "source_axis": "source_state",
        "boundary_axis": "obstacle_timing",
        "horizon": 6,
        "alpha": 0.2,
        "target_obstacle_body_x": 30.0,
        "target_obstacle_body_y": 0.2,
        "target_obstacle_half_width": 0.8,
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.03,
    }
    interventions = [
        {
            "intervention_variant": "response_delay_obs",
            "supported_intervention": True,
            "intervention_collision": True,
            "intervention_margin": 0.005,
            "margin_gap_from_normal": 0.025,
            "success_drop_from_normal": True,
            "prefix_l2_mean": 0.02,
            "first_action_l2_from_normal": 0.03,
        }
    ]
    rows = accepted_history_rows_for_candidate(
        normal,
        interventions,
        primary_margin_gap_threshold=0.01,
        mitigation_margin_gap_threshold=0.02,
        action_l2_threshold=0.014,
        require_action_gap=True,
    )
    classes = {row["accepted_class"] for row in rows}
    assert classes == {"primary_self_id", "mitigation"}
    assert all(row["history_sensitive"] for row in rows)


def test_route_classification_orders_contract_proxy_and_sparse():
    accepted = []
    for idx in range(12):
        accepted.append(
            {
                "seed": idx,
                "source_group_id": idx,
                "source_index": idx,
                "fault_family_pair": f"pair{idx % 6}",
                "preferred_fault_family": f"family{idx % 6}",
                "preferred_fidelity_class": "current_model_fault",
                "warmup_mode": "natural_policy" if idx % 2 == 0 else "brake_tap",
                "fault_onset_bucket": ["preexisting", "warmup", "emergency_entry"][idx % 3],
                "boundary_axis": "obstacle_timing",
            }
        )
    assert (
        classify_extreme_hidden_dynamics_route(
            actor_changed=True,
            residual_changed=False,
            unsupported_variants=[],
            source_snapshots=10,
            replay_errors=0,
            accepted_self_id_rows=accepted,
            accepted_mitigation_rows=[],
            min_self_id_rows=10,
            min_seeds=5,
            min_source_groups=5,
            min_fault_pairs=3,
            min_warmup_modes=2,
            min_onset_buckets=3,
            max_seed_dominance=0.5,
            max_source_group_dominance=0.5,
            max_fault_pair_dominance=0.5,
            history_sensitive_candidate_rows=12,
        )
        == "v4_extreme_hidden_dynamics_data_route_contract_violation"
    )
    assert (
        classify_extreme_hidden_dynamics_route(
            actor_changed=False,
            residual_changed=False,
            unsupported_variants=[],
            source_snapshots=10,
            replay_errors=0,
            accepted_self_id_rows=[{**row, "preferred_fidelity_class": "current_model_proxy"} for row in accepted],
            accepted_mitigation_rows=[],
            min_self_id_rows=10,
            min_seeds=5,
            min_source_groups=5,
            min_fault_pairs=3,
            min_warmup_modes=2,
            min_onset_buckets=3,
            max_seed_dominance=0.5,
            max_source_group_dominance=0.5,
            max_fault_pair_dominance=0.5,
            history_sensitive_candidate_rows=12,
        )
        == "v4_extreme_hidden_dynamics_data_route_proxy_only"
    )
    assert (
        classify_extreme_hidden_dynamics_route(
            actor_changed=False,
            residual_changed=False,
            unsupported_variants=["wrong_cross_fault_history"],
            source_snapshots=10,
            replay_errors=0,
            accepted_self_id_rows=accepted,
            accepted_mitigation_rows=[],
            min_self_id_rows=10,
            min_seeds=5,
            min_source_groups=5,
            min_fault_pairs=3,
            min_warmup_modes=2,
            min_onset_buckets=3,
            max_seed_dominance=0.5,
            max_source_group_dominance=0.5,
            max_fault_pair_dominance=0.5,
            history_sensitive_candidate_rows=12,
        )
        == "v4_extreme_hidden_dynamics_data_route_sparse"
    )


def test_matched_pair_builder_finds_action_divergent_rows():
    base = {
        "reconstructed": True,
        "collision": False,
        "seed": 1,
        "target_obstacle_body_x": 40.0,
        "target_obstacle_body_y": 0.0,
        "target_obstacle_half_width": 0.8,
        "ego_vx_norm": 0.8,
        "ego_vy_norm": 0.1,
        "ego_yaw_rate_norm": 0.0,
        "min_clearance_margin": 0.02,
        "warmup_mode": "natural_policy",
        "fault_onset_bucket": "preexisting",
        "preferred_fidelity_class": "current_model_fault",
    }
    rows = [
        {
            **base,
            "candidate_id": 1,
            "preferred_fault_family": "global_mu_drop",
            "first_steer": 0.1,
            "first_throttle": 0.0,
            "first_brake": 0.3,
        },
        {
            **base,
            "candidate_id": 2,
            "preferred_fault_family": "brake_authority_drop",
            "first_steer": 0.18,
            "first_throttle": 0.0,
            "first_brake": 0.2,
        },
    ]
    pairs = build_matched_action_divergent_rows(
        rows,
        ego_distance_threshold=0.08,
        obstacle_distance_threshold=0.08,
        first_action_l2_threshold=0.02,
        max_pairs=4,
    )
    assert len(pairs) == 1
    assert pairs[0]["pair_type"] == "matched_action_divergent_proxy"
    metrics = matched_pair_diversity_metrics(pairs)
    assert metrics["unique_fault_family_pair_count"] == 1
    assert metrics["unique_left_seed_count"] == 1


def test_source_diversity_metrics_counts_proxy_and_fault_rows():
    rows = [
        {"seed": 1, "source_group_id": 1, "source_index": 1, "fault_family_pair": "a", "preferred_fault_family": "a", "preferred_fidelity_class": "current_model_fault", "warmup_mode": "natural_policy", "fault_onset_bucket": "preexisting", "boundary_axis": "obstacle_timing"},
        {"seed": 2, "source_group_id": 2, "source_index": 2, "fault_family_pair": "b", "preferred_fault_family": "b", "preferred_fidelity_class": "current_model_proxy", "warmup_mode": "brake_tap", "fault_onset_bucket": "warmup", "boundary_axis": "obstacle_lateral_offset"},
    ]
    metrics = source_diversity_metrics(rows)
    assert metrics["current_model_fault_rows"] == 1
    assert metrics["current_model_proxy_rows"] == 1
    assert metrics["unique_seed_count"] == 2
    assert np.isclose(metrics["max_seed_dominance"], 0.5)
