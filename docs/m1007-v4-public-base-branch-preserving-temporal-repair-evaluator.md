# M1007 V4 Public Base Branch-Preserving Temporal Repair Evaluator

## Purpose

M1007 implements and runs the no-update evaluator designed in M1006. The goal is
to test whether fixed active-row branch-ceiling and branch-separation terms can
distinguish the M974 public base from M1002 proof-washing temporal candidates
before another actor update.

This milestone does not train, run PPO, run promotion gates, use private
holdout, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.branch_preserving_temporal_repair_evaluator \
  --base-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --candidate-checkpoints runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv \
  --corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --m267-corpus runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --run-dir runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator \
  --device auto \
  --active-rows 6,15,11,16 \
  --max-continuation-steps 60
```

## Result

```text
result_class: branch_preserving_temporal_repair_evaluator_not_sensitive
failure_types: metric_artifact
finite_metrics: true
temporal_base_reproduced: true
base_branch_near_zero: true
proofwashing_candidates_active: false
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The evaluator is numerically valid but not useful enough for repair training.

## What Worked

The evaluator successfully reconstructs active M267/M264 rows:

```text
primary rows: 6, 15
secondary rows: 11, 16
```

It also reproduces the M1000 temporal base metrics and leaves actor parameters
unchanged.

The M974 branch loss is exactly zero:

```text
base_weighted_branch_total_loss: 0.0
```

## What Failed

The fixed one-step branch proxy does not respond to the smallest proof-washing
candidate:

| checkpoint | branch total loss | wrong logp delta mean | wrong logp delta max | first-action distance min |
| --- | ---: | ---: | ---: | ---: |
| M974 base | 0.000000e+00 | 0.000000 | 0.000000 | 0.038225 |
| alpha 0.01 | 0.000000e+00 | 0.000064 | 0.000313 | 0.038044 |
| alpha 0.02 | 0.000000e+00 | 0.000122 | 0.000626 | 0.037864 |
| alpha 0.05 | 0.000000e+00 | 0.000261 | 0.001559 | 0.037330 |
| alpha 0.10 | 0.000000e+00 | 0.000374 | 0.003098 | 0.036458 |
| alpha 0.20 | 4.144670e-07 | 0.000160 | 0.006115 | 0.034783 |

This is too weak. M1004 showed alpha `0.01` already makes rows `6` and `15`
wrong-history successful in closed-loop replay, but M1007's fixed one-step
ceiling/separation terms do not activate for alpha `0.01`.

## Interpretation

The failure is a metric artifact in the proposed no-update evaluator:

```text
closed-loop replay evidence:
  alpha 0.01 loses rows 6 and 15

fixed one-step evaluator evidence:
  alpha 0.01 branch loss remains 0.0
```

Therefore the M1006 proxy is not a reliable repaired objective by itself. The
public proof washout is driven by closed-loop terminal margin sensitivity, not
by an easily detected fixed-observation one-step logp or action-separation
collapse.

## Supported Claims

- M1007 does not mutate model parameters.
- M997 temporal objective metrics still reproduce M1000.
- M974 base is safe under the fixed branch proxy.
- The fixed one-step branch proxy is too insensitive to protect rows `6` and
  `15` at small alpha.

## Unsupported Claims

- M1007 does not justify an actor update.
- M1007 does not provide a sufficient branch-preserving repair objective.
- M1007 does not solve M1004 proof washout.

## Decision

```text
branch_preserving_temporal_repair_evaluator_not_sensitive_route_to_evaluator_sensitivity_audit
```

Next:

```text
m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit
```

M1008 should compare fixed one-step branch metrics against the M1004 closed-loop
margin changes and design a replacement residual. The replacement likely needs
to be margin-aware or trajectory-aware, not just one-step logp/separation on a
fixed observation.
