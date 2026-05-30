# M1759 Paper-Route Task-Quality Scenario Taxonomy Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_single_cell_seed_repair_completion_design`
- synthesized range: `M1749-M1758`
- no rollout: true
- training/replay/PPO: false

## Evidence Summary

M1749-M1758 turned the revised scenario-taxonomy route from a design into an
almost-complete public diagnostic execution path:

- M1749 defined the revised execution requirements: preserve M1743 outcome
  semantics, separate metadata specs from executable specs, and add
  applicability-aware metric completeness.
- M1750 implemented that adapter layer and metric completeness reporting without
  changing actor inputs, reward, dynamics, termination, profiles, or training.
- M1751 audited the adapter as clean and admitted a measured execution design.
- M1752 fixed the revised execution protocol: M1743 metadata specs, M1734
  executable specs, M1743 workload, output directory, seed base, and no-ranking
  boundaries.
- M1753 ran the fixed protocol but failed as an execution-plumbing milestone:
  `504/864` completed rows, `360` failures, dominated by `359`
  `ControllerProfileObservationWrapper.config` `AttributeError` failures plus
  one reset-time sampling failure.
- M1755 repaired the wrapper config proxy with red/green tests and full-suite
  validation.
- M1756 reran the protocol after that repair and reached `863/864` rows:
  `AttributeError` count `0`, metric completeness passed on completed rows, and
  one reset-time sampling failure remained.
- M1758 probed that single failure without rollout. Exact seed `175761` still
  failed, but `95/100` neighboring seeds within radius `50` succeeded, all with
  sampled label `unavoidable`.

The branch has a coherent execution path now. The remaining blocker is not
adapter semantics, wrapper access, or scenario-spec infeasibility; it is a
single deterministic seed-fragility artifact in one mitigation-diagnostic cell.

## Supported Claims

Supported:

- the revised runner can preserve outcome semantics and metric-completeness
  outputs;
- the wrapper/evaluator config access bug is fixed;
- the revised scenario taxonomy protocol can execute almost the full `864`-cell
  public diagnostic matrix;
- the only observed remaining reset failure is seed-fragile but feasible under
  the same scenario/profile/spec combination;
- scenario-spec repair is not the next justified move.

These are infrastructure and public diagnostic execution claims only.

## Falsified Claims

Falsified or blocked:

- M1753 failures were not controller-family performance evidence;
- M1756 `863/864` partial rows are not complete ranking or paper-level evidence;
- the exact failed row should not be silently dropped;
- the M1758 failure is not evidence that `m1728-s4-02` is spec-filter
  infeasible;
- the branch does not yet support controller-family ranking, profile comparison,
  private-holdout claims, paper-level benchmark results, or level3
  self-identification evidence.

## Failure Taxonomy Summary

- `metric_artifact`: M1749-M1751 handled a metric-semantics risk where revised
  outcome metrics could exist but be uninterpretable without semantics
  pass-through and completeness checks.
- `scenario_sampling_failure`: M1753/M1756 exposed reset-time sampling failures
  under fixed public diagnostic seeds.
- `seed_fragility`: M1758 localized the remaining failure to exact seed
  `175761`; the same row is feasible for nearby seeds.

The prior wrapper issue is best understood as execution plumbing. It is repaired
and should not drive the next branch.

## Public-Gate Overfit Risk

Risk level: `moderate`.

The branch is still using a public diagnostic matrix, and the same fixed
workload has been inspected across multiple repair and rerun milestones. The
risk is manageable only if the next step treats the seed repair as explicit
execution-completion provenance, not as hidden tuning:

- record the failed seed and replacement seed in artifacts;
- use a deterministic nearest-successful-seed rule;
- preserve the original failed row as diagnostic evidence;
- do not rank controller families until a completed artifact is audited;
- do not treat the replacement as private-holdout evidence.

## Next Branch Decision

Continue within `paper_route_task_quality_scenario_taxonomy`.

Next step: M1760 single-cell seed-repair completion design.

The design should pre-register:

- the replacement-seed rule;
- the chosen replacement seed, with `175760` as the deterministic nearest
  lower-offset candidate unless the design justifies a different tie-break;
- how the one repaired row will be generated;
- how the repaired row will be merged with M1756 completed rows or rerun;
- required provenance fields for seed override;
- the audit gates that must pass before interpreting the completed matrix.

The next milestone must still block controller-family ranking, paper-level
claims, private-holdout claims, and level3 self-ID claims. The only allowed
claim after M1760 is that a seed-repair completion protocol has been designed.

## Guardrails

- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Admit M1760 single-cell seed-repair completion design. Do not execute, merge, or
rank anything until that design has pre-registered the replacement-seed rule and
provenance requirements.
