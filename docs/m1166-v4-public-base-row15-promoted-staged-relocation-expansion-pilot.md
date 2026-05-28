# M1166 V4 Public Base Row15 Promoted Staged Relocation Expansion Pilot

## Purpose

M1166 ran the small staged relocation pilot designed in M1165.

The milestone reused the existing M1161 outcome CSV, reduced the candidate
budget, and evaluated only `wrong_matched_history`. It did not rerun mining,
rerun the outcome gate, train actor weights, run PPO, promote, use private
holdout, convert a surface, or change actor inputs.

## Input

```text
outcome_csv:
  runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv

run_dir:
  runs/m1166_row15_promoted_staged_relocation_pilot_seed116100

current public-gate base:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

## Pilot Scope

```text
max_candidates: 240
max_candidates_per_physical_pair: 4
max_candidates_per_checkpoint_target: 64
target margins: 0.001,0.0025,0.005,0.01,0.02
body longitudinal offsets: -1.0,0.0,1.0
body lateral offsets: -0.3,0.0,0.3
report variants: wrong_matched_history only
```

## Result

The pilot completed and wrote the expected summary artifact:

```text
summary:
  runs/m1166_row15_promoted_staged_relocation_pilot_seed116100/summary.json

source_budget_ready: true
source candidate wrong-history rows: 4585
source eligible physical pairs: 242

selected rows: 240
selected physical pairs: 240
selected left steps: 27
selected targets: 3
max selected pair fraction: 0.004167

raw relocation rows: 4605
accepted wrong-history rows: 1
accepted wrong-history physical pairs: 1
accepted wrong-history left steps: 1
accepted wrong-history checkpoints: 1
accepted wrong-history targets: 1
accepted wrong-history normal-margin buckets: 1
accepted wrong-history normal-margin max: 0.002457
max rows per physical pair fraction: 1.0
control accepted wrong-history rows: 0
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

The only accepted row came from:

```text
checkpoint: row15_current
target: future_yaw_response
physical pair: 116117:39:116124:15
normal margin: 0.002457
wrong-history margin: -0.000075
margin gap: 0.002532
```

## Comparison With M1161

M1165 pre-registered the comparison against M1161:

```text
M1161 accepted wrong-history rows: 15
M1161 accepted wrong-history physical pairs: 2
M1161 accepted wrong-history normal-margin buckets: 1
M1161 accepted wrong-history normal-margin max: 0.002483
```

M1166 did not improve any of the useful-improvement criteria:

```text
accepted_wrong_history_rows >= 5 within pilot: false
accepted_wrong_physical_pairs >= 2: false
accepted_wrong_normal_margin_buckets >= 2: false
accepted_wrong_normal_margin_max > 0.002483: false
```

## Interpretation

The negative result is not a source-budget failure. The source pool remained
broad, and the pilot selected `240` rows across `240` physical pairs. The
failure happens after relocation: wrong-matched-history intervention rarely
turns a normal-success continuation into a wrong-history failure under the
current row15-promoted base and relocation settings.

This narrows the blocker from "not enough candidates" to wrong-history
mechanism scarcity after relocation. Continuing to enlarge the same relocation
cross product is therefore not justified before auditing why the wrong-history
branch is so often safe.

## Guardrail

No actor training, PPO, promotion, private holdout, new mining, outcome rerun,
surface conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: row15_promoted_staged_relocation_pilot_reject_route_to_wrong_history_mechanism_audit
next: m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit
```
