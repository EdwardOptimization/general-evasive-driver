# M2256 Paper-Route Current-Sim Offtrack Failure-Slice Diagnosis Implementation

- status: completed
- decision: `current_sim_offtrack_failure_slice_diagnosis_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2256-paper-route-current-sim-offtrack-failure-slice-diagnosis-implementation.json`
- result artifact: `runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/summary.json`

## Execution Result

M2256 completed the no-rerun failure-slice diagnosis over existing episode rows:

```text
result_class: current_sim_offtrack_failure_slice_diagnosis_pass
baseline_episode_count: 480
repaired_episode_count: 480
support_complete: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
primary_route: stronger_offtrack_recovery_corridor_repair_design
```

No reset, rollout, policy action, training, replay, PPO, private holdout, or
promotion was run.

## Global Delta

M2256 confirms the M2254 synthesis result:

| metric | baseline M2244 | repaired M2253 | delta |
| --- | ---: | ---: | ---: |
| episodes | `480` | `480` | `0` |
| success | `277` | `269` | `-8` |
| offtrack | `110` | `118` | `+8` |
| collision | `93` | `93` | `0` |
| mean return | `49.83740` | `64.21352` | `+14.37612` |

The repaired reward branch improves return but worsens actual offtrack outcome.

## Slice Evidence

Offtrack timing delta:

| timing bucket | baseline offtrack | repaired offtrack | delta |
| --- | ---: | ---: | ---: |
| mid_offtrack | `88` | `102` | `+14` |
| late_offtrack | `22` | `16` | `-6` |

Offtrack severity delta:

| severity bucket | baseline offtrack | repaired offtrack | delta |
| --- | ---: | ---: | ---: |
| mild_overshoot | `15` | `26` | `+11` |
| severe_overshoot | `81` | `81` | `0` |
| trace_overshoot | `14` | `11` | `-3` |

Clearance risk delta:

| clearance bucket | baseline offtrack | repaired offtrack | delta |
| --- | ---: | ---: | ---: |
| safe_clearance_margin | `95` | `102` | `+7` |
| medium_clearance_margin | `15` | `16` | `+1` |
| collision | `93` | `93` | `0` collision delta |

Profile-seed deltas are not dominated by one absolute `>=5` regression row.
The largest local guardrail concern is:

```text
L3_online_gru|222602:
  success_delta: -4
  collision_delta: +4
  offtrack_delta: 0
```

## Classification

Primary classification:

```text
midcourse_mild_boundary_containment_regression
```

Supported:

- The offtrack regression is mainly mid-episode, not late-only.
- The offtrack regression is mainly mild overshoot, not severe loss of control.
- Collision count is unchanged globally.
- Many new offtrack rows still have safe clearance margins, so this is more of
  a road/corridor containment failure than an obstacle-clearance failure.

Not supported:

- Collision/clearance guardrail repair as the sole next route.
- Profile-seed-specific repair as the sole next route.
- Another scalar return-oriented reward tweak.
- Any ranking, paper-level, finite-window-vs-GRU, or self-ID claim.

## Route Decision

Route to:

```text
m2257-paper-route-current-sim-offtrack-failure-slice-diagnosis-result-audit
```

M2257 should decide whether this supports:

```text
midcourse corridor-containment repair design
recovery/corridor curriculum redesign
branch synthesis or stop if the current simulator/task is too brittle
```

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another scalar reward tweak before audit
```

## Next

Pre-register:

```text
m2257-paper-route-current-sim-offtrack-failure-slice-diagnosis-result-audit
```
