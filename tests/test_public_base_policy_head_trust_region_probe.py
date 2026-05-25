import torch

from autodrift.public_base_policy_head_trust_region_probe import (
    classify_policy_head_trust_region_probe,
    interpolate_actor_mean_state,
    set_actor_mean_trainable_only,
    state_checksums,
)
from autodrift.public_base_policy_head_raw_direction_feasibility import (
    classify_policy_head_raw_direction_feasibility,
)
from autodrift.public_base_controlled_fusion_surface_probe import (
    classify_controlled_fusion_surface_probe,
    interpolate_controlled_surface_state,
    set_controlled_fusion_trainable_only,
)
from autodrift.public_base_controlled_fusion_raw_direction_feasibility import (
    classify_controlled_fusion_raw_direction_feasibility,
)
from autodrift.train_ppo import ActorCritic


def test_classify_policy_head_trust_region_probe_candidate():
    assert (
        classify_policy_head_trust_region_probe(
            non_actor_mean_changed=False,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=1,
            any_tail_lift=True,
            any_normal_retained_tail_lift=True,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_policy_head_trust_region_probe_candidate"
    )


def test_classify_policy_head_trust_region_probe_contract_artifact():
    assert (
        classify_policy_head_trust_region_probe(
            non_actor_mean_changed=True,
            actor_mean_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=1,
            any_tail_lift=True,
            any_normal_retained_tail_lift=True,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_policy_head_trust_region_probe_contract_artifact"
    )


def test_set_actor_mean_trainable_only_freezes_other_parameters():
    model = ActorCritic(obs_dim=4, act_dim=2, hidden_size=8)
    set_actor_mean_trainable_only(model)

    trainable_names = {name for name, parameter in model.named_parameters() if parameter.requires_grad}

    assert trainable_names == {"actor_mean.weight", "actor_mean.bias"}


def test_interpolate_actor_mean_state_preserves_non_actor_parameters():
    model = ActorCritic(obs_dim=4, act_dim=2, hidden_size=8)
    base = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    raw = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    raw["actor_mean.weight"] = raw["actor_mean.weight"] + 2.0
    raw["actor_mean.bias"] = raw["actor_mean.bias"] - 1.0
    raw["critic.weight"] = raw["critic.weight"] + 5.0

    mixed = interpolate_actor_mean_state(base, raw, 0.25)

    assert torch.allclose(mixed["actor_mean.weight"], base["actor_mean.weight"] + 0.5)
    assert torch.allclose(mixed["actor_mean.bias"], base["actor_mean.bias"] - 0.25)
    assert torch.allclose(mixed["critic.weight"], base["critic.weight"])


def test_state_checksums_separate_actor_head_from_backbone():
    model = ActorCritic(obs_dim=4, act_dim=2, hidden_size=8)
    base = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    updated = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    updated["actor_mean.weight"] = updated["actor_mean.weight"] + 0.1

    base_checksums = state_checksums(base)
    updated_checksums = state_checksums(updated)

    assert base_checksums["actor_mean"] != updated_checksums["actor_mean"]
    assert base_checksums["feature_backbone"] == updated_checksums["feature_backbone"]
    assert base_checksums["critic"] == updated_checksums["critic"]
    assert base_checksums["log_std"] == updated_checksums["log_std"]
    assert base_checksums["non_actor_mean"] == updated_checksums["non_actor_mean"]


def test_classify_policy_head_raw_direction_feasibility_trust_region_conflict():
    assert (
        classify_policy_head_raw_direction_feasibility(
            non_actor_mean_changed_between_checkpoints=False,
            actor_mean_changed_between_checkpoints=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=0,
            any_tail_lift=True,
            any_normal_retained_tail_lift=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_policy_head_raw_direction_feasibility_trust_region_conflict"
    )


def test_classify_policy_head_raw_direction_feasibility_contract_artifact():
    assert (
        classify_policy_head_raw_direction_feasibility(
            non_actor_mean_changed_between_checkpoints=True,
            actor_mean_changed_between_checkpoints=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=0,
            any_tail_lift=True,
            any_normal_retained_tail_lift=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_policy_head_raw_direction_feasibility_contract_artifact"
    )


def test_set_controlled_fusion_trainable_only_freezes_encoders():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    set_controlled_fusion_trainable_only(model)

    trainable_names = {name for name, parameter in model.named_parameters() if parameter.requires_grad}

    assert trainable_names == {
        "actor_mean.weight",
        "actor_mean.bias",
        "response_context_fusion.0.weight",
        "response_context_fusion.0.bias",
    }


def test_interpolate_controlled_surface_preserves_forbidden_parameters():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    base = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    raw = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    raw["actor_mean.weight"] = raw["actor_mean.weight"] + 2.0
    raw["response_context_fusion.0.bias"] = raw["response_context_fusion.0.bias"] - 1.0
    raw["response_encoder.0.weight"] = raw["response_encoder.0.weight"] + 5.0

    mixed = interpolate_controlled_surface_state(base, raw, 0.25)

    assert torch.allclose(mixed["actor_mean.weight"], base["actor_mean.weight"] + 0.5)
    assert torch.allclose(mixed["response_context_fusion.0.bias"], base["response_context_fusion.0.bias"] - 0.25)
    assert torch.allclose(mixed["response_encoder.0.weight"], base["response_encoder.0.weight"])


def test_classify_controlled_fusion_surface_probe_candidate():
    assert (
        classify_controlled_fusion_surface_probe(
            forbidden_parameter_changed=False,
            actor_mean_changed=True,
            fusion_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=1,
            any_tail_lift=True,
            any_normal_retained_tail_lift=True,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_controlled_fusion_surface_probe_candidate"
    )


def test_classify_controlled_fusion_raw_direction_feasibility_contract_artifact():
    assert (
        classify_controlled_fusion_raw_direction_feasibility(
            forbidden_parameter_changed_between_checkpoints=True,
            allowed_surface_changed_between_checkpoints=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=0,
            any_tail_lift=True,
            any_normal_retained_tail_lift=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_controlled_fusion_raw_direction_feasibility_contract_artifact"
    )
