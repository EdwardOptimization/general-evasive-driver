# M967 V4 Public Base Direction Target Actor-Fit Promotion Generalization Design

## Purpose

M967 designs the next gate layer for the M966 replay-gate-passing
direction-target actor-fit candidate.

Candidate:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Baseline:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M967 does not train, run PPO, change actor inputs, use private holdout, or
promote. Its purpose is to prevent a public proof-gate pass from being treated
as a promotion decision.

## M966 Evidence To Preserve

M966 produced:

```text
result_class: direction_target_actor_fit_replay_gate_pass
candidate_preflight_pass_count: 5 / 5
selected_alpha: 1.0
public_replay_gates_passed: 6 / 6
source_diverse_protected_status: pass
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

The selected candidate passed:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

It also retained behavior seeds `9505` and `9506`:

```text
base success:      0.8625
candidate success: 0.8625
reset success:     0.8500
zero-all success:  0.8000
```

This is enough to call `alpha_1_0` a public-proof-passing candidate. It is not
enough to promote it.

## Gate Tiers

M968 should implement a no-training promotion/generalization gate with three
separate tiers.

### Tier 1: Proof Retention

Required proof gates:

```text
M183/M168 replay gate
M183/M170 replay gate
M193/M189 replay gate
M212/M204 replay gate
M223/M219 replay gate
M267/M264 replay gate
source-diverse protected diagnostic bundle
old key 9944 diagnostic-only report
actor-input contract check
```

Pass rule:

```text
all six public replay gates pass
M267/M264 success_drop_count remains 17 / 17
source-diverse protected diagnostics pass or are explicitly diagnostic-only
actor_inputs_changed == false
```

### Tier 2: Fresh Generalization

M968 should add fresh public randomized evaluations that were not used to fit
M964.

Primary fresh distribution:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
episodes: 256
seeds: 96700 and 96701
policies: M399 base, M964 alpha_1_0 candidate
```

Moderate OOD distribution:

```text
config: configs/eval_m574_moderate_ood_l3.json
episodes: 128
seed: 96720
policies: M399 base, M964 alpha_1_0 candidate
```

Metrics:

```text
success_rate
termination_rate
min_clearance_margin_mean
return_mean
collision/off-road/spin termination histogram if available
```

Pass rule:

```text
candidate success_rate >= base success_rate - 0.01
candidate termination_rate <= base termination_rate + 0.01
candidate min_clearance_margin_mean >= base margin_mean - 0.005
no new dominant termination reason appears
```

The intent is non-regression, not a broad capability claim. M966 already
records the mechanism-side advantage through target-fit improvement and public
proof-margin retention; M968 checks that this does not harm fresh scenario
behavior.

### Tier 3: Behavior And Ablation Retention

Required behavior checks:

```text
seeds: 9505, 9506, 96730, 96731
policies: M399 base, M964 alpha_1_0 candidate
candidate ablations: none, reset_recurrent_state, zero_all_response
episodes per seed: 80
```

Pass rule:

```text
candidate normal success >= base success - 0.01
candidate normal termination <= base termination + 0.01
candidate normal success >= candidate reset success >= candidate zero_all success
```

The reset/zero-all ordering is not a full self-ID proof, but it remains a
cheap guard against losing the response-history dependence already visible in
the public proof rows.

## Promotion Decision

M968 must not promote. It should classify the candidate into one of these
states:

```text
direction_target_actor_fit_promotion_gate_candidate
direction_target_actor_fit_promotion_gate_proof_washout
direction_target_actor_fit_promotion_gate_generalization_regression
direction_target_actor_fit_promotion_gate_behavior_regression
direction_target_actor_fit_promotion_gate_contract_artifact
```

Only `direction_target_actor_fit_promotion_gate_candidate` should route to a
separate promotion audit.

Actual promotion should remain a later explicit milestone, because the project
needs a durable update to:

```text
docs/current-status.md
experiments/research_status.json
scoreboard lineage
promotion rationale
```

## Holdout Discipline

M968 uses public fresh randomized evaluation only. It should not use private
holdout evidence.

Private holdout remains reserved for later paper-quality promotion evidence.
If private holdout failures are used to repair or tune a checkpoint, the
holdout must be rotated before any unbiased claim.

## Forbidden Shortcuts

M968 must not:

```text
train or update weights
run PPO
change actor inputs
use private holdout
promote the candidate
select thresholds after seeing failures
drop public replay surfaces because fresh eval passes
```

## Required M968 Artifacts

M968 should write:

```text
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/summary.json
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/proof_replay_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/fresh_randomized_eval_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/ood_eval_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/behavior_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/behavior_comparison.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/route_decision.csv
```

## Next Blocker

M967 routes to:

```text
m968-v4-public-base-direction-target-actor-fit-promotion-generalization-gate-implementation
```

M968 should implement the no-training candidate comparison gate. Passing M968
should route to a promotion audit. Failing M968 should route to the matching
proof/generalization/behavior audit.
