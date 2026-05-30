# M1801 Executable V2 Label-Source Compatibility Result Audit

- status: completed
- decision: `compatibility_result_audit_route_to_stable_source_label_topup_design`
- source artifact: `runs/m1800_executable_v2_label_source_compatibility_preflight/summary.json`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Evidence Summary

M1800 successfully materialized source-label compatibility artifacts:

```text
input_spec_count: 312
input_reset_row_count: 312
compatible_spec_count: 272
compatibility_violation_count: 36
sparse_failure_count: 4
unobserved_count: 0
replacement_need_count: 6
profile_control_count: 12
role_surface_count: 6
guardrail_violation_count: 0
```

Support-status groups:

```text
supported_observed: 20
unsupported_systematic: 3
sparse_fragile: 3
```

The claim boundary is clean:

```text
compatible_reset_rerun_subset: admissible
measured_execution: not admissible
controller_family_ranking: not admissible
paper_level_result: not admissible
```

## Replacement Needs

Systematic stable source-label replacement needs:

| source | label | hidden | road | timing | lateral | missing profiles |
| --- | --- | --- | --- | --- | --- | ---: |
| `m1771-bp1-00` | `aes_feasible` | `nominal` | `nominal` | `medium` | `center` | 12 |
| `m1771-bp1-02` | `aes_feasible` | `friction_step` | `nominal` | `late` | `center` | 12 |
| `m1771-bp1-05` | `aeb_feasible` | `brake_variation` | `moderate` | `late` | `wide_offset` | 12 |

Sparse hidden-robust AES replacement/probe needs:

| source | hidden | road | timing | lateral | missing profiles |
| --- | --- | --- | --- | --- | ---: |
| `m1771-bp3-00` | `actuator_delay` | `moderate` | `medium` | `mixed` | 1 |
| `m1771-bp3-02` | `brake_drive_variation` | `moderate` | `late` | `mixed` | 2 |
| `m1771-bp3-04` | `mass_cg_shift` | `moderate` | `close` | `mixed` | 1 |

## Route Options

### Helper Repair

Rejected for now. M1800 matched all pre-registered counts, produced the expected
artifact set, preserved profile controls, and kept guardrails clean.

### Compatible-Subset Reset Rerun

Admissible but not highest leverage. A `272`-row subset reset rerun would verify
that already-compatible rows remain resettable, but it would not repair the
`stable_avoidance_aes` balance gap or make measured execution admissible.

### Sparse Hidden-Robust Seed Probe

Deferred. The sparse failures affect `4` rows across `3` groups. They should be
handled after the systematic stable source-label gap, otherwise the branch risks
optimizing small public cells before repairing the dominant panel defect.

### Stable Source-Label Top-Up

Chosen. The stable systematic failures remove `36` rows and cut
`stable_avoidance_aes` compatible coverage to `36` rows. This is the blocker
that prevents measured execution and ranking from becoming meaningful.

## Next Route

Route to:

```text
m1802-executable-v2-stable-source-label-topup-design
```

M1802 should design a no-reset top-up plan that:

- identifies candidate stable source specs for the three unsupported
  source-label groups;
- separates metadata-only label support from observed reset support;
- preserves all `12` profile controls;
- keeps actor inputs label-free;
- writes candidate, replacement, and claim-boundary artifacts;
- does not run reset or rollout.

A later milestone can implement and execute the top-up preflight, then run
reset-only feasibility over the repaired panel.

## Guardrails

- environment reset started: `false`
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

- M1800 compatibility artifact audit;
- compatible reset-rerun subset is admissible as a diagnostic path;
- measured execution and ranking remain blocked;
- stable source-label top-up is the next highest-leverage route.

Unsupported:

- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
