import torch

from autodrift.engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight import (
    REQUIRED_NON_ACTOR_HEAD_GROUPS,
    build_checkpoint_manifest,
    build_parameter_group_trace_rows,
    build_response_target_schema_rows,
)


def test_m2846_response_target_schema_includes_only_ego_response_targets():
    rows = build_response_target_schema_rows()
    included = [int(row["observation_index"]) for row in rows if row["included_in_response_prediction"]]
    excluded = [int(row["observation_index"]) for row in rows if not row["included_in_response_prediction"]]

    assert included == list(range(9))
    assert {9, 10, 11}.issubset(set(excluded))
    assert not any(row["hidden_or_oracle"] for row in rows)
    assert not any(row["label_or_verdict"] for row in rows)


def test_m2846_parameter_trace_rejects_actor_mean_only(tmp_path):
    source = tmp_path / "source.pt"
    candidate = tmp_path / "candidate.pt"
    state = {
        "actor_mean.weight": torch.zeros((3, 2)),
        "actor_mean.bias": torch.zeros(3),
        "response_encoder.0.weight": torch.zeros((2, 2)),
        "response_encoder.0.bias": torch.zeros(2),
        "online_gru_cell.weight_ih": torch.zeros((6, 2)),
        "online_gru_cell.weight_hh": torch.zeros((6, 2)),
        "online_gru_cell.bias_ih": torch.zeros(6),
        "online_gru_cell.bias_hh": torch.zeros(6),
        "response_context_fusion.0.weight": torch.zeros((2, 2)),
        "response_context_fusion.0.bias": torch.zeros(2),
        "critic.weight": torch.zeros((1, 2)),
        "critic.bias": torch.zeros(1),
        "log_std": torch.zeros(3),
        "response_prediction_head.weight": torch.zeros((4, 5)),
        "response_prediction_head.bias": torch.zeros(4),
    }
    candidate_state = {key: value.clone() for key, value in state.items()}
    candidate_state["response_encoder.0.bias"] = torch.ones(2)
    torch.save({"model_state": state}, source)
    torch.save({"model_state": candidate_state}, candidate)

    rows = build_parameter_group_trace_rows(source, candidate)
    manifest = build_checkpoint_manifest(
        source,
        candidate,
        ppo_config=type("Config", (), {"response_prediction_dim": 9, "response_prediction_horizon": 4})(),
        source_load_mode="strict",
        parameter_group_rows=rows,
        training_status="completed",
        train_error="",
    )

    changed = set(manifest["changed_parameter_groups"])
    assert changed & REQUIRED_NON_ACTOR_HEAD_GROUPS
    assert manifest["actor_mean_bias_only"] is False
