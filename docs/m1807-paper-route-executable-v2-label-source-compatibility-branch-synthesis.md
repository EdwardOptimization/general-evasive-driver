# M1807 Paper-Route Executable V2 Label-Source Compatibility Branch Synthesis

- status: completed
- decision: `continue_to_stable_source_materialization_design`
- workflow synthesis decision: `continue`
- synthesized range: `M1797-M1806`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Evidence Summary

M1797-M1806 completed the first executable v2 label-source compatibility repair
loop:

- M1797 designed the source-label compatibility repair: support statuses,
  quarantine artifacts, replacement needs, compatible subset, and claim
  boundary.
- M1798 implemented the no-reset compatibility helper with focused tests.
- M1799 fixed the exact no-reset project-artifact compatibility command and
  pre-registered counts.
- M1800 executed the compatibility preflight: `312` specs in, `272` compatible
  rows, `36` systematic stable violations, `4` sparse hidden-robust failures,
  zero unobserved rows, and zero guardrail violations.
- M1801 audited M1800 and chose stable source-label top-up before compatible
  subset reset rerun or measured execution.
- M1802 designed stable source-label top-up and candidate classes:
  `exact_existing_candidate`, `metadata_only_untrusted`,
  `near_existing_candidate`, and `new_materialization_required`.
- M1803 implemented the no-reset stable top-up planner with focused tests.
- M1804 fixed the exact no-reset project-artifact top-up command and expected
  counts.
- M1805 executed the top-up preflight: `3` stable targets, `36` missing
  profiles, `5` candidate rows, `0` direct replacements, and `3` new
  materialization needs.
- M1806 audited M1805 and routed to branch synthesis before the next narrow
  source-materialization repair.

The branch produced clean compatibility and top-up planning infrastructure. It
did not produce repaired reset feasibility or measured execution evidence.

## Supported Claims

Supported:

- metadata-only label assignment is insufficient for executable v2 role-surface
  rows;
- source-label support must be validated or quarantined before reset rerun and
  measured execution;
- M1800 cleanly separates compatible rows from systematic and sparse failures;
- the compatible subset is useful for later diagnostics but is not ranking
  evidence;
- the stable surface has three systematic source-label gaps totaling `36`
  missing profiles;
- the current M1771 stable source pool has no trusted direct replacement for
  those gaps;
- stable source materialization is the next technical repair direction.

The branch supports a methods claim about process discipline and task-quality
compatibility gating. It does not support controller-family ranking, repaired
panel feasibility, or paper-level benchmark conclusions.

## Falsified Claims

Falsified or blocked:

- executable v2 specs can be treated as reset-ready without source-label support
  validation;
- metadata-compatible sibling labels can replace observed unsupported labels;
- near candidates are direct replacements for exact stable source-label gaps;
- the `272` compatible subset is enough to proceed to controller-family ranking;
- M1805 top-up planning repairs the stable panel;
- M1797-M1806 provide level3 self-identification evidence.

The key falsified assumption is that existing stable source metadata contains a
trusted replacement for each missing stable label-source group. It does not.

## Failure Taxonomy Summary

Primary failure types:

- `scenario_sampling_failure`: M1794 exposed reset-time failures; M1800
  classifies `36` stable rows as systematic and `4` hidden-robust rows as
  sparse.
- `metric_artifact`: the role-surface metric contract was ahead of executable
  source-label support, so nominal metric labels did not imply sampler support.

Deferred:

- `seed_fragility`: the `4` sparse hidden-robust failures remain deferred until
  after the systematic stable source materialization route.

Not implicated:

- `contract_violation`: label leakage and actor-input guardrails remained clean.
- `training_instability`: no training ran.
- `proof_washout`: no policy update ran.
- `promotion_gate_failure`: no checkpoint promotion was attempted.

## Public Gate Overfit Risk

Risk remains high if the project keeps editing around the same public `312`
executable v2 rows. The next repair must avoid three failure modes:

- treating metadata-only candidates as executable replacements;
- selecting source seeds by profile-specific tuning;
- claiming measured execution or ranking from compatibility/top-up planning
  artifacts.

The next materialization design should therefore:

- pre-register candidate generation rules before creating source rows;
- preserve all `12` profile controls;
- keep labels out of actor inputs;
- materialize only source specs, not policy behavior;
- run reset-only support before any measured rollout;
- keep compatibility, reset feasibility, measured execution, and ranking as
  separate gate tiers.

## Next Branch Decision

Continue within the same branch after synthesis:

```text
paper_route_executable_v2_label_source_compatibility_repair
```

Immediate next milestone:

```text
m1808-executable-v2-stable-source-materialization-design
```

M1808 should design a no-reset source materialization repair for the three
stable targets:

```text
nominal / nominal / medium / center / aes_feasible
friction_step / nominal / late / center / aes_feasible
brake_variation / moderate / late / wide_offset / aeb_feasible
```

It should specify materialization fields, source provenance, profile-control
preservation, candidate naming, duplicate avoidance, no-label-leakage checks,
and the later reset-only validation route. It should not run reset, rollout,
measured execution, training, replay, PPO, private holdout, profile tuning, or
ranking.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
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

## Claim Boundary

Supported:

- branch synthesis and continue decision;
- source-label compatibility repair infrastructure is coherent;
- stable source materialization is the next technical repair direction;
- reset feasibility and ranking remain blocked until materialized sources pass
  reset-only validation.

Unsupported:

- repaired reset feasibility pass;
- stable source materialization result;
- measured execution;
- controller-family ranking;
- checkpoint promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
