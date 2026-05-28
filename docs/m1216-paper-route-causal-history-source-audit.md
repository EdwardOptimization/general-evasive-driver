# M1216 Paper-Route Causal History Source Audit

## Summary

M1216 audits existing matched-current and history-intervention artifacts before
running the causal-history gate designed in M1215.

Decision:

```text
source_audit_selects_current_family_matched_current_export
```

No training, PPO, replay gate, checkpoint repair, promotion, private holdout,
profile tuning, or actor-input change occurs in M1216.

## Audit Question

M1215 requires a source-diverse surface where the current observation is matched
but command-response history may differ. M1216 asks:

```text
Can existing public artifacts support the first causal-history run directly,
or should the paper route export a fresh current-family matched-current
surface first?
```

## Artifact Inventory

### M503 Natural Boundary-Pressure Surface

Artifact:

```text
runs/m503_natural_boundary_pressure_matched_current_summary/combined_matched_pairs.csv
runs/m503_natural_boundary_pressure_matched_current_summary/combined_summary.json
```

Summary:

```text
accepted pairs:          5727
physical pairs:          3716
probe seeds:                6
obstacle labels:            3
targets:                    3
left steps:                24
obstacle buckets:          26
single seed share:      0.185
surface gate:           pass
```

Assessment:

```text
source quality: high
tooling relevance: high
current-family compatibility: partial
```

M503 is the best template for surface diversity and matching thresholds. It is
not the best first M1215 run source because it was mined for an older
boundary-pressure branch, not the current corrected profile checkpoints.

### M524 Multisurface History-Value Ablation

Artifact:

```text
runs/m524_natural_history_value_ablation/summary.json
runs/m524_natural_history_value_ablation/history_value_rows.csv
```

Summary:

```text
classification:          event_history_value_signal
row count:               4408
L0 candidate count:       480
L0 event rows:             18
probe seeds:               12
targets:                    3
surface count:              2
```

Assessment:

```text
source quality: useful diagnostic
tooling relevance: medium
current-family compatibility: indirect
```

M524 shows public event-level L3-vs-reset diagnostic signal on natural
surfaces, but it is not a matched-current wrong/delayed-history gate. It should
inform interpretation and failure taxonomy, not serve as the first current
paper-route causal surface.

### M537/M538 Public Natural-Surface Matrix

Artifacts:

```text
runs/m537_full_public_natural_surface_eval_aggregate/summary.json
runs/m538_natural_surface_paired_advantage_audit/summary.json
```

Summary:

```text
M537 rows per level:     6732
L3 success:             0.851901
L2 success:             0.833482
L0 success:             0.831551
L3-L0 success delta:   +0.020351
L3-L2 success delta:   +0.018419
L3-L0 margin delta:    +0.144301
L3-L2 margin delta:    +0.113771
L3-L2 positive seeds:   2 / 3
```

Assessment:

```text
source quality: strong public architecture diagnostic
tooling relevance: medium
current-family compatibility: indirect
```

M537/M538 support the paper route by showing that paired public natural-surface
comparison is available and that L3 can outperform L0/L2 on public diagnostics.
They do not prove causal hidden-history use. The L3-L2 seed fragility also
argues against using broad profile comparison as the next evidence step.

### M585-M587 BC5660 History-Intervention Path

Artifacts:

```text
runs/m586_bc5660_matched_current_fresh_seed25560/summary.json
runs/m586_bc5660_matched_current_ood_seed25660/summary.json
runs/m587_bc5660_history_action_screen_fresh_seed25560/summary.json
runs/m587_bc5660_history_action_screen_ood_seed25660/summary.json
```

M586 matched-current source quality:

```text
fresh route accepted pairs:      666
fresh physical pairs:            192
fresh left steps:                 15
fresh obstacle buckets:           14
OOD accepted pairs:              403
OOD physical pairs:              152
OOD left steps:                   14
OOD obstacle buckets:             14
```

M587 action screen result:

```text
wrong/delayed history: negative on both surfaces
zero current response: positive control passes on every screened row
zero action history:   action-sensitive on both surfaces
reset hidden:          weak or near-threshold
```

Assessment:

```text
source quality: high
tooling relevance: high
current-family compatibility: negative baseline only
```

M585-M587 is the closest existing precedent for M1215. It also provides an
important negative lesson: source-diverse matched-current pairs do not guarantee
wrong/delayed hidden-history sensitivity. The first current-family gate must
allow the same negative outcome and should not skip the action screen.

## Tooling Compatibility

| Tool | Role | Status |
| --- | --- | --- |
| `matched_current_response_ambiguity` | export matched-current ambiguity pairs | usable now |
| `matched_history_intervention_gate` | action-level reset/delayed/wrong/zero controls | usable for online recurrent checkpoints |
| `persistent_wrong_history_intervention_gate` | outcome-level persistent wrong-history replay | usable after action-screen admission |
| `outcome_critical_matched_current_selector` | compact outcome-critical corpus selection | usable after action and outcome rows exist |
| `history_value_ablation_runner` | L3-vs-level summary on existing outcome tables | diagnostic only |
| `frozen_source_surface_eval` | L0/L2/L3 matched baseline comparison | useful for architecture comparison, not hidden injection |

Current corrected L3 checkpoints exist:

```text
runs/m1209_corrected_profile_pilot/profile_runs/L3_online_gru/seed_110600/checkpoint.pt
runs/m1209_corrected_profile_pilot/profile_runs/L3_online_gru/seed_110601/checkpoint.pt
runs/m1209_corrected_profile_pilot/profile_runs/L3_online_gru/seed_110602/checkpoint.pt
runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt
runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt
runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
```

The corrected public config is available:

```text
configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
```

It preserves the P0 human-view no-wheel no-oracle contract and uses
`obstacle_relative_velocity_mode = zero`.

## Decision

Do not use old M503/M524/M537/M538/M586/M587 rows as the first M1215 causal run.

Use them as:

```text
threshold precedents;
negative/positive interpretation precedent;
source-diversity standards;
tooling compatibility evidence.
```

The first run should export a fresh matched-current surface for the current
corrected-profile L3 family:

```text
checkpoint family: M1212 corrected L3 online GRU repeat
env config:        configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
probe seeds:       fresh public seeds not used by M1209/M1212 eval
output:            runs/m1217_current_family_matched_current_export
```

Rationale:

```text
M1212 is the latest corrected profile repeat.
M1212 L3 online beat corrected reset in aggregate but did not prove hidden
history causality.
A current-family matched-current export is the cleanest bridge from M1214's
profile branch to M1215's causal-history gate.
```

## M1217 Route

M1217 should run pair mining only:

```text
no action intervention;
no outcome intervention;
no training;
no PPO;
no promotion;
no private holdout;
no self-identification claim.
```

Initial command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy l3_s111600=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt \
  --checkpoint-policy l3_s111601=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --probe-seeds 122600,122601,122602,122603 \
  --episodes 32 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 120 \
  --device cpu \
  --run-dir runs/m1217_current_family_matched_current_export
```

M1217 pass criteria:

```text
accepted pairs >= 120
physical pairs >= 30
probe seeds >= 3
left steps >= 5
obstacle buckets >= 4
targets >= 2
no actor-input contract violation
```

If M1212-only mining is source-narrow, the fallback is to add the M1209
corrected L3 block as an expanded source family before action screening.

## Decision

```text
source_audit_selects_current_family_matched_current_export
```

Next blocker:

```text
m1217-paper-route-current-family-matched-current-export
```
