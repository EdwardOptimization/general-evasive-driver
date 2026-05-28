# M1275 Paper-Route Fidelity Fault Source Synthesis

## Summary

M1275 synthesizes the `paper_route_fidelity_fault_source_design` branch from
M1265 through M1274.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
fidelity_fault_source_synthesis_promote_to_source_intervention_materialization
```

The branch should close as a source-construction branch and promote to a new
branch:

```text
paper_route_four_wheel_source_intervention_materialization
```

Rationale:

```text
M1265-M1274 established a compact four-wheel source model and a strict
capability-separable source corpus. The next question is no longer whether the
source exists; it is how to materialize source rows into intervention/replay
artifacts that can later test or train a human-view driver without leaking
hidden fault metadata.
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, or self-identification claim occurs in M1275.

## Evidence Summary

M1265 identified the source-fidelity gap:

```text
The single-track source model has no left/right or per-wheel force channel, so
it cannot express split-mu, stuck-caliper brake pull, single-wheel grip
collapse, or halfshaft asymmetry as physical left/right yaw-moment sources.
```

M1266 implemented the compact four-wheel fault primitive:

```text
left-low split-mu yaw moment: -786.3186173
right-low split-mu yaw moment: 786.3186173
front-left brake-pull yaw moment: 750.1433310
front-right brake-pull yaw moment: -750.1433310
```

M1267 defined clean source integration:

```text
source-only first;
no Gym replacement;
no policy training;
human-view 72-value observation compatibility;
fault/per-wheel metadata remains artifact-only.
```

M1268 ran the first source-shape smoke and fixed a metric artifact:

```text
initial artifact: horizon-only rows were incorrectly accepted;
fixed semantics: success = no collision and (obstacle_completed or safe_stop).
```

Final M1268 result:

```text
accepted_separable_pairs: 0
best_actions_diverged_pairs: 27
low_regret_pairs: 92
own_branch_viability_fail_count: 103
all_four_rollouts_collision_count: 103
top min_cross_regret: 0.1793146044
```

M1269 audited the blocker shift:

```text
old blocker: action-divergent but low-regret
new blocker: high-regret but own-branch nonviable / collision dominated
```

M1270 designed viability calibration, and M1271 ran it:

```text
scenario_profile: viability_calibration
matched_pair_count: 720
accepted_separable_pairs: 108
best_actions_diverged_pairs: 216
low_regret_pairs: 561
accepted_fault_family_pairs: 3
result_class: capability_separable_signal
source_positive: true
```

M1272 audited source diversity and boundary usefulness:

```text
unique accepted geometries: 71
near-boundary rows at min own margin <= 0.20: 19
high-regret rows at min cross-regret >= 0.05: 32
halfshaft accepted rows: 0
halfshaft best_action_l2 max: 0.0
```

M1273 exported the stratified source corpus:

```text
all accepted rows: 108
near-boundary rows: 19
high-regret rows: 32
family-balanced rows: 63
inactive fault family count: 1
```

M1274 audited the corpus:

```text
corpus is suitable source material;
direct actor/Gym integration remains blocked;
branch cadence requires synthesis before another narrow source step.
```

## Supported Claims

Supported:

```text
The compact in-repo four-wheel source model can produce signed left/right yaw
response for split-mu and brake-pull faults.
```

Supported:

```text
Under matched visible source state and unchanged actor-input guardrails, the
four-wheel source model can produce strict capability-separable source rows:
two hidden fault branches require different action sequences and have
nontrivial cross-regret.
```

Supported:

```text
The previous repeated zero-accepted source gap was not inherent to the overall
research goal. It was at least partly a source-fidelity and viability-window
problem.
```

Supported:

```text
M1273 provides reusable source artifacts for the next branch:
all accepted, near-boundary, high-regret, family-balanced, and inactive-family
subsets.
```

Supported:

```text
Halfshaft torque-loss is not useful under the current brake-dominant source
lattice because it is viable but action-equivalent. It should be dropped from
the immediate accepted corpus or mined later under throttle-on conditions.
```

## Falsified Claims

Falsified:

```text
The M1268 default close/fast source grid is sufficient for four-wheel
capability-separable rows.
```

Falsified:

```text
Horizon-only no-collision rows can be counted as success for source acceptance.
```

Falsified:

```text
All fault families in the initial four-wheel source set are equally useful.
Halfshaft remains action-equivalent in the current source lattice.
```

Falsified:

```text
Source-positive rows can be treated as driver performance or self-ID evidence.
M1271-M1273 are open-loop no-policy source artifacts only.
```

Not yet proven:

```text
A human-view recurrent actor can use these source rows to produce better
closed-loop behavior.
```

Not yet proven:

```text
Wrong-history or delayed-history actor interventions will degrade behavior on
this four-wheel source family.
```

Not yet proven:

```text
The compact four-wheel source model is high-fidelity or real-vehicle validated.
```

## Failure Taxonomy Summary

Resolved failure:

```text
metric_artifact:
  M1268 initially accepted horizon-only rows; success semantics were corrected.
```

Resolved failure:

```text
scenario_sampling_failure:
  M1268 was collision dominated. M1271 viability calibration restored
  own-branch viability and produced accepted source rows.
```

Active limitation:

```text
source_subset_boundary_risk:
  The full accepted set is margin-easy on average; near-boundary and high-regret
  subsets must guide the next branch.
```

Active limitation:

```text
inactive_fault_family:
  Halfshaft is action-equivalent under the current source lattice.
```

Not observed:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
private_holdout_contamination
```

## Public Gate Overfit Risk

Risk level:

```text
moderate
```

Reason:

```text
M1271 was calibrated after M1268 showed collision dominance, and all source
artifacts are public research artifacts.
```

Mitigating evidence:

```text
accepted rows span 71 geometries, 3 speeds, 5 obstacle distances, 4 half-widths,
and 3 accepted fault-family pairs.
```

Remaining risk:

```text
lateral-offset diversity is weak because 96/108 accepted rows are centered;
near-boundary subset is only 19 rows;
halfshaft contributes no accepted rows.
```

Policy:

```text
Do not use M1271-M1273 as private generalization evidence. Treat them as public
source-construction artifacts and require later fresh source/generalization
checks before any paper-level claim.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
paper_route_fidelity_fault_source_design
```

Open:

```text
paper_route_four_wheel_source_intervention_materialization
```

Next branch question:

```text
Can the M1273 source corpus be materialized into intervention/replay artifacts
that preserve human-view input constraints and expose the counterfactual
relationship between hidden fault branch, preferred action sequence, rejected
action sequence, and terminal outcome?
```

The first next milestone should be design-only:

```text
m1276-paper-route-four-wheel-source-intervention-materialization-design
```

It should start from:

```text
near_boundary_source_rows.csv
high_regret_source_rows.csv
family_balanced_source_rows.csv
```

It should not train or integrate the actor yet.

## Guardrails

The next branch must preserve:

```text
actor observation remains human-view;
fault labels/per-wheel metadata stay training/artifact-only;
accepted thresholds remain strict;
horizon-only success remains non-success;
source artifacts are not driver performance;
no PPO or actor training until intervention/replay artifacts are audited.
```

## Next Step

Pre-register:

```text
experiments/manifests/m1276-paper-route-four-wheel-source-intervention-materialization-design.json
```
