# M1217 Paper-Route Current-Family Matched-Current Export

## Summary

M1217 exports the first current-family matched-current ambiguity surface for
the M1215 causal-history gate.

Decision:

```text
current_family_matched_current_surface_pass_admit_action_screen
```

No action intervention, outcome intervention, training, PPO, checkpoint repair,
promotion, private holdout, profile tuning, or actor-input change occurs in
M1217.

## Command

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

## Artifacts

```text
runs/m1217_current_family_matched_current_export/summary.json
runs/m1217_current_family_matched_current_export/matched_pairs.csv
runs/m1217_current_family_matched_current_export/candidate_pairs.csv
runs/m1217_current_family_matched_current_export/target_summary.csv
```

## Result

Top-level summary:

```text
candidate pairs:                 177579
accepted pairs:                    1790
accepted physical pairs:            427
accepted left steps:                 21
accepted obstacle buckets:           12
accepted targets:                     3
ambiguity surface found:           true
```

Accepted pairs by target:

| Target | Accepted Pairs |
| --- | ---: |
| future braking deceleration | `1051` |
| future yaw response | `697` |
| future lateral accel response | `42` |

Accepted pairs by checkpoint:

| Checkpoint | Accepted Pairs | Share |
| --- | ---: | ---: |
| l3_s111600 | `444` | `0.2480` |
| l3_s111601 | `745` | `0.4162` |
| l3_s111602 | `601` | `0.3358` |

Accepted pairs by probe seed:

| Probe Seed | Accepted Pairs | Share |
| ---: | ---: | ---: |
| `122600` | `450` | `0.2514` |
| `122601` | `448` | `0.2503` |
| `122602` | `469` | `0.2620` |
| `122603` | `423` | `0.2363` |

Accepted pairs by obstacle label:

| Label | Accepted Pairs | Share |
| --- | ---: | ---: |
| aes_feasible | `805` | `0.4497` |
| unavoidable | `658` | `0.3676` |
| drift_required | `327` | `0.1827` |

Distance and ambiguity diagnostics:

```text
visible distance mean / p50 / p90:          0.145139 / 0.142511 / 0.177156
target z delta mean / p50 / p90:            1.587169 / 1.347001 / 2.524232
current-response distance mean / p50 / p90: 0.233510 / 0.239258 / 0.337155
response-hidden distance mean / p50 / p90:  0.187010 / 0.195176 / 0.261010
reset-hidden distance mean / p50 / p90:     0.270881 / 0.287655 / 0.376937
```

Obstacle geometry:

```text
left obstacle distance mean / p10 / p50 / p90: 7.876175 / 3.195882 / 7.536720 / 13.640807
left obstacle lateral mean / p10 / p50 / p90: -0.944031 / -1.751919 / -0.889966 / -0.379212
```

## Pass Criteria

Pre-registered M1217 thresholds:

```text
accepted pairs >= 120
physical pairs >= 30
probe seeds >= 3
left steps >= 5
obstacle buckets >= 4
targets >= 2
```

Observed:

```text
accepted pairs = 1790
physical pairs = 427
probe seeds = 4
left steps = 21
obstacle buckets = 12
targets = 3
```

M1217 passes the surface-diversity gate.

## Interpretation

M1217 provides the correct substrate for the next causal-history stage:

```text
same or close current response/context;
different future response targets;
source-diverse current corrected L3 checkpoints;
public probe seeds;
P0 human-view no-wheel no-oracle actor contract.
```

This does not prove history necessity or self-identification. Pair mining only
shows that matched-current ambiguity exists. Causal evidence requires M1218
action interventions and later outcome interventions if the action screen
admits them.

The strongest caveat is target imbalance:

```text
future lateral accel response contributes only 42 rows.
```

This is acceptable for M1218 because the surface still spans 3 targets and the
two dominant targets are the braking/yaw envelopes most relevant to emergency
avoidance. If M1218 action signal is source-narrow, later mining should increase
lateral-response coverage.

## Decision

```text
current_family_matched_current_surface_pass_admit_action_screen
```

Next blocker:

```text
m1218-paper-route-current-family-history-action-screen
```
