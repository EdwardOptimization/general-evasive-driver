# M964 V4 Public Base Direction Target Actor-Fit Objective Implementation

## Purpose

M964 runs the first objective-only actor-fit probe on the M962 exported
direction-target corpus.

It updates only `actor_mean`. It does not run PPO, change actor inputs, use
private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_direction_target_actor_fit
```

## Artifacts

```text
runs/m964_v4_public_base_direction_target_actor_fit/summary.json
runs/m964_v4_public_base_direction_target_actor_fit/target_fit_metrics.csv
runs/m964_v4_public_base_direction_target_actor_fit/proof_anchor_metrics.csv
runs/m964_v4_public_base_direction_target_actor_fit/retention_anchor_metrics.csv
runs/m964_v4_public_base_direction_target_actor_fit/m267_preflight_summary.csv
runs/m964_v4_public_base_direction_target_actor_fit/route_decision.csv
```

## Implementation

M964 adds:

```text
src/autodrift/public_base_direction_target_actor_fit.py
tests/test_public_base_direction_target_actor_fit.py
```

Training surface:

```text
trainable: actor_mean
frozen: feature backbone, response/context encoders, GRU, critic, log_std
```

Objective inputs:

```text
accepted direction targets: 1280
branch-separated proof anchors: 160
retention anchors: 1149
```

Objective terms:

```text
direction target MSE
proof anchor MSE
retention anchor MSE
actor_mean parameter anchor
```

## Result

```text
result_class: direction_target_actor_fit_candidate
candidate_alpha_count: 5
candidate_alphas: 0.05, 0.10, 0.20, 0.50, 1.00
target_fit_improved_count: 5
proof_preflight_pass_count: 5
retention_pass_count: 5
```

All evaluated interpolation alphas pass:

```text
alpha 0.05
alpha 0.10
alpha 0.20
alpha 0.50
alpha 1.00
```

Best target-fit among evaluated alphas is `alpha=1.00`:

```text
baseline direction-target weighted MSE: 0.0000080667
alpha 1.00 direction-target weighted MSE: 0.0000054974
```

M267/M264 active proof preflight remains intact for all alphas:

```text
candidate_success_drop_count: 4 / 4
active_rows_pass: true
```

Retention and proof anchors stay inside tolerance:

```text
alpha 1.00 proof_anchor weighted MSE: 0.0000000405
alpha 1.00 retention_anchor weighted MSE: 0.0000007908
```

Checksum audit:

```text
actor_mean_changed: true
non_actor_mean_changed: false
feature_backbone_changed: false
critic_changed: false
log_std_changed: false
actor_input_contract_changed: false
ppo_used: false
promoted: false
```

Candidate checkpoints:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_05.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_1.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_2.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_0_5.pt
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

## Interpretation

M964 proves the exported M962 target corpus is fit-able by the policy head
without immediately washing out the active M267/M264 proof preflight.

Supported:

- M962 target export is trainable by `actor_mean`;
- direction-target loss improves at every evaluated interpolation alpha;
- M267/M264 active proof rows stay branch-separated under the candidate heads;
- retention anchors stay within tolerance;
- broader actor/recurrent inputs remain unchanged.

Not yet proven:

- full public replay stack passes;
- behavior seeds pass;
- full M267/M264 replay surface remains `17 / 17`;
- candidate improves closed-loop behavior outside the target/proof anchor sets;
- PPO continuation is safe.

## Next Blocker

M964 routes to:

```text
m965-v4-public-base-direction-target-actor-fit-replay-gate-design
```

M965 should design the no-training replay gate for the M964 candidates. It
should evaluate candidate alphas through the public replay stack and behavior
seeds before any PPO or promotion.
