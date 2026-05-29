# M1676 Paper-Route Controller-Family Decisive Task-Source Mapping Design

## Summary

M1676 designs the next controller-family-compatible decisive task-source mapping
route after the standard-layer one-seed pilot passed plumbing but remained
scientifically non-decisive.

Decision:

```text
decisive_task_source_mapping_design_admit_metadata_preflight
```

This milestone is design-only. It does not train, replay, run PPO, promote,
use private holdout, change actor inputs, repair the M1663 artifact, execute a
task-source mapping, or claim controller-family ranking, paper-level evidence,
or level3 self-identification.

## Why This Branch Is Needed

M1674/M1675 proved the 12-profile runner works, but the standard task layer does
not answer the paper question:

```text
L2 current-tiled controls match L2 success/collision on the one-seed standard layer;
L3 reset-control beats L3 online on the one-seed standard layer;
M1497 already showed the same standard-layer caution at three seeds.
```

The missing evidence is not another standard-profile repeat. It is a
controller-family-compatible decisive task source where current-response,
current-tiled finite-window controls, and reset-GRU controls are explicit
challengers.

## M1615 Use Policy

M1615 remains public diagnostic evidence, not a direct controller-family
benchmark.

Allowed uses:

```text
identify source-family names and active-set contours;
identify useful source-edge/window patterns;
identify diagnostic guardrail types;
guide metadata preflight coverage.
```

Forbidden uses:

```text
use M1615 hidden tensors as controller-family labels;
use M1615 preferred actions as benchmark targets for L0/L1/L2 profiles;
use M1615 rows as private holdout;
claim L3 superiority because M1615 was generated through an online-GRU proof harness.
```

The first mapping preflight should therefore inspect metadata only. If metadata
is insufficient to reconstruct controller-family-compatible task sources, the
route should pivot to fresh source generation.

## Target Task Families

### T4 Same-Current / Same-Recent / Different-Older-History

Purpose:

```text
make older command-response history relevant while matching current and recent
evidence closely enough that L1 and short current-tiled controls are real
challengers.
```

Candidate source families to inventory first:

```text
actuator_delay_step
capability_step_up
capability_step_down
curved_boundary_obstacle
t5_near_boundary_warmup
t5_boundary_axis_retarget
```

These come from the clean-source and contour branches where public evidence
already found pairability or clean history-control rows.

### T5 Terminal-Boundary Near-Constraint

Purpose:

```text
make the history/control choice matter for terminal collision, road departure,
or clearance margin rather than only action residual.
```

Candidate source families to inventory first:

```text
t5_boundary_axis_retarget
t5_near_boundary_warmup
t5_high_speed_close_obstacle
late_reveal_boundary
curved_boundary_obstacle
```

T5 source mapping should require recoverability or near-boundary evidence before
history interventions are attempted.

## Mapping Artifact Contract

The next preflight should create:

```text
runs/m1677_controller_family_decisive_task_source_mapping_preflight/summary.json
runs/m1677_controller_family_decisive_task_source_mapping_preflight/task_source_mapping.json
```

The mapping artifact should contain only deployable task metadata:

```text
task_family: T4 or T5
source_family
source_run_or_doc
seed namespace
capability/fault family name used by sampler only
road/obstacle/source metadata if available
candidate window/reveal/decision step metadata if available
allowed controller profiles
required controls
mapping_status
mapping_risk
```

It must not include deployable actor inputs that violate P0, hidden labels as
actor inputs, or M1615 hidden tensors/actions as benchmark targets.

## Source-Diversity Gates

The preflight should report these counts:

```text
candidate_source_family_count
candidate_task_family_count
candidate_edge_count
candidate_window_count
candidate_seed_namespace_count
max_single_source_family_share
```

Design thresholds for an implementation route:

```text
candidate_source_family_count >= 5
candidate_task_family_count >= 2
candidate_edge_count >= 8
candidate_window_count >= 4
max_single_source_family_share <= 0.35
```

These are metadata gates only. Passing them does not prove task quality.

## Control-Substitution Gates

Every future mapped task must reserve these comparisons:

```text
L1_one_step
L2 normal windows
matched L2 current-tiled windows
L3_online_gru
L3_reset_control_corrected
```

For later measured runs, every candidate should report:

```text
L2 normal - current-tiled success and margin delta;
L3 online - reset success and margin delta;
L1 versus best L2/L3;
normal history versus wrong/delayed history only if the task source supports it.
```

If L1 or current-tiled controls solve the task, the result is a valid negative
or conditional result, not a failure of the project.

## Stop Rules

Stop or pivot before implementation if:

```text
M1615 metadata is too hidden-tensor-specific to reconstruct task sources;
only one source family dominates;
T4/T5 task families cannot both be represented;
current-response/current-tiled/reset controls cannot be applied equally;
the design would require profile-specific tuning;
the route needs private holdout to debug public task construction.
```

Fallback:

```text
if M1615 cannot map safely, route to fresh source-generation preflight using
existing decisive-history source families and public seed namespaces.
```

## Next Step

Admit exactly one no-training metadata preflight:

```text
m1677-paper-route-controller-family-decisive-task-source-mapping-preflight
```

M1677 should read existing public metadata and write a task-source mapping
summary. It must not run training, replay, PPO, environment rollout, private
holdout, promotion, actor-input changes, or self-ID claims.

## Guardrails

```text
training_started: false
replay_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1677-paper-route-controller-family-decisive-task-source-mapping-preflight
```
