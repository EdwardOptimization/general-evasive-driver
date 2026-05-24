# M560 Collision-Margin Route-Screen Selection

## Purpose

M560 trains the M559 collision/clearance-margin reward configs and evaluates all
interval/final checkpoints with route-screen v2 on a fresh selection seed.

This milestone does not promote a checkpoint. Because no candidate clears
route-screen v2, it does not admit public frozen-source diagnostics.

## Training Runs

| Variant | Run Dir | Final Eval Return | Final Eval Termination |
| --- | --- | ---: | ---: |
| `collision35_terminal4` | `runs/m560_l3_collision35_terminal4_seed3540` | `10.716457` | `1.000000` |
| `collision35_dense002` | `runs/m560_l3_collision35_dense002_seed3540` | `11.064788` | `1.000000` |
| `collision45_terminal4` | `runs/m560_l3_collision45_terminal4_seed3540` | `0.809814` | `1.000000` |

Higher collision penalties lower return as expected, but final checkpoints remain
route-unhealthy.

## Route-Screen V2

M560 evaluated:

```text
references = L0 + L2
candidates = 51 L3 interval/final checkpoints
episodes = 64
seed = 16560
uses_public_frozen_source_rows = false
```

Artifacts:

```text
runs/m560_collision_margin_route_screen_selection/summary.json
runs/m560_collision_margin_route_screen_selection/policy_summary.csv
runs/m560_collision_margin_route_screen_selection/episodes.csv
runs/m560_collision_margin_route_screen_selection/candidate_decisions.csv
runs/m560_collision_margin_route_screen_selection/family_best_candidates.csv
```

## Reference Result

| Policy | Success | Collision | Return | Margin Mean |
| --- | ---: | ---: | ---: | ---: |
| `l0_s3540` | `0.093750` | `0.796875` | `26.399848` | `0.080347` |
| `l2_s3540` | `0.671875` | `0.328125` | `67.820221` | `1.031682` |

## Candidate Gate Result

Overall decision:

```text
would_admit_public_eval = false
selected_candidate_label = None
admissible_candidate_count = 0 / 51
```

Route-screen v2 subchecks:

```text
passes_l0_success = 51 / 51
passes_l0_margin = 0 / 51
passes_l0_collision_tolerance = 0 / 51
passes_all = 0 / 51
```

Best candidate per family:

| Family | Best Candidate | Success | Margin Mean | Collision | Return | Success - L0 | Margin - L0 | Collision - L0 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `c35dense` | `c35dense_s3328` | `0.125000` | `0.012087` | `0.875000` | `22.352439` | `+0.031250` | `-0.068260` | `+0.078125` |
| `c35term` | `c35term_s3584` | `0.125000` | `0.013326` | `0.875000` | `21.978105` | `+0.031250` | `-0.067022` | `+0.078125` |
| `c45term` | `c45term_s1280` | `0.125000` | `0.011090` | `0.875000` | `13.745110` | `+0.031250` | `-0.069258` | `+0.078125` |

## Interpretation

Reward shaping moved the best candidate margins from negative in M556 to small
positive values on the fresh route-screen distribution. But L0's margin is also
positive and much higher on this seed block, so every candidate still fails the
margin rule.

The collision rule is unchanged:

```text
all best candidates collision_rate = 0.875000
L0 collision_rate = 0.796875
candidate_collision_minus_l0 = +0.078125
```

This suggests that the current L3 from-scratch PPO recipe is still learning a
more contact-prone obstacle strategy. Increasing collision penalty and adding
clearance-margin reward did not repair the route-screen failure.

## Decision

```text
collision_margin_route_screen_reject_admit_l2_to_l3_distillation_design
```

Failure types:

```text
training_instability
promotion_gate_failure
```

No public frozen-source diagnostics are admitted.

## Next Step

M561 should pivot away from another reward or PPO-stability sweep and design an
L2-to-L3 behavior distillation / anchoring route. L2 remains much stronger on
route-screen v2, and the recurrent L3 branch may need supervised grounding
before PPO continuation.
