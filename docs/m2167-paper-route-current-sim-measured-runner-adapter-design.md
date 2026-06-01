# M2167 Paper-Route Current-Sim Measured Runner Adapter Design

- status: completed
- decision: `current_sim_measured_runner_adapter_design_admit_fake_rollout_implementation`
- parent audit: `docs/m2166-paper-route-current-sim-measured-readiness-inventory-result-audit.md`
- implementation in M2167: `false`
- rollout/measured execution in M2167: `false`
- policy actions executed in M2167: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Adapter Scope

M2167 designs a current-sim-specific measured runner adapter. The adapter exists
to preserve M2151 panel semantics and to fail closed until profile checkpoints
exist. It must not rank controller families or decide finite-window vs GRU.

The adapter should reuse low-level rollout utilities from existing measured
runners where possible, but its output schema must be current-sim-specific.

## Metadata Contract

Episode and failure rows must preserve these M2151 fields.

Spec-derived fields:

```text
task_source_id
benchmark_spec_id
task_family
claim_level_target
scenario_source
source_kind
source_reference
source_index
source_seed
eval_seed_override
materialization_semantics
paper_validity_status
generated_proxy_source
actor_input_contract
metric_gap_policy
source_family_template
capability_pair
reveal_step
```

Workload-derived fields:

```text
workload_id
profile_name
profile_level
profile_config_path
checkpoint_path
checkpoint_required_for_measured_execution
history_representation
history_window_steps
reset_or_truncated_control
environment_reset_scheduled
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

Measured outcome fields should include at least:

```text
eval_seed
success
collision
min_clearance_margin
return
steps
action_rate_mean
high_sideslip_fraction
termination_reason
outcome_bucket
reset_sampled_obstacle_label
environment_rollout_started
policy_action_executed
measured_rollout_started
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
winner_selected
```

## Validation Rules

The adapter must fail closed before real rollout if:

```text
checkpoint_required_for_measured_execution == true
and checkpoint_path is blank or missing on disk
```

Focused tests may use an injected `rollout_fn` so that metadata, aggregation,
resume behavior, failure rows, and claim boundaries can be verified without
loading checkpoints or executing real policy actions.

Real M2151 execution remains blocked until checkpoint/profile materialization
is audited.

## Aggregates

The adapter should write aggregate CSVs by:

```text
profile_name
profile_level
history_representation
task_family
source_family_template
capability_pair
outcome_bucket
termination_reason
```

These aggregates are descriptive only. They must not select a winner.

## Planned Implementation

M2168 should implement:

```text
src/autodrift/paper_route_current_sim_controlled_comparison_measured_runner.py
tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_measured_runner.py
```

Implementation constraints:

```text
no real M2151 measured execution;
no policy checkpoint training;
no profile ranking;
no paper-level evidence claim;
no finite-window vs GRU verdict;
no level3 self-ID claim.
```

## Planned Artifacts

The implementation milestone should write only code/test/docs artifacts, not a
real measured-execution run. It may use temporary test artifacts under pytest
tmp paths.

Later, after checkpoint materialization is complete, a separate command-design
milestone should freeze the real 320-episode command.

## Claim Boundary

Supported after M2168 if tests pass:

```text
the current-sim measured runner adapter preserves the panel metadata contract
and can execute fake-rollout tests without ranking claims.
```

Unsupported:

```text
real measured execution;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2168-paper-route-current-sim-measured-runner-adapter-implementation
```
