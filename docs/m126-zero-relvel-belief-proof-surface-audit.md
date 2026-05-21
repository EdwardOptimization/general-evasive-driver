# M126 Zero-Relvel Belief Proof Surface Audit

M125 rejected PPO admission because behavior retention repeated but
hidden-envelope lift failed fresh probe seeds. M126 audits whether the
zero-relvel hidden-envelope targets are a reliable proof surface, and whether
the outcome-critical wrong-history surface is a better next gate.

## Hidden-Envelope Reliability Audit

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.hidden_envelope_reliability_audit \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --checkpoint-policy m105_9710=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --checkpoint-policy m124_9821=runs/m124_calib_s120_lr5e5_anchor10_seed9821/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --split-seeds 9610,9611,9612,9613,9614 \
  --sample-limits 400,800 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m126_zero_relvel_hidden_envelope_reliability_audit_seed9510
```

Result:

```text
passed=False
```

### Target Stability

At `800` samples, target means are stable across probe seeds:

| Checkpoint | Target | Mean of target mean | Target mean range | Mean target std |
| --- | --- | ---: | ---: | ---: |
| M105 | braking | 2.492204 | 0.021480 | 1.178009 |
| M105 | lateral | 1.279399 | 0.040924 | 1.104107 |
| M105 | yaw | 0.356801 | 0.006224 | 0.440009 |
| M124 | braking | 2.492027 | 0.022244 | 1.179194 |
| M124 | lateral | 1.305749 | 0.041717 | 1.101528 |
| M124 | yaw | 0.354795 | 0.006415 | 0.438500 |

The failure is not primarily target mean drift.

### Aggregate Lift

At `800` samples, response-hidden minus reset-hidden lift:

| Checkpoint | Target | Lift mean | Lift std | Lift min | Pass fraction |
| --- | --- | ---: | ---: | ---: | ---: |
| M105 | braking | -0.202113 | 0.231726 | -0.754720 | 0.200000 |
| M105 | lateral | -0.336667 | 0.434900 | -1.352829 | 0.333333 |
| M105 | yaw | -0.946768 | 1.287077 | -5.104909 | 0.133333 |
| M124 | braking | -0.272462 | 0.296682 | -1.139100 | 0.066667 |
| M124 | lateral | -0.305144 | 0.405397 | -1.140461 | 0.333333 |
| M124 | yaw | -0.924079 | 1.176599 | -4.534275 | 0.066667 |

Current-response comparison at `800` samples:

| Checkpoint | Target | Current response mean R2 | Reset hidden mean R2 | Response hidden mean R2 |
| --- | --- | ---: | ---: | ---: |
| M105 | braking | 0.3050 | 0.1191 | -0.0831 |
| M105 | lateral | 0.0743 | 0.0500 | -0.2867 |
| M105 | yaw | 0.2676 | 0.0342 | -0.9126 |
| M124 | braking | 0.3030 | 0.1261 | -0.1464 |
| M124 | lateral | 0.0669 | 0.0041 | -0.3010 |
| M124 | yaw | 0.2773 | 0.0418 | -0.8823 |

Interpretation: current response and reset-hidden baselines are stronger than
carried response hidden on this probe surface. The hidden-envelope R2 gate is
not a reliable admission proof for M124.

## Outcome-Critical Wrong-History Check

M126 also repeats the strict zero-relvel snapshot-bank relocation miner on the
M124 9821 checkpoint:

```text
runs/m126_zero_relvel_m124_strict_60ep_seed9720
```

Result:

| Metric | Value |
| --- | ---: |
| Candidates | 3134 |
| Visible matches | 1632 |
| Accepted outcome rows | 15 |
| Success-drop pairs | 12 |
| Selected rows | 7 |
| Selected physical pairs | 7 |
| Selected seeds | 6 |
| Intervention snippets | 14 |
| Max snippet margin gap | 0.046191 |

Accepted rows cover `7` physical pairs, `6` seeds, and source steps:

```text
24, 27, 28, 30, 36, 42, 45, 48
```

All exported intervention snippets are perturbed-source rows:

```text
source_conditions: {'perturbed': 14}
```

This confirms that the outcome-critical wrong-history surface survives the
M124 calibrated objective and is stronger than the M122 M105 surface.

## Decision

M126 rejects the hidden-envelope R2 probe as the primary continuation gate for
the zero-relvel line.

What is reliable:

- target means are stable across probe seeds at `800` samples;
- behavior retention and zero-response ablations are stable from M125;
- strict zero-relvel outcome-critical wrong-history mining remains
  source-diverse for M124.

What is not reliable:

- response hidden does not robustly beat reset hidden;
- response hidden does not beat current-response baselines;
- yaw/lateral R2 lift is strongly split/probe-seed fragile.

Next step: M127 should formalize an outcome-centric proof gate around strict
zero-relvel wrong-history interventions, including repeat miners and controls,
instead of tuning PPO or optimizing another hidden-envelope R2 objective.
