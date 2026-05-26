# M1021 V4 Public Base Candidate B Promotion Generalization Design

## Purpose

M1021 designs the next gate layer for Candidate B after M1019 passed full
public replay and M1020 closed the local temporal-objective repair branch.

Candidate:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Baseline:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M1021 does not train, run PPO, change actor inputs, use private holdout, or
promote. Its purpose is to prevent a public replay pass from being treated as a
promotion decision.

## M1019 Evidence To Preserve

M1019 produced:

```text
result_class: m1013_candidate_b_full_replay_gate_pass
exact_contract_pass_count: 1 / 1
candidate_preflight_pass_count: 1 / 1
public_replay_gates_passed: 6 / 6
source_diverse_pass: true
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

The exact temporal retention evidence was:

```text
weighted_total_loss: -0.883306770
total_loss_improvement: 0.001893922
candidate_action_l2_mean: 0.001016231
candidate_action_l2_max: 0.001998572
changed parameters: actor_mean.bias; actor_mean.weight
```

The selected candidate passed all six replay surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

This is enough to call Candidate B a full public-gate candidate. It is not
enough to promote it as the new public base.

## Gate Tiers

M1022 should implement a no-training promotion/generalization gate with five
separate tiers.

### Tier 0: Contract And Exact Retention

Required checks:

```text
actor input config equals M974 base
non-actor parameters equal M974 base
changed parameters are only actor_mean.bias and actor_mean.weight
M997 temporal exact retention is recomputed
```

Pass rule:

```text
exact_contract_gate_pass == true
actor_inputs_changed == false
non_actor_parameter_changed == false
```

M1022 must recompute the exact metrics rather than reusing M1019 summary only.

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
```

Pass rule:

```text
all six public replay gates pass
M267/M264 success_drop_count remains 17 / 17
source-diverse protected diagnostics pass
actor_inputs_changed == false
```

### Tier 2: Fresh Public Generalization

M1022 should add fresh public randomized evaluations that were not used to
select Candidate B.

Primary fresh distribution:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
episodes: 256
seeds: 102100, 102101
policies: M974 base, Candidate B
```

Moderate OOD distribution:

```text
config: configs/eval_m574_moderate_ood_l3.json
episodes: 128
seeds: 102120
policies: M974 base, Candidate B
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
candidate collision_rate <= base collision_rate + 0.01
```

The intent is non-regression, not a broad capability claim. M1019 already
records proof retention; M1022 checks whether this candidate harms fresh
scenario behavior.

### Tier 3: Behavior And Ablation Retention

Required behavior checks:

```text
seeds: 9505, 9506, 102130, 102131
policies: M974 base, Candidate B
Candidate B ablations: none, reset_recurrent_state, zero_all_response
episodes per seed: 80
```

Pass rule:

```text
candidate normal success >= base success - 0.01
candidate normal termination <= base termination + 0.01
candidate normal success >= candidate reset success >= candidate zero_all success
```

The reset/zero-all ordering is not full self-ID proof, but it is a cheap guard
against losing response-history dependence.

### Tier 4: Promotion Decision Routing

M1022 must not promote. It should classify Candidate B into one of these states:

```text
candidate_b_promotion_gate_candidate
candidate_b_promotion_gate_exact_retention_failed
candidate_b_promotion_gate_proof_washout
candidate_b_promotion_gate_generalization_regression
candidate_b_promotion_gate_behavior_regression
candidate_b_promotion_gate_contract_artifact
```

Only `candidate_b_promotion_gate_candidate` should route to a separate M1023
promotion audit. Actual promotion remains a later explicit milestone because it
needs a durable update to:

```text
docs/current-status.md
experiments/research_status.json
scoreboard lineage
promotion rationale
post-promotion synthesis / PPO readiness blocker
```

## Holdout Discipline

M1022 uses public fresh randomized evaluation only. It should not use private
holdout evidence.

Private holdout remains reserved for later paper-quality evidence. If a private
holdout failure is used to repair or tune a checkpoint, the holdout must be
rotated before any unbiased claim.

## Forbidden Shortcuts

M1022 must not:

```text
train or update weights
run PPO
change actor inputs
use private holdout
promote Candidate B
select thresholds after seeing failures
drop public replay surfaces because fresh eval passes
```

## Required M1022 Artifacts

M1022 should write:

```text
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/summary.json
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/exact_contract_summary.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/proof_replay_summary.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/fresh_randomized_eval_summary.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/ood_eval_summary.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/generalization_comparison.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/behavior_summary.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/behavior_comparison.csv
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/route_decision.csv
```

## Next Blocker

M1021 routes to:

```text
m1022-v4-public-base-candidate-b-promotion-generalization-gate
```

M1022 should implement the no-training Candidate B promotion/generalization
gate. Passing M1022 should route to a promotion audit. Failing M1022 should
route to the matching exact/proof/generalization/behavior audit.

## Decision

```text
candidate_b_promotion_generalization_design_admit_m1022_gate
```
