# M1063 V4 Public Base Family-Intersection Gate Integration Design

## Purpose

M1063 designs how the M1061 family-intersection corpus becomes a first-class
public proof gate before any medium PPO escalation.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Inputs

Current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

M1061 selector artifacts:

```text
runs/m1061_family_intersection_selector/family_intersection_selected_rows.csv
runs/m1061_family_intersection_summary/summary.json
```

M1061 compact source corpora:

```text
short61049:
  runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv

short61050:
  runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv

short61051:
  runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
```

Source family checkpoints:

```text
short61049: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050: runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051: runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

## Gate Meaning

M1061 has two different roles:

```text
corpus validation:
  all three short-PPO family policies agree that the selected rows are
  normal-history success and wrong-history failure rows.

future PPO proposal gate:
  a new candidate checkpoint must preserve those rows when replayed as the
  candidate policy.
```

The future PPO proposal gate should not rerun all six family-to-family
directions every time. Those six directions are the corpus-validation evidence
from M1061. For a new candidate checkpoint, the public proof gate should run
three source-to-candidate replay gates:

```text
short61049 corpus:
  baseline: short61049
  candidate: proposed_checkpoint

short61050 corpus:
  baseline: short61050
  candidate: proposed_checkpoint

short61051 corpus:
  baseline: short61051
  candidate: proposed_checkpoint
```

This checks that the candidate preserves the refreshed family-intersection
proof rows across all three source checkpoints.

## Pass/Fail Rules

Use the same conservative retention thresholds as current boundary replay
gates:

```text
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
max_continuation_steps: 60
env_config: configs/m121_human_view_zero_obstacle_relvel.json
```

For each of the three source corpora, require:

```text
gate_pass: true
candidate_success_drop_count >= baseline_success_drop_count
candidate_normal_success_rate >= baseline_normal_success_rate
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
```

Global M1061 gate pass:

```text
family_intersection_replay_gate_count: 3
family_intersection_replay_gates_passed: 3
overall_pass: true
failure_types: none
```

Any failure should classify as:

```text
proof_washout
```

and must block PPO promotion or PPO length escalation.

## Implementation Design

M1064 should add a reusable wrapper:

```text
src/autodrift/family_intersection_public_gate.py
tests/test_family_intersection_public_gate.py
```

The wrapper should reuse `boundary_outcome_replay_gate`, not duplicate rollout
logic.

CLI shape:

```text
python -m autodrift.family_intersection_public_gate \
  --source-policy short61049=... \
  --source-policy short61050=... \
  --source-policy short61051=... \
  --candidate-policy proposal=... \
  --source-corpus short61049=... \
  --source-corpus short61050=... \
  --source-corpus short61051=... \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --run-dir runs/...
```

Output artifacts:

```text
summary.json
replay_gate_summary.csv
diagnostic_summary.csv
replay_gates/<source>_to_<candidate>/
```

Summary fields:

```text
run_type: family_intersection_public_gate
source_policy_count
source_corpus_count
candidate_policy
replay_gate_count
replay_gates_passed
failed_replay_gates
overall_pass
failure_types
actor_inputs_changed
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

The wrapper should validate:

```text
source policy labels match source corpus labels
candidate policy label differs from source labels
all corpus CSVs exist
all source checkpoints exist
candidate checkpoint exists
```

## Public Gate Stack Placement

After M1064 implements the wrapper, M1065 should integrate it into the guarded
PPO public gate stack.

Current guarded PPO route:

```text
PPO proposal
  -> exact active-set checks
  -> old public replay proof gates
  -> source-diverse diagnostics
  -> fresh/OOD generalization
  -> behavior retention
```

New route:

```text
PPO proposal
  -> exact active-set checks
  -> old public replay proof gates
  -> M1061 family-intersection public gate
  -> source-diverse diagnostics
  -> fresh/OOD generalization
  -> behavior retention
```

The M1061 gate belongs in the proof tier. It should run before
generalization/behavior because a candidate that loses refreshed wrong-history
proof rows is not eligible for broader evaluation or promotion.

## Interaction With Existing Gates

M1061 does not replace older proof gates.

Keep:

```text
M183/M170 row16 and old replay surfaces
M267/M264 row15 and current-family replay surface
M297/M270 exact objectives
M997 temporal objective
combined active-set anchor
source-diverse diagnostics
fresh/OOD and behavior retention
```

Add:

```text
M1061 family-intersection replay gate
```

Reason:

```text
Older gates protect known historical proof rows.
M1061 protects a fresh post-short-PPO family proof surface.
Both are public proof gates and should be retained before medium PPO.
```

## Medium PPO Readiness Rule

Medium PPO should remain blocked until:

```text
1. M1064 implements and validates the reusable family-intersection public gate.
2. M1065 integrates it into the guarded PPO/full public gate stack.
3. A no-PPO preflight confirms the current public-gate base passes the expanded
   gate stack.
```

Only then should the project design a medium PPO escalation.

## Decision

```text
post_short_promotion_family_gate_integration_design_admit_m1064_wrapper
```

Next:

```text
m1064-v4-public-base-family-intersection-public-gate-implementation
```
