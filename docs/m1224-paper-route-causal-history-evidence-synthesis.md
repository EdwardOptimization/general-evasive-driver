# M1224 Paper-Route Causal-History Evidence Synthesis

## Summary

M1224 synthesizes the causal-history branch from M1215 through M1223.

Decision:

```text
causal_history_synthesis_promote_to_terminal_boundary_materialization
```

No new source mining, outcome intervention, training, PPO, checkpoint repair,
promotion, private holdout, profile tuning, or actor-input change occurs in
M1224.

## Evidence Summary

The branch answered progressively sharper questions.

M1215 designed the gate:

```text
same or matched current observation;
different command-response history;
action screen before outcome gate;
outcome gate only after source-diverse action or boundary evidence;
no hidden/oracle actor inputs.
```

M1217 established a current-family matched-current substrate:

```text
accepted pairs: 1790
physical pairs: 427
probe seeds:       4
left steps:       21
targets:           3
```

M1218 showed the first critical negative result:

```text
wrong_matched_history action mean / above-threshold: 0.001075 / 0
delayed_history action mean / above-threshold:       0.000154 / 0
reset_hidden action mean / above-threshold:          0.041795 / 629
```

M1220 separated hidden-path availability from real-history evidence:

```text
random_hidden_unit action mean / above-threshold: 0.057720 / 713
reset_hidden action mean / above-threshold:       0.041795 / 629
scaled_hidden_2_0 action mean / above-threshold:  0.038319 / 509
wrong_matched_history action mean / above:         0.001075 / 0
delayed_history action mean / above:               0.000154 / 0
```

M1222 improved source mining but still failed outcome materialization:

```text
near_boundary_preferred_snapshots: 45
all_action_threshold_rows:       274
accepted_rows:                     0
margin_gap >= 0.010 rows:          0
success_drop_rows:                 0
max margin gap:             0.002370
```

M1223 classified the branch state:

```text
near_boundary_action_gap_but_no_outcome_gap
```

## Supported Claims

Supported:

```text
The corrected L3 online-GRU actors have a functional hidden path.
The M1217 current-family matched-current surface is source-diverse.
The original M1217 surface is not action-critical for real wrong/delayed histories.
A broader normal-success boundary source can find sustained wrong-history
action divergence.
The current-family action-divergent rows are not yet outcome-critical.
```

Engineering implications:

```text
The history-intervention harness is working.
The workflow correctly blocked outcome gates after failed action screens.
The branch preserved negative evidence instead of training on empty or weak
corpora.
```

## Falsified Claims

Falsified or currently unsupported:

```text
Current matched histories already prove action-level history necessity.
Reset-hidden sensitivity is sufficient self-identification evidence.
Future-response ambiguity alone is enough to create action divergence.
Action divergence alone is enough to prove causal-history outcome sensitivity.
The current-family L3 actor is ready for PPO, preference training, or promotion
from these rows.
```

Still blocked:

```text
online self-identification;
recurrent-belief advantage;
paper-level history-necessity claim;
private-holdout generalization;
closed-loop causal-history outcome proof.
```

## Failure Taxonomy Summary

The branch failures are evidence-bearing, not harness failures:

```text
M1218: current-family wrong/delayed histories are action-equivalent.
M1220: hidden path works, but real histories remain action-equivalent.
M1222: normal-success action gaps exist, but no margin/success degradation.
```

Process classification:

```text
not contract_violation
not training_instability
not metric_artifact
not proof_washout
not promotion_gate_failure
```

Scientific classification:

```text
source_action_equivalence
off_manifold_hidden_positive_control_only
near_boundary_action_gap_but_no_outcome_gap
```

## Public Gate Overfit Risk

Risk:

```text
The branch is now optimizing public diagnostic surfaces and could drift toward
gate-passing if it keeps rerunning nearby source-mining variants.
```

Mitigation:

```text
Close the current branch.
Open a new branch with a different evidence axis.
Keep M1218/M1220/M1222 negative evidence as constraints.
Do not use private holdout.
Do not tune thresholds after seeing failures.
Require source-diverse accepted rows before any training or outcome proof claim.
```

The next branch must treat M1222 action-divergent rows as candidate material,
not as proof.

## Next Branch Decision

Selected next branch:

```text
paper_route_terminal_boundary_materialization
```

Why this branch:

```text
M1222 already produced real-history action-divergent rows.
The remaining gap is outcome materialization.
M1222 candidate rows include obstacle geometry, unlike the older M1175
artifact-only candidate export.
Terminal-boundary materialization directly tests whether the action gaps can be
made margin/success-critical under bounded scene relocation.
```

Why not immediate cross-fault:

```text
Cross-fault/extreme dynamics is important, but it changes the source
distribution before closing the current-family action-gap evidence. It should
remain the fallback if terminal-boundary materialization is source-limited or
collapses to one active set.
```

Why not simple longer horizon first:

```text
M1222 max margin gap is only 0.002370 and both branches succeeded at rate
1.000. Longer horizon alone is lower leverage than deliberately materializing
terminal boundaries around the action-divergent rows.
```

## Requirements For The New Branch

M1225 should design a terminal-boundary materialization route that:

```text
uses M1222 all-action-threshold rows as candidate material;
preserves source diversity by physical pair, left seed, target, and obstacle geometry;
relocates obstacle timing/geometry only within bounded limits;
requires normal-history success or near-boundary positive margin;
requires wrong-history margin gap or success drop after relocation;
keeps actor inputs unchanged;
does not train or promote;
records failure if accepted rows collapse to one active set.
```

The branch should learn from M1177:

```text
action-divergent candidate score does not guarantee source-diverse
materialization;
source geometry must be available before candidate balancing;
single active-set dominance must be a failure, not a pass.
```

## Decision

```text
causal_history_synthesis_promote_to_terminal_boundary_materialization
```

Next blocker:

```text
m1225-paper-route-terminal-boundary-materialization-design
```
