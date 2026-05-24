# M556 L3 Repair V2 Route-Screen Selection

## Purpose

M556 trains the three M555 L3 repair-v2 configs and applies reusable
route-screen v2 to all saved interval/final checkpoints before any public
frozen-source diagnostic.

This milestone does not promote a checkpoint. Because route-screen v2 rejects
all candidates, it also does not admit public frozen-source diagnostics.

## Training Runs

| Variant | Run Dir | Final Eval Return | Final Eval Termination |
| --- | --- | ---: | ---: |
| `epoch1_clip01` | `runs/m556_l3_repair_epoch1_clip01_seed3540` | `21.049852` | `1.000000` |
| `longseq_epoch1` | `runs/m556_l3_repair_longseq_epoch1_seed3540` | `22.860050` | `1.000000` |
| `lowentropy_epoch1` | `runs/m556_l3_repair_lowentropy_epoch1_seed3540` | `22.112663` | `1.000000` |

The training-time final eval remains unhealthy for all three variants, so
checkpoint selection must rely on the pre-registered route-screen v2 over all
saved interval/final checkpoints.

## Route-Screen V2 Command

M556 evaluated:

```text
references = L0 + L2
candidates = 43 L3 interval/final checkpoints
episodes = 64
seed = 15560
uses_public_frozen_source_rows = false
```

Artifacts:

```text
runs/m556_l3_repair_v2_route_screen_selection/summary.json
runs/m556_l3_repair_v2_route_screen_selection/policy_summary.csv
runs/m556_l3_repair_v2_route_screen_selection/episodes.csv
runs/m556_l3_repair_v2_route_screen_selection/candidate_decisions.csv
runs/m556_l3_repair_v2_route_screen_selection/family_best_candidates.csv
```

## Reference Result

| Policy | Success | Collision | Return | Margin Mean |
| --- | ---: | ---: | ---: | ---: |
| `l0_s3540` | `0.078125` | `0.812500` | `23.848425` | `-0.005521` |
| `l2_s3540` | `0.703125` | `0.296875` | `67.567267` | `1.177296` |

L2 remains far stronger than L0 and all L3 candidates on this public-neutral
route-screen distribution.

## Candidate Gate Result

Overall decision:

```text
would_admit_public_eval = false
selected_candidate_label = None
admissible_candidate_count = 0 / 43
```

Route-screen v2 subchecks:

```text
passes_l0_success = 35 / 43
passes_l0_margin = 0 / 43
passes_l0_collision_tolerance = 0 / 43
passes_all = 0 / 43
```

Best candidate per family:

| Family | Best Candidate | Success | Margin Mean | Collision | Return | Success - L0 | Margin - L0 | Collision - L0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `epoch1` | `epoch1_s256` | `0.109375` | `-0.051892` | `0.890625` | `29.332102` | `+0.031250` | `-0.046370` | `+0.078125` |
| `longseq` | `longseq_s512` | `0.109375` | `-0.064717` | `0.890625` | `29.155302` | `+0.031250` | `-0.059195` | `+0.078125` |
| `lowentropy` | `lowentropy_s256` | `0.109375` | `-0.053911` | `0.890625` | `29.311382` | `+0.031250` | `-0.048389` | `+0.078125` |

Interpretation:

```text
The best M555 candidates slightly beat L0 on binary success,
but all are worse than L0 on clearance margin and collision rate.
```

This is exactly why M551/M553 route-screen v2 needs obstacle margin and
collision checks instead of return or success alone.

## Decision

M556 rejects public diagnostics:

```text
l3_repair_v2_route_screen_reject_admit_m557_failure_audit
```

Failure types:

```text
training_instability
promotion_gate_failure
```

## Next Step

M557 should audit the M556 route-screen failure before more training. The audit
should compare candidate action patterns and terminal outcomes against L0/L2 on
the route-screen episodes, because the new variants improve binary success over
L0 but worsen margin and collision.
