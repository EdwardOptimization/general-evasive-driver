# M366 Alpha02 Old-Key Regression Audit

M366 audits the first failing old-key interpolation from M364/M365. It does not
run PPO, promote alpha `0.2`, lower old-key thresholds, or change actor inputs.

## Inputs

Passing alpha:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

First failing tested alpha:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt
```

Comparison artifact:

```text
runs/m364_old_key_aware_repair_alpha02_old_key_replay_gate/old_key_replay_comparison_rows.csv
```

## Gate Summary

Alpha `0.2` fails only one compact old-key row:

```text
candidate accepted regressions: 1
candidate normal-success regressions: 0
candidate gap p10: -0.000002079
candidate gap min: -0.000003317
failure: candidate_accepted_regressions>0
```

## Failing Row

```text
case_id: 9951|perturbed|35|32|10.000000|-1.200000|1.400000
seed_block: C
seed: 9951
source_condition: perturbed
source_step: 35
paired_step: 32
target_obstacle_distance: 10.0
relocated_obstacle_body_y: -1.2
relocated_obstacle_half_width: 1.4
```

The row is a wrong-history branch crossing, not a normal-branch failure.

| Policy | Accepted | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m360_base | true | +0.000939132658 | -0.000000094854 | +0.000939227512 |
| m364a_0_1 | true | +0.000939372160 | -0.000000015094 | +0.000939387253 |
| m364a_0_2 | false | +0.000939642885 | +0.000000087150 | +0.000939555735 |

Normal margin improves monotonically. The failure appears because the
wrong-history rollout becomes barely successful at alpha `0.2`.

## Interpretation

This is not broad source-diverse proof washout. It is a single old-key hard row
where the rejected/wrong-history branch has almost no negative margin slack:

```text
m360 wrong-history margin:  -9.49e-8
m364 alpha 0.1 margin:      -1.51e-8
m364 alpha 0.2 margin:      +8.72e-8
```

The M363 old-key surrogate sees action/logprob preference and local action
anchors, but it does not directly encode terminal wrong-history margin sign.
The next repair should therefore make this hard row explicit rather than
loosening the closed-loop gate.

## Decision

Do not promote alpha `0.2`.

Do not lower the old-key acceptance rule.

Admit:

```text
m367-old-key-hard-row-weighting-design
```

Decision:

```text
admit_m367_old_key_hard_row_weighting_design
```

M367 should design how old-key replay regressions feed back into the
training-time old-key preference corpus, for example:

- mark alpha `0.2` accepted-regression rows as `hard_row`;
- increase wrong-history preference and rejected-action anchor weight on hard
  rows;
- include baseline wrong-history margin slack as a weight or metadata field;
- keep closed-loop old-key replay as the authoritative outer proof gate.
