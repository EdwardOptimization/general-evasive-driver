# m324-single-key-window-override-policy-design Research Review

## Summary

- Generated at UTC: 20260523T062158Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m325_source_diverse_policy_full_gate_for_m316_repaired
- Decision reason: M324 defines source-diverse protected bundle as first-class gate and keeps 9944 as diagnostic; singleton-window saturation can advance to full public gate but not promote alone

## Hypothesis

M323 shows the repaired endpoint passes refreshed source-diverse protected surfaces while failing the old saturated 9944 window, so the project needs an explicit override/audit policy before any candidate can progress under the new gate.

## Lineage

- parent_checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt, runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- parent_dataset: runs/m323_source_diverse_gate_repaired_endpoint_probe/summary.json, runs/m316_protected_key_sweep/guard_results.csv
- parent_config: experiments/manifests/m323-source-diverse-gate-retrospective-endpoint-probe.json, docs/m323-source-diverse-gate-retrospective-endpoint-probe.md
- parent_objective: define explicit policy for candidates that pass source-diverse protected gate but fail old singleton protected-key window
- derived_from: m323-source-diverse-gate-retrospective-endpoint-probe
- blocked_by: m323-source-diverse-gate-retrospective-endpoint-probe
- supersedes: None
- invalidates: None

## Success Criteria

- define single-key-window failure taxonomy and handling
- define minimum source-diverse evidence required to override old-key hard veto
- define promotion escalation order under the new protected policy
- register the next diagnostic or full-gate milestone
- no PPO is run

## Failure Criteria

- design deletes or ignores 9944
- design allows promotion without full public gates
- design changes actor inputs
- M324 runs PPO

## Evidence Gates

- do not run PPO
- do not promote M316 repaired endpoint
- preserve human-view actor input contract
- define when old 9944 window failure is diagnostic-only versus hard failure
- define required evidence before full public gate can be run under source-diverse protected policy

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not delete 9944
- do not promote a candidate solely because source-diverse gate passes
- do not run PPO in M324
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m324-single-key-window-override-policy-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m325_source_diverse_policy_full_gate_for_m316_repaired
- reason: M324 defines source-diverse protected bundle as first-class gate and keeps 9944 as diagnostic; singleton-window saturation can advance to full public gate but not promote alone

## Next Blocker

m325-source-diverse-policy-full-gate-for-m316-repaired
