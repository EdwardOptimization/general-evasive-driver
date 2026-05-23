# M472 Fresh-Window Near-Boundary Anchor Design

## Purpose

M472 designs the next step after M471 showed that a larger same-window
matched-current pool can meet the adversarial-pair count threshold but still
fails source balance.

No training, PPO, checkpoint update, actor-input change, outcome probe, or
checkpoint promotion is performed.

## M471 Failure Mode

M471 expanded same-window mining on seeds `10200`, `10300`, and `10400`:

```text
candidate pairs:              380877
accepted pairs:                 1702
accepted physical pairs:        1608
adversarial pairs:                67
near-boundary left states:        24
probe seed count:                  3
label count:                       2
target count:                      3
single seed share:          0.671642
single label share:         0.597015
search_pass:                   False
```

The count threshold passed, but seed `10200` contributed `45/67` adversarial
pairs. This is not a reason to relax the `0.50` single-seed cap. It means the
same source window still dominates the adversarial surface.

The failure class is:

```text
seed_fragility / source_balance_failure
```

## Design Decision

The next step is fresh-window near-boundary anchor discovery, not another
outcome probe on M471.

M473 should run the full anchor-discovery pipeline on fresh seed windows that
were not used to build M467/M469/M471:

```text
window A: 10500,10600,10700
window B: 10800,10900,11000
```

For each window, run:

1. Expanded matched-current mining with the M471 sampling settings.
2. Wrong-history targeted pair triage over that window's `candidate_pairs.csv`.
3. Matched-history action intervention gate.
4. Matched-history continuation outcome gate.
5. Outcome-critical selector.
6. Near-boundary wrong-history selector.

The output of M473 is a fresh near-boundary anchor surface. The output is not a
proof gate expansion yet.

## Why This Is Different From M471

M471 reused the M467 near-boundary anchors and only enlarged the right-history
candidate pool. That tested whether the old left-state window had enough
wrong-history alternatives. It did not test whether the task family can produce
near-boundary anchors across disjoint source windows.

M473 changes the source of the left states:

```text
old path:
  M467 anchors from 10200/10300/10400
  + expanded same-window right histories

new path:
  fresh matched-current windows
  + fresh targeted wrong-history probes
  + fresh near-boundary anchor classification
```

This keeps source balance as a hard gate and avoids optimizing around one
overrepresented seed.

## M473 Command Plan

Run the following pipeline for each fresh window. The example below shows window
A. Window B should use `10800,10900,11000` and matching `m473b_*` run dirs.

Expanded matched-current mining:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --probe-seeds 10500,10600,10700 \
  --episodes 80 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 2400 \
  --nearest-k 32 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 640 \
  --max-pairs-per-physical-pair 2 \
  --max-pairs-per-left-step 40 \
  --max-pairs-per-source-obstacle-bucket 80 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 120 \
  --device cpu \
  --run-dir runs/m473a_fresh_window_matched_current_seed10500
```

Wrong-history targeted pair triage:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_targeted_pair_triage \
  --candidate-pairs-csv runs/m473a_fresh_window_matched_current_seed10500/candidate_pairs.csv \
  --min-target-z-delta 1.0 \
  --max-rows 240 \
  --max-per-probe-seed 80 \
  --max-per-left-seed 80 \
  --max-per-label 120 \
  --max-per-target 96 \
  --max-per-obstacle-bucket 24 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-targeted-rows 96 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m473a_fresh_window_targeted_pair_triage
```

Action intervention gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m473a_fresh_window_targeted_pair_triage/targeted_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.05 \
  --max-pairs-per-checkpoint-target 96 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m473a_fresh_window_action_gate
```

Outcome gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m473a_fresh_window_targeted_pair_triage/targeted_pairs.csv \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 96 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m473a_fresh_window_outcome_gate
```

Outcome-critical selector:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_critical_matched_current_selector \
  --pairs-csv runs/m473a_fresh_window_targeted_pair_triage/targeted_pairs.csv \
  --action-interventions-csv runs/m473a_fresh_window_action_gate/action_interventions.csv \
  --outcome-interventions-csv runs/m473a_fresh_window_outcome_gate/outcome_interventions.csv \
  --max-pairs-per-checkpoint-target 96 \
  --min-margin-gap 0.02 \
  --min-action-distance 0.05 \
  --max-normal-pair-action-distance 0.08 \
  --min-target-z-delta 1.0 \
  --max-rows 160 \
  --max-per-probe-seed 48 \
  --max-per-target 64 \
  --max-per-variant 64 \
  --max-per-obstacle-bucket 16 \
  --min-accepted-rows 16 \
  --run-dir runs/m473a_fresh_window_outcome_selector
```

Near-boundary wrong-history selector:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.near_boundary_wrong_history_selector \
  --candidates-csv runs/m473a_fresh_window_outcome_selector/candidates.csv \
  --normal-margin-ceiling 0.75 \
  --min-margin-gap 0.02 \
  --min-return-gap-for-completion-drop 1.0 \
  --min-proof-rows 16 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --min-success-or-collision-or-completion-rows 4 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m473a_fresh_window_near_boundary_selector
```

## M473 Pass Criteria

M473 is an anchor-discovery gate. It does not need to prove wrong-history
outcome degradation yet, but it must produce source-diverse fresh anchors.

Pass if:

```text
both fresh matched-current windows complete without sampling failure
each targeted triage exports >= 96 rows
combined near-boundary candidate count >= 64
combined near-boundary probe seed count >= 4
combined near-boundary obstacle label count >= 2
combined near-boundary target count >= 2
combined single seed share <= 0.50
combined single label share <= 0.70
actor inputs unchanged
no checkpoint promoted
```

If fresh proof candidates appear, they should be reported separately and may
admit a later wrong-history proof gate. If only near-boundary no-effect rows
appear, M474 should combine the fresh anchors with M467 and rerun adversarial
right-history search across all source windows.

## Rejection Conditions

Reject M473 if:

```text
fresh windows fail scenario sampling
near-boundary candidates remain source-narrow
single seed share exceeds 0.50
only aes-feasible high-slack rows are found
the pipeline changes actor inputs
the pipeline trains or promotes a checkpoint
```

## Decision

```text
admit_m473_fresh_window_anchor_discovery_run
```

No checkpoint is promoted.
