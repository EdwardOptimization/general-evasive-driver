# M2191 Paper-Route Current-Sim Offtrack-Support Repair Branch Synthesis

- status: completed
- decision: `current_sim_offtrack_support_repair_branch_synthesis_continue_to_candidate_artifact_audit`
- manifest: `experiments/manifests/m2191-paper-route-current-sim-offtrack-support-repair-branch-synthesis.json`
- synthesis window: `M2181-M2190`
- next manifest: `experiments/manifests/m2192-paper-route-current-sim-offtrack-support-candidate-artifact-audit.json`
- implementation in M2191: `false`
- reset in M2191: `false`
- measured execution in M2191: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2181/M2182 repaired and audited repeat metadata preservation in the measured
runner. That made training repeat IDs and seed metadata durable enough for a
repeat panel without changing the actor contract.

M2184 then ran the repeat measured execution cleanly:

```text
episodes: 640
failures: 0
profiles: 8
task families: 5
success: 100
collision: 36
offtrack: 504
metadata missing: 0
guardrail violations: 0
```

M2187 combined the original and repeat panels into a 960-episode no-rerun audit:

```text
combined_success_count: 163
combined_success_rate: 0.16979166666666667
combined_collision_count: 56
combined_offtrack_count: 741
combined_offtrack_rate: 0.771875
outcome_support_pass: false
comparison_ready: false
seed_diversity_status: suspicious_identical_repeat_outcome_vectors
```

M2188 classified the branch as not comparison-ready. The primary blocker is
task-quality/outcome support: the current task set is offtrack-dominated and
does not have enough successful support to compare controller families. The
secondary blocker is seed-diversity suspicion: repeat outcome vectors are
identical enough that they cannot be treated as independent paper evidence.

M2189 designed a bounded support-repair wave instead of ranking the current
data. M2190 implemented that no-rollout generator and produced:

```text
candidate_count: 288
offtrack_saturation_relief: 96
terminal_boundary_support_ladder: 64
older_history_ambiguity_support_ladder: 64
diagnostic_warmup_support_ladder: 32
positive_support_preservation: 32
public_debug: 176
public_gate: 112
duplicate_candidate_id_count: 0
boolean_guardrail_violation_count: 0
profile_specific_candidate_count: 0
actor_input_contract_change_count: 0
```

## Supported Claims

The branch now supports these limited claims:

```text
1. The current-sim measured runner can preserve repeat metadata.
2. A 3-repeat, 960-episode current-sim panel exists and is internally complete.
3. That panel is not comparison-ready because offtrack dominates outcomes.
4. The project has a deterministic 288-candidate no-rollout repair artifact.
5. The repair artifact is quota-balanced and does not change actor inputs.
```

These are workflow and task-quality claims. They are not controller-family
performance claims.

## Falsified Claims

The branch explicitly rejects these claims:

```text
1. The current 960-episode panel can rank L0/L1/L2/L3 controllers.
2. The repeat panel is paper-level evidence.
3. L2 finite-window vs L3 GRU has a verdict.
4. Online GRU has level3 self-identification evidence from this branch.
5. Offtrack-dominated current tasks are acceptable for a decisive comparison.
```

The paper-route plans remain binding: GRU/self-ID is a bounded hypothesis, and
a finite-window/current-response controller may still be the engineering winner
under fair evidence. This branch only improves task-quality readiness.

## Failure Taxonomy Summary

Primary failure class:

```text
scenario_sampling_failure
```

Reason: the measured panel completes, but task outcomes are too offtrack-heavy
to support the intended comparison.

Secondary data-quality warning:

```text
seed_diversity_suspicious_identical_repeat_outcome_vectors
```

This is not a controller failure. It means the next runnable panel must preserve
repeat metadata and then prove that repaired tasks produce useful outcome
support and non-degenerate repeat variation.

## Public-Gate Overfit Risk

Risk is `medium`.

M2190 candidates are derived from public measured artifacts, so they are valid
for repair and debugging but not for unbiased final paper claims. The next
steps must keep the split boundary:

```text
public_debug: repair/debug use
public_gate: gate use before measured execution
private/paper holdout: still unused
```

If the candidate panel is tuned repeatedly from the same public failures, the
project must synthesize or pivot again before claiming broader evidence.

## Actual Capability Change

The branch changed the project capability from:

```text
complete but offtrack-dominated current-sim panel
```

to:

```text
complete panel plus a deterministic support-repair candidate artifact
```

This is real infrastructure/data progress, but it does not yet change the paper
verdict. The next capability change must be executable repaired tasks that pass
reset validation and later measured execution with improved support.

## Next Branch Decision

Decision: `continue`.

The branch should continue to M2192 candidate artifact audit, then only if that
audit passes:

```text
M2192 candidate artifact audit
  -> candidate materialization design
  -> no-rollout materialization/preflight
  -> reset validation
  -> measured execution
  -> result audit before any controller-family comparison
```

Hard blocks remain:

```text
no controller ranking
no winner selection
no finite-window vs GRU verdict
no paper-level benchmark evidence
no level3 self-identification claim
```

Stop or pivot if the repaired candidates cannot create executable tasks with
better outcome support, or if repeat diversity remains suspicious after the
repaired measured execution.
