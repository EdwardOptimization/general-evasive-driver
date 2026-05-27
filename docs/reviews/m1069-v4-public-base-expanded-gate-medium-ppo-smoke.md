# m1069-v4-public-base-expanded-gate-medium-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260527T080132Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: expanded_gate_medium_ppo_reject_proof_washout_route_to_audit
- Decision reason: M1069 PPO completes and broad fresh/OOD plus behavior gates pass but exact public replay family-intersection and source-diverse proof gates fail so the checkpoint is rejected

## Hypothesis

One 8192-step guarded PPO proposal from the M1052 public-gate base can complete with finite metrics and preserve exact, proof, family-intersection, source-diverse, fresh/OOD, and behavior gates without promotion.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
- parent_dataset: docs/m1066-v4-public-base-pre-medium-ppo-readiness-synthesis.md, docs/m1067-v4-public-base-family-gate-propagation-audit.md, docs/m1068-v4-public-base-expanded-gate-medium-ppo-design.md
- parent_config: configs/ppo_m1069_expanded_gate_medium_seed61069.json, experiments/manifests/m1068-v4-public-base-expanded-gate-medium-ppo-design.json
- parent_objective: run one 8192-step guarded PPO proposal from the current public-gate base and gate it with the expanded public proof stack
- derived_from: m1068-v4-public-base-expanded-gate-medium-ppo-design
- blocked_by: M1068 admits a single conservative medium-ramp PPO proposal after family-intersection gate propagation is fixed
- supersedes: None
- invalidates: claiming medium PPO safety without an expanded-gate 8192-step proposal

## Success Criteria

- config configs/ppo_m1069_expanded_gate_medium_seed61069.json exists
- PPO run completes and writes runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
- training metrics are finite
- actor inputs are unchanged
- exact and combined active-set gates pass
- all six old public replay surfaces pass
- M1061 family-intersection gate passes
- source-diverse diagnostics pass
- fresh public and moderate-OOD gates pass
- behavior ablation gates pass
- row15 row16 and M1061 family-intersection rollback checks pass
- no promotion or private holdout occurs

## Failure Criteria

- PPO run crashes or checkpoint is missing
- training metrics are non-finite
- actor inputs change
- exact or combined active-set gate fails
- a public replay surface fails
- M1061 family-intersection gate fails
- row15 wrong-history branch becomes successful
- row16 normal-history branch becomes unsuccessful
- fresh/OOD or behavior gate regresses
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1069 must run exactly one 8192-step guarded PPO proposal
- M1069 must not promote
- M1069 must not use private holdout
- M1069 must preserve the P0 actor-input contract
- M1069 must gate the raw PPO checkpoint against exact M997/M297/M270 and combined active-set checks
- M1069 must gate the raw PPO checkpoint against six old public proof replay surfaces
- M1069 must gate the raw PPO checkpoint against the M1061 family-intersection public proof gate
- M1069 must gate source-diverse diagnostics, fresh public seeds, moderate-OOD seed, and behavior ablations
- M1069 must fail on M267/M264 row15 wrong-history success, M183/M170 row16 normal-history failure, or any M1061 source-to-candidate family-intersection success-drop loss

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run multiple medium seeds
- do not run 16k or long PPO
- do not change actor inputs
- do not use private holdout
- do not promote from M1069
- do not skip exact or combined active-set checks
- do not skip proof replay gates
- do not relax the M1061 family-intersection gate
- do not accept aggregate eval if row15 row16 or family-intersection proof washes out
- do not change loss coefficients while testing this medium-ramp escalation

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1069-v4-public-base-expanded-gate-medium-ppo-smoke
- type: driver_candidate
- checkpoint: runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: expanded_gate_medium_ppo_reject_proof_washout_route_to_audit
- reason: M1069 PPO completes and broad fresh/OOD plus behavior gates pass but exact public replay family-intersection and source-diverse proof gates fail so the checkpoint is rejected

## Next Blocker

m1070-v4-public-base-medium-ppo-proof-washout-audit
