# M453 Response-Critical Ablation Corpus Design

## Purpose

M452 showed that the M451 robust challenge configs are runnable and harder than
the broad M121 distribution, but the aggregate ablation evidence is weak:

- near robust: zero-current/zero-all drops M399 success from `0.906250` to
  `0.859375`, reset drops to `0.882812`, no-action stays `0.906250`;
- late robust: base is `0.859375`, reset/zero-response are `0.851562`, and
  no-action is `0.867188`;
- many base-success to ablation-fail flips are road-boundary failures with
  positive obstacle clearance margin, not clean obstacle-collision margin
  failures.

M453 therefore designs a corpus step before any more training. The goal is to
turn sparse M452 ablation rows into structured evidence that separates what the
policy depends on:

- explicit current ego response;
- recurrent hidden history;
- previous action/command history;
- road-boundary stability;
- true obstacle clearance/collision margin.

This milestone does not train or promote a checkpoint.

## What M452 Actually Proved

M452 is a useful negative/weak-positive result:

- It proved the robust configs can run the intended ablation benchmark.
- It found some current-response sensitivity, especially on near robust.
- It did not prove recurrent self-identification.

The key diagnostic issue is that `zero_current_response` and `zero_all_response`
are identical in the current `history_length=1` setup, while `reset_hidden` and
`zero_action_history` barely affect aggregate success. That pattern says:

```text
current response matters in some rows;
recurrent history necessity is not yet established.
```

This is not a failure of the project. It means the next evidence step must mine
the rows where ablations matter and classify their mechanism before designing
new rewards, new PPO, or new task distributions.

## Corpus Row Schema

M454 should export a response-critical ablation corpus with at least these
columns:

```text
source_config
source_run
source_seed_block
seed
ablation_policy
dependency_class
failure_class
divergence_types
score
base_success
candidate_success
base_collision
candidate_collision
base_margin
candidate_margin
delta_margin
base_return
candidate_return
delta_return
base_lateral_peak
candidate_lateral_peak
delta_lateral_peak
base_beta_peak
candidate_beta_peak
obstacle_label
mu
mu_bucket
initial_mu
initial_mu_bucket
mass_scale
brake_scale
tire_stiffness_scale
steer_tau_scale
```

The corpus should not add any of these fields to actor input. They are mining,
diagnostic, and training/evaluation metadata only.

## Dependency Classes

Each row should be classified by the ablation that caused the divergence.

```text
current_response_sensitive
```

Use when `m399_zero_current` or `m399_zero_all` diverges from `m399_base`.
Because `history_length=1`, these two are expected to match or nearly match.

```text
recurrent_hidden_sensitive
```

Use when `m399_reset` diverges from `m399_base`. This is the closest available
aggregate diagnostic for online recurrent state, but it remains imperfect
because the current response frame still enters the GRU cell each step.

```text
action_history_sensitive
```

Use when `m399_noact` diverges from `m399_base`.

```text
mixed_dependency
```

Use when multiple ablation families diverge on the same seed.

```text
weak_behavior_shift
```

Use when there is no success/collision/margin-sign flip, but return, lateral
peak, beta peak, or clearance margin shifts enough to be worth keeping as a
non-promotional diagnostic.

## Failure Classes

M454 should classify the outcome mechanism separately from dependency class.

```text
obstacle_collision_margin_crossing
```

Use when the candidate creates a collision flip or margin sign flip and
`candidate_collision = true`.

```text
near_boundary_obstacle_margin
```

Use when either base or candidate obstacle margin is near zero and the margin
changes by at least the configured threshold, even if the success label does
not flip.

```text
road_boundary_failure
```

Use when base succeeds, candidate fails, candidate collision is false, and
candidate lateral peak exceeds the configured track-width boundary.

```text
stability_failure
```

Use when base succeeds, candidate fails, candidate collision is false, and
candidate beta peak or high-sideslip fraction is the dominant degradation.

```text
return_only_shift
```

Use when the row is selected only because return changes materially.

```text
ablation_rescue
```

Use as a negative-control class when the ablation succeeds on a row where base
fails. M452 late seed `9942` is an example: `m399_noact` rescues a base
near-boundary collision. These rows are not proof of self-ID, but they are
important because they expose brittle baseline behavior.

## Selection Priority

M454 should rank rows in this order:

1. base-success to ablation-fail with collision flip or margin sign crossing;
2. base-success to ablation-fail with road-boundary failure;
3. near-boundary obstacle margin deltas;
4. large negative margin or return deltas without success flip;
5. ablation rescues as negative controls;
6. return-only shifts after all stronger evidence is represented.

Rows where ablation improves clearance or success must not be silently dropped.
They are not positive self-ID proof, but they are useful for diagnosing whether
the base policy is carrying brittle memory/action habits.

## Source Diversity Limits

Compact corpus target:

```text
max_rows = 96
max_rows_per_seed = 2
max_rows_per_policy = 24
max_rows_per_config = 48
max_rows_per_obstacle_label = 32
max_rows_per_mu_bucket = 32
max_rows_per_failure_class = 32
```

Promotion-grade evidence is not the goal here. Still, a useful corpus should
prefer:

- both near and late configs;
- all three obstacle labels if present;
- low, medium, and high mu buckets;
- at least two dependency classes;
- both road-boundary and obstacle-margin/collision cases if present.

If the compact corpus is dominated by return-only shifts, that should be
classified as weak diagnostic evidence and should trigger a task-family redesign
rather than training.

## M454 Implementation Plan

M454 should implement a reusable response-critical corpus exporter rather than
hand-processing M452 CSV files. The exporter can build on
`policy_difference_miner`, but it must add:

- dependency-class labeling;
- failure-class labeling;
- source-config/source-run bookkeeping;
- lateral-peak and beta-peak columns;
- source-diverse compact selection with failure-class limits;
- summary JSON with counts by dependency class and failure class.

Suggested CLI shape:

```bash
PYTHONPATH=src python -m autodrift.response_critical_ablation_corpus \
  --episodes-csv runs/m452_near_robust_ablation_seed9900/episodes.csv \
  --source-config near_robust \
  --baseline-policy m399_base \
  --candidate-policy m399_reset \
  --candidate-policy m399_zero_current \
  --candidate-policy m399_zero_all \
  --candidate-policy m399_noact \
  --run-dir runs/m454_response_critical_near_v0
```

Then combine near and late outputs into:

```text
runs/m454_response_critical_ablation_corpus/candidates.csv
runs/m454_response_critical_ablation_corpus/compact_corpus.csv
runs/m454_response_critical_ablation_corpus/summary.json
```

## Pass/Redirect Criteria

M454 should pass if it exports the corpus artifacts and reports the evidence
quality honestly. It should not require the corpus to prove self-ID.

Evidence interpretation:

```text
strong:
  compact corpus has source-diverse recurrent_hidden_sensitive and
  action_history_sensitive success/collision or near-boundary rows.

moderate:
  compact corpus has source-diverse current_response_sensitive rows but few
  recurrent/action-history rows.

weak:
  compact corpus is dominated by return-only or road-boundary cases, or by one
  config/seed/label.
```

Expected result from M452 is probably `moderate` to `weak`, not `strong`.

Redirect rules:

- If M454 is strong, admit a robust response-critical gate over fresh seed
  blocks.
- If M454 is moderate, admit a larger seed-block corpus expansion before any
  training.
- If M454 is weak, admit task-family redesign: warm-up/probing phases,
  hidden-dynamics changes during episode, or tighter matched-current
  wrong-history scenarios.

## Decision

M453 completes the design and admits implementation:

```text
m454-response-critical-ablation-corpus-export
```

No checkpoint is promoted.
