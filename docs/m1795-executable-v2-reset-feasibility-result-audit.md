# M1795 Executable V2 Reset-Feasibility Result Audit

- status: completed
- decision: `executable_v2_reset_failures_localized_route_to_branch_synthesis`
- source artifact: `runs/m1794_executable_v2_reset_feasibility_preflight/summary.json`
- reset rerun: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Evidence Summary

M1794 attempted all `312` executable v2 reset specs. It produced:

- reset successes: `272`
- sampling failures: `40`
- profile count: `12`
- role surface count: `6`
- reset-ready spec count: `312`
- metadata join incomplete count: `0`
- labels entering actor input: `0`
- ranking admissible by default: `0`
- guardrail violation count: `0`

All failures are the same reset-time sampling error:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

No policy action, rollout, replay, PPO, private holdout, actor-input change, or
ranking claim was involved.

## Failure Localization

By role surface:

| role surface | failures |
| --- | ---: |
| `stable_avoidance_aes` | 36 |
| `hidden_robust_aes_feasible` | 4 |

By task label:

| task label | failures |
| --- | ---: |
| `aes_feasible` | 28 |
| `aeb_feasible` | 12 |

By hidden-dynamics bucket:

| hidden bucket | failures |
| --- | ---: |
| `brake_variation` | 12 |
| `nominal` | 12 |
| `friction_step` | 12 |
| `brake_drive_variation` | 2 |
| `actuator_delay` | 1 |
| `mass_cg_shift` | 1 |

By source scenario spec:

| source spec | surface | label | hidden bucket | failures |
| --- | --- | --- | --- | ---: |
| `m1771-bp1-05` | `stable_avoidance_aes` | `aeb_feasible` | `brake_variation` | 12 |
| `m1771-bp1-00` | `stable_avoidance_aes` | `aes_feasible` | `nominal` | 12 |
| `m1771-bp1-02` | `stable_avoidance_aes` | `aes_feasible` | `friction_step` | 12 |
| `m1771-bp3-02` | `hidden_robust_aes_feasible` | `aes_feasible` | `brake_drive_variation` | 2 |
| `m1771-bp3-00` | `hidden_robust_aes_feasible` | `aes_feasible` | `actuator_delay` | 1 |
| `m1771-bp3-04` | `hidden_robust_aes_feasible` | `aes_feasible` | `mass_cg_shift` | 1 |

The three `stable_avoidance_aes` failures are full `12`-profile blocks. They are
not single-seed or single-profile artifacts:

- `m1771-bp1-00`: `aeb_feasible` succeeds for all `12`, `aes_feasible` fails for all `12`.
- `m1771-bp1-02`: `aeb_feasible` succeeds for all `12`, `aes_feasible` fails for all `12`.
- `m1771-bp1-05`: `aes_feasible` succeeds for all `12`, `aeb_feasible` fails for all `12`.

The `hidden_robust_aes_feasible` failures are sparse: the same source/label
families mostly reset successfully (`11/12`, `10/12`, and `11/12`). These look
like tight-filter or seed/profile-fragile cells, not a full source-label
incompatibility.

## Interpretation

M1794 did not expose an adapter metadata bug. The adapter preserved v2 metadata,
reported zero incomplete joins, and kept all guardrails clean.

The dominant issue is a source-label compatibility artifact introduced while
making the v2 panel executable. The v2 materialization split labels across
reused M1771 source specs, but some reused specs only support one label under
the inherited sampling filters. That is especially clear for the three stable
surface blocks, where each source has one label that resets and one label that
fails across every profile.

The smaller hidden-robust AES failures should not drive a broad spec redesign by
themselves. They should be handled after the systematic stable source-label
compatibility repair, using a seed-fragility or tight-filter audit if they
persist.

## Failure Taxonomy

Primary:

- `scenario_sampling_failure`: reset-time scenario sampling fails for `40/312`
  executable specs.
- `metric_artifact`: the v2 role-surface metric design is not yet executable
  for all inherited source-label combinations, so controller ranking remains
  blocked.

Secondary:

- `seed_fragility`: plausible only for the four sparse hidden-robust AES cells.
- `public_gate_overfit`: moderate to high if the project keeps repairing the
  same public panel rows without branch synthesis.

Not supported by the evidence:

- adapter schema failure;
- actor input contract violation;
- policy behavior regression;
- self-identification failure;
- controller-family ranking result.

## Next Route

Do not rerun reset immediately and do not start measured execution. The branch
has reached the `10`-milestone synthesis cadence (`M1786` through `M1795`), and
M1794/M1795 show that the repair branch needs a synthesis decision before
another narrow repair step.

Route to:

```text
m1796-paper-route-role-specific-panel-metric-repair-branch-synthesis
```

The synthesis should decide whether to pivot into a focused executable
label-source compatibility repair branch. A likely next branch is:

```text
paper_route_executable_v2_label_source_compatibility_repair
```

That branch should first repair systematic source-label incompatibilities, then
re-run reset-only feasibility, and only then revisit sparse hidden-robust seed
or filter failures.

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

- M1794 reset failures are localized.
- The dominant failure mode is source-label compatibility on stable v2 surfaces.
- Ranking, measured execution, and paper-level claims remain blocked.
- Branch synthesis is required before another narrow repair milestone.

Unsupported:

- executable v2 panel feasibility pass;
- measured controller performance;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
