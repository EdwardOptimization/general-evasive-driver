# M1257 Paper-Route Capability-Separable Source-Construction Synthesis

## Summary

M1257 synthesizes the `paper_route_capability_separable_source_construction`
branch from M1241 through M1256.

Decision:

```text
capability_separable_source_construction_synthesis_promote_to_richer_fault_source_branch
```

Close the current local source-construction branch:

```text
paper_route_capability_separable_source_construction
```

Open the next branch:

```text
paper_route_richer_fault_capability_source
```

The current branch answered an important prerequisite question negatively for
the current source family:

```text
Under the current single-track/current-model fault source, matched-current
hidden-dynamics pairs repeatedly do not produce accepted capability-separable
rows under unchanged thresholds.
```

This does not make the research target infeasible. It means the current source
family is not yet rich or boundary-shaped enough to create the paper-route
training/evaluation rows needed for history-necessity gates.

## Evidence Summary

M1241 defined the source-validity question:

```text
Does the simulator contain matched-current hidden-dynamics cases where the
right first action or short action sequence is genuinely different?
```

The branch then tried increasingly stronger source-construction variables:

| Milestone | Source variable | Accepted rows | Key result |
| --- | --- | ---: | --- |
| M1242 | first-action lattice | 0 | 160 matched pairs, 24000 action rollouts, low regret |
| M1244 | short-sequence lattice | 0 | 120 matched pairs, 10320 sequence rollouts, low regret |
| M1246 | viability-band relocation | 0 | 48 relocated pairs, 24 near-boundary pairs, one near-positive row |
| M1247 | fine relocation | 0 | 96 fine candidates, one near-boundary viable selected pair |
| M1250 | condition-wise trajectory proposals | 0 | 425 proposals, near-miss with two-sided regret but negative margin |
| M1252 | targeted margin restoration | 0 | near-miss margin improved to `-0.0006610772` but stayed negative |
| M1255 | denser event timing/source state | 0 | 424 proposals, 848 rollouts, viable/action-equivalent and action-divergent/nonviable rows |

M1255 is the final local-source smoke in this branch. It found:

```text
near_boundary_viability_pairs: 1
best_actions_diverged_pairs: 2
low_regret_pairs: 8
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
```

The M1255 row pattern is decisive enough for a branch-level decision:

```text
viable rows exist but are action-equivalent;
action-divergent rows exist but are nonviable or one-sided;
accepted capability-separable rows do not appear.
```

## Supported Claims

Supported engineering claims:

```text
The capability-separable constructor infrastructure works.
The actor input contract was preserved.
The source labels stayed offline and did not enter deployable actor inputs.
First-action, short-sequence, trajectory proposal, relocation, and source-timing
variables can all be run and audited reproducibly.
```

Supported scientific/process claims:

```text
Hidden-dynamics randomization does not automatically imply action separability.
The current source family can produce partial evidence, but not accepted
capability-separable rows under the current thresholds.
More local source-window or proposal-budget tweaks would likely optimize the
harness rather than discover a new mechanism.
```

## Falsified Claims

Falsified for this branch:

```text
The M1236/M1241 current-model fault source is sufficient to produce accepted
matched-current capability-separable rows with local action/sequence/proposal
search and event-timing repair.
```

Not falsified:

```text
the overall General Evasive Driver objective;
closed-loop RL emergency avoidance;
the value of recurrent command-response history;
the possibility of capability-separable rows under richer fault/source families;
the need for high-fidelity or four-wheel validation later.
```

Still blocked:

```text
source-positive capability-separable corpus;
history-necessity actor gates on capability-separable rows;
PPO readiness;
paper-level self-identification evidence;
real-vehicle or high-fidelity physical claims.
```

## Failure Taxonomy Summary

Primary taxonomy:

```text
scenario_sampling_failure
```

Branch subtype:

```text
capability_separable_source_family_gap
```

Observed failure modes:

```text
low_regret_action_equivalence:
  broad lattice/sequence/proposal searches often find both hidden branches
  prefer the same maneuver.

near_positive_nonviable_source_row:
  trajectory proposal and targeted margin restoration create two-sided regret
  near-misses, but own-branch best margins remain slightly negative.

viable_action_equivalent_row:
  event timing creates at least one viable near-boundary row, but it has zero
  action separation and zero cross regret.

action_divergent_nonviable_or_one_sided_row:
  event timing creates large action separation in some pairs, but either one
  branch remains nonviable or one-sided regret stays below threshold.
```

Not observed:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
private_holdout_contamination
metric_artifact
```

## Public Gate Overfit Risk

Risk level if continuing the same branch:

```text
high
```

Reasons:

```text
The same public source families, seeds, and near-miss rows have now shaped
multiple local repairs.

M1251 already allowed one targeted margin-restoration repair; M1252 used it.

M1254 allowed one event-timing/source-state smoke; M1255 used it.

Another local tweak would be selected from known failures rather than a new
source-family hypothesis.
```

Mitigation:

```text
Close the local source-construction branch and open a new source-family branch
with a different evidence variable.
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close:

```text
paper_route_capability_separable_source_construction
```

Open:

```text
paper_route_richer_fault_capability_source
```

Next milestone:

```text
m1258-paper-route-richer-fault-capability-source-design
```

M1258 should design a bounded richer-fault/source-family bridge before any run.
The first candidate source should reuse existing v4 low-margin/fault-family
infrastructure where possible:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

That config already separates current-model faults, current-model proxies, and
future four-wheel/high-fidelity-only claims. The next branch may use proxy
faults for source mining, but must not claim true single-wheel blowout,
split-mu, stuck-caliper, halfshaft, suspension, or per-wheel ABS physics until
a four-wheel or high-fidelity dynamics engine exists.

M1258 must preserve:

```text
no training
no PPO
no private holdout
no promotion
no actor-input expansion
no acceptance-threshold relaxation
```

The next source run, if admitted later, should change the evidence variable to
source family / fault richness, not another local timing or proposal-budget
tweak.
