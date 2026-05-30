# M1760 Single-Cell Seed-Repair Completion Design

- status: completed
- decision: `admit_seed_repair_completion_runner_implementation`
- no rollout: true
- training/replay/PPO: false

## Summary

M1760 designs a traceable completion protocol for the single M1756 missing row.
M1758 proved the exact seed is fragile rather than spec-infeasible, and M1759
synthesis admitted continuation. The repair must be explicit, deterministic,
and auditable.

This milestone does not run the missing episode and does not merge rows. It
admits a small runner/provenance implementation milestone before any completion
execution.

## Replacement Seed Rule

Use this deterministic rule:

```text
1. Start from the exact failed eval seed: 175761.
2. Consider only M1758 reset-only neighbor rows with reset_success == true.
3. Require sampled_obstacle_label == unavoidable.
4. Minimize abs(seed_offset).
5. If there is a tie, choose the lower eval seed.
```

Chosen replacement seed:

```text
original_eval_seed: 175761
replacement_eval_seed: 175760
replacement_seed_offset: -1
seed_repair_rule: nearest_successful_neighbor_tie_lower
seed_repair_source: m1758_single_sampling_failure_reset_only_probe
```

The tie candidate `175762` also succeeded, but `175760` is chosen by the
pre-registered lower-seed tie-break.

## Completion Protocol

M1761 should implement a completion runner that:

- reads M1756 completed `episode_rows.csv` and `failure_rows.csv`;
- verifies the only M1756 failure is
  `m1728-s4-02::L2_window_13_current_tiled` at seed `175761`;
- reconstructs the exact workload row from M1743 semantics metadata and M1734
  executable specs;
- runs only that one missing cell with replacement seed `175760`;
- writes a fresh output directory rather than mutating M1756 artifacts;
- writes augmented `episode_rows.csv` with seed-repair provenance columns on all
  rows;
- writes the original failed row as a diagnostic artifact;
- recomputes summary, outcome, profile, scenario-family, role, metric
  completeness, and guardrail aggregates from the completed `864` rows.

Required provenance columns:

```text
seed_repair_applied
seed_repair_source
seed_repair_rule
original_eval_seed
replacement_eval_seed
replacement_seed_offset
original_failure_error_type
original_failure_error_message
original_workload_id
```

For the copied M1756 rows, `seed_repair_applied=false` and the other provenance
fields should be empty. For the repaired row, `seed_repair_applied=true`.

## Completion Pass Gate

The later completion execution may pass only if:

- completed episode rows equal `864`;
- failure rows equal `0` in the completed output;
- exactly one row has `seed_repair_applied=true`;
- that row is the failed M1756 workload;
- `replacement_eval_seed == 175760`;
- M1743 semantics fields are preserved;
- metric completeness passes;
- selected metrics are finite under the existing rules;
- unsupported fault-like features remain explicitly uncovered;
- no actor input, reward, dynamics, termination, profile config, or scenario spec
  changes occur;
- no controller-family ranking, private-holdout, paper-level, or level3 self-ID
  claim is made.

## Rejected Alternatives

Do not silently drop the row. That would turn a known sampling failure into a
biased incomplete matrix.

Do not change scenario specs. M1758 showed the same spec/profile is feasible for
nearby seeds.

Do not rerun broad training or PPO. This is an execution-completion issue, not a
policy-learning issue.

Do not interpret the completed matrix before an audit. Completion only creates a
candidate complete public diagnostic artifact.

## Guardrails

- policy rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Admit M1761 seed-repair completion runner implementation. M1761 should add the
minimal provenance-aware completion helper and focused tests, but still should
not execute the missing policy episode. The execution should be a later
pre-registered milestone after the helper is validated.
