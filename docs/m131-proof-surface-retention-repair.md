# M131 Proof-Surface Retention Diagnosis

M130 rejects PPO readiness because M129 improves fixed M128 loss but weakens
fresh strict outcome-surface diversity. M131 diagnoses the regression mode
before changing the training recipe again.

## Compared Artifacts

Same strict miner seed:

```text
runs/m130_zero_relvel_m124_strict_60ep_seed9860
runs/m130_zero_relvel_m129_strict_60ep_seed9860
```

Both use the M121 zero-relvel profile and strict M127 thresholds.

## Selected Surface

| Policy | Accepted rows | Selected pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 | 23 | 6 | 4 | 23 | 0.035959 |
| M129 | 14 | 5 | 4 | 14 | 0.015155 |

M129 retains a surface, but it is smaller and has lower max margin gap.

## Filter-Level Diagnosis

Visible and perturbed margin-gap accepted rows:

| Policy | Rows | Seeds | Pairs | Gap mean | Gap max | First-action dist mean | First-action dist max | Trajectory dist mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M124 | 158 | 6 | 10 | 0.020974 | 0.188070 | 0.087288 | 0.120638 | 0.032974 |
| M129 | 156 | 6 | 8 | 0.009717 | 0.023838 | 0.099090 | 0.183385 | 0.026182 |

Strict accepted rows:

| Policy | Rows | Seeds | Pairs | Gap mean | Gap max | First-action dist mean | First-action dist max | Trajectory dist mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M124 | 23 | 4 | 6 | 0.017592 | 0.035959 | 0.101018 | 0.112682 | 0.036507 |
| M129 | 14 | 4 | 5 | 0.008877 | 0.015155 | 0.109515 | 0.182635 | 0.022577 |

The regression is not a simple loss of one-step action difference. M129 has
larger first-action distance, but lower trajectory distance and much smaller
rollout margin gaps. The fixed logprob objective made the corpus easier to fit
without preserving the fresh rollout-level outcome degradation that the proof
surface needs.

## Interpretation

M129 likely overfits the fixed M128 snippets as a one-step logprob separation
problem:

```text
preferred hidden -> higher probability of preferred action
rejected hidden -> lower probability of preferred action
```

That does not guarantee:

```text
wrong history -> worse closed-loop clearance margin
```

For the ideal driver proof, the second statement matters more. M131 therefore
keeps M130's PPO rejection and changes the next repair target.

## Decision

M131 is a diagnosis result, not a repair.

What is now clear:

- M129 behavior retention is not the blocker;
- M62 control cleanliness is not the blocker;
- fixed M128 loss improvement is not sufficient;
- the blocker is fresh rollout-margin proof-surface retention;
- no-action neutrality and perturbed-only source coverage remain limitations.

Next step: M132 should test a repair that preserves fresh rollout margin gaps
and selected-pair diversity, not just fixed snippet logprob loss.
