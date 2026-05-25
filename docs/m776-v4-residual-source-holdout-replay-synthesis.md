# M776 V4 Residual Source-Holdout Replay Synthesis

## Purpose

M776 is the required workflow synthesis for the
`v4_residual_source_holdout_replay` branch. The validator blocked direct replay
implementation because the branch reached the synthesis cadence.

This synthesis asks:

```text
Should the branch continue to one limited broader residual replay
implementation, pivot to more source mining, or stop?
```

This milestone is synthesis-only:

```text
no residual replay
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

The branch evidence is:

```text
M761:
  no-PPO frozen-backbone residual objective probe
  1213/1213 reconstruction
  alpha 0.2 improves exact gap metrics with small normal action drift

M764:
  public closed-loop residual replay
  alpha 0.2 passes with normal success 1213/1213 and 0 normal collisions
  intervention action gap and margin gap improve

M767/M768:
  fresh disjoint-seed source-holdout wave
  995 clean positives, 25 seeds, 13 fault-family pairs
  sparse and concentrated, but clean enough for limited replay

M770/M771:
  limited fresh holdout residual replay
  alpha 0.2 passes with normal success 995/995 and 0 normal collisions
  intervention action gap and margin gap improve
  result remains limited because rows and collision sensitivity are concentrated

M772/M773:
  broader fresh source-holdout wave
  matched pairs 24576
  reset-only rows 1389
  source rows 1024 across 63 seeds and 22 source fault-family pairs
  exported positives 2652 across 49 seeds and 17 positive fault-family pairs
  clean artifact gates but hard-negative sparse

M774/M775:
  audit and design conclude that M773 is broad enough for limited no-PPO
  residual replay, but not broad enough for generalization, PPO, or promotion.
```

Key M773 versus M767 comparison:

```text
positive_rows:
  M767: 995
  M773: 2652

unique_positive_seeds:
  M767: 25
  M773: 49

unique_positive_fault_family_pairs:
  M767: 13
  M773: 17

max_positive_seed_dominance:
  M767: 0.247236
  M773: 0.171569

max_positive_fault_family_pair_dominance:
  M767: 0.265327
  M773: 0.208145
```

## Supported Claims

The branch supports:

```text
1. The residual self-ID mechanism is not purely a public-corpus artifact.
   It survived a limited disjoint-seed holdout replay in M770.

2. Scenario coverage was a real blocker. The broader M773 source wave produced
   a much larger clean positive surface than M767.

3. The M761 residual head can be tested in closed-loop replay without mutating
   the actor, without optimizer state, without PPO, and without promotion.

4. The next useful question is narrow and well-posed:
   Does alpha 0.2 still preserve normal behavior and increase intervention
   sensitivity on the broader M773 corpus?
```

## Falsified Claims

The branch falsifies:

```text
1. The M761 residual signal only exists in exact/offline first-action metrics.

2. The residual signal immediately fails on any fresh disjoint-seed corpus.

3. Broader extreme-fault source mining cannot materially expand the evidence
   surface.

4. The current blocker is only PPO/training instability; scenario sampling is
   also a first-class blocker.
```

The branch has not proven:

```text
1. Broad generalization.

2. Driver promotion readiness.

3. PPO safety.

4. True per-wheel, blowout, halfshaft, split-mu, or four-wheel physical
   fidelity.

5. Residual replay success on the broader M773 corpus.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reasons:

```text
M773 strict broad gates still miss:
  unique_positive_fault_family_pairs: 17 < 18
  max_positive_seed_dominance: 0.171569 > 0.15

M773 hard negatives remain incomplete:
  hard_negative_rows: 2134
  positive_rows: 2652
  positives_without_hard_negative: 872

Dominant positive concentration remains visible:
  seed: 77069
  fault-family pair: mass_cg_shift->front_lateral_authority_drop
```

Not current failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not proof_washout
not behavior_regression
not training_instability
not promotion_gate_failure
```

## Public Gate Overfit Risk

The risk is moderate, not negligible:

```text
low risk:
  M770 already used fresh disjoint seeds relative to M761.
  M773 uses another fresh disjoint seed block.
  M773 artifact gates are clean.

remaining risk:
  M761 residual head was trained from the public M755 source family.
  M773 positives are still dominated by reset/zero-command-style interventions.
  M773 hard negatives are sparse.
  Source dominance is lower than M767 but still above the strict broad target.
```

This means:

```text
M777 may test limited broader replay.
M777 may not be interpreted as a promotion gate.
M777 may not justify PPO.
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Reason:

```text
The branch has enough clean, broader evidence to justify exactly one limited
no-PPO residual replay implementation on M773, but not enough evidence for PPO,
promotion, or broad generalization claims.
```

Next milestone:

```text
m777-v4-limited-broader-residual-replay-implementation
```

M777 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m777_v4_limited_broader_residual_replay \
  --device cpu \
  --alphas 0.0,0.2,0.5,1.0
```

M777 must preserve:

```text
primary alpha: 0.2
diagnostic alphas: 0.5, 1.0
no actor mutation
no residual training
no optimizer
no PPO
no promotion
source concentration caveat
hard-negative sparsity caveat
current_model_or_proxy claim boundary
```

If M777 passes, the next milestone must be an audit, not PPO.
If M777 fails or is dominated by a few seeds/pairs, the branch should pivot to
source-balanced or targeted fault-pair mining.
