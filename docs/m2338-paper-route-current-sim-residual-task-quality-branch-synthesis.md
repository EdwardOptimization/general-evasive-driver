# M2338 Paper-Route Current-Sim Residual Task-Quality Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_support_coverage_gap_source_mapping_design`
- manifest: `experiments/manifests/m2338-paper-route-current-sim-residual-task-quality-branch-synthesis.json`
- synthesis artifact: `docs/m2338-paper-route-current-sim-residual-task-quality-branch-synthesis.md`
- synthesis window: `M2320-M2337`
- reset/rollout/policy action in M2338: `false`
- measured execution in M2338: `false`
- training/replay/PPO in M2338: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2320-M2321 audited residual task-quality structure after the R0 safe-stop
semantics repair. The residual map became:

```text
input scenario specs: 72
input episodes: 1080
residual scenarios: 48
R0 residuals: 0
R1 residuals: 0
route labels:
  support_policy_coverage_candidate: 23
  scenario_or_support_redesign_candidate: 12
  mitigation_semantics_or_support_redesign_candidate: 12
  metric_semantics_audit_candidate: 1
guardrail_violation_count: 0
```

M2323-M2324 converted those residual rows into role-stratified task-quality
categories:

```text
role_stratified_residual_row_count: 48
R4 mitigation metric availability gap: 12
R2/R3/R5 coverage rows: 23
R2/R3/R5 redesign rows: 12
metric edge rows: 1
```

M2326-M2330 repaired the R4 metric export gap and reran the bounded R4-only
diagnostic panel:

```text
R4 scenario specs: 12
support policies: 3
seed repeats: 5
episodes: 180
failure_count: 0
required_r4_export_missing_field_count: 0
global success / collision / offtrack: 0 / 173 / 6
guardrail_violation_count: 0
```

M2332-M2333 then separated available R4 impact proxies from unavailable
post-collision continuation semantics:

```text
scenario_count: 12
impact_proxy_available_scenario_count: 12
post_collision_blocked_scenario_count: 12
ranking_admissible_count: 0
winner_selected_count: 0
```

M2335-M2336 rescored the full residual map after R0 and R4 semantics updates:

```text
rescored_residual_scenario_count: 48
support_policy_coverage_gap_count: 23
scenario_or_support_redesign_gap_count: 12
r4_proxy_semantics_post_collision_blocked_count: 12
metric_semantics_edge_count: 1
unclassified_residual_route_count: 0
guardrail_violation_count: 0
```

Role-level split:

```text
R2_handling_limit_drift_capable_avoidance:
  coverage gaps: 7
  redesign gaps: 5

R3_recovery_after_limit:
  coverage gaps: 8
  redesign gaps: 3
  metric edge rows: 1

R4_unavoidable_mitigation:
  post-collision blocked rows: 12

R5_hidden_dynamics_robustness:
  coverage gaps: 8
  redesign gaps: 4
```

## Supported Claims

M2338 supports these bounded claims:

- The residual task-quality branch produced a complete 48-row residual route
  map with zero unclassified rows.
- R0 and R1 are no longer residual blockers in this current-sim pack.
- R4 metric export is no longer missing: impact proxy fields are available for
  all 12 R4 scenarios.
- R4 is still not ranking-admissible because all 12 R4 scenarios remain
  post-collision blocked. Impact proxies do not establish mitigation
  performance.
- The largest remaining actionable bucket is the R2/R3/R5 support-policy
  coverage gap bucket:

```text
support-policy coverage gaps: 23
scenario/support redesign gaps: 12
R4 post-collision blocked: 12
metric edge rows: 1
```

## Falsified Claims

M2338 falsifies or blocks these claims:

- The current-sim scenario pack is ready for controller-family comparison.
- The R4 proxy fields are sufficient to rank mitigation performance.
- The 48 residual rows prove driver failure or self-identification failure.
- The residual support problem is solved.
- Another local metric-semantics audit is the highest-leverage next step.
- Training, replay, PPO, or support-policy/controller ranking should resume
  before the remaining task-quality route is selected.

This synthesis does not provide finite-window vs GRU, level3 self-ID, or
paper-level result evidence.

## Failure Taxonomy Summary

```text
metric_artifact:
  R0 safe-stop success and R4 field export were both metric/artifact issues.
  R0 is repaired. R4 field export is repaired, but R4 post-collision semantics
  remain outside the current-sim metric window.

scenario_sampling_failure:
  12 residual rows still look like scenario/support redesign gaps. These may
  be over-hard, poorly balanced, or under-specified current-sim tasks.

objective_overfit:
  Prior guarded repair/training was attempted before scenario task quality was
  sufficiently calibrated. The current branch prevents another training loop
  from interpreting unsupported residual rows as controller evidence.

support_policy_coverage_gap:
  23 rows across R2/R3/R5 remain mixed rather than clear. This is the largest
  immediate blocker because it prevents the pack from distinguishing between
  missing support coverage and impossible or poorly specified scenarios.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate and rising.

This branch has repeatedly analyzed the same 72-spec current-sim pack and the
same support-policy panel. The work was still useful because it removed two
real artifact blockers: R0 safe-stop semantics and R4 metric export. But
continuing to adjust labels, one role at a time, would become local search.

The next branch must therefore change the question from:

```text
Can another residual label be repaired?
```

to:

```text
Where do the 23 coverage gaps come from across role, hidden condition, timing,
lateral geometry, failure mode, and support-policy behavior?
```

If source mapping shows that gaps are concentrated in a small set of scenario
sources, the next route should be scenario/support redesign. If the gaps are
source-diverse and support-policy-specific, the next route should materialize
bounded support-policy coverage before controller comparison.

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. M2338 evaluates no driver checkpoint and runs no controller.

mechanism evidence for history dependence:
  no new support. No wrong-history, reset-hidden, zero-history, finite-window,
  current-response, or GRU comparison is run.

scenario/task-quality evidence:
  positive. The branch now has a clean residual route map and a role-stratified
  blocker split. Current-sim controller comparison remains blocked by task
  quality, not by a missing residual accounting artifact.

high-fidelity validation readiness:
  not ready. The current-sim verdict and controller set are not frozen, and R4
  post-collision continuation remains a current-sim semantic limitation.

workflow or complexity reduction:
  positive. M2338 stops the residual-semantics micro-loop and selects a broader
  source-mapping branch before more local repairs.
```

## Next Branch Decision

Decision:

```text
continue
```

New branch:

```text
paper_route_current_sim_support_coverage_gap_source_mapping
```

Next milestone:

```text
m2339-paper-route-current-sim-support-coverage-gap-source-mapping-design
```

M2339 should design an artifact-only source mapping over the 23
support-policy coverage gaps. It should not rerun the environment. The mapping
should group coverage gaps by:

```text
role family;
hidden condition or dynamics bucket;
obstacle timing bucket;
obstacle lateral offset bucket;
support policy;
dominant termination/failure mode;
whether support failures are source-diverse or source-concentrated;
whether each row looks like support-policy coverage materialization or
scenario/support redesign.
```

The purpose is to decide whether the next implementation should:

```text
materialize better support-policy coverage;
redesign or rebalance scenarios;
split a role-specific metric edge;
or stop and ask for user review before controller comparison.
```

## Blocked Routes

Blocked until the M2339 source mapping is designed and implemented:

```text
direct controller-family comparison;
support-policy ranking;
driver checkpoint promotion;
training or PPO repair;
finite-window vs GRU comparison;
level3 self-ID claim;
paper-level current-sim result;
high-fidelity validation target freeze.
```

R4 post-collision continuation remains tracked, but it is not the immediate
next route because the largest actionable current-sim blocker is the 23-row
R2/R3/R5 coverage-gap bucket.
