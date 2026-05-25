# M943 V4 Public Base Controlled Fusion Candidate Compatibility Design

## Purpose

M942 found strict objective-level candidates on the M940 raw controlled-fusion
direction:

```text
candidate_alphas: 0.0675, 0.0700, 0.0725
```

M943 designs the next exact no-update compatibility step. It does not create
checkpoints, train, run replay, run PPO, use private holdout, or promote.

## Candidate Selection

Primary candidate:

```text
alpha: 0.0725
reason: best normal-retaining row by low-tail fraction and deficit
```

Primary metrics from M942:

```text
normal_retention_pass: true
tail_lift_pass: true
target_loss_pass: true
target_tolerance_pass: true
first_action_drift_from_base_mean: 0.0026981827
first_action_drift_from_base_p95:  0.0064748540
normal_anchor_mse_mean:            0.0000038589
normal_anchor_mse_p95:             0.0000139746
normal_intervention_gap_p10:       0.0113417562
gap_deficit_mean:                  0.0129708514
low_tail_fraction:                 0.3264633119
target_action_mse_mean:            0.0005227432
```

Backup candidates:

```text
alpha: 0.0675
alpha: 0.0700
```

These are slightly more conservative and should be materialized alongside the
primary candidate in case exact checkpoint re-evaluation exposes a materialized
checkpoint or rounding issue.

## M944 Implementation Design

M944 should add a small no-update compatibility tool:

```text
autodrift.public_base_controlled_fusion_candidate_compatibility
```

The tool should:

1. Materialize the selected interpolated checkpoints with
   `checkpoint_interpolation.write_interpolation_sweep`.
2. Re-run exact objective metrics for each materialized checkpoint by comparing
   M399 base to the materialized checkpoint with alpha `1.0`.
3. Verify the materialized checkpoint only differs from M399 on:

```text
actor_mean.*
response_context_fusion.0.*
```

4. Confirm the exact metrics still pass after loading the checkpoint normally,
   not only through in-memory interpolation.
5. Write an aggregate compatibility summary.

## Candidate Checkpoint Artifacts

M944 should create:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/
  interpolation/
    manifest.json
    checkpoint_policies.csv
    checkpoint_policy_args.txt
    checkpoints/
      alpha_0_0675.pt
      alpha_0_07.pt
      alpha_0_0725.pt
  alpha_0_0675_exact/
    summary.json
    alpha_metrics.csv
  alpha_0_07_exact/
    summary.json
    alpha_metrics.csv
  alpha_0_0725_exact/
    summary.json
    alpha_metrics.csv
  summary.json
```

The aggregate `summary.json` should report:

```text
primary_alpha
candidate_alphas
materialized_checkpoint_count
exact_candidate_count
primary_candidate_exact_pass
backup_candidate_exact_pass_count
forbidden_parameter_changed
training_started
optimizer_started
replay_used
ppo_used
promoted
```

## Exact Compatibility Criteria

M944 should pass only if:

```text
materialized_checkpoint_count == 3
exact_candidate_count >= 1
primary_candidate_exact_pass is true
forbidden_parameter_changed is false
training_started is false
optimizer_started is false
replay_used is false
ppo_used is false
promoted is false
```

Each materialized candidate should be evaluated with:

```text
alphas: 1.0
```

because the checkpoint itself is already the interpolated candidate.

## Safeguards

M944 must not:

```text
train;
run replay;
run PPO;
promote;
change actor inputs;
unfreeze response_encoder, context_encoder, or online_gru_cell;
use private holdout;
claim closed-loop driver improvement.
```

If exact compatibility fails for all candidates, the controlled-fusion branch
should return to synthesis rather than retrying more public-row objective
variants.

If exact compatibility passes, the next step can design replay/proof retention
checks for the materialized candidate checkpoint. Promotion remains blocked
until replay, behavior, and generalization gates are explicitly passed.

## Decision

M943 admits M944 as a no-update implementation milestone.

Next blocker:

```text
m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation
```
