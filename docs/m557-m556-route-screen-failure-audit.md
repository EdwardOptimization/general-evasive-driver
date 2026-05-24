# M557 M556 Route-Screen Failure Audit

## Purpose

M557 audits why M556 L3 repair-v2 candidates pass L0 binary success more often
than L0 but still fail route-screen v2 margin and collision checks.

This audit uses only M556 public-neutral route-screen artifacts. It does not run
training, public frozen-source diagnostics, or checkpoint promotion.

## Artifacts

```text
runs/m557_m556_route_screen_failure_audit/summary.json
runs/m557_m556_route_screen_failure_audit/terminal_pair_audit.csv
runs/m557_m556_route_screen_failure_audit/bucket_audit.csv
runs/m557_m556_route_screen_failure_audit/worst_margin_seeds.csv
```

Source:

```text
runs/m556_l3_repair_v2_route_screen_selection/summary.json
runs/m556_l3_repair_v2_route_screen_selection/episodes.csv
```

Provenance:

```text
uses_public_frozen_source_rows = false
```

## Gate Recap

M556 route-screen v2:

```text
candidate_count = 43
passes_l0_success = 35
passes_l0_margin = 0
passes_l0_collision_tolerance = 0
admissible_count = 0
```

Best candidates per family:

```text
epoch1_s256
longseq_s512
lowentropy_s256
```

## L0 Comparison

For `epoch1_s256` vs L0:

| L0 Outcome | Candidate Outcome | Seeds | Success Delta | Collision Delta | Margin Delta Mean |
| --- | --- | ---: | ---: | ---: | ---: |
| collision | collision | `47` | `0.0` | `0.0` | `-0.008702` |
| non-collision termination | collision | `7` | `0.0` | `+1.0` | `-0.783132` |
| collision | completed | `5` | `+1.0` | `-1.0` | `+0.536128` |
| completed | collision | `3` | `-1.0` | `+1.0` | `-0.497142` |
| completed | completed | `2` | `0.0` | `0.0` | `+0.867010` |

The other two best candidates show the same pattern.

Interpretation:

```text
The L3 variants gain binary success by converting 5 L0 collisions to completions,
but they also convert 7 L0 non-collision terminations into collisions and
3 L0 completions into collisions.
```

So this is not a benign success-only improvement. It is a collision-dominated
margin failure.

## L2 Comparison

For `epoch1_s256` vs L2:

| L2 Outcome | Candidate Outcome | Seeds | Success Delta | Collision Delta | Margin Delta Mean |
| --- | --- | ---: | ---: | ---: | ---: |
| completed | collision | `38` | `-1.0` | `+1.0` | `-1.723093` |
| collision | collision | `19` | `0.0` | `0.0` | `+0.005770` |
| completed | completed | `7` | `0.0` | `0.0` | `-1.900012` |

The L3 candidates are still far behind L2. Even when both complete, L3 has much
less clearance margin.

## Bucket Pattern

For `epoch1_s256` vs L0 by obstacle label:

| Label | Seeds | Success Delta | Collision Delta | Margin Delta Mean |
| --- | ---: | ---: | ---: | ---: |
| `aes_feasible` | `4` | `0.000000` | `+0.250000` | `-0.147832` |
| `drift_required` | `25` | `+0.080000` | `+0.080000` | `-0.087539` |
| `unavoidable` | `35` | `0.000000` | `+0.057143` | `-0.005369` |

By `mu_bucket`, the worst L0 margin loss is high-`mu`:

| Mu Bucket | Seeds | Success Delta | Collision Delta | Margin Delta Mean |
| --- | ---: | ---: | ---: | ---: |
| `high` | `10` | `0.000000` | `+0.200000` | `-0.270369` |
| `medium` | `37` | `+0.027027` | `+0.081081` | `-0.013852` |
| `low` | `17` | `+0.058824` | `0.000000` | `+0.014618` |

This does not look like a pure hidden-capability failure under low friction. It
looks more like an aggressive route policy that sometimes clears the obstacle
but often accepts too little clearance or hits the obstacle.

## Worst Seeds

The worst L0 margin deltas are dominated by:

```text
L0 non-collision termination -> L3 collision
L0 completed -> L3 collision
```

Examples:

| Seed | L0 Outcome | Candidate Outcome | Label | Mu | Brake | Steering Tau | Margin Delta |
| ---: | --- | --- | --- | --- | --- | --- | ---: |
| `15609` | non-collision termination | collision | `drift_required` | high | strong | nominal | `-1.494045` |
| `15594` | non-collision termination | collision | `aes_feasible` | medium | strong | slow | `-1.018631` |
| `15601` | non-collision termination | collision | `drift_required` | high | weak | slow | `-0.844396` |
| `15585` | completed | collision | `drift_required` | medium | strong | slow | `-0.711006` |

## Classification

```text
collision_dominated_margin_failure_after_binary_success_gain
```

The M555 PPO-stability variants did not fix the route/public bridge. They
created policies that are slightly more likely than L0 to complete some route
episodes, but at the cost of more collisions and lower clearance margin.

## Decision

```text
audit_admit_targeted_collision_margin_repair_design
```

No public frozen-source diagnostic should run from M556. The next step should
design a targeted collision/margin repair branch, with a fresh route-screen seed
for selection so M556's route-screen rows do not become the next overfit target.
