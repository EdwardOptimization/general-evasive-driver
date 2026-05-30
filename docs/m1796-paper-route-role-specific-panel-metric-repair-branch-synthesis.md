# M1796 Paper-Route Role-Specific Panel Metric Repair Branch Synthesis

- status: completed
- decision: `pivot_to_executable_v2_label_source_compatibility_repair`
- workflow synthesis decision: `pivot`
- synthesized range: `M1786-M1795`
- reset rerun: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Evidence Summary

M1786-M1795 completed the role-specific panel/metric repair branch through
reset-only feasibility:

- M1786 converted scorecard blockers into a v2 role-specific repair design:
  stable AES, drift-required recovery, split hidden-robust surfaces, and
  unavoidable mitigation.
- M1787 materialized the v2 repair contract: `6` role surfaces, `276` panel
  matrix rows, `12` preserved profile controls, and zero guardrail violations.
- M1788 audited the contract as coherent but not yet reset-ready.
- M1789 defined the executable v2 panel spec schema and M1771 reuse mapping.
- M1790 materialized `312` executable v2 specs across `6` role surfaces and
  `12` profiles, with zero label leakage, zero default ranking admission, and
  zero guardrail violations.
- M1791 audited M1790 and required a v2 reset adapter before any reset run.
- M1792 implemented the executable v2 reset-only adapter with focused tests and
  metadata preservation.
- M1793 fixed the exact full reset-only command and target counts.
- M1794 ran the full reset-only preflight: `312` attempted specs, `272`
  successes, `40` sampling failures, zero metadata join failures, and zero
  guardrail violations.
- M1795 localized the `40` failures: `36` are systematic stable source-label
  compatibility failures across three full profile blocks; `4` are sparse
  hidden-robust AES cells.

The branch succeeded as a role/metric repair and executable-spec infrastructure
branch. It did not produce a reset-feasible panel ready for measured execution.

## Supported Claims

Supported:

- the v2 role-specific metric contract fixes the earlier mixed-role
  interpretation problem at the schema level;
- the profile-control matrix remains intact for later L0/L1/L2/L3 comparisons;
- executable v2 specs can be generated with no actor-input label leakage, no
  default ranking admission, and no profile-specific tuning;
- the v2 reset adapter is a valid infrastructure component;
- reset feasibility is partially established (`272/312`) but incomplete;
- the dominant reset blocker is source-label compatibility, not adapter
  metadata loss.

The branch can support a methods claim about disciplined task-quality repair
and claim-boundary enforcement. It cannot yet support controller ranking or a
paper-level benchmark result.

## Falsified Claims

Falsified or blocked:

- `reset_ready_spec=true` in M1790 is sufficient to imply reset feasibility;
- reused M1771 source specs can be label-split without checking actual
  source-label support under inherited filters;
- the stable AES surface is executable as materialized;
- the v2 panel is ready for measured execution;
- M1794 can be interpreted as controller-family performance evidence;
- M1786-M1795 provide level3 self-identification evidence.

The key falsified assumption is that label balance can be created by assigning
new labels to reused sources. M1794/M1795 show that label balance must be backed
by source-label sampler feasibility.

## Failure Taxonomy Summary

Primary failure types:

- `scenario_sampling_failure`: M1794 has `40/312` reset-time sampling failures.
- `metric_artifact`: the executable v2 label split does not yet respect source
  feasibility, so the role-surface metric contract is not executable for all
  cells.

Secondary:

- `seed_fragility`: plausible for the four sparse hidden-robust AES failures,
  because their source/label families mostly reset successfully.

Not implicated:

- `contract_violation`: actor-input and label-leakage guardrails are clean.
- `training_instability`: no training ran.
- `proof_washout`: no policy update ran.
- `promotion_gate_failure`: no checkpoint promotion was attempted.

## Public Gate Overfit Risk

Risk is high if the next steps repeatedly tune seeds or filters against the
same public `312` cells. The correct repair unit is not a profile-specific
patch and not immediate measured execution. It is a source-label compatibility
contract that decides which source-label pairs are executable before they enter
the panel.

The next branch should therefore repair the materialization rules first:

- explicitly derive or validate source-label support;
- do not force unsupported sibling labels into a reused source spec;
- keep unsupported combinations as diagnostics, not executable rows;
- preserve all profile controls and no-label-leakage guardrails;
- only after systematic compatibility repair, handle sparse hidden-robust cells
  with a seed-fragility or tight-filter probe.

## Next Branch Decision

Pivot to a new branch:

```text
paper_route_executable_v2_label_source_compatibility_repair
```

Immediate next milestone:

```text
m1797-executable-v2-label-source-compatibility-repair-design
```

M1797 should design the compatibility repair without running reset. It should
define:

- source-label support fields;
- compatibility violation artifacts;
- deterministic source replacement rules for unsupported labels;
- treatment of sparse hidden-robust failures after systematic repair;
- preservation of all `12` profile controls;
- no actor-input, reward, dynamics, termination, or profile-tuning changes.

The branch should not proceed to measured execution until a later reset-only
preflight reaches complete feasibility or explicitly quarantines unsupported
cells as diagnostic-only non-ranking rows.

## Guardrails

- environment reset rerun: `false`
- environment rollout started: `false`
- policy action executed: `false`
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

- branch synthesis and pivot decision;
- task-quality infrastructure progress through M1795;
- reset feasibility is blocked by source-label compatibility.

Unsupported:

- reset feasibility pass;
- measured execution;
- controller-family ranking;
- checkpoint promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
