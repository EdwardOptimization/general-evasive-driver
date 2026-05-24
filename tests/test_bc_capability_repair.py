import torch

from autodrift.bc_capability_repair import (
    CAPABILITY_TARGETS,
    CapabilityHead,
    CapabilityRepairWeights,
    build_capability_repair_metadata,
    capability_rank_loss,
    capability_regression_loss,
    capability_repair_loss,
)


def test_capability_regression_loss_decreases_on_synthetic_case():
    torch.manual_seed(5930)
    hidden = torch.randn(64, 5)
    target = torch.stack(
        [
            hidden[:, 0] * 0.4 + hidden[:, 1] * 0.1,
            hidden[:, 2] * -0.3,
            hidden[:, 3] * 0.2 + hidden[:, 4] * 0.2,
        ],
        dim=1,
    )
    head = CapabilityHead(hidden_size=5, output_dim=3)
    optimizer = torch.optim.Adam(head.parameters(), lr=0.03)
    target_mean = target.mean(dim=0, keepdim=True)
    target_std = target.std(dim=0, keepdim=True)

    with torch.no_grad():
        initial = capability_regression_loss(
            head(hidden),
            target,
            target_mean=target_mean,
            target_std=target_std,
        ).item()

    for _ in range(120):
        optimizer.zero_grad()
        loss = capability_regression_loss(
            head(hidden),
            target,
            target_mean=target_mean,
            target_std=target_std,
        )
        loss.backward()
        optimizer.step()

    final = capability_regression_loss(
        head(hidden),
        target,
        target_mean=target_mean,
        target_std=target_std,
    ).item()
    assert final < initial * 0.25


def test_capability_rank_loss_rewards_correct_ordering():
    target_std = torch.ones(1, 3)
    target_left = torch.tensor([[2.0, -1.0, 0.5]])
    target_right = torch.tensor([[0.0, 1.0, 0.0]])
    good_left = torch.tensor([[2.0, -1.5, 0.7]])
    good_right = torch.tensor([[0.1, 0.8, 0.0]])
    bad_left = good_right
    bad_right = good_left

    good_loss = capability_rank_loss(
        good_left,
        good_right,
        target_left,
        target_right,
        target_std=target_std,
    )
    bad_loss = capability_rank_loss(
        bad_left,
        bad_right,
        target_left,
        target_right,
        target_std=target_std,
    )

    assert good_loss.item() < bad_loss.item()


def test_capability_repair_loss_is_weighted_and_differentiable():
    action = torch.tensor([[0.1, 0.2, -0.1]], requires_grad=True)
    target_action = torch.zeros(1, 3)
    anchor_action = torch.ones(1, 3) * 0.05
    capability_prediction = torch.tensor([[0.2, -0.1, 0.3]], requires_grad=True)
    capability_target = torch.zeros(1, 3)
    pair_prediction_left = torch.tensor([[0.5, -0.2, 0.1]], requires_grad=True)
    pair_prediction_right = torch.tensor([[0.0, 0.3, -0.1]], requires_grad=True)
    pair_target_left = torch.tensor([[1.0, -1.0, 0.4]])
    pair_target_right = torch.zeros(1, 3)
    target_mean = torch.zeros(1, 3)
    target_std = torch.ones(1, 3)

    losses = capability_repair_loss(
        action=action,
        target_action=target_action,
        anchor_action=anchor_action,
        capability_prediction=capability_prediction,
        capability_target=capability_target,
        pair_prediction_left=pair_prediction_left,
        pair_prediction_right=pair_prediction_right,
        pair_target_left=pair_target_left,
        pair_target_right=pair_target_right,
        target_mean=target_mean,
        target_std=target_std,
        weights=CapabilityRepairWeights(
            action_bc=1.0,
            capability_regression=1.0,
            capability_rank=1.0,
            action_anchor=1.0,
        ),
    )

    losses.total.backward()
    assert torch.isfinite(losses.total)
    assert action.grad is not None
    assert capability_prediction.grad is not None
    assert pair_prediction_left.grad is not None
    assert pair_prediction_right.grad is not None


def test_capability_repair_metadata_preserves_actor_contract():
    metadata = build_capability_repair_metadata(
        {
            "input_contract": "P0_human_view_no_wheel_no_oracle",
            "actor_encoder": "human_view_online_gru",
            "actor_history_length": 1,
            "ppo_used": True,
            "promoted": True,
        }
    )

    assert metadata["input_contract"] == "P0_human_view_no_wheel_no_oracle"
    assert metadata["actor_encoder"] == "human_view_online_gru"
    assert metadata["actor_history_length"] == 1
    assert metadata["ppo_used"] is False
    assert metadata["promoted"] is False
    assert metadata["capability_repair"]["labels_enter_actor_input"] is False
    assert metadata["capability_repair"]["training_only_targets"] == list(CAPABILITY_TARGETS)
