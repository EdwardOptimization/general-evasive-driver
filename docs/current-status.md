# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Current Research Blocker

Latest completed milestone:

```text
m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis
```

Latest attempted milestone:

```text
m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis
result: completed
```

Current next task:

```text
m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel
```

Current route:

```text
M2451 synthesized M2443-M2450 and made a branch decision:
`promote_to_next_branch`. The metric-selected validation branch is closed. Its
main result is negative but useful: the soft-boundary metric route is
executable, yet fresh metric-selected measured validation remains hard-offtrack
dominated with actual_success_rate `0.06685714285714285`,
hard_offtrack_failure_rate `0.7468571428571429`, and target consolidation
showing `21` hard-offtrack target rows plus `56` guardrail rows. The old
hard-termination-row soft-boundary relabel was falsified as a predictor of true
soft-boundary execution. The next branch is
`paper_route_current_sim_dual_axis_scenario_quality_discriminant`, starting with
M2452 artifact-only panel over M2445 episode rows and M2449 target/guardrail
rows. No rerun, policy action, repair, training, ranking, winner selection,
scenario redesign, paper/FW-vs-GRU/self-ID/training-repair verdict, or
current-sim verdict is supported.

M2448 accepted M2447 localization as actionable enough for artifact-only target
consolidation. That route has now been executed by M2449. M2447 localized the
M2445 hard-offtrack-dominated measured outcome from artifacts only: 65
localization rows over 5250 episodes with global actual_success_rate
`0.06685714285714285`, hard_offtrack_rate `0.7468571428571429`,
collision_rate `0.1761904761904762`, soft_offtrack_violation_rate
`0.0032380952380952383`, and diagnostic_pattern `hard_offtrack_dominated`.

M2446 accepted M2445 as a complete measured artifact but classified the fresh
soft-boundary execution as hard-offtrack dominated. The important correction is
that M2438 old-row relabel was diagnostic, not predictive: old hard-termination
rows stop at first boundary crossing, so relabeling them cannot prove the
closed-loop policy will recover or stay within the new 0.20 m tolerance once
termination is removed. M2445 is the fresh execution test and measured
actual_success_rate `0.06685714285714285`, hard_offtrack_failure_rate
`0.7468571428571429`, soft_offtrack_violation_rate
`0.0032380952380952383`, boundary_tolerated_success_rate `0.0`. The next task
is M2447 artifact-only outcome localization over M2445 rows before any repair,
training, scenario-quality route, ranking, winner selection, paper/FW-vs-GRU/
self-ID/training-repair verdict, or current-sim verdict claim.

M2445 executed the audited M2443 metric-selected workload as fresh closed-loop
measured validation under `soft_offtrack_metric_enabled=true` and
`soft_offtrack_tolerance_m=0.20`. It completed 5250/5250 episodes with
failure/validation/metadata/metric-completeness/actor-contract/guardrail counts
all 0. Raw measured rates: actual success `0.06685714285714285`, hard-offtrack
failure `0.7468571428571429`, soft-offtrack violation `0.0032380952380952383`,
and boundary-tolerated success `0.0`. Global aggregate is still offtrack-heavy:
collision rate `0.1761904761904762`, offtrack rate `0.7453333333333333`,
dominant_failure_mode `offtrack_dominated_failure`. This is a measured artifact,
not a verdict. The next task is M2446 result audit to classify the mismatch
between old diagnostic relabel soft success and fresh soft-boundary execution,
then choose a bounded route without rerun, repair, training, ranking, winner
selection, or paper/FW-vs-GRU/self-ID/training-repair verdict claims.

M2444 accepted M2443 as a complete metric-selected validation preflight and
routes to bounded full metric-selected measured-validation implementation.
Accepted evidence: 5250/5250 source cells, no duplicate or missing cells,
350/350 reset success, unchanged actor observation shape, 0 policy actions, and
0 guardrail violations. This audit still does not measure driving performance
or support actual-success, ranking, scenario redesign, paper/FW-vs-GRU/self-ID,
training-repair, or current-sim verdict claims. The next task is M2445, which
may execute the M2443 workload as fresh closed-loop data but must not repair,
train, rank, select winners, promote checkpoints, or claim a verdict before a
later result audit.

M2443 implemented and ran the metric-selected validation preflight for the M2413
denominator under soft-boundary config. It materialized 5250 workload cells from
350 reset targets x 15 selected checkpoints, verified source-cell coverage with
0 duplicate cells and 0 missing targets/checkpoints/cells, reset 350/350
soft-boundary env configs successfully, preserved actor observation shape, and
executed 0 policy actions. This is reset/config readiness evidence only: no
measured driving rollout, repair, training, ranking, actual-success claim,
scenario redesign execution, paper/FW-vs-GRU/self-ID claim, or current-sim
verdict is supported. The next task is M2444 preflight result audit before any
full metric-selected measured validation route.

M2442 synthesized M2437-M2441 after the local-search guard blocked another
ordinary audit. The synthesis decision is continue, but only to fresh
metric-selected validation preflight evidence. The branch now has hard/soft
metric semantics, a classifier panel, an audit, a measured-validation protocol,
and opt-in soft-boundary env support. Old-row soft success and env tests remain
separate from actual success. The next task is M2443 workload/reset preflight
for the M2413 denominator under soft-boundary config, with no policy rollout,
repair, training, ranking, or verdict claim.

M2441 implemented opt-in soft-boundary env support. Default offtrack termination
behavior is preserved, enabled mode continues inside tolerance and terminates
beyond tolerance, actor observation shape is unchanged, and focused tests passed
4/4. The change adds runtime diagnostics for soft_offtrack_violation,
soft_offtrack_step_count, soft_offtrack_duration_s, hard_offtrack_failure, and
metric_selected_termination_reason. This is infrastructure only: no measured
rollout, repair, training, ranking, scenario redesign execution, paper/
FW-vs-GRU/self-ID, or current-sim verdict claim is supported. The local-search
guard blocks another ordinary audit, so the next task is M2442 branch
synthesis.

M2440 designed the metric-selected measured-validation protocol. It selects
0.20 m as the primary soft-boundary tolerance with 0.02/0.05/0.10/0.20 m
sensitivity reporting, and uses the M2413 350 x 15 source-linked measured panel
as the primary fresh-validation denominator. The design found a prerequisite:
current env offtrack termination is hard-coded at abs(lateral_error) >
track_width, and track_width scaling would alter actor-visible road geometry.
The next task is M2441 opt-in soft-boundary env support implementation with
focused tests. No measured rollout, repair, training, ranking, paper/FW-vs-GRU/
self-ID, scenario-redesign execution, or current-sim verdict claim is supported
yet.

M2439 accepted M2438 as a complete hard/soft offtrack metric split
implementation and routes to metric-selected measured-validation design. The
metric split preserved measured actual_success, kept guardrail violations at 0,
and showed nonempty hard and soft offtrack classes. Old-row soft success remains
diagnostic-only, so the next task is M2440 protocol design for fresh measured
validation under the selected hard/soft metric. No rollout, repair, training,
ranking, scenario redesign execution, paper/FW-vs-GRU/self-ID, or current-sim
verdict claim is supported yet.

M2438 implemented the hard/soft offtrack metric split panel over existing M2362,
M2397, and M2413 episode rows. It produced 12 panel rows across 3 sources and
the fixed 0.02/0.05/0.10/0.20 m threshold grid, preserved measured
actual_success exactly, and produced guardrail_violation_count 0. At 0.20 m the
min diagnostic soft-success gain remains 0.7175925925925926, while max actual
success remains 0.06685714285714285. This supports a result audit route only:
soft success is diagnostic, not actual success, and no rollout, repair,
training, ranking, scenario redesign execution, paper/FW-vs-GRU/self-ID, or
current-sim verdict claim is supported yet. The next task is M2439 result audit.

M2437 completed the hard/soft offtrack metric split design after M2436 promoted
the route to task-boundary metric redesign. The contract separates actual
success, collision/obstacle-risk failure, hard offtrack failure, soft offtrack
violation, and boundary-tolerated diagnostics. It preserves that counterfactual
soft success is not actual success, uses a fixed diagnostic threshold grid
0.02/0.05/0.10/0.20 m, and routes to M2438 implementation over existing M2362,
M2397, and M2413 episode rows. No rollout, repair, training, ranking, scenario
redesign execution, paper/FW-vs-GRU/self-ID, or current-sim verdict claim is
supported yet.

M2391 materialized run-dir-only effective candidate pack artifacts by joining
M2385 overlay candidates to M2356 reset-valid repaired pack scenario specs.
M2394 implemented and ran the reset-only adapter for M2391 effective candidate
artifacts. All 2049 candidate-scenario references passed static validation, all
350 unique reset targets reset successfully, and all 54 effective candidates
passed candidate-level reset aggregation. No environment step or policy action
occurred. M2395 accepted this as reset-readiness evidence only and routed to a
bounded measured-validation design. M2396 froze the effective-candidate
measured-validation protocol: 2049 candidate-scenario references times 15
selected checkpoints, for 30735 closed-loop episodes. M2397 implemented and ran
that full panel with clean lineage and guardrails. M2398 accepted the artifact
as complete but classified the measured outcome as offtrack-dominated. The next
task is M2399 artifact-only outcome localization over M2397 rows, with no
rerun, repair, training, ranking, or paper/self-ID/current-sim verdict route.
M2399 materialized localization slices; M2400 must audit whether those slices
are actionable enough for consolidation or whether the branch should pivot,
synthesize, or stop. M2400 accepted localization as actionable but too broad for
direct repair, and routed to M2401 artifact-only actionable target
consolidation. M2401 consolidated those slices into compact repair-target and
guardrail tables while keeping candidate/profile/pack axes diagnostic-only. The
next task is M2402 result audit.
M2402 accepted M2401 consolidation, but because M2393-M2402 reached synthesis
cadence, the next task is M2403 branch synthesis before repair-plan
materialization.
M2403 synthesized M2393-M2402 and decided to continue only to artifact-only
bounded repair-plan materialization. It did not promote a driver result: the
offtrack-dominated blocker remains, and paper/current-sim/self-ID/FW-vs-GRU
claims are still blocked.
M2404 materialized that bounded repair plan: 1313 plan rows, including 203
offtrack repair-plan rows, 65 collision guardrail rows, 57 R4 mitigation rows,
and 1048 diagnostic monitoring rows. No repair/training/ranking/verdict action
occurred. The next task is M2405 result audit.
M2405 accepted M2404 completeness and guardrail separation, and routed to M2406
compact run-dir-only offtrack containment repair candidate materialization. This
still does not execute repair, overwrite active configs, train, rank, or make a
current-sim verdict.
M2406 materialized 4 compact run-dir-only candidate overlays and assigned all
203 offtrack repair-plan rows. Collision and R4 guardrail metadata were attached
to every candidate. No repair/training/ranking/verdict action occurred. The next
task is M2407 result audit.
M2407 accepted M2406 completeness, run-dir-only boundary, and guardrail metadata
as sufficient for read-only adapter validation. The next task is M2408 adapter
load validation, not measured rollout or repair execution.
M2408 read-only validated all 4 overlays and their guardrail/claim-boundary
metadata. It did not run measured rollout or reset the environment. The harness
blocked another ordinary audit after the non-evidence milestone limit, so the
next task is M2409 branch synthesis.
M2409 synthesized M2404-M2408 and closed the repair-plan materialization branch
with `promote_to_next_branch`. This is a workflow branch promotion, not a
checkpoint or driver-result promotion. The new branch is source-linked reset
evidence, because M2406 overlays are semantic repair families and not directly
executable env-config patches.
M2410 implemented that source-linked reset evidence panel. It joined the four
M2406 candidate families to M2391 reset-valid effective candidate specs,
produced 3505 source-linked scenario references, and reset all 350 unique env
configs successfully. All four families passed reset evidence. The result is
reset-only: no environment step, policy action, repair execution, training,
ranking, or current-sim verdict occurred. The next task is M2411 result audit,
including the 95 unmatched source-key diagnostic caveat.
M2411 accepted M2410 as clean reset-only source-linked evidence and routed to
M2412 measured-validation design. The next denominator should be 350 unique
reset targets times the selected checkpoint set, with overlapping family
membership treated as diagnostic slices rather than ranking. The 95 unmatched
source keys remain a required caveat.
M2412 froze that design: 350 unique reset targets x 15 selected checkpoints =
5250 measured episodes. M2413 should implement and run this measured panel,
writing one primary episode row per reset target/checkpoint and separate
exploded family-membership diagnostic rows. It must not execute repair, train,
rank families, select a winner, or make current-sim/paper/self-ID verdict
claims.
M2413 implemented and ran the bounded measured panel. It completed 5250/5250
episodes across 350 reset targets and 15 selected checkpoints, wrote 18300
family-membership diagnostic rows, and had zero failure, validation, metadata,
metric, contract, or guardrail failures. The measured outcome remains
offtrack-dominated: global role success rate 0.06685714285714285, collision
rate 0.1761904761904762, and offtrack rate 0.7424761904761905. M2414 must
audit this result and choose localization, consolidation, synthesis, stop, or
pivot without rerun, repair, training, ranking, or verdict claims.
M2414 accepted M2413 as a complete measured-validation artifact but kept the
driver blocker as offtrack-dominated. The audit routes to M2415 artifact-only
outcome localization over M2413 rows, with family/profile/controller axes kept
diagnostic-only and no rerun, repair, training, ranking, or verdict claims.
M2415 materialized that artifact-only localization: 2844 slice rows, including
272 offtrack targets, 114 collision guardrails, 49 R4 mitigation semantics,
325 max-step slices, 124 speed-too-low slices, and 2504 diagnostic-only slices.
It kept primary episode rows and overlapping family-membership rows separated.
M2416 accepted this localization as actionable but too broad for direct repair,
and routed to M2417 artifact-only target consolidation before any repair-
planning route.
M2417 consolidated M2415 slices into source-linked target and guardrail
artifacts: 59 offtrack repair-target rows, 30 collision guardrail rows, 43 R4
mitigation rows, 1 max-step noncompletion row, 1 speed-too-low row, 2733
diagnostic guardrail rows, and 110 family-membership diagnostic rows.
Family/profile repair-target counts, ranking, winner selection, guardrail
violations, repair execution, training, and verdict claims all remain zero. The
M2418 accepted M2417 as a complete target-consolidation artifact. Because the
source-linked branch has now produced reset evidence, measured validation,
outcome localization, target consolidation, and audits, M2418 routes to M2419
branch synthesis before any repair-plan materialization.
M2419 synthesized M2410-M2418 and decided to continue to bounded source-linked
repair-plan materialization. This is still a workflow route, not a driver
success, paper, finite-window-vs-GRU, self-ID, scenario-redesign, or current-sim
verdict. The next task is M2420 artifact-only repair-plan materialization from
M2417 target and guardrail rows.
M2420 materialized that bounded source-linked repair-plan artifact: 2844 plan
rows, with 59 offtrack repair-plan rows, 30 collision guardrails, 43 R4
mitigation rows, 1 max-step guardrail, 1 speed-too-low guardrail, 2733
diagnostic monitoring rows, and 110 family-membership diagnostics. Repair
execution, training, ranking, winner selection, guardrail violations, and
verdict claims remain zero. M2421 accepted M2420 as complete and routes to
M2422 run-dir-only source-linked repair-candidate materialization. The route is
still artifact-only: no repair execution, training, active config overwrite,
ranking, or verdict claim.
M2422 materialized four compact source-linked run-dir-only repair-candidate
overlays and assigned all 59 offtrack repair-plan rows. Every overlay carries
collision, R4, max-step, speed-too-low, diagnostic-monitoring, and
family-membership diagnostic metadata, for 24 guardrail metadata rows total.
Diagnostic and family rows remain monitoring-only and non-ranking. Active
config overwrite, repair execution, training, ranking, winner selection,
guardrail violations, and verdict claims remain zero. The next task is M2423
result audit: decide whether this candidate artifact admits read-only
reset/load validation adapter implementation, artifact repair, scenario-quality
pivot, or stop. It is not a repair execution or measured rollout route.
M2423 accepted M2422 as complete and adapter-validation-ready. This is still a
process decision only: it does not prove repair success or driver improvement.
The next task is M2424, a read-only source-linked candidate reset/load
validation adapter over the four overlay JSONs and 24 guardrail metadata rows.
M2424 must not execute repair, run measured rollout, train, rank candidates or
families, overwrite active configs, or make current-sim/paper/self-ID verdict
claims.
M2424 implemented and ran that read-only adapter. All four overlays loaded and
matched their table rows, all 24 guardrail metadata refs exist, diagnostic and
family metadata remained monitoring-only, and claim-boundary/outside-run-dir/
active-overwrite/ranking/guardrail failures are zero. No environment reset,
policy action, measured rollout, repair, training, ranking, or verdict claim
occurred. The next task is M2425 branch synthesis before another artifact-only
step.
M2425 synthesized M2420-M2424 and closed the source-linked repair-plan
materialization branch with `promote_to_next_branch`. This is a workflow branch
promotion, not a checkpoint or driver-result promotion. The branch produced four
run-dir-only source-linked repair-candidate overlays, complete 59/59 offtrack
assignment, 24 guardrail metadata rows, and 4/4 read-only overlay validation,
but no reset success, measured driver improvement, repair execution, training,
ranking, current-sim verdict, paper verdict, finite-window-vs-GRU result, or
level3 self-ID claim. The next task is M2426: build a source-linked
repair-candidate reset-only evidence panel by joining M2422 candidate source
keys to M2391 reset-valid effective scenario specs. M2426 must not execute an
environment step, policy action, repair, training, replay, PPO, ranking, winner
selection, active config overwrite, or verdict claim.
M2426 implemented and ran that reset-only evidence panel. The result is clean
fail-closed: 3/4 candidate families matched M2391 effective candidates, 2049
source-linked scenario refs materialized, 350 unique reset targets reset
successfully, static validation failures are zero, environment step count is
zero, policy action is false, and guardrail violations are zero. The blocker is
source coverage: c04 source-linked outcome-failure-surface containment has zero
matched effective candidates because the
`episode_rows:outcome_bucket:off_track_noncollision_noncompletion` key has no
M2391 source match. The next task
is M2427 result audit, which must decide source-coverage repair, matched-subset
measured-validation design with explicit c04 exclusion, scenario-quality
reassessment, synthesis, or stop. It must not rerun reset, run measured rollout,
execute repair, train, rank, or make current-sim/paper/self-ID verdict claims.
M2427 accepted M2426 as clean reset-only evidence for the matched 3-family
subset, but rejected all-four-family measured readiness because c04 has zero
matched effective candidates. The audit also verified that the M2426 350 reset
targets exactly equal the already measured M2413 reset-target set, with zero
missing keys in either direction. Therefore the next task is M2428 measured-
result reindex: join existing M2413 measured episode rows to M2426 c01/c02/c03
matched family memberships, explicitly exclude c04, and produce non-ranking
diagnostic aggregates without reset rerun, measured rollout rerun, repair,
training, ranking, winner selection, or verdict claims.
M2428 implemented that reindex. It reused 5250 existing M2413 measured episode
rows and produced 13050 matched-family membership rows for c01/c02/c03, with
exact reset-key coverage, c04 excluded, no reset rerun, no new measured rollout,
no repair/training/replay/PPO, no ranking, no winner, and zero guardrail
violations. The reindexed matched slices remain offtrack-dominated: c01
success/offtrack is 0.06689655172413793/0.7583908045977011, c02 is
0.06/0.8269047619047619, and c03 is 0.078/0.8162222222222222. The next task is
M2429 result audit, which must decide whether this should trigger branch
synthesis, c04 source-coverage repair, scenario-quality reassessment, bounded
next evidence, or stop. It must not rerun measured rollout, execute repair,
train, rank candidate families, or make current-sim/paper/self-ID verdict
claims.
M2429 accepted M2428 as a complete reindex artifact but classified the outcome
as negative for matched-subset task-quality improvement: c01/c02/c03 all remain
offtrack-dominated, and c04 remains excluded. The audit routes to M2430 branch
synthesis before any more local artifact repair, training, or measured rerun.
M2430 must decide whether to pursue scenario-quality reassessment, c04
source-coverage repair, bounded next evidence, high-fidelity/backend pivot, or
stop. It must not treat M2428 as driver improvement or candidate-family ranking.
M2430 synthesized M2425-M2429 and pivoted away from source-linked local repair
to a current-sim task-quality decision branch. This is not a driver or
checkpoint promotion. It is a route decision: the reset/reindex artifacts are
complete and guardrail-clean, but c01/c02/c03 remain offtrack-dominated and c04
is excluded. M2431 then implemented the task-quality decision panel from
existing measured artifacts only. The panel passed as an evidence artifact:
6/6 included measured panels are offtrack-dominated, success ranges from
0.04054010086220921 to 0.078, offtrack ranges from 0.7262962962962963 to
0.8425898812428827, c04 source coverage gap is preserved, and guardrail
violations are zero. The current next task is M2432 result audit, which must
decide task-semantics reassessment, source-coverage repair, high-fidelity/
backend preparation, synthesis/stop, or another bounded route without rollout,
repair, training, ranking, or verdict claims.
M2432 accepted M2431 and routed to event-level offtrack semantics instead of
another local repair step. M2433 implemented that panel over existing primary
episode rows from M2362, M2397, and M2413 only. It passed as a diagnostic
artifact: 3/3 primary panels are road-boundary dominated by the registered
positive-clearance low-overshoot criterion. The minimum positive-clearance
low-overshoot offtrack rate is 0.9841229193341869, the maximum is
0.9882130888640653, the minimum high-clearance offtrack rate is
0.895112016293279, and the maximum mean offtrack overshoot is
0.07326005531775727 m. This does not prove driver improvement or scenario
redesign success. The current next task is M2434 result audit: decide
offtrack-boundary task-semantics reassessment, metric/termination threshold
design, high-fidelity/backend preparation, synthesis/stop, or another bounded
route, without rollout, repair, training, ranking, or verdict claims.
M2434 accepted M2433 and routed to boundary-threshold sensitivity analysis.
M2435 implemented that panel from existing primary episode rows only, evaluating
0.02, 0.05, 0.10, and 0.20 m road-boundary tolerance. It passed as a
counterfactual metric-sensitivity artifact: at 0.20 m, the minimum soft-success
gain is 0.717, the minimum counterfactual soft-success rate is
0.7827777777777778, and the maximum counterfactual soft-success rate is
0.8752562225475842, while maximum actual success remains only
0.066. M2435 does not claim actual success improvement, scenario redesign,
driver progress, or current-sim verdict. The current next task is M2436 result
audit: decide task-boundary metric/termination redesign design, hard/soft
offtrack metric split, high-fidelity/backend preparation, synthesis/stop, or
another bounded route, without rollout, repair, training, ranking,
actual-success, or verdict claims.
M2436 synthesized the M2431-M2435 task-quality decision branch and promoted the
workflow to a new branch:
`paper_route_current_sim_dual_axis_task_boundary_metric_redesign`. The synthesis
keeps counterfactual soft success separate from actual rollout success. It does
not claim driver improvement, scenario redesign execution, current-sim verdict,
paper result, finite-window-vs-GRU result, or level3 self-identification. The
current next task is M2437: design a hard/soft offtrack metric and termination
split that defines hard offtrack failure, soft offtrack violation, collision-
risk failure, and actual success semantics before any implementation or
measured validation.
```

## Latest Evidence

M2362 produced the complete measured panel over the repaired five-pack family:

```text
episode_count: 5400
config_pack_count: 5
scenario_specs_per_pack_count: 72
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
global success_rate: 0.06518518518518518
global offtrack_rate: 0.7262962962962963
global collision_rate: 0.19962962962962963
dominant_failure_mode: offtrack_dominated_failure
```

M2390 schema repair design:

```text
decision: effective_candidate_pack_schema_repair_route_to_materialization
base env config lineage: M2356 repaired five-pack family
base reset validation: M2359 360/360 reset successes
base measured execution lineage: M2362 5400 episodes
candidate overlays: M2385 54 run-dir-only files
schema correction: overlay + base pack scenario selection, not one env_config per overlay
M2391 output target: effective_candidate_configs/*.json under run dir only
M2391 blocked: environment load/reset/step, policy action, repair execution,
  training/replay/PPO, ranking/winner, paper/FW-vs-GRU/level3 self-ID,
  scenario-redesign/training-repair/current-sim verdict claims
```

M2391 materialization result:

```text
result_class: current_sim_dual_axis_effective_config_schema_repair_materialization_pass
source_candidate_config_count: 54
static_validation_pass_count: 54
effective_candidate_config_written_count: 54
effective_candidate_config_outside_run_dir_count: 0
candidate_without_matching_scenarios_count: 0
candidate_without_env_config_count: 0
actor_contract_violation_count: 0
base_pack_count: 5
base_scenario_specs_per_pack_count: 72
selected_scenario_reference_count: 2049
min/max selected_scenario_count: 6/180
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_step_count: 0
guardrail_violation_count: 0
```

M2392 synthesis decision:

```text
synthesis window: M2387-M2391
synthesis_decision: continue
decision: continue_to_effective_candidate_reset_validation_adapter_design
actual capability changed: effective candidate pack artifact generation
still blocked: reset compatibility, rollout/measured execution, repair
  execution, training, ranking, paper/FW-vs-GRU/level3 self-ID/current-sim
  verdict claims
next task: M2393 reset-validation adapter design
```

M2393 adapter design:

```text
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
duplicate policy: deduplicate by pack_id + scenario_spec_id
future M2394 reset scope: reset-only, no environment step and no policy action
future pass target: 350/350 reset successes and 54/54 candidate reset passes
still blocked: rollout/measured execution, repair execution, training, ranking,
  paper/FW-vs-GRU/level3 self-ID/current-sim verdict claims
```

M2394 reset-validation adapter result:

```text
result_class: current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass
source_candidate_config_count: 54
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
static_validation_pass_count: 2049
static_validation_failure_count: 0
environment_load_attempt_count: 350
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
candidate_reset_pass_count: 54
candidate_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
guardrail_violation_count: 0
```

M2395 reset-validation adapter result audit:

```text
decision: effective_candidate_reset_validation_result_accepted_route_to_measured_validation_design
accepted evidence: M2394 reset-readiness only
observed failure types: none
reset rerun/rollout/policy action/repair/training/ranking: false
blocked claims: measured performance, repair success, paper verdict,
  finite-window-vs-GRU, level3 self-ID, scenario redesign executed,
  current-sim verdict
next task: M2396 measured-validation design
```

M2396 effective-candidate measured-validation design:

```text
decision: effective_candidate_measured_validation_design_admit_implementation
effective candidates: 54
candidate-scenario references: 2049
unique reset targets: 350
selected checkpoints: 15
target measured episodes: 30735
denominator: candidate_id + pack_id + scenario_spec_id + selected checkpoint
reset/rollout/policy action in M2396: false/false/false
blocked claims: ranking, paper verdict, finite-window-vs-GRU, level3 self-ID,
  scenario redesign executed, training repair success, current-sim verdict
next task: M2397 measured-validation implementation
```

M2397 effective-candidate measured-validation implementation:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_validation_pass
episode_count: 30735
target_episode_count: 30735
source_candidate_count: 54
candidate_scenario_reference_count: 2049
unique_pack_scenario_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
global success_rate: 0.04054010086220921
global offtrack_rate: 0.8425898812428827
global collision_rate: 0.10157800553115341
dominant_failure_mode: offtrack_dominated_failure
ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: false
next task: M2398 measured-validation result audit
```

M2398 effective-candidate measured-validation result audit:

```text
decision: effective_candidate_measured_validation_complete_offtrack_dominated_route_to_outcome_localization
accepted artifact: M2397 complete 30735/30735 episodes
failure/validation/metadata/metric/contract/guardrail counts: 0/0/0/0/0/0
outcome_quality: offtrack_dominated_failure
global success_rate: 0.04054010086220921
global offtrack_rate: 0.8425898812428827
global collision_rate: 0.10157800553115341
metric_artifact/lineage_invalid/contract_violation: not observed
ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: false
next task: M2399 artifact-only measured outcome localization implementation
```

M2399 effective-candidate measured outcome localization:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass
source_episode_count: 30735
source_candidate_count: 54
source_profile_count: 5
source_role_family_count: 6
slice_row_count: 1313
offtrack_target_slice_count: 1132
collision_guardrail_slice_count: 364
r4_mitigation_semantics_slice_count: 57
diagnostic_only_slice_count: 96
high_priority_offtrack_slice_count: 658
route_class_counts: offtrack_target 796, offtrack_target_with_collision_guardrail 336, collision_guardrail 28, r4_mitigation_semantics 57, diagnostic_only 96
ranking_admissible_count/winner_selected_count/guardrail_violation_count: 0/0/0
top localized blockers: centerline offtrack, drift_required offtrack+collision, early_far offtrack, guarded_offtrack_containment_repair offtrack+collision, R4 collision semantics
next task: M2400 localization result audit
```

M2400 effective-candidate measured outcome localization result audit:

```text
decision: effective_candidate_measured_outcome_localization_accepted_route_to_actionable_target_consolidation
accepted M2399 localization: source episodes 30735, slice rows 1313
offtrack/collision/R4/diagnostic/high-priority-offtrack counts: 1132/364/57/96/658
route_class_counts: offtrack_target 796, offtrack_target_with_collision_guardrail 336, collision_guardrail 28, r4_mitigation_semantics 57, diagnostic_only 96
classification: actionable enough to continue but too broad for direct repair
blocked: raw slice ranking, candidate/profile ranking, direct repair, paper/current-sim/self-ID verdict
next task: M2401 artifact-only actionable target consolidation implementation
```

M2401 effective-candidate actionable target consolidation:

```text
result_class: current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass
source_slice_row_count: 1313
consolidated_row_count: 1313
offtrack_repair_target_row_count: 203
collision_guardrail_row_count: 65
r4_mitigation_semantics_row_count: 57
diagnostic_guardrail_row_count: 1034
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count/winner_selected_count/guardrail_violation_count: 0/0/0
top repair targets: centerline, early_far, priority_offtrack_containment_repair, mid timing, slow_steer_actuator
top collision guardrails: R5 right_offset/late_close, R2 right_offset, guarded weak_brake, guarded same_scene_balanced_panel
next task: M2402 actionable target consolidation result audit
```

M2402 effective-candidate actionable target consolidation result audit:

```text
decision: effective_candidate_actionable_target_consolidation_accepted_route_to_branch_synthesis
accepted M2401 consolidation: source/consolidated rows 1313/1313
offtrack/collision/R4/diagnostic counts: 203/65/57/1034
diagnostic-axis repair target/R4 ordinary repair target/ranking/winner/guardrail counts: 0/0/0/0/0
classification: targets are meaningful but require branch synthesis before repair planning
synthesis cadence: M2393-M2402 reached 10 milestones since M2392 synthesis
next task: M2403 effective-candidate measured-validation branch synthesis
```

M2403 effective-candidate measured-validation branch synthesis:

```text
synthesis decision: continue
route decision: continue_to_bounded_repair_plan_materialization
branch evidence: M2394 reset pass 350/350; M2397 measured panel 30735/30735;
  M2399 localization 1313 slices; M2401 consolidation 203 offtrack targets,
  65 collision guardrails, 57 R4 semantics rows, 1034 diagnostics
driver outcome: still offtrack-dominated, not a positive current-sim result
supported: bounded target/guardrail categories are ready for repair-plan materialization
blocked: ranking, paper/current-sim verdict, FW-vs-GRU conclusion, level3 self-ID,
  scenario-redesign/training-repair success
next task: M2404 artifact-only bounded repair-plan materialization
```

M2404 bounded repair-plan materialization:

```text
result_class: current_sim_dual_axis_bounded_repair_plan_materialization_pass
repair-plan rows total/offtrack/collision/R4/diagnostic: 1313/203/65/57/1048
plan route counts: collision_guardrail_constraint 5; diagnostic_monitoring_only 1048;
  offtrack_repair_plan 143; offtrack_repair_plan_with_collision_guardrail 60;
  r4_mitigation_semantics_guardrail 57
diagnostic-axis repair/R4 ordinary repair/collision-as-plain-repair: 0/0/0
repair execution/training/ranking/winner/guardrail: 0/0/0/0/0
next task: M2405 bounded repair-plan materialization result audit
```

M2405 bounded repair-plan materialization result audit:

```text
decision: bounded_repair_plan_materialization_accepted_route_to_offtrack_containment_candidate_materialization
accepted plan rows total/offtrack/collision/R4/diagnostic: 1313/203/65/57/1048
guardrail separation failures diagnostic-axis/R4/collision-as-plain: 0/0/0
execution/training/ranking/winner/guardrail counts: 0/0/0/0/0
next task: M2406 compact run-dir-only offtrack containment repair candidate materialization
```

M2406 offtrack containment repair candidate materialization:

```text
result_class: current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass
assigned offtrack repair-plan rows: 203/203
candidate overlays written/outside run dir: 4/0
candidate families: geometry_timing, hidden_dynamics_response, general_boundary,
  role_conditioned
collision/R4/diagnostic source rows: 65/57/1048
guardrail metadata rows: 8
active overwrite/repair/training/ranking/winner/guardrail: 0/0/0/0/0/0
next task: M2407 candidate materialization result audit
```

M2407 offtrack containment repair candidate materialization result audit:

```text
decision: offtrack_containment_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter
accepted candidates count/written/outside-run-dir: 4/4/0
assigned rows: 203/203
guardrail metadata rows/missing: 8/0
collision/R4 source rows: 65/57
active overwrite/repair/training/ranking/winner/guardrail: 0/0/0/0/0/0
next task: M2408 read-only candidate reset/load validation adapter
```

M2408 offtrack containment candidate reset/load validation adapter:

```text
result_class: current_sim_dual_axis_offtrack_containment_candidate_reset_load_validation_adapter_pass
candidate/overlay load pass: 4/4
schema/table/source-key/outside-run-dir failures: 0/0/0/0
guardrail metadata/claim boundary failures: 0/0
missing collision/R4 guardrails: 0/0
active overwrite/repair/training/ranking/winner/contract/oracle/guardrail: 0/0/0/0/0/0/0/0
next task: M2409 repair-plan materialization branch synthesis
```

M2363 audited M2362 and blocked raw ranking or paper interpretation:

```text
primary offtrack target roles: R0, R2, R3, R5
separate mitigation semantics role: R4_unavoidable_mitigation
profile aggregates: diagnostic only
pack aggregates: diagnostic only
winner selected: false
finite-window vs GRU conclusion: false
level3 self-ID claim: false
```

M2364 designed artifact-only localization. M2365 implemented and ran it:

```text
result_class: current_sim_dual_axis_measured_outcome_localization_pass
source_episode_count: 5400
slice_row_count: 313
offtrack_target_slice_count: 198
collision_guardrail_slice_count: 95
r4_mitigation_semantics_slice_count: 48
high_priority_offtrack_slice_count: 99
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

M2365 route classes:

```text
offtrack_target: 118
offtrack_target_with_collision_guardrail: 80
collision_guardrail: 15
r4_mitigation_semantics: 48
diagnostic_only: 52
```

M2366 audit decision:

```text
M2365 localization accepted: true
next route: actionable target consolidation design
diagnostic-only/guardrail-heavy axes: global, pack_id, profile_name, sampling_repair_class
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  timing bucket, lateral bucket, hidden dynamics bucket, and role-conditioned
  timing/lateral/hidden axes
R4 mitigation semantics: separate route, not ordinary offtrack repair
```

M2367 design decision:

```text
diagnostic-only axes: global, pack_id, profile_name, sampling_repair_class,
  pack/profile composites
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  hidden dynamics, timing, lateral, and role-conditioned hidden/timing/lateral
ordinary repair target excludes: diagnostic axes and R4 semantics rows
M2368 command: artifact-only consolidation, no reset/rollout/training/ranking
```

M2368 result:

```text
source_slice_row_count: 313
consolidated_row_count: 313
offtrack_repair_target_row_count: 54
collision_guardrail_row_count: 28
r4_mitigation_semantics_row_count: 48
diagnostic_guardrail_row_count: 190
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
guardrail_violation_count: 0
```

M2369 audit decision:

```text
M2368 consolidation accepted: true
next route: bounded offtrack guardrail repair design
ordinary offtrack repair targets: 54
collision guardrail rows: 28
R4 mitigation semantics rows: 48
diagnostic guardrail rows: 190
direct training/repair-success claim: blocked
```

M2370 design decision:

```text
repair families: priority offtrack, ordinary offtrack, guarded offtrack,
  collision guardrail, R4 mitigation semantics guardrail, diagnostic guardrail
allowed repair levers are names only; none are executed in M2370/M2371
blocked: actor input change, oracle features, profile-specific tuning,
  winner selection, R4 ordinary repair, collision-blind offtrack objective,
  scenario-redesign-executed claim, training-repair-success claim
```

M2371 result:

```text
repair_spec_row_count: 320
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
profile_or_pack_repair_spec_count: 0
r4_ordinary_repair_spec_count: 0
collision_blind_mixed_repair_spec_count: 0
guardrail_violation_count: 0
```

M2372 audit decision:

```text
M2371 repair specs accepted: true
next route: bounded offtrack guardrail repair implementation design
ordinary offtrack specs: 36
mixed guarded offtrack specs: 18
collision guardrail specs: 28
R4 mitigation semantics guardrail specs: 48
diagnostic no-ranking guardrail specs: 190
profile/pack ordinary repair specs: 0
R4 ordinary repair specs: 0
collision-blind mixed repair specs: 0
repair execution/training/replay/PPO: false
```

M2373 implementation design decision:

```text
implementation route: artifact-only repair plan materialization
future outputs: repair plan, reward deltas, curriculum weights, guardrail constraints
ordinary offtrack direct repair specs: 36
mixed guarded specs requiring collision constraints: 18
guardrail-only specs: 28 collision, 48 R4, 190 diagnostic
active config overwrite: blocked
actor input change/oracle feature/profile-specific tuning: blocked
repair execution/training/replay/PPO: false
next route: outcome-localization branch synthesis
```

M2374 branch synthesis decision:

```text
synthesis decision: continue
next branch: paper_route_current_sim_dual_axis_repair_plan_materialization
next route: artifact-only repair-plan materialization
supported: task-quality artifacts are clean enough for repair-plan artifacts
blocked: repair success, scenario redesign executed, ranking, current-sim verdict,
  finite-window-vs-GRU, level3 self-ID
```

M2375 repair-plan materialization result:

```text
input_repair_spec_row_count: 320
ordinary/mixed/collision/R4/diagnostic source counts: 36/18/28/48/190
reward_delta_row_count: 54
curriculum_weight_row_count: 54
guardrail_constraint_row_count: 284
mixed_guarded_constraint_row_count: 18
profile_specific_tuning_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
collision_blind_mixed_repair_count: 0
r4_ordinary_repair_count: 0
guardrail_violation_count: 0
repair execution/training/replay/PPO: false
```

M2376 audit decision:

```text
M2375 repair-plan artifacts accepted: true
next route: bounded static config-patch application design
reward/curriculum rows: 54/54
guardrail/mixed guarded constraints: 284/18
exclusions and guardrail violations: 0
active config overwrite/repair execution/training: blocked
```

M2377 application design decision:

```text
design: overlay-only config-patch materializer
expected reward/curriculum/guardrail patch rows: 162/54/284
active config overwrite: blocked
actor input change/oracle feature/profile-specific tuning: blocked
repair execution/training/replay/PPO: false
next route: artifact-only config-patch materialization
```

M2378 config-patch materialization result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass
source reward/curriculum/guardrail/mixed rows: 54/54/284/18
reward_config_patch_row_count: 162
curriculum_config_patch_row_count: 54
guardrail_config_patch_row_count: 284
target namespaces: candidate_reward_overlay 162, candidate_curriculum_overlay 54,
  candidate_guardrail_overlay 284
guardrail targets: collision 46, R4 semantics 48, no-ranking 190
active_config_overwrite_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
profile_specific_tuning_count: 0
repair_execution_count/training_count/ranking_admissible_count/winner_selected_count: 0/0/0/0
guardrail_violation_count: 0
```

M2379 audit decision:

```text
M2378 config-patch artifacts accepted: true
next route: repair-plan materialization branch synthesis before application design
reward/curriculum/guardrail patch rows: 162/54/284
target namespaces: candidate overlay namespaces only
active config overwrite/repair execution/training/ranking: blocked
current-sim verdict/paper/self-ID claims: blocked
```

M2380 branch synthesis decision:

```text
synthesis window: M2375-M2379
synthesis decision: continue
next route: bounded candidate config-patch application design
actual capability changed: artifact capability only
driver behavior/training/validation changed: false
public gate overfit risk: moderate
local-search guard: triggered correctly and reset by synthesis
paper/self-ID/current-sim verdict claims: blocked
```

M2381 application design decision:

```text
design: artifact-only application-plan materializer
candidate_application_spec_count expected: 54
reward/curriculum/guardrail patch references expected: 162/54/284
mixed_guarded_candidate_requirement_count expected: 18
active config overwrite/config patch application/candidate config generation: blocked
reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2382 application-plan materialization result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass
candidate_application_spec_count: 54
candidate repair families: priority 26, ordinary 10, guarded mixed 18
reward/curriculum/guardrail patch references: 162/54/284
mixed_guarded_candidate_requirement_count: 18
candidate_without_reward/curriculum/guardrail counts: 0/0/0
active_config_overwrite_count/config_patch_applied_count/candidate_config_file_written_count: 0/0/0
guardrail_violation_count: 0
```

M2383 audit decision:

```text
M2382 application-plan artifacts accepted: true
next route: bounded candidate config generation design
candidate_application_spec_count: 54
reward/curriculum/guardrail patch references: 162/54/284
active config overwrite/config patch application/candidate config generation: blocked
reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2384 candidate config generation design:

```text
design: run-dir-only candidate config generation materializer
candidate_config_file_written_count expected in M2385: 54
candidate_config_files_outside_run_dir_count expected: 0
source reward/curriculum/guardrail references expected: 162/54/284
mixed_guarded_candidate_requirement_count expected: 18
active config overwrite/reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
next after M2385: branch synthesis, not another narrow audit
```

M2385 candidate config generation result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass
source_candidate_application_spec_count: 54
candidate_config_file_written_count: 54
candidate_config_files_outside_run_dir_count: 0
source reward/curriculum/guardrail references: 162/54/284
mixed_guarded_candidate_requirement_count: 18
candidate_without_reward/curriculum/guardrail counts: 0/0/0
candidate repair families: priority 26, ordinary 10, guarded mixed 18
active_config_overwrite_count: 0
active_config_patch_application_count: 0
loaded_into_environment_count: 0
environment_reset_count: 0
guardrail_violation_count: 0
repair/training/replay/PPO/ranking/winner claims: false
paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim claims: false
next: M2386 branch synthesis
```

M2386 branch synthesis decision:

```text
synthesis window: M2381-M2385
synthesis decision: continue
next route: bounded candidate config safety/reset-validation design
actual capability changed: artifact capability only
driver behavior/training/validation changed: false
public gate overfit risk: moderate
local-search guard: triggered correctly and reset by synthesis
paper/self-ID/current-sim verdict claims: blocked
```

M2387 safety validation design:

```text
design: static safety checks plus future reset-only validation
source candidate configs: 54
target static_validation_pass_count in M2388: 54
target effective_config_written_count in M2388: 54 if schema permits
target environment_reset_attempt_count in M2388: 54 if static checks pass
environment_step_count target: 0
active_config_overwrite target: 0
policy action/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2388 reset validation implementation result:

```text
result_class: current_sim_dual_axis_candidate_config_reset_validation_fail
source_candidate_config_count: 54
static_validation_pass_count: 54
static_validation_failure_count: 0
schema_incomplete_candidate_count: 54
effective_config_written_count: 0
effective_config_outside_run_dir_count: 0
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_reset_success_count: 0
environment_step_count: 0
active_config_overwrite_count: 0
guardrail_violation_count: 0
failure_types_observed: effective_config_materialization_failure
```

M2389 result audit decision:

```text
decision: schema_incomplete_reset_validation_failure_route_to_effective_config_schema_repair_design
schema incompleteness vs sampler incompatibility: schema incompleteness
reset compatibility demonstrated: false
unsafe execution observed: false
next route: bounded effective-config schema repair design
```

## Current Interpretation Boundary

Allowed claim:

```text
Run-dir-only candidate config artifacts have been generated from audited
application-plan artifacts without active config overwrite or execution.
```

Blocked claims:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Immediate Next Step

M2390 should design effective-config schema repair from:

```text
docs/m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit.md
runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_rows.csv
```

The design must identify legitimate base env config lineage, define candidate
overlay merge semantics, and specify run-dir-only effective config artifacts.
It must fail closed if no base lineage is defensible. It must not materialize
effective configs, reset, execute repair, train, replay, use PPO, rank profiles
or packs, select a winner, claim scenario redesign executed, claim repair
success, current-sim verdict, or paper/self-ID claims.
