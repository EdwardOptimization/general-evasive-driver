# M1735 Paper-Route Task-Quality Scenario Taxonomy Sampling Repair Preflight Result Audit

- status: completed
- decision: `sampling_repair_preflight_audit_admit_repaired_execution_design`
- audited preflight: `docs/m1734-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight.md`
- audited summary: `runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/summary.json`

## Summary

M1735 audits M1734 as a clean reset-only sampling-feasibility repair. The M1734
artifacts repair the M1731 reset-time failure mode without mutating M1728 in
place and without changing the actor contract, controller profiles, checkpoint
lineage, reward, training, replay, or PPO.

No policy rollout, training, replay, PPO, checkpoint promotion, private holdout,
actor input change, profile tuning, controller-family ranking, paper-level
claim, or level3 self-identification claim occurred in this audit.

## Pass/Fail Audit

M1734 passed the pre-registered reset-stress preflight:

| field | observed | required |
| --- | ---: | ---: |
| repaired specs | `72` | `72` |
| repaired matrix cells | `864` | `864` |
| profiles | `12` | `12` |
| reset-stress rows | `864` | `864` |
| reset successes | `864` | `864` |
| sampling failures | `0` | `0` |
| contract violations | `0` | `0` |
| unsupported features | `5` | `5` |
| silent unsupported approximations | `0` | `0` |
| guardrail violations | `0` | `0` |

The label distribution also matches the intended family roles:

```text
S1 ordinary_stable_avoidance: aeb_feasible=144
S2 aeb_infeasible_stable_aes: aes_feasible=144
S3 drift_required_avoidance: drift_required=144
S4 unavoidable_mitigation: unavoidable=144
S5 off_track_boundary_stress: aes_feasible=43, drift_required=101
S6 hidden_dynamics_stress: aes_feasible=29, drift_required=71, unavoidable=44
```

## Interpretation Boundary

M1734 is reset-only. It proves that the repaired scenario taxonomy can sample
all planned cells before policy evaluation. It does not prove:

- policy success or failure;
- controller-family ranking;
- scenario-family task quality;
- recurrent advantage;
- finite-window history necessity;
- paper-level benchmark evidence;
- level3 self-identification.

Those claims remain blocked until a repaired measured execution and follow-up
audit exist.

## Decision

Admit M1736 repaired scenario taxonomy execution design.

M1736 should design an execution over:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv
```

The design should preserve the M1731 metadata joins and aggregate requirements,
add repair-variant and sampled-label provenance where useful, and keep result
interpretation deferred to a post-execution audit.
