# M1127 V4 Public Base Row15 Projection Full Public Gate

## Purpose

M1127 evaluates the M1123 alpha `0.15` row15 projection candidate with the
pre-registered M1107 exact recheck and expanded full public gate from M1126.

This milestone is evaluation-only. It does not train actor weights, run PPO,
promote a checkpoint, use private holdout, or change actor inputs.

## Candidate

```text
candidate_label: alpha_0_15
candidate_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

base_checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

The candidate came from a no-training interpolation projection that directly
kept row15 wrong-history terminal margins unsafe while preserving exact M1107
improvement and first replay.

## M1107 Exact Recheck

Artifact:

```text
runs/m1127_row15_projection_m1107_exact_eval/summary.json
```

Result:

```text
proof_current exact loss: 0.679117321968
alpha_0_15 exact loss:   0.678699851036
delta vs proof_current:  -0.000417470932
```

The branch-specific exact objective remains improved relative to the current
public-gate base.

## Expanded Full Public Gate

Artifact:

```text
runs/m1127_row15_projection_full_public_gate/summary.json
```

Top-level result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
failure_types: none
```

Exact contract summary:

```text
full exact contract gate: pass
exact_m297_delta_vs_base: 0.0
exact_m270_delta_vs_base: 0.0
combined_anchor_total_loss: 0.000009034
changed parameter groups: allowed actor-coupling surface only
```

## Public Proof Replay

All old public replay surfaces retain their baseline success-drop counts:

```text
m183_m168: 16/16 pass
m183_m170: 17/17 pass
m193_m189: 14/14 pass
m212_m204: 17/17 pass
m223_m219: 17/17 pass
m267_m264: 17/17 pass
```

Normal success delta is `0.0` on each surface. The candidate therefore fixes the
row15 wrong-history-safe failure that rejected the full M1118 actor update
without losing normal-history success on the old public proof rows.

## Family and Source-Diverse Gates

M1061 family-intersection replay passes again inside the expanded gate:

```text
short61049: 25/25 success drops retained
short61050: 27/27 success drops retained
short61051: 27/27 success drops retained
```

The source-diverse protected diagnostic also passes:

```text
current_m333_surface: 17/17 pass
m314_continuity_surface: 17/17 pass
m317_continuity_surface: 17/17 pass
```

## Generalization and Behavior

Fresh randomized public eval:

```text
seed 103900: success 0.8671875 -> 0.8671875, margin delta +0.000155861
seed 103901: success 0.87109375 -> 0.87109375, margin delta +0.000155100
```

Moderate OOD eval:

```text
seed 103920: success 0.640625 -> 0.640625, margin delta -0.001488440
```

Behavior seeds retain baseline success:

```text
9505:   0.8625 -> 0.8625
9506:   0.8625 -> 0.8625
103930: 0.8375 -> 0.8375
103931: 0.8250 -> 0.8250
```

The reset and zero-all-response behavior checks remain below the normal
candidate policy on the registered behavior seeds, so the expanded behavior
ordering gate passes.

## Interpretation

M1127 is a positive full-public-gate result for alpha `0.15`. It supports the
claim that the no-training row15 unsafe-margin projection is public-proof clean
under the expanded gate stack.

It does not support a new PPO claim, private-holdout claim, paper-level
generalization claim, real-vehicle claim, or level3 anticipatory
self-identification claim. It also does not promote the checkpoint; promotion
requires a separate audit or synthesis decision.

## Process Note

The `failed_wrong_history_retention_repair` branch now spans M1118 through
M1127, which reaches the 10-milestone synthesis cadence. Therefore the next
step should be branch synthesis before any promotion audit, PPO, private
holdout, or new repair experiment.

## Decision

```text
row15_projection_full_public_gate_pass_route_to_branch_synthesis
```

Next milestone:

```text
m1128-v4-public-base-row15-projection-branch-synthesis
```
