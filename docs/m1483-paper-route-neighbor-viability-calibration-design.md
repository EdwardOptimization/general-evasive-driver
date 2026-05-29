# M1483 Paper-Route Neighbor Viability Calibration Design

## Summary

M1483 designs the next no-training route after M1482 showed that source-diverse
pressure replay reached diverse sources but produced history positives only on
the original source family.

Decision:

```text
neighbor_viability_calibration_design_admit_implementation
```

M1483 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Problem

M1481 replay split:

```text
original source rows: 36
original normal viable rows: 36
original history positives: 12
original control positives: 15

neighbor source rows: 216
neighbor normal viable rows: 66
neighbor normal failed rows: 150
neighbor history positives: 0
neighbor control positives: 0
```

The source-diverse candidate path works mechanically, but the neighbor rows are
not landing in the joint window required for useful replay evidence:

```text
normal history must be viable;
history intervention must degrade margin or success;
action sequence difference must be large enough;
controls must remain separated.
```

## Design Principle

The next generator should calibrate neighbor rows, not expand the original
source again.

Use M1481 as:

```text
normal-viability map for neighbor sources
source-diverse failure map
control-sensitivity diagnostic
```

Do not use M1481 as:

```text
training corpus
promotion evidence
paper-level self-identification evidence
level3 anticipatory self-identification evidence
```

## Neighbor Calibration Generator

Implement a no-training generator:

```text
src/autodrift/neighbor_viability_calibration.py
```

Inputs:

```text
runs/m1481_source_diverse_pressure_bounded_replay_smoke/actual_replay_rows.csv
runs/m1481_source_diverse_pressure_bounded_replay_smoke/history_positive_rows.csv
runs/m1481_source_diverse_pressure_bounded_replay_smoke/control_positive_rows.csv
```

Outputs:

```text
neighbor_viability_audit_rows.csv
neighbor_viability_proposal_rows.csv
neighbor_viability_candidate_rows.csv
summary.json
```

The generator should:

```text
1. Identify the original positive source family.
2. Mark all other source families as neighbor candidates.
3. Keep zero-current and reset controls separate.
4. Classify each neighbor row:
   - too_hard: normal branch fails or normal margin < 0;
   - near_boundary: normal viable and normal margin in a target band;
   - too_easy: normal viable but margin too large or intervention gap too weak.
5. Generate calibration deltas that move neighbor rows into normal-viable,
   margin-gap-sensitive boundary windows.
6. Preserve source_step and candidate_step_column == source_step.
7. Cap original-source diagnostics so they cannot dominate.
```

## Calibration Policy

Recommended classes:

```text
too_hard:
  normal_success false or normal_margin < 0
  action: ease the scene by moving obstacle farther, reducing half-width, or
  moving it away from ego centerline.

near_boundary:
  normal_success true and 0 <= normal_margin <= 1.0
  action: small local grid around the replay geometry.

too_easy:
  normal_success true and normal_margin > 1.0, or gap too weak
  action: tighten the scene by moving obstacle earlier, increasing half-width,
  or moving it toward ego centerline.
```

Ranking should prefer:

```text
1. neighbor rows with normal viable near-boundary state;
2. too_hard rows with positive margin gap but small negative normal margin;
3. too_easy rows with strong action divergence;
4. source and capability diversity;
5. control diagnostics last.
```

The original source should be included only as a capped diagnostic:

```text
original_source_cap <= 8
```

Controls should be kept in separate outputs and should not count as
history-positive candidates.

## Future Gate

M1484 should implement the generator and focused tests only. It should not run
preflight or replay.

Implementation passes if:

```text
neighbor viability generator exists
focused tests cover original-source exclusion/capping
focused tests cover too_hard / near_boundary / too_easy classification
focused tests cover source_step preservation
focused tests cover control separation
focused tests cover source-diverse selection caps
no preflight, replay, training, PPO, promotion, private holdout, corpus export,
or actor-input change occurs
```

After M1484, admit a proposal smoke only. A future preflight or replay is
allowed only after proposal smoke proves calibrated neighbor candidates exist.

## Stop Conditions

Stop this branch and synthesize if:

```text
neighbor rows cannot be calibrated without replaying the original source;
calibrated candidates collapse back to one seed or capability pair;
controls cannot be separated from history-positive candidates;
the generator requires actor-input changes or hidden/oracle fields;
the next proposal smoke again produces only original-source candidates.
```

## Guardrails

M1483 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1484-paper-route-neighbor-viability-calibration-implementation
```
