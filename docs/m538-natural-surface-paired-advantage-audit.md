# M538 Natural-Surface Paired Advantage Audit

## Purpose

M538 audits the M537 public natural-surface result with paired source-key
comparisons. The goal is to distinguish a real history-level signal from an
unmatched aggregate mean artifact.

This is still a public diagnostic gate. It does not train, tune, or promote a
checkpoint.

## Command

M538 aggregates the four M537 `surface_outcomes.csv` files, reconstructs the
M526 event overlay key with `right_tail_step = right_step + tail_offset`, and
pivots each matched source state by training seed and history level.

Paired comparisons:

```text
L3_minus_L0 = L3_online_gru - L0_current_observation
L3_minus_L2 = L3_online_gru - L2_finite_window
```

Artifacts:

```text
runs/m538_natural_surface_paired_advantage_audit/summary.json
runs/m538_natural_surface_paired_advantage_audit/paired_deltas.csv
runs/m538_natural_surface_paired_advantage_audit/aggregate_paired_deltas.csv
runs/m538_natural_surface_paired_advantage_audit/surface_paired_deltas.csv
runs/m538_natural_surface_paired_advantage_audit/seed_paired_deltas.csv
runs/m538_natural_surface_paired_advantage_audit/event_paired_deltas.csv
runs/m538_natural_surface_paired_advantage_audit/bootstrap_ci.csv
runs/m538_natural_surface_paired_advantage_audit/dominance_summary.csv
```

## Join Integrity

| Metric | Count |
| --- | ---: |
| Input outcome rows | `20196` |
| Unique matched source/train keys | `6732` |
| Complete L0/L2/L3 triplet keys | `6732` |
| Incomplete triplet keys | `0` |
| M526 event keys after seed expansion | `54` |

The paired join is exact for all M537 rows. No unmatched aggregate comparison is
needed for the main conclusion.

## Aggregate Paired Deltas

Positive success, obstacle completion, return, and clearance margin deltas favor
L3. Negative collision deltas favor L3.

| Comparison | Rows | Success Delta | Completion Delta | Collision Delta | Return Delta | Margin Delta | Margin Positive Share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L3 - L0 | `6732` | `+0.020351` | `+0.020202` | `-0.020351` | `+0.841956` | `+0.144301` | `0.761735` |
| L3 - L2 | `6732` | `+0.018419` | `+0.018717` | `-0.018419` | `+0.665702` | `+0.113771` | `0.573232` |

Bootstrap confidence intervals over paired rows:

| Comparison | Metric | Mean | 95% CI Low | 95% CI High |
| --- | --- | ---: | ---: | ---: |
| L3 - L0 | success | `0.020351` | `0.017231` | `0.023916` |
| L3 - L0 | collision | `-0.020351` | `-0.023767` | `-0.017083` |
| L3 - L0 | clearance margin | `0.144301` | `0.136393` | `0.152003` |
| L3 - L2 | success | `0.018419` | `0.014557` | `0.022285` |
| L3 - L2 | collision | `-0.018419` | `-0.022434` | `-0.014706` |
| L3 - L2 | clearance margin | `0.113771` | `0.102916` | `0.123873` |

The aggregate paired signal is clearly positive for both comparisons on the
public diagnostic surfaces.

## Surface Dominance

| Comparison | Positive Margin Surfaces | Positive Success Surfaces | Max Surface Margin Share |
| --- | ---: | ---: | ---: |
| L3 - L0 | `4 / 4` | `4 / 4` | `0.479382` |
| L3 - L2 | `4 / 4` | `4 / 4` | `0.476644` |

Both comparisons are positive on all four public natural surfaces. The margin
signal is not from a single surface.

## Seed Dominance

| Comparison | Positive Margin Seeds | Positive Success Seeds | Max Seed Margin Share |
| --- | ---: | ---: | ---: |
| L3 - L0 | `3 / 3` | `3 / 3` | `0.467824` |
| L3 - L2 | `2 / 3` | `2 / 3` | `0.442512` |

The seed result is the important caveat:

- `L3 - L0` is positive for all three training seeds.
- `L3 - L2` is aggregate-positive, surface-positive, and CI-positive, but not
  seed-uniform.

Per-seed L3-L2 deltas:

| Seed | Success Delta | Return Delta | Margin Delta | Margin Positive Share |
| ---: | ---: | ---: | ---: | ---: |
| `3530` | `+0.047683` | `+2.206215` | `+0.278216` | `0.776292` |
| `3531` | `-0.013815` | `+0.034789` | `-0.143703` | `0.138592` |
| `3532` | `+0.021390` | `-0.243898` | `+0.206800` | `0.804813` |

Seed `3531` is a real finite-window counterexample: L2 beats L3 on success and
clearance margin for that matched training seed.

## M526 Event Overlay

The M526 event rows remain public diagnostics.

| Comparison | Event? | Rows | Success Delta | Collision Delta | Return Delta | Margin Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| L3 - L0 | no | `6678` | `+0.020216` | `-0.020216` | `+0.870717` | `+0.136627` |
| L3 - L0 | yes | `54` | `+0.037037` | `-0.037037` | `-2.714826` | `+1.093348` |
| L3 - L2 | no | `6678` | `+0.018269` | `-0.018269` | `+0.677726` | `+0.107952` |
| L3 - L2 | yes | `54` | `+0.037037` | `-0.037037` | `-0.821234` | `+0.833322` |

The event subset supports L3 on success, collision, and margin, but it is small
and public. It should not be treated as private generalization evidence.

## Interpretation

M538 confirms that M537 was not an unmatched aggregate artifact:

```text
L3 has a robust public paired advantage over L0.
L3 has an aggregate public paired advantage over L2, but the L2 comparison is
seed-fragile because seed 3531 favors L2.
```

The right next step is not to promote L3 or immediately enlarge PPO. First, M539
should audit the seed-3531 L2 counterexample and determine whether this is:

- a short-training variance artifact;
- a sign that finite-window history is enough on part of the public surface;
- a recurrent training instability;
- or a surface-specific behavior difference that should inform the next matched
  training recipe.

## Decision

```text
paired_l3_l0_pass_l3_l2_seed_fragile_admit_m539_seed_fragility_audit
```
