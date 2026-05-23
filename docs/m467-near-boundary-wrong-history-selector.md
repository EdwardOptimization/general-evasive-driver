# M467 Near-Boundary Wrong-History Selector

## Purpose

M467 implements and runs the normal-margin-aware selector designed in M466. It
classifies wrong-history rows into proof candidates, near-boundary no-effect
rows, and high-slack diagnostics.

No policy rollout, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Implementation

Added:

```text
src/autodrift/near_boundary_wrong_history_selector.py
tests/test_near_boundary_wrong_history_selector.py
```

The selector consumes an existing `candidates.csv` artifact and writes:

```text
wrong_history_classified.csv
near_boundary_candidates.csv
proof_candidates.csv
near_boundary_no_effect.csv
high_slack_diagnostics.csv
summary.json
```

Proof filter:

```text
variant == wrong_matched_history
matched_current_pass == true
normal_success == true
0 < normal_margin <= normal_margin_ceiling
outcome degradation:
  success_drop
  collision_gap
  obstacle_completion_drop with return_gap >= 1.0
  margin_gap >= 0.02
action_prefilter_pass == true
```

Default normal-margin ceiling:

```text
0.75 m
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.near_boundary_wrong_history_selector \
  --candidates-csv runs/m465_targeted_wrong_history_selector/candidates.csv \
  --normal-margin-ceiling 0.75 \
  --min-margin-gap 0.02 \
  --min-return-gap-for-completion-drop 1.0 \
  --min-proof-rows 16 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --min-success-or-collision-or-completion-rows 4 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.60 \
  --run-dir runs/m467_near_boundary_wrong_history_selector
```

## Results

```text
wrong-history rows:                  199
near-boundary candidates:             35
proof candidates:                      0
near-boundary no-effect rows:         35
high-slack diagnostics:                7
wrong-history gate pass:           False
```

Near-boundary rows by label:

```text
drift_required: 20
unavoidable:    15
```

Near-boundary rows by probe seed:

```text
10200: 24
10300:  4
10400:  7
```

High-slack diagnostics:

```text
count:                    7
label:                    aes_feasible only
normal margin range:      3.548401 to 7.612638
```

Artifacts:

```text
runs/m467_near_boundary_wrong_history_selector/summary.json
runs/m467_near_boundary_wrong_history_selector/wrong_history_classified.csv
runs/m467_near_boundary_wrong_history_selector/near_boundary_candidates.csv
runs/m467_near_boundary_wrong_history_selector/proof_candidates.csv
runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv
runs/m467_near_boundary_wrong_history_selector/high_slack_diagnostics.csv
```

## Interpretation

M467 rejects wrong-history proof expansion. The current M457/M464/M465 branch
does contain near-boundary normal-success wrong-history rows, but wrong history
does not degrade them. The only wrong-history rows with accepted margin
degradation are high-slack `aes_feasible` diagnostics and are excluded from
proof by the normal-margin ceiling.

This is a useful negative result: the blocker is no longer selector ambiguity.
The current task family does not yet create source-diverse near-boundary states
where wrong command-response history changes emergency outcome.

## Validation

```text
tests/test_near_boundary_wrong_history_selector.py: 4 passed
```

## Decision

```text
reject_wrong_history_gate_admit_m468_task_family_redesign
```

Do not expand wrong-history gates from M467. The next step should redesign the
task family or intervention construction to create low-normal-margin
wrong-history outcome failures.
