# M1929 Executable V2 Task-Quality Scenario Redesign Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- completed branch: `paper_route_task_quality_scenario_redesign`
- next branch: `paper_route_task_quality_reset_execution`
- decision: `task_quality_scenario_redesign_branch_synthesis_promote_to_reset_execution_branch`
- reset/rollout/measured execution in M1929: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1919-M1928 replaced the failed fixed-source repair-axis panel with a fresh,
balanced, executable scenario-quality pipeline.

The branch started from the M1917/M1918 blocker:

```text
joint_clearance_containment: 0 / 1536
clearance_only_offtrack: 1257 / 1536
containment_collision: 261 / 1536
collision_and_offtrack: 18 / 1536
near_miss_rows: 644 / 1536
```

That was a scenario/task-quality failure, not a controller-ranking result. The
branch response was to stop repairing the same fixed sources and build a new
five-tier source distribution.

Durable outputs:

```text
M1919: task-quality scenario redesign plan
M1920: source-mining schema
M1921: 640-row deterministic candidate template
M1923: source-mining execution, 399 supported sources, 44142 accepted cells
M1924: tier/split/role audit, all 640 rows joined, support across all tiers
M1925: 80-source non-holdout balanced subset design
M1926: 80-source subset artifact, 0 holdout, exact tier-role/surface balance
M1927: materialization command design, focused materializer required
M1928: 80 executable specs and 960 workload rows, contract/guardrail clean
```

The branch materially changed project capability:

```text
before:
  a fixed panel with zero joint outcomes and no clean path to ranking

after:
  a fresh public scenario source distribution,
  a balanced non-holdout 80-source subset,
  one representative accepted cell per source,
  no-rollout executable specs,
  960 controller-profile workload rows,
  and clean human-view contract checks
```

## Supported Claims

Supported scenario/task-quality claims:

- the redesigned source template can produce positive support;
- source support is not limited to one role or one tier;
- public debug and public gate splits both contain supported rows;
- holdout candidates exist but were not used for repair, selection, or ranking;
- a balanced public subset can be selected without holdout leakage;
- every tier-role cell has exactly four selected sources;
- every tier-role cell has two steady and two post-friction sources;
- every selected source can join to a representative accepted obstacle cell;
- the panel can be materialized into 80 executable specs and 960 workload rows;
- materialized specs pass human-view env contract checks;
- no forbidden-key, actor-input, ranking, paper, or level3 self-ID guardrail was tripped.

Supported workflow claim:

- the synthesis/local-search guard worked: it blocked a direct M1929 result
  audit and forced branch-level synthesis before further execution design.

## Falsified Or Unsupported Claims

Still unsupported:

- reset success;
- rollout success;
- measured controller performance;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- self-identification or history-necessity evidence;
- paper-level benchmark result;
- high-fidelity validation readiness.

Not falsified:

- scenario-quality route remains viable;
- current-sim benchmark construction remains viable;
- later controller comparison remains admissible after reset/materialized
  execution gates.

## Failure Taxonomy Summary

Branch-local technical failures:

```text
none after M1919 pivot
```

Process findings:

```text
M1917/M1918 failure type:
  scenario_task_quality_zero_joint_support

M1929 validator trigger:
  workflow_cadence_required_synthesis
```

The branch did include multiple design/implementation/audit steps, but they
changed evidence state: source support, selected panel, executable specs, and
workload rows. This was not a pure fixed-public-row repair loop.

## Public Gate Overfit Risk

Current overfit risk: `medium`.

Risk reducers:

- the branch mined a fresh 640-row source distribution instead of repairing the
  same 16-source panel;
- selected rows are source/role/tier/surface balanced;
- paper holdout candidates were not used;
- controller ranking remains blocked.

Remaining risks:

- selected rows are still public debug/gate rows, not paper holdout rows;
- no reset or rollout evidence exists yet;
- no controller family has been evaluated on the panel;
- the representative accepted-cell rule is deterministic and public, so it must
  be frozen before controller comparison.

The next branch may use these public rows for reset/materialized execution
debugging. It must not use paper holdout rows for repair or threshold tuning.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_task_quality_reset_execution
```

Reason:

```text
M1928 passed the executable materialization gate:
  executable_spec_count: 80
  selected_accepted_cell_count: 80
  workload_cell_count: 960
  profile_count: 12
  unmappable_source_count: 0
  contract_violation_count: 0
  forbidden_key_violation_count: 0
  guardrail_violation_count: 0
```

The project should now move from no-rollout executable materialization to
reset/materialized execution validation. The next branch must still be staged:
first design reset-only or reset-first execution, then implement, then audit,
then only later consider measured rollout and controller comparison.

## Guardrails For Next Branch

The next branch must preserve:

- no actor input changes;
- no hidden/oracle/slip/wheel/path/TTC/reference actor inputs;
- no private holdout use;
- no controller ranking before reset/materialized execution gates pass;
- no paper-level claim before multi-seed measured results and baselines exist;
- no level3 self-ID claim from scenario-quality infrastructure alone.

## Next

Next milestone:

```text
m1930-executable-v2-task-quality-reset-execution-design
```

M1930 should design the reset/materialized execution route over the M1928
executable specs. It should define exact commands, target counts, failure
taxonomy, and claim boundaries before any reset or rollout execution.
