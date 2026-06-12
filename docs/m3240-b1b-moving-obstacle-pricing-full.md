# M3240: B1b Moving-obstacle Pricing Full

Status: completed. This is the full preregistered B1b moving-obstacle pricing
panel admitted by M3239. It runs no training, writes no policy checkpoint,
does not mutate the incumbent, and makes no driver-performance, validation,
promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, C2-admission, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3240-b1b-moving-obstacle-pricing-full.json`
- Preregistration: `experiments/feasibility_audit/moving_obstacle_pricing_prereg.json`
- Result JSON: `experiments/feasibility_audit/moving_obstacle_pricing.json`
- Episode rows: `runs/feasibility_audit/moving_obstacle_pricing/episode_rows.csv`
- Harness log: `runs/research/m3240-b1b-moving-obstacle-pricing-full_20260612T080610Z/command.log`

## Measured

Protocol gates:

| gate | value |
|---|---:|
| selection/validation seeds disjoint | true |
| validation rows | 32 |
| rows visible under fixed_star | 32 |
| oracle-attempted rows | 32 |
| structured/CEM-or-success coverage | true |

Compute budget:

| readout | value |
|---|---:|
| selection episodes | 540 |
| validation arm episodes | 128 |
| oracle rollouts | 40 |
| elapsed seconds | 13.9 |

The selected `fixed_star` grid was the identity `(1.0, 1.0, 1.0)`, with
20/20 pooled selection successes. The identity grid also had 20/20 pooled
selection successes.

Full-panel pricing:

| cell | oracle-solved rows | oracle solvability | fixed_star | v4_rls | v4_pertuned | oracle - pertuned |
|---|---:|---:|---:|---:|---:|---:|
| `slow_early_centering` | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `fast_late_centering` | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `slow_late_edge` | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `fast_mid_opposite_edge` | 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

No cell qualified by the frozen B1b rule:
`qualifying_cells=[]`.

Row diagnostics:

| readout | value |
|---|---:|
| `aeb_feasible` labels | 32/32 |
| fixed_star successes | 32/32 |
| v4_pertuned successes | 32/32 |
| oracle successes | 32/32 |
| fixed_star min clearance margin | 4.1125 m |
| reveal-step range | 7-50 |
| fixed_star step range | 90-130 |

Oracle successes were achieved by simple structured candidates:
`structured:full_brake` on 24 rows and `structured:brake_steer_+0.35` on
8 rows.

## Inferred

The B1b current moving-crosser formulation is negative. The reason is not
oracle failure or protocol coverage: oracle solvability was 1.0 and every row
was visible and searched. The reason is that the reflex family already solves
the entire full panel. The full-panel demand was still classified
`aeb_feasible` in every row, and the incumbent/identity fixed* arm cleared all
validation rows with large clearance margins.

This rejects the preregistered B1b prize as currently formulated. It does not
prove that no moving-obstacle task can ever create a gap; it says this
constant-velocity crosser panel does not create the type-(b) timing/prediction
region that B1b was meant to price. Any later moving-obstacle hardening would
need a new preregistration and should be treated as a new unit, not a repair
of M3240.

## Decision

Verdict: `b1b_moving_obstacle_pricing_negative`.

B1b current formulation is done-negative. No moving-obstacle Track C extension,
C2 admission, training, or driver-performance claim is admitted. The roadmap
should move to the next independent OPEN pricing unit, B2b high-speed domain
pricing.
