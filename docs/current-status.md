# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Actor Contract

Mainline actor:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deployable inputs:

- ego kinematics / IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road / free-space / obstacle geometry in ego frame;
- recurrent state from past command-response history.

Not allowed in the deployable actor:

- `mu`, mass, CG, tire stiffness, brake scale, actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode or rule branch;
- `speed_ref`, `beta_target`, path error, heading error, path curvature;
- TTC, required clearance, oracle stopping distance, reference trajectory;
- collision/success/progress labels or any precomputed answer.

## Current Checkpoints

Latest public-gate base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Status: M1158 promoted the M1154 alpha `0.05` row15-promoted projection
checkpoint as the current public-gate base after M1154 repaired the promoted
failed-row unsafe surface, M1156 passed expanded public diagnostics, and M1157
audited the result. This is a proof-hardening public-gate promotion only; it is
not a medium-PPO performance claim. Private holdout, medium/long PPO stability,
paper-level generalization, real-vehicle claims, and level3 anticipatory
self-identification claims remain blocked. The near-boundary wrong-history
margin caveat remains active:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

Previous public-gate base:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Status: M1129 promoted the M1123 alpha `0.15` row15 projection checkpoint as
the previous public-gate base after M1127 passed exact, old public replay,
M1061 family-intersection, source-diverse, fresh/OOD, and behavior gates. M1158
supersedes it with the M1154 alpha `0.05` row15-promoted projection candidate.
M1078, M1052, M1049, M1044, M1038 combined active-set, Candidate B, M974, M964
alpha `1.0`, and M399 alpha `0.05` remain older lineage points.

Latest active diagnostic BC checkpoint:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

Status: M568 scaled BC L3 checkpoint selected by M569 and used for M570-M752
diagnostics. It is not the public-gate base and is not promoted as the current
driver checkpoint.

## Paper-Route Governance Update

M1182a records a paper-oriented route plan:

```text
docs/paper-route-finite-window-vs-gru-plan.md
```

The project should not assume `GRU > finite-window`. Future publication claims
must compare:

```text
L0-current
L1-one-step feedback
L2-finite-window command-response history
L3-GRU recurrent belief
```

The paper route now separates:

- engineering feedback-driver performance;
- history-conditioned output feedback;
- conditional recurrent-belief advantage;
- strong self-identification evidence.

M1182 no-residual source-rich adapter is scoped as data-generation support. It
does not by itself justify a GRU recurrent-belief claim, a paper-level result,
PPO readiness, or promotion. M1184 has now designed the gate utility audit that
will classify historical proof gates and row-specific repair logic before they
remain permanent active training blockers or are demoted.

## Current Blocker

```text
m1220-paper-route-current-family-hidden-action-sensitivity-probe
```

M1219 completed the negative action-screen audit:

```text
artifact: docs/m1219-paper-route-current-family-action-screen-negative-audit.md
decision: negative_action_screen_admit_hidden_action_sensitivity_probe
```

M1219 conclusion:

```text
M1218 is a real negative for wrong/delayed matched-history action signal.
Reset-hidden sensitivity is not self-identification evidence.
Persistent outcome rollout is blocked until hidden-action sensitivity is
classified.
```

Next branch:

```text
paper_route_causal_history_evidence
```

The next task is hidden-action sensitivity probing, not outcome intervention or
training:

```text
checkpoint family: M1212 corrected L3 online GRU repeat
env config:        configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
pair source:       runs/m1217_current_family_matched_current_export/matched_pairs.csv
run dir:           runs/m1220_current_family_hidden_action_sensitivity_probe
```

M1220 should compare real wrong/delayed hidden histories against reset,
shuffled, scaled, and random hidden perturbations plus zero-current/zero-action
controls. Off-manifold hidden sensitivity cannot be claimed as self-ID; it only
classifies the next route.

M1218 completed current-family history action screening:

```text
artifact: docs/m1218-paper-route-current-family-history-action-screen.md
run dir: runs/m1218_current_family_history_action_screen
decision: current_family_history_action_screen_negative_route_to_audit
```

M1218 action-screen result:

```text
wrong_matched_history mean / above-threshold: 0.001075 / 0
delayed_history mean / above-threshold:       0.000154 / 0
reset_hidden mean / above-threshold:          0.041795 / 629
zero_action_history mean / above-threshold:   0.013854 / 0
zero_current_response mean / above-threshold: 0.017431 / 20
```

M1217 completed current-family matched-current export:

```text
artifact: docs/m1217-paper-route-current-family-matched-current-export.md
run dir: runs/m1217_current_family_matched_current_export
decision: current_family_matched_current_surface_pass_admit_action_screen
```

M1217 source-diversity result:

```text
accepted pairs:          1790
physical pairs:           427
probe seeds:                4
left steps:                21
obstacle buckets:          12
targets:                    3
```

M1216 completed the causal-history source/tooling audit:

```text
artifact: docs/m1216-paper-route-causal-history-source-audit.md
decision: source_audit_selects_current_family_matched_current_export
```

M1216 conclusion:

```text
Old M503/M524/M537/M538/M586/M587 artifacts are useful as threshold and
interpretation precedents, but they should not be the first current paper-route
causal-history run source.
```

M1215 completed the causal-history gate design:

```text
artifact: docs/m1215-paper-route-causal-history-gate-design.md
decision: causal_history_gate_design_admit_source_audit
```

M1215 gate structure:

```text
Stage A: matched-current surface with source-diverse ambiguity.
Stage B: action-level screen with reset, delayed, wrong-history, zero-response,
         zero-action, and current-tiled/current-response controls.
Stage C: persistent outcome gate using success, collision, completion, and
         clearance-margin degradation.
```

M1214 completed corrected profile evidence synthesis:

```text
artifact: docs/m1214-paper-route-corrected-profile-evidence-synthesis.md
decision: corrected_profile_synthesis_promote_to_causal_history_gate_design
```

M1213 completed the M1209/M1212 cross-block audit:

```text
artifact: docs/m1213-paper-route-corrected-profile-repeat-result-audit.md
decision: corrected_profile_repeat_audit_route_to_branch_synthesis
```

M1213 classification:

```text
L2 finite-window history necessity: stable negative
current-tiled controls: required for future profile claims
L3 family ranking: unstable across seed blocks
L3 online-vs-reset: weak positive in M1212, inconclusive across blocks
self-identification: not supported
```

The strongest corrected-profile finding is negative but useful: L2
finite-window performance should not be treated as history-necessity evidence.
The branch now needs synthesis, not another automatic repeat.

M1212 completed the fresh corrected profile repeat:

```text
artifact: docs/m1212-paper-route-corrected-profile-repeat-run.md
run dir: runs/m1212_corrected_profile_repeat
decision: corrected_profile_repeat_completed_route_to_repeat_result_audit
```

M1212 aggregate trend:

```text
L0_current_masked success/collision/margin:              0.2240 / 0.6250 / 0.3540
L1_one_step success/collision/margin:                    0.3385 / 0.5156 / 0.4758
L2_window_13 success/collision/margin:                   0.4062 / 0.4792 / 0.5237
L2_window_13_current_tiled success/collision/margin:     0.4271 / 0.4427 / 0.6153
L2_window_25 success/collision/margin:                   0.4115 / 0.4740 / 0.5240
L2_window_25_current_tiled success/collision/margin:     0.4271 / 0.4427 / 0.6191
L3_online_gru success/collision/margin:                  0.1875 / 0.8073 / 0.1225
L3_reset_control_corrected success/collision/margin:     0.1354 / 0.8646 / 0.0651
```

M1212 reinforces the negative L2 history-necessity result: current-tiled
controls outperform normal L2 on success, collision, and mean margin. It also
shows aggregate online-GRU > reset-control within the L3 pair, but the L3 family
does not repeat M1209's overall strength. M1213 must audit cross-block stability
before any synthesis or causal history gates.

M1211 completed fresh corrected profile repeat design:

```text
artifact: docs/m1211-paper-route-corrected-profile-repeat-design.md
decision: corrected_profile_repeat_design_admit_fresh_repeat_run
```

M1212 is pre-registered:

```text
profiles: same 8 corrected profiles
training_seed_base: 111600
training_seed_offsets: [0, 1, 2]
eval_seed_base: 121600
eval_episodes_per_checkpoint: 64
budget: same 8192-step CPU/sync profile budget
```

Interpretation thresholds are fixed before the run. L2 history necessity
requires normal L2 to beat current-tiled control on success and margin without
meaningful collision regression. L3 recurrent-hidden benefit requires online
GRU to beat corrected reset-control on success or margin without collision
regression and in at least 2 of 3 seeds. M1212 still cannot claim self-ID; that
requires later causal history gates.

M1210 completed the M1209 corrected pilot audit:

```text
artifact: docs/m1210-paper-route-corrected-profile-pilot-result-audit.md
decision: corrected_profile_pilot_audit_route_to_fresh_repeat_design
```

M1210 classification:

```text
M1209 artifact validity: valid public pilot
L2 finite-window history necessity: negative
L3 architecture-family trend: positive
L3 recurrent-hidden benefit: inconclusive
strong self-identification: negative / not supported
```

Key audit deltas:

```text
L2_window_13 - current_tiled:
  success +0.0208, collision +0.0052, mean margin -0.0419
L2_window_25 - current_tiled:
  success +0.0052, collision +0.0208, mean margin -0.0430
L3_online_gru - corrected_reset:
  success +0.0000, collision +0.0104, mean margin +0.0404
```

Next is a fresh public repeat design, not longer training. M1209's L3 aggregate
is promising but seed-fragile, and the corrected controls block history/belief
claims.

M1209 completed the corrected public profile pilot:

```text
artifact: docs/m1209-paper-route-corrected-profile-pilot-run.md
run dir: runs/m1209_corrected_profile_pilot
decision: corrected_profile_pilot_completed_route_to_result_audit
```

M1209 result:

```text
result_class: corrected_profile_pilot_completed
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

Aggregate public pilot trend:

```text
L0_current_masked success/collision/margin:              0.1406 / 0.7135 / 0.2349
L1_one_step success/collision/margin:                    0.1406 / 0.7396 / 0.1747
L2_window_13 success/collision/margin:                   0.1302 / 0.8073 / 0.0622
L2_window_13_current_tiled success/collision/margin:     0.1094 / 0.8021 / 0.1041
L2_window_25 success/collision/margin:                   0.1198 / 0.8177 / 0.0620
L2_window_25_current_tiled success/collision/margin:     0.1146 / 0.7969 / 0.1050
L3_online_gru success/collision/margin:                  0.3594 / 0.5729 / 0.4966
L3_reset_control_corrected success/collision/margin:     0.3594 / 0.5625 / 0.4562
```

Interpretation is deliberately limited. The corrected pilot supports a public
trend that the L3 architecture family is stronger in this short run, but it
does not prove recurrent hidden benefit because corrected reset-control matches
success and termination. The L2 normal profiles do not beat current-tiled
capacity controls; finite-window history necessity remains unsupported.
M1210 must audit these results before repeat, longer training, or branch
synthesis.

M1208 completed generated corrected profile config smoke:

```text
artifact: docs/m1208-paper-route-corrected-profile-config-smoke-run.md
run dir: runs/m1208_corrected_profile_config_smoke
decision: corrected_profile_config_smoke_pass_route_to_corrected_pilot_run
```

M1208 result:

```text
result_class: controller_profile_runtime_smoke_pass
config_count: 8
all_configs_instantiated: true
contract_ok: true
model_forward_ok: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
current_tiled_profile_count: 2
current_tiled_profiles_observed: true
corrected_reset_profile_count: 1
corrected_reset_policy_routing_ok: true
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

M1209 may now run the fixed corrected public profile pilot. It remains public
pilot trend evidence only: no promotion, private holdout, per-profile tuning,
self-ID claim, or paper-level claim.

M1207 completed corrected profile config generation:

```text
artifact: docs/m1207-paper-route-corrected-profile-config-generation.md
run dir: runs/m1207_corrected_profile_config_generation
decision: corrected_profile_configs_generated_route_to_config_smoke
```

M1207 generated eight corrected profile configs under:

```text
configs/paper_route_corrected_profiles
```

Generated set:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Key semantics:

```text
L2_window_13_current_tiled: capacity-matched temporal-GRU with older frames replaced by frame 0
L2_window_25_current_tiled: capacity-matched temporal-GRU with older frames replaced by frame 0
L3_reset_control_corrected: online-GRU reset-control metadata with every_step_control eval policy
```

Focused tests passed (`28 passed, 1 warning`). M1207 did not train controllers,
run PPO, use private holdout, promote, tune profiles, or claim self-ID/profile
superiority. M1208 smoke-tested the generated configs successfully.

M1206 completed the corrected public pilot design:

```text
artifact: docs/m1206-paper-route-corrected-profile-pilot-design.md
decision: corrected_profile_pilot_design_admit_config_generation
```

Corrected pilot profile set:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

M1207 materialized these configs; M1208 must now load and smoke-test them before
any corrected PPO run.

M1205 completed the finite-window vs GRU evidence synthesis:

```text
artifact: docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md
decision: continue_to_corrected_profile_pilot_design
```

Synthesis result: M1195-M1204 established train-loop-capable profiles, a valid
short public L2 trend, and working corrected controls. It did not establish
finite-window history necessity, GRU recurrent-belief advantage, self-ID, or
paper-level architecture ranking. The next branch step is M1206 corrected public
pilot design.

M1204 completed the no-training corrected-control runtime smoke, and M1205
synthesized the branch before M1206/M1207. Those earlier results remain the
reason M1208 is allowed to smoke-test generated configs, not a reason to skip
the generated-config smoke.

M1203 completed profile control repair implementation:

```text
artifact: docs/m1203-paper-route-profile-control-repair-implementation.md
source: src/autodrift/controller_profile_runtime.py, src/autodrift/evaluate.py
tests: tests/test_controller_profile_runtime.py, tests/test_controller_profile_train_entrypoint_mask.py, tests/test_evaluate_reset_hidden_policy.py
decision: profile_control_repair_implementation_ready_for_corrected_runtime_smoke
```

Implemented:

```text
ObservationMaskSpec.history_transform = current_tiled
ObservationMaskSpec.reset_hidden_policy metadata
ActorPolicy reset_hidden_policy=every_step_control semantics
```

Focused tests passed (`17 passed`). M1204 must run a no-training runtime smoke
before any corrected PPO pilot.

M1202 completed profile control repair design:

```text
artifact: docs/m1202-paper-route-profile-control-repair-design.md
decision: profile_control_repair_design_admit_runtime_implementation
```

M1202 requires the next implementation to add:

```text
1. public eval support for controller_profile.reset_hidden_policy;
2. current-tiled L2 controls that preserve temporal-GRU capacity but remove older-history information.
```

No longer profile comparison should run until M1203 implements and tests these
diagnostic controls.

M1201 completed the profile separability audit:

```text
artifact: docs/m1201-paper-route-profile-separability-audit.md
run dir: runs/m1201_profile_separability_audit
decision: profile_separability_audit_route_to_profile_control_repair_design
```

M1201 result:

```text
configs_differ_as_intended: true
l2_observation_stacks_nonidentical: true
l2_older_tiled_action_l2_mean_overall: 0.001374
l2_older_zeroed_action_l2_mean_overall: 0.060810
l3_online_normal_vs_reset_action_l2_mean: 0.044612
reset_control_external_eval_semantics_mismatch: true
```

Interpretation: M1199's L2 trend is not yet finite-window history evidence,
because plausible current-tiled older-history ablation barely changes actions.
Also, the M1199 `L3_reset_control` diagnostic was a metric artifact: external
eval did not enforce every-step hidden reset. M1202 must design reset-eval
semantics and a current-tiled L2 capacity control before more training.

M1200 completed the M1199 result audit:

```text
artifact: docs/m1200-paper-route-fair-comparison-pilot-result-audit.md
decision: fair_comparison_pilot_audit_route_to_profile_separability_audit
```

M1200 keeps M1199 valid as a public pilot trend but blocks direct scaling into
a longer comparison. Two audit flags are now active:

```text
L2 window-equivalence: inconclusive_but_suspicious
L3 reset-parity: negative_for_recurrent_hidden_benefit_in_this_pilot
```

Next step is M1201: verify config, observation-stack, and action-level profile
separability without training, PPO, private holdout, promotion, or claim
expansion.

M1199 completed the fixed public fair comparison pilot:

```text
artifact: docs/m1199-paper-route-fair-comparison-pilot-run.md
run dir: runs/m1199_fair_comparison_pilot
decision: fair_comparison_pilot_completed_route_to_result_audit
```

M1199 result:

```text
profile_count: 8
main_profile_count: 7
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
candidate_replay_started: false
actor_input_contract_changed: false
profile_specific_tuning: false
self_identification_claimed: false
paper_level_claimed: false
```

Public pilot trend, averaged over three training seeds and 64 fixed public eval
episodes per seed:

```text
L0_current_masked success/collision/margin: 0.1458 / 0.8333 / 0.1072
L1_one_step success/collision/margin:       0.2969 / 0.6562 / 0.3505
L2_window_13 success/collision/margin:     0.3854 / 0.4219 / 0.7175
L2_window_25 success/collision/margin:     0.3854 / 0.4219 / 0.7189
L2_window_50 success/collision/margin:     0.3854 / 0.4219 / 0.7189
L2_window_100 success/collision/margin:    0.3854 / 0.4219 / 0.7189
L3_online_gru success/collision/margin:    0.2552 / 0.7448 / 0.2726
L3_reset_control success/collision/margin: 0.2656 / 0.7135 / 0.2934
```

Interpretation is deliberately limited: L2 finite-window profiles are strongest
in this short public pilot, L1 improves over L0, and L3 online-GRU does not show
recurrent-hidden benefit over its reset diagnostic. Before scaling, M1200 must
audit the near-identical L2 window metrics and the L3 reset-control parity.

M1198 completed the fair public L0/L1/L2/L3 comparison pilot design:

```text
artifact: docs/m1198-paper-route-fair-comparison-pilot-design.md
decision: fair_comparison_pilot_design_admit_public_pilot_run
```

M1198 fixed the next public pilot protocol:

```text
main profiles: L0_current_masked, L1_one_step, L2_window_13, L2_window_25, L2_window_50, L2_window_100, L3_online_gru
diagnostic control: L3_reset_control
training_seeds_per_profile: 3
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
eval_episodes_per_checkpoint: 64
eval_seed_base: 119800
```

The M1196/M1197 smoke metrics remain plumbing diagnostics only. They are not
profile comparison evidence. M1199 may now run the fixed public pilot, but it
must not promote, use private holdout, tune profile-specific hyperparameters,
change actor inputs, or claim recurrent-belief/self-identification evidence.

M1197 completed the bounded Stage B all-profile training smoke:

```text
artifact: docs/m1197-paper-route-profile-training-smoke-stage-b-run.md
run dir: runs/m1197_profile_training_smoke_stage_b
decision: profile_training_smoke_stage_b_pass_route_to_fair_comparison_pilot_design
```

M1197 result:

```text
profiles: L0_current_masked, L1_one_step, L2_window_13, L2_window_25, L2_window_50, L2_window_100, L3_online_gru, L3_reset_control
total_steps_per_profile: 1024
num_envs: 2
all_profiles_complete: true
all_eval_metrics_finite: true
l0_runtime_mask_metadata_present: true
training_started: true
optimizer_started: true
ppo_used: true
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_superiority_claimed: false
driver_performance_claimed: false
```

The eval values in M1197 are smoke diagnostics only, not performance
comparisons.

M1196 completed the bounded Stage A profile training smoke:

```text
artifact: docs/m1196-paper-route-profile-training-smoke-stage-a-run.md
run dir: runs/m1196_profile_training_smoke_stage_a
decision: profile_training_smoke_stage_a_pass_route_to_stage_b_full_profile_smoke
```

M1196 result:

```text
profiles: L0_current_masked, L1_one_step, L2_window_25, L3_online_gru
total_steps_per_profile: 1024
num_envs: 2
all_profiles_complete: true
all_eval_metrics_finite: true
l0_runtime_mask_metadata_present: true
training_started: true
optimizer_started: true
ppo_used: true
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_superiority_claimed: false
driver_performance_claimed: false
```

M1195 completed train/eval vector-path profile-mask integration:

```text
artifact: docs/m1195-paper-route-train-entrypoint-profile-mask-integration.md
source: src/autodrift/vector_env.py, src/autodrift/train_ppo.py
tests: tests/test_controller_profile_train_entrypoint_mask.py
decision: train_entrypoint_profile_mask_integration_ready_for_stage_a_training_smoke
```

M1195 result:

```text
sync vector env masks L0 reset/step observations
parallel vector env masks L0 reset/step observations
sync vector env leaves unmasked L1 observations unchanged
train_ppo reads top-level controller_profile mask metadata
evaluate_actor accepts the same profile mask spec
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

Focused verification:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_train_entrypoint_mask.py tests/test_controller_profile_runtime.py tests/test_controller_profile_runtime_smoke.py
15 passed
```

M1194 completed the required workflow synthesis:

```text
artifact: docs/m1194-paper-route-finite-window-gru-infrastructure-synthesis.md
decision: paper_route_infrastructure_synthesis_continue_to_train_entrypoint_mask_integration
synthesis_decision: continue
```

M1194 supported claims:

```text
active gate policy exists
L0/L1/L2/L3 comparison contract exists
eight generated profile configs exist
no-training runtime smoke passes
single-env L0 runtime mask works
unmasked profiles remain unchanged
```

M1194 blocked claims:

```text
metadata alone is not enough for L0 training
runtime smoke is not PPO readiness
GRU superiority is unsupported
runtime smoke is not driver performance evidence
self-identification evidence has not been tested in this branch
```

M1193 designed the bounded fair controller-profile training-smoke protocol and
found two blockers before training:

```text
artifact: docs/m1193-paper-route-controller-profile-training-smoke-design.md
decision: training_smoke_design_routes_to_branch_synthesis_before_mask_integration
```

Key M1193 finding:

```text
train_ppo -> make_vector_env -> SyncAutoDriftVectorEnv / ParallelAutoDriftVectorEnv
vector envs construct AutoDriftEnv directly
controller_profile_runtime wrapper is not yet applied there
```

Profile training remains blocked after synthesis until controller-profile
observation masks are integrated into train/eval vector paths. The follow-up
integration must prove with focused tests that `L0_current_masked` zeros
previous-command fields `[9,10,11]` in vector reset/step observations while
unmasked profiles remain unchanged.

M1193's planned training-smoke ladder after synthesis and mask integration:

```text
Stage A: L0_current_masked, L1_one_step, L2_window_25, L3_online_gru
Stage A budget: 1024 steps, 2 envs, 1 seed, CPU, no performance claim
Stage B: all eight generated profiles under the same smoke budget
Stage C: separate fair comparison pilot after another manifest
```

M1192 completed the integrated no-training runtime smoke for all generated
controller-profile configs:

```text
artifact: docs/m1192-paper-route-controller-profile-runtime-smoke-run.md
source: src/autodrift/controller_profile_runtime_smoke.py
tests: tests/test_controller_profile_runtime_smoke.py
run dir: runs/m1192_controller_profile_runtime_smoke
decision: controller_profile_runtime_smoke_pass_route_to_training_smoke_design
```

M1192 result:

```text
config_count: 8
all_configs_instantiated: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
contract_ok: true
model_forward_ok: true
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

The L0 runtime wrapper did real work after a nonzero control step:

```text
raw_step_previous_command_abs_sum: 1.4500000476837158
wrapped_step_previous_command_abs_sum: 0.0
```

Focused verification:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_runtime_smoke.py tests/test_controller_profile_runtime.py tests/test_controller_profile_configs.py tests/test_controller_profiles.py
25 passed
```

M1191 implemented runtime observation-mask support for controller-profile
configs:

```text
artifact: docs/m1191-paper-route-observation-mask-runtime-wrapper-implementation.md
source: src/autodrift/controller_profile_runtime.py
tests: tests/test_controller_profile_runtime.py
decision: runtime_observation_mask_ready_route_to_profile_runtime_smoke
```

M1191 result:

```text
L0_current_masked runtime mask: zero_previous_command_fields
masked fields: [9, 10, 11]
mask location: AutoDriftEnv reset/step observations via ControllerProfileObservationWrapper
unmasked profiles: unchanged and not wrapped
training_started: false
optimizer_started: false
ppo_used: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
```

Focused verification:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_profile_runtime.py tests/test_controller_profile_configs.py tests/test_controller_profiles.py
22 passed
```

The next blocker is M1192: instantiate all generated L0/L1/L2/L3 profile
configs with runtime masks and write a no-training smoke artifact before any
controller training or evaluation claim.

M1190 implemented generated controller-profile smoke configs:

```text
artifact: docs/m1190-paper-route-controller-profile-config-generation-implementation.md
source: src/autodrift/controller_profile_configs.py
tests: tests/test_controller_profile_configs.py
configs: configs/paper_route_profiles/m1190_*_smoke.json
run dir: runs/m1190_controller_profile_config_generation
decision: controller_profile_configs_generated_route_to_runtime_mask_wrapper
```

M1190 generated eight smoke configs with L0 mask metadata, four L2 finite
windows `[13,25,50,100]`, L3 variants, and no training/PPO/replay/promotion.

Older route notes below retain their then-next milestone wording as history;
the active blocker is the M1198 fair comparison pilot design above.

M1189 completed controller-profile config-generation design:

```text
artifact: docs/m1189-paper-route-controller-profile-config-generation-design.md
decision: controller_profile_config_generation_design_admit_implementation
next manifest: experiments/manifests/m1190-paper-route-controller-profile-config-generation-implementation.json
```

M1189 specifies eight generated smoke configs under
`configs/paper_route_profiles/`, based on
`configs/m121_human_view_zero_obstacle_relvel.json`, with profile-specific
history lengths and profile metadata. It requires L0 config metadata to include
`observation_mask=zero_previous_command_fields` and previous-command indices
`[9,10,11]`. It does not claim the runtime training/eval entrypoints already
apply the mask; if M1190 exposes a gap, the route is a focused runtime mask
wrapper before any L0 training.

M1189 did not generate final configs, train, run replay, run PPO, promote, use
private holdout, or change actor inputs. The next blocker is M1190: implement
generated config files and tests without running those configs for training.

M1188 implemented the controller-profile scaffold:

```text
artifact: docs/m1188-paper-route-controller-profile-scaffold-implementation.md
source: src/autodrift/controller_profiles.py
tests: tests/test_controller_profiles.py
smoke: runs/m1188_controller_profile_scaffold_smoke/summary.json
decision: controller_profile_scaffold_ready_route_to_config_generation_design
```

Profiles now available:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

M1188 verifies L0 previous-command masking `[9,10,11]`, no hidden/oracle actor
inputs, no wheel/slip actor inputs, no reference/TTC actor inputs, model
instantiation for representative profiles, and profile smoke artifact writing.
It did not train controllers, run replay, run PPO, promote, use private
holdout, or change actor inputs. The next blocker is M1189: design generated
train/eval smoke configs and L0 runtime mask handling before any controller
training.

M1187 completed the fair controller-comparison design:

```text
artifact: docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md
decision: l0_l1_l2_l3_controller_comparison_design_admit_profile_scaffold
```

The controller levels are now defined as:

- L0: current-only human-view frame with previous-command fields masked to zero.
- L1: canonical 72-value one-step command-response feedback frame.
- L2: finite-window command-response history with 13, 25, 50, and 100 step
  windows for 0.25s, 0.50s, 1.00s, and 2.00s at `dt=0.02s`.
- L3: online human-view GRU recurrent state, with reset/truncation controls.

M1187 also fixes task families, public split policy, capacity/inference-cost
reporting, and gate triggers. It did not train controllers, run replay, run
PPO, promote, use private holdout, or change actor inputs. The next blocker is
M1188: implement profile metadata, L0 masking, profile instantiation tests, and
contract checks before any training.

M1186 completed the active gate policy:

```text
artifact: docs/m1186-paper-route-active-gate-policy-design.md
policy: docs/active-gate-policy.md
decision: active_gate_policy_design_admit_l0_l1_l2_l3_controller_comparison_design
```

The active gate schedule is now:

- Stack A: daily engineering and controller-comparison admission. It is core
  for actor contract, broad behavior, and process validation, but it is not
  mechanism proof.
- Stack B: active public proof default for public-base hardening, guarded PPO
  admission, source-rich proof conversion, and mechanism claims.
- Stack C: extended historical regression for promotion, branch synthesis,
  paper table freeze, and hard failure localization.
- Legacy diagnostics: keep for provenance and compatibility, but do not use as
  single-row global blockers unless reinstated by manifest.
- Deprecated objectives: do not use for training or promotion without a new
  reinstatement manifest.

M1186 did not run replay, delete gates, train, run PPO, promote, use private
holdout, or change actor inputs. The next blocker is M1187: design the fair
L0/L1/L2/L3 controller comparison before any controller training or GRU-first
paper claim.

M1185 completed the first gate utility matrix:

```text
artifact: docs/m1185-paper-route-gate-utility-matrix-run.md
matrix: docs/gate-utility-matrix.md
run dir: runs/m1185_gate_utility_matrix
decision: gate_utility_matrix_pass_route_to_active_gate_policy_design
candidate rows: 12
gate utility rows: 13
gate stacks: Stack A minimal engineering, Stack B balanced public, Stack C full historical diagnostic
```

M1185 result:

- Stack A remains core for engineering behavior, but it can miss proof washout
  that preserves aggregate behavior.
- Stack B is the recommended active public default for the paper route because
  it catches known wrong-history-safe and duplicate-dominated surface failures.
- Stack C should remain extended regression and paper appendix diagnostics
  unless a later executable audit shows a member has unique Stack-B-missing
  failure coverage.
- Legacy singletons such as the old `9944` protected key should not be
  single-row global blockers.
- Deprecated metric-artifact or sign-wrong objectives should not guide future
  training without a new reinstatement manifest.

M1185 did not run candidate replay, demote gates, delete tooling, train, run
PPO, promote, use private holdout, or change actor inputs. The next blocker is
M1186: turn the matrix into a written active gate policy before the L0/L1/L2/L3
controller comparison design.

M1184 completed the paper-route gate utility audit design:

```text
artifact: docs/m1184-paper-route-gate-utility-audit-design.md
decision: paper_route_gate_utility_audit_design_admit_matrix_run
candidate classes: good promoted/admitted, known bad, near-miss, null/no-op
gate stacks: Stack A minimal engineering, Stack B balanced public, Stack C full historical diagnostic
classifications: core, research-only, extended-regression, legacy, deprecated
```

M1184 did not run candidate replay, demote gates, delete tooling, train, run
PPO, promote, use private holdout, or change actor inputs. Its only active
effect is to pre-register M1185:

```text
manifest: experiments/manifests/m1185-paper-route-gate-utility-matrix-run.json
success artifact: docs/m1185-paper-route-gate-utility-matrix-run.md
required matrix: docs/gate-utility-matrix.md
run dir: runs/m1185_gate_utility_matrix
```

M1185 should populate a candidate manifest, gate utility matrix, and gate stack
decision table from existing artifacts only. If inventory is insufficient, it
should route to candidate inventory rather than weaken gate standards.

M1183 ran the bounded source-rich adapter metadata smoke:

```text
run: runs/m1183_current_base_no_residual_source_rich_smoke/summary.json
result_class: current_base_source_rich_adapter_metadata_ready
required_metadata_pass: true
missing_required_metadata_fields: []
source_group_rows: 2
source_result_rows: 2
boundary_search_plan_rows: 4
residual_head_required: false
actor_backbone_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

This confirms the no-residual adapter can emit source-rich metadata for the
current public-gate actor. It is infrastructure evidence only and does not
claim source-rich proof, driver performance, recurrent-belief evidence, PPO
readiness, promotion, or paper-level results.

Given M1182a's paper route, the next blocker is M1184: design the gate utility
audit that will classify historical gates, corpora, repair/projection tools,
and row-specific proof rows as `core`, `research-only`, `extended-regression`,
`legacy`, or `deprecated` before broad training, gate demotion, or paper-level
claims.

M1182 implemented the current-base no-residual source-rich adapter:

```text
source: src/autodrift/current_base_source_rich_adapter.py
tests: tests/test_current_base_source_rich_adapter.py
```

M1181 audited existing source-rich v4 tooling:

```text
artifact: docs/m1181-v4-public-base-source-rich-route-compatibility-audit.md
decision: source_rich_route_compatibility_audit_route_to_no_residual_adapter_implementation
```

Finding:

```text
existing source-rich v4 tools require --residual-head;
M761 residual_head feature_dim: 64;
current public-base feature_dim: 12;
loader result: residual feature_dim=64 does not match actor feature_dim=12.
```

`alpha=0` is not a valid workaround because the residual head is loaded before
alpha can neutralize the residual action. M1182 should implement a minimal
current-base no-residual source-rich adapter and focused tests only. No
source-rich mining, full replay, training, PPO, promotion, private holdout,
row conversion, or actor-input change should happen in M1182.

M1127 completed the expanded full public gate for the row15 projection
candidate:

```text
candidate:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

M1107 exact:
  proof_current loss: 0.679117322
  alpha_0_15 loss:   0.678699851
  delta:             -0.000417471

expanded full public gate:
  exact_pass: true
  proof_pass: true
  family_intersection_pass: true
  source_diverse_pass: true
  generalization_pass: true
  behavior_pass: true
  actor_inputs_changed: false
  ppo_used: false
  promoted: false
  private_holdout_used: false
```

Old public replay retained all success drops across six surfaces; M1061
family-intersection replay retained `25/25`, `27/27`, and `27/27` success
drops; source-diverse replay retained `17/17` on all three protected surfaces.
Fresh randomized public eval and moderate-OOD eval kept success deltas at `0.0`;
behavior seeds `9505`, `9506`, `103930`, and `103931` retained baseline
success. This is a positive public proof-hardening result, not a PPO,
promotion, private-holdout, paper-level, or real-vehicle claim.

M1128 completed the branch synthesis. It closes
`failed_wrong_history_retention_repair` and opens
`row15_projection_promotion_audit`. The supported claim is narrow:
`alpha_0_15` is ready for a separate public proof-base hardening promotion
audit. It does not prove PPO readiness, medium/long training stability,
private-holdout generalization, paper-level evidence, real-vehicle transfer, or
level3 anticipatory self-identification.

M1139 completed the deterministic family-intersection selector for the M1136
cross-family replay rows. It kept rows that pass under all five expected
policies:

```text
row15_current
previous_m1078_base
short61049
short61050
short61051
```

Selector result:

```text
family_rows: 172
kept_rows: 148
dropped_rows: 24
physical_pairs: 13
source_labels: 5
targets: 2
left_steps: 6
max_physical_pair_fraction: 0.135135
max_source_label_fraction: 0.283784
decision: row15_promoted_intersection_selector_pass_route_to_target_materialization_design
```

M1140 designed current public-gate base target-policy materialization for these
rows:

```text
target_policy_label: row15_current
target_policy_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
expected_rows: 148
min_physical_pairs: 12
min_source_labels: 4
min_targets: 2
min_left_steps: 6
max_physical_pair_fraction: 0.25
max_source_label_fraction: 0.45
```

M1141 synthesized the `row15_promoted_base_surface_refresh` branch. Supported
claim:

```text
source-policy surface:
  172 rows, 15 physical pairs, 5 checkpoints, 3 targets
all-policy materialization surface:
  148 rows, 13 physical pairs, 5 source labels, 2 targets
```

Direct mixed-family objective conversion remains blocked. The branch is now
closed and the next branch is `row15_promoted_target_materialization`.

M1142 ran the existing `row15_current` materializer and passed:

```text
rows: 148
normal_success_count: 148
wrong_history_success_count: 0
success_drop_count: 148
finite_objective_rows: 148
physical_pairs: 13
source_labels: 5
targets: 2
left_steps: 6
min_normal_margin: 0.000997985
max_wrong_history_margin: -0.000063233
min_margin_gap: 0.001313707
```

Output:

```text
runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
```

M1143 designed the corpus/objective sanity run over these materialized rows.
Read-only pre-audit:

```text
raw materialized rows: 148
unique boundary geometry rows: 76
physical_pairs: 13
targets: 2
left_steps: 6
source_labels: 5
```

M1144 built the row15-current corpus and ran objective sanity:

```text
corpus_rows: 76
physical_pairs: 13
targets: 2
success_drop_rows: 76
selected_source_rows: 76
action_reconstruction_error_max: 0.0
action_reconstruction_error_mean: 0.0
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 3.211031
min_val_combined_loss_improvement: 2.906849
mean_val_pairwise_accuracy_after: 1.0
```

M1145 audited the result as strong enough to admit a guarded actor-update
design only:

```text
admitted_next: guarded_actor_update_design
direct_actor_update_admitted: false
ppo_admitted: false
promotion_admitted: false
```

M1146 designed the guarded actor-update probe:

```text
init checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
snippet npz:
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
seeds: 114600, 114601, 114602
steps: 10
learning_rate: 0.00005
train_scope: actor_coupling
train_log_std: false
action_anchor_coef: 100.0
snippet_action_anchor_coef: 100.0
```

M1147 ran the pre-registered actor-coupling probes and pre-replay gates:

```text
base exact M1144 loss: 0.417700
m1147_114600 exact loss: 0.409554
m1147_114601 exact loss: 0.409563
m1147_114602 exact loss: 0.409408
best candidate: m1147_114602
best exact delta: -0.008292
max action-anchor MSE: 0.000008367
max snippet-action-anchor MSE: 0.000019765
changed tensors: actor_mean.* and response_context_fusion.0.* only
log_std changed: false
```

M1148 designed first replay for `m1147_114602`:

```text
old-public surfaces: 6
source-diverse surfaces: 3
row15-promoted materialized surfaces: 1
max_continuation_steps: 60
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

M1149 ran first replay for `m1147_114602` and rejected the candidate:

```text
surface_count: 10
passed_surface_count: 8
failed_surface_count: 2
old_public_first_replay_pass: false
source_diverse_first_replay_pass: true
row15_promoted_materialized_replay_pass: false
lost_success_drop_events: 76
normal_lost_events: 0
wrong_history_safe_events: 76
```

Failed surfaces:

```text
m267_m264:
  baseline success drops: 17
  candidate success drops: 16

row15_promoted_materialized:
  baseline success drops: 148
  candidate success drops: 73
```

This is not normal-history collapse. The candidate keeps normal success rate at
`1.0` on every surface, but wrong-history branches become safe.

M1150 audited the failure:

```text
materialized_lost_rows: 75
materialized_lost_unique_boundary_geometries: 49
lost_rows_boundary_geometry_selected_in_m1144_fraction: 1.0
m267_failure_present_in_m1144_objective: false
failed_rows_weight_mean: 0.003962
nonfailed_rows_weight_mean: 0.015196
failed_rows_wrong_history_margin_mean: -0.000463
nonfailed_rows_wrong_history_margin_mean: -0.004114
```

The materialized failures were covered by M1144, so this is not a materialized
corpus coverage miss. The failure is objective-form insufficiency: exact M1144
preference loss can improve while low-weight near-boundary braking rows lose
wrong-history terminal-margin negativity. M267 remains a separate old-public
retention row outside the M1144 corpus.

M1151 synthesized the branch and closed
`row15_promoted_target_materialization`.

Supported claim:

```text
The promoted-base materialized surface and exact objective signal are real, and
M1147 shows a small actor-coupling update can improve exact M1144 loss under
the allowed parameter contract.
```

Falsified claim:

```text
Direct M1144 exact-objective actor-update continuation is replay-safe.
```

The opened branch is:

```text
row15_promoted_unsafe_margin_projection
```

M1152 designed the unsafe-margin projection:

```text
alpha_grid:
  0.0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075,
  0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0

failed-row unsafe rule:
  normal_success == true
  normal_margin >= 0
  wrong_history_success == false
  wrong_history_margin < 0

exact rule:
  selected nonzero alpha must improve exact M1144 objective
```

M1152 also found that the old M1123 `row15_unsafe_margin_projection_probe`
should not be reused directly because it hardcodes the old single-row cliff and
requires M1115 anchor NPZs.

M1153 implemented the promoted projection runner:

```text
runner:
  src/autodrift/row15_promoted_unsafe_margin_projection_probe.py

tests:
  tests/test_row15_promoted_unsafe_margin_projection_probe.py

focused pytest:
  5 passed
```

The runner consumes arbitrary failed-row CSVs, groups by surface, applies the
M1152 unsafe-margin rule, evaluates exact M1144 objective, and only then allows
selected-alpha M1149 first replay. M1153 did not run the projection experiment.

M1154 ran the no-training projection:

```text
selected_alpha: 0.05
selected_checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
exact_M1144_delta: -0.000378
failed_row_count: 76
failed_row_unsafe_margin_pass_count: 76
first_replay_pass: true
first_replay_surface_count: 10
```

The selected alpha restores the M1149 failed-row proof surface:

```text
m267_m264 wrong_history_margin_max: -0.000260
row15_promoted_materialized wrong_history_margin_max: -0.000000497
row15_promoted_materialized first replay: 148 / 148 success drops retained
```

This is a positive proof-repair result, but it is not promotable. The margin is
very close to zero on the promoted materialized surface, and the checkpoint has
not passed M1061 family-intersection replay, behavior diagnostics, full public
gate, private holdout, or PPO stability.

M1155 designed the next diagnostic run for `alpha_0_05`:

```text
1. M1144 exact recheck against row15_current.
2. Expanded public diagnostic wrapper if exact remains improved.
```

The wrapper includes allowed-surface contract, M297/M270 exact, old-public
proof replay, M1061 family-intersection replay, source-diverse diagnostics,
fresh/OOD eval, and behavior seeds `9505`, `9506`, `103930`, and `103931`.

The next milestone is M1156: run only those diagnostics. It must not train, run
PPO, mine rows, promote, use private holdout, or change actor inputs. A pass is
not promotion; it only admits a later synthesis or promotion-audit design.

M1156 ran those diagnostics and passed:

```text
candidate:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

M1144 exact recheck:
  row15_current loss: 0.417700052
  alpha_0_05 loss:   0.417321652
  delta:             -0.000378400

expanded public diagnostic:
  exact_pass: true
  proof_pass: true
  family_intersection_pass: true
  source_diverse_pass: true
  generalization_pass: true
  behavior_pass: true
  actor_inputs_changed: false
  ppo_used: false
  promoted: false
  private_holdout_used: false
```

Old-public replay retained all success drops across six surfaces; M1061
family-intersection replay retained `25/25`, `27/27`, and `27/27` success
drops; source-diverse replay retained `17/17` on all three protected surfaces.
Fresh randomized public eval and moderate-OOD eval kept success deltas at
`0.0`; behavior seeds `9505`, `9506`, `103930`, and `103931` retained baseline
success and reset/zero-all ordering.

This is still diagnostic, not promotion. The M1154 selected alpha remains near
the wrong-history unsafe-margin boundary:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

M1157 should audit the M1156 result and decide whether `alpha_0_05` is ready
for a separate promotion-audit design or needs additional margin-slack
diagnostics. M1157 must not train, run PPO, run replay, mine rows, promote, use
private holdout, or change actor inputs.

M1157 completed that audit. It found the M1156 evidence internally consistent
and sufficient to admit a separate promotion audit:

```text
M1156 exact/proof/family/source/generalization/behavior all-pass: true
near-boundary caveat preserved: true
direct promotion from M1156: blocked
promotion audit admitted: true
PPO/private-holdout/driver-performance claim: blocked
```

The next milestone is M1158: decide whether `alpha_0_05` should replace
`alpha_0_15` as the current public-gate base for proof-base hardening only.
M1158 must preserve the near-zero wrong-history margin caveat and must not run
training, PPO, replay, mining, private holdout, or actor-input changes.

M1158 completed the promotion audit and promoted `alpha_0_05`:

```text
new_public_gate_base:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
previous_public_gate_base:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
scope: public proof-base hardening only
medium_ppo_performance_claim: false
private_holdout_claim: false
paper_level_generalization_claim: false
driver_performance_claim: false
level3_self_identification_claim: false
```

M1159 should synthesize the post-promotion state, close
`row15_promoted_unsafe_margin_projection`, and choose the next branch before
any PPO, private holdout, mining, or medium-scale training.

M1159 completed that synthesis:

```text
closed_branch: row15_promoted_unsafe_margin_projection
opened_branch: row15_promoted_margin_slack_surface_refresh
current_public_gate_base:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
supported_claim_scope: public proof-base hardening
```

Immediate PPO remains blocked. The next branch should refresh source-diverse
current-base protected/preference surfaces with explicit margin-slack coverage
so the next objective/replay corpus is not only a thin near-zero row15 repair
surface.

M1160 should design that refresh only. It must not mine rows, run replay, run
PPO, promote, use private holdout, or change actor inputs.

M1160 completed the design. M1161 should run the pre-registered three-stage
surface refresh:

```text
source family:
  alpha_0_05 current base
  alpha_0_15 previous base
  previous M1078 base
  short61049
  short61050
  short61051

minimum accepted wrong-history rows: 100
minimum physical pairs: 12
minimum left steps: 6
minimum checkpoints: 4
minimum targets: 2
minimum normal-margin buckets at 0.005m: 3
minimum normal-margin max: 0.01m
```

M1161 must not train, run PPO, promote, use private holdout, change actor
inputs, weaken thresholds after seeing results, or convert the surface into an
objective corpus inside the same milestone.

M1161 ran and rejected the surface:

```text
matched-current accepted pairs: 4585
matched-current physical pairs: 242
outcome rows: 27510
source budget ready: true
selected rows before relocation: 1200
selected physical pairs before relocation: 242

final accepted wrong-history rows: 15
final accepted physical pairs: 2
final accepted targets: 1
final accepted normal-margin buckets: 1
final normal-margin max: 0.002483
max rows per physical pair fraction: 0.666667
decision: reject_duplicate_dominated_boundary_surface
```

M1161 did not invalidate the M1158 public-gate-base promotion, but it blocks
objective conversion and PPO from this fresh surface. M1162 should audit why a
strong source budget collapses into a sparse, duplicate-dominated, low-slack
accepted surface after relocation.

M1162 completed that audit:

```text
source_budget_shortfall: false
source_budget_ready: true
wrong_matched_relocated_rows: 4250
wrong_matched_accepted_rows: 15
wrong_matched_normal_and_variant_success_rows: 4086
accepted_reset_rows before final wrong-history balancing: 1010
accepted_zero_current_response_rows before final wrong-history balancing: 655
failure: relocation active-set collapse plus wrong-history scarcity
```

The next step is M1163: design a bounded relocation-expansion diagnostic using
the existing M1161 outcome CSV. It should expand relocation search dimensions
without rerunning source mining or weakening M1160 acceptance thresholds.

M1163 completed that design. M1164 should run only the bounded relocation
expansion over:

```text
runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
```

The expansion uses `1600` candidates, body longitudinal offsets
`-1.0,0.0,1.0`, body lateral offsets `-0.3,0.0,0.3`, and unchanged M1160
acceptance thresholds. It must not rerun mining or the outcome gate, train,
run PPO, promote, use private holdout, change actor inputs, weaken thresholds,
or convert the surface in the same milestone.

M1164 attempted that expansion but was interrupted after roughly `33` minutes
with no summary artifact and an empty run directory. This is a resource-scope
failure, not evidence that relocation expansion cannot recover a surface.

M1165 should redesign the expansion as a staged, smaller pilot over the same
existing M1161 outcome CSV. It should keep scientific acceptance thresholds
unchanged while reducing the resource footprint enough to produce a diagnostic
summary.

M1165 completed that design. M1166 should run a `240`-candidate,
wrong-history-only body-offset pilot over the existing M1161 outcome CSV:

```text
input: runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
max_candidates: 240
target margins: 0.001,0.0025,0.005,0.01,0.02
body offsets: 3 x 3
variants: wrong_matched_history only
```

M1166 is only a pilot diagnostic. It must not convert the surface, claim full
surface pass, rerun mining or the outcome gate, run PPO, promote, use private
holdout, or change actor inputs.

M1049 and M1050 now give three 4096-step guarded PPO public-gate passes from
the current public-gate base. Each raw checkpoint passed exact, proof,
source-diverse, fresh/OOD, and behavior gates while retaining row15
wrong-history failure and row16 normal-history success. M1051 synthesized this
branch, and M1052 promoted the M1049 seed `61049` checkpoint as the current
public-gate base. M1053 synthesized the post-promotion route and selected
current-base source-diverse surface refresh before any medium PPO design.
M1054 designed that refresh, and M1055 mined a strong current-base
wrong-history boundary surface. M1055 did not pass robustness because all
accepted normal margins fell into one `0.01m` bucket. M1056 should audit whether
that is a coarse bucket-edge artifact or true margin-diversity sparsity. M1056
found that `0.005m` and `0.0025m` diagnostic bucket widths both pass, so the
next step is compact objective/replay corpus conversion. M1057 designed that
conversion using the M1056 `0.005m` accepted rows and cross-family replay
sanity. M1058 objective conversion succeeded for all three short-PPO family
checkpoints, but one cross-family replay sanity gate failed by losing three
success-drop rows. M1059 audited this as a missing family-intersection
replay-calibration filter. M1060 designed a deterministic family-intersection
selector. M1061 implemented that selector, filtered the surface to all-family
success-drop rows, and passed objective plus six cross-family replay sanity
gates. The next step is to synthesize M1054-M1061 before adding another narrow
surface-refresh step or moving toward medium PPO. M1062 synthesized M1054-M1061,
closed the `post_short_promotion_surface_refresh` branch, and routed to
first-class public gate integration for the M1061 family-intersection corpus.
M1063 designed that gate integration and admitted a reusable wrapper
implementation before medium PPO. M1064 implemented that wrapper and validated
that the current public-gate base passes all three M1061 source-to-candidate
replay gates. M1065 integrated the wrapper into the full public gate stack and
validated the new proof tier on the current base without PPO. M1066 synthesized
the short-PPO promotion, refreshed proof surface, and expanded proof stack, and
admitted a conservative medium PPO design milestone. A pre-design audit then
found that `combined_active_set_guarded_ppo_smoke` needed to propagate
`family_intersection_pass` from the full public gate into its own proof
classification before medium PPO design can proceed. M1067 fixed that
propagation gap. M1068 then designed one conservative 8192-step medium-ramp PPO
proposal from the current M1049 public-gate base under the expanded exact,
public replay, M1061 family-intersection, source-diverse, fresh/OOD, and
behavior gate stack. M1068 did not train, run PPO, promote, or use private
holdout. The next step is to run exactly one M1069 medium-ramp PPO proposal and
reject it as `proof_washout` if any exact, replay, or family-intersection proof
gate regresses. M1069 ran that single 8192-step proposal. PPO completed and
fresh/OOD plus behavior gates passed, but exact, old public replay,
family-intersection, and source-diverse proof gates failed. The checkpoint is
therefore rejected as `proof_washout`; the next step is an audit before any new
PPO proposal. M1070 completed that audit and classified the failure as coupled
proof washout: exact active-set trust region violation plus wrong-history
branches becoming marginally safe on old public replay, M1061
family-intersection, and source-diverse continuity surfaces. M1070 routes to
projection design before any new PPO. M1071 completed that design and decided
that the next step is not an optimizer yet: first export a source-labeled
failed-row projection corpus covering old public, M1061 family-intersection,
and source-diverse failed rows. M1072 completed that export: 22 source-labeled
rows across eight surfaces were written into a loadable current-family conflict
NPZ. M1073 then ran a no-PPO repair/projection probe using that corpus and
selected `m1031_line_row16x4_s40_a1` as a first-replay-safe candidate. M1074
ran the expanded full public gate for that candidate. Closed-loop proof, M1061
family-intersection, source-diverse, fresh/OOD, and behavior gates all passed,
but the selected candidate failed the allowed-surface contract because it
changed parameter groups outside `actor_mean.` and
`response_context_fusion.0.`. The candidate is rejected as a contract artifact,
not proof washout. M1075 audited the M1073 projection metrics and found 13
exact-pass contract-clean candidates. It selected
`m1031_base_row16x4_s40_a1`, which changes only `actor_mean.` and
`response_context_fusion.0.` parameters and improves exact M297/M270 versus
base. M1076 ran the expanded full public gate for that contract-clean
candidate. Exact, allowed-surface contract, old public replay,
family-intersection, source-diverse, fresh/OOD, and behavior gates all passed.
The candidate is best described as proof-base hardening rather than
medium-PPO performance improvement. The workflow synthesis cadence has fired,
so M1077 synthesized M1068-M1076, closed
`expanded_gate_medium_ppo_readiness`, and opened
`contract_clean_projection_promotion`. M1078 promoted the M1076 candidate as
the current public-gate base, scoped strictly to proof-base hardening. The next
step is M1079: post-promotion synthesis and next-branch selection. M1079 closed
`contract_clean_projection_promotion` and opened
`proof_hardened_base_surface_refresh`. The next step is M1080: design a fresh
current-base source-diverse protected/preference surface refresh before any new
medium PPO. M1080 completed that design with a four-checkpoint family and a
primary `0.005` margin-bucket robustness gate. The next step is M1081: run the
pre-registered surface refresh. M1081 found a non-sparse wrong-history surface
but rejected direct conversion because the primary robustness gate failed on
physical-pair diversity, success-drop fraction, and single-pair dominance. The
next step is M1082: design a retargeted refresh without weakening thresholds.
M1082 completed that design by increasing source coverage, tightening
near-boundary success-drop pressure, and keeping the robustness thresholds
unchanged. M1083 ran the retargeted refresh. It fixed success-drop fraction to
`1.0` and found 626 accepted wrong-history rows, but the primary robustness
gate still failed because rows concentrated into only six physical pairs and
one pair held 30.7% of accepted rows. The next step is M1084: synthesize
M1080-M1083 before another retarget. M1084 closed
`proof_hardened_base_surface_refresh` and opened
`source_balanced_boundary_tooling`. M1085 designed source-budget and
source-balanced boundary export tooling. It rejects post-filtering M1083's
six-pair accepted set and preserves the existing robustness thresholds. The
next step is M1086: implement and test that tooling without PPO, actor
training, promotion, private holdout, or a full new mining run. M1086
implemented source-budget, source-balanced candidate selection, balanced export
marking, artifact writing, and an existing-artifact smoke CLI with 20 focused
tests passing. M1087 added a process-v4 staged training discipline: future
manifests must declare `training_stage`, and any `autodrift.train_ppo` command
must be in `guarded_rl` stage with pre/posttrain, exact/proof, and rollback or
repair admission evidence. M1088 ran the existing-artifact smoke and found that
the pre-boundary source budget is ready, but the old M1083 accepted boundary
export remains limited to six physical pairs. The next step is M1089:
relocation-time source-balanced run design. M1089 completed that design and
found that existing code cannot yet feed source-balanced selected candidates
into relocation replay; the next step is M1090 runner implementation before
any new surface run. M1090 implemented the full source-balanced relocation
runner and process-v5 self-identification evidence discipline; the next step is
M1091, the first full source-balanced boundary relocation replay under
unchanged robustness thresholds. M1091 completed that replay. It fixed the
source-diversity failure but missed the accepted-row threshold by four rows:
`accepted_wrong_rows=76` versus `80` required. All other robustness gates
passed, so the next step is a coverage expansion run rather than threshold
weakening. M1092 expanded selected candidates from `512` to `1024`, and the
source-balanced boundary export passed all robustness gates with `146`
accepted wrong-history rows. The next step is compact objective/replay corpus
conversion design before any future PPO. M1093 found that direct per-checkpoint
conversion would be sparse even though the aggregate M1092 surface is robust,
so the next step was a compactability audit before selecting the conversion
contract. M1094 implemented and ran that audit. It confirmed per-checkpoint
compact conversion remains sparse: at `min_margin_gap=0.0` with no cap,
`proof_current` has only `16` rows and `4` physical pairs, `short61049` has
`17` rows and `8` pairs, `short61050` has `13` rows and `8` pairs, and only
`short61051` passes the compact threshold. Family aggregate compact-dedup is
also row-limited at `75` rows. The raw-retained family aggregate preserves the
M1092 surface with `146` rows, `18` physical pairs, `9` left steps, `4`
checkpoints, `3` targets, success-drop fraction `1.0`, and max pair fraction
`0.136986`. M1094 therefore recommends a new family-aggregate raw-retained
conversion design with replay sanity before objective optimization. The branch
has reached the workflow synthesis cadence. M1095 synthesizes M1085-M1094,
closes `source_balanced_boundary_tooling`, and opens
`family_aggregate_boundary_conversion`. The next step is M1096: design the
family-aggregate raw-retained conversion contract, including source-policy
metadata, duplicate-geometry semantics, replay sanity before objective
optimization, and hidden-state/source-policy handling. M1096 completes that
design. It selects an export-only contract first: keep raw retained rows,
source checkpoint labels/paths, duplicate geometry groups, and a replay plan;
do not write a mixed-source objective NPZ because the existing objective path
intentionally avoids hidden-state space mixing. The next step is M1097:
implement and run the export-only conversion without replay or objective
optimization. M1097 passes the export gate with `146` rows, `18` physical
pairs, `9` left steps, `4` checkpoints, `3` targets, success-drop fraction
`1.0`, and max pair fraction `0.136986`. It writes `replay_plan.json` and keeps
`replay_started=false`, `objective_optimization_started=false`, and
`mixed_source_objective_npz_written=false`. The next step is M1098: design
source-aware replay sanity before any objective optimization. M1098 completes
that design. It will use a wrapper around the existing boundary replay
function, map `row_id = family_row_id`, preserve source and duplicate geometry
metadata, require source-policy source-row gates, and write cross-family replay
reports before any objective optimization. The next step is M1099: implement
and run that replay sanity wrapper. M1099 passes the source-policy source-row
gate for all `146` rows across the four source labels: normal success `146`,
wrong-history success `0`, and success-drop count `146`. Cross-family replay
writes `584` replay rows and `40` summary rows, but reports `14` failed
duplicate geometry groups. These are cross-family report failures, not
source-policy gate failures. The next step is M1100: audit those cross-family
failures before choosing family-intersection, source-specific, or target-base
objective routing. M1100 completes that audit. Source-policy proof remains
valid, but direct mixed-source objective optimization is not defensible because
13 family rows fail under at least one non-source policy. The all-policy
intersection remains broad enough: `133` rows, `14` physical pairs, `4` source
labels, `3` targets, and `9` left steps. M1100 therefore routes to M1101:
design a deterministic family-intersection selector over the M1099
replay-calibrated rows before any objective optimization. M1101 completes that
design. The selector will keep only rows that pass normal-history success and
wrong-history failure under all four family policies, preserve source and
duplicate-geometry metadata, and fail closed unless it keeps at least `80`
rows, `10` physical pairs, `4` source labels, `3` targets, and `8` left steps.
The next step is M1102: implement and run the selector over existing M1097/M1099
artifacts only. M1102 implements and runs that selector. It keeps `133` of
`146` rows and drops the `13` cross-family failure rows. The diversity gate
passes with `14` physical pairs, `4` source labels, `3` targets, `9` left
steps, max physical-pair fraction `0.150376`, and max source-label fraction
`0.368421`. Direct objective conversion is still blocked because the kept rows
retain source checkpoint labels and source-row metrics. The next step is M1103:
design target-policy materialization so objective-ready rows use one target
policy's replay-calibrated margins and hidden-state space. M1103 completes that
design. The first target is `proof_current`; materialized rows should use
`proof_current` replay margins/actions for objective fields while preserving
source metadata under diagnostic fields. The materializer must not replay, train,
optimize, or write an objective NPZ. The next step is M1104: implement and run
that proof-current materializer. M1104 implements and runs it. The materialized
`proof_current` rows pass validation with `133` rows, `133` normal successes,
`0` wrong-history successes, `133` success drops, finite objective margins, `14`
physical pairs, `4` source labels, `3` targets, and `9` left steps. No objective
NPZ is written. The next step is M1105: design the single-checkpoint
boundary-outcome corpus/objective sanity run using these materialized rows.
M1105 completes that design. It explicitly separates raw proof rows (`133`) from
the deduplicated objective corpus input expected from the existing corpus
builder (`68` unique boundary rows). The objective corpus threshold is therefore
`>= 60` unique rows with `>= 10` physical pairs and `3` targets, plus action
reconstruction and objective-sanity gates. The workflow synthesis cadence has
fired, so the next step is M1106: synthesize M1096-M1105 and open the next
branch before running corpus build or objective sanity. M1106 completes that
synthesis. It closes `family_aggregate_boundary_conversion` and opens
`materialized_objective_corpus_sanity`. The supported claim is conversion
readiness for a level2 replay-calibrated proof surface; unsupported claims
remain driver improvement, PPO readiness, promotion, private generalization, and
level3 anticipatory self-identification. The next step is M1107: run the
pre-registered proof-current corpus build and auxiliary objective sanity only.
M1107 passes: `68` corpus rows, `14` physical pairs, `3` targets, zero action
reconstruction error, and `objective_pass=true` across three optimization seeds
with mean validation pairwise accuracy `0.944444`. This is still only auxiliary
objective evidence. The next step is M1108: audit whether a guarded actor-update
design is admissible and define required post-update gates. M1108 completes the
audit. M1107 is strong enough to admit guarded actor-update design only; direct
actor update, PPO, promotion, and driver-improvement claims remain blocked. The
next step is M1109: design an actor-coupling-only update with exact, replay, and
behavior gates before any implementation. M1109 completes that design. The next
probe is allowed to train only `actor_coupling` with frozen `log_std`, use both
rollout action anchors and snippet action anchors, include rejected hidden
states, audit changed parameter prefixes, and pass exact M1107 objective gates
before any replay. PPO, promotion, private holdout, mining, corpus rebuild, and
actor-input changes remain blocked. The next step is M1110: run three
low-drift actor-coupling candidates and classify them before any replay. M1110
runs those three candidates. All improve exact M1107 loss (`0.679117` base;
best `m1110_110901=0.674349`), keep action/snippet anchor MSE below `0.0001`,
and change only `actor_mean.` plus `response_context_fusion.0.` tensors with
`log_std` unchanged. This admits full public gate design only; no replay, PPO,
promotion, or private holdout has run. The next step is M1111: design the full
public gate for primary candidate `m1110_110901`. M1111 completes that design
and requires an exact M1107 recheck plus the expanded full public gate wrapper
before any closed-loop claim. Candidate switching after failure is blocked. The
next step is M1112: run that exact recheck and full public gate for
`m1110_110901` only. M1112 rejects the candidate. Exact M1107 remains improved
and the actor-input/allowed-surface contract passes, but old public replay
passes only `3/6`, M1061 family-intersection passes `0/3`, and source-diverse
replay passes `0/3`. Fresh/OOD and behavior gates pass, so the failure is a
proof-surface washout: wrong-history branches became too safe while aggregate
behavior stayed intact. The next step is M1113: audit existing failure artifacts
before any new update, replay, PPO, promotion, private holdout, or backup
candidate retry. M1113 completes that audit: across failed gates there are `47`
lost success-drop events, `0` normal-lost events, and `47` wrong-history-safe
events. The missing constraint is therefore closed-loop rejected-history
trajectory retention, not normal-history repair. The next step is M1114: design
failed wrong-history retention before any new actor update. M1114 completes
that design. It requires M1115 to export a failed-row registry and target-base
rejected-history trajectory anchors, while keeping short61049/short61050/
short61051 rows as replay diagnostics until target-policy materialization is
designed. Direct short-family hidden-state anchors are forbidden.

```text
decision:
  materialized_failed_wrong_history_retention_design_admit_export
```

M1068 design:

```text
base_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
config: configs/ppo_m1069_expanded_gate_medium_seed61069.json
total_steps: 8192
seed: 61069
promotion: blocked
private_holdout: blocked
next: m1069-v4-public-base-expanded-gate-medium-ppo-smoke
```

M1061 result:

```text
family_intersection_candidates: 305
selected rows: 79
selected physical pairs: 15
selected targets: 3
objective_pass_count: 3 / 3
objective rows: 25, 27, 27
cross-family replay gates: 6 / 6
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

M1062 result:

```text
closed_branch: post_short_promotion_surface_refresh
opened_branch: post_short_promotion_family_gate_integration
next: m1063-v4-public-base-family-intersection-gate-integration-design
scope: gate integration design only before medium PPO
```

M1063 result:

```text
new_gate: M1061 family-intersection public proof gate
future_candidate_gate: 3 source-to-candidate replay gates
source corpora: short61049, short61050, short61051
decision: implement reusable wrapper before medium PPO
next: m1064-v4-public-base-family-intersection-public-gate-implementation
```

M1064 result:

```text
result_class: family_intersection_public_gate_pass
replay_gate_count: 3
replay_gates_passed: 3
failed_replay_gates: []
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1065-v4-public-base-family-intersection-stack-integration
```

M1065 result:

```text
integrated_into: candidate_b_combined_active_set_full_public_gate
new_full_gate_field: family_intersection_pass
failure_route: public_replay_washout / proof_washout
current_base_preflight: passed
replay_gate_count: 3
replay_gates_passed: 3
next: m1066-v4-public-base-pre-medium-ppo-readiness-synthesis
```

M1066 result:

```text
closed_branch: post_short_promotion_family_gate_integration
opened_branch: expanded_gate_medium_ppo_readiness
medium_ppo_design_admitted: true
medium_ppo_run_started: false
required_next_scope: propagation audit/fix before design
next: m1067-v4-public-base-family-gate-propagation-audit
```

M1067 result:

```text
fixed: combined_active_set_guarded_ppo_smoke now consumes family_intersection_pass
proof_pass: public_replay_pass && family_intersection_pass
family gate failure route: public_replay_washout / proof_washout
focused_tests: 12 passed
next: m1068-v4-public-base-expanded-gate-medium-ppo-design
```

M1068 result:

```text
designed_config: configs/ppo_m1069_expanded_gate_medium_seed61069.json
base_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
total_steps: 8192
seed: 61069
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1069-v4-public-base-expanded-gate-medium-ppo-smoke
```

M1069 result:

```text
result_class: combined_active_set_guarded_ppo_exact_retention_regression
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: false
public_replay_pass: false
family_intersection_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
old_public_replay: 3 / 6 passed
family_intersection: 0 / 3 passed
source_diverse: 1 / 3 passed
promoted: false
private_holdout_used: false
next: m1070-v4-public-base-medium-ppo-proof-washout-audit
```

M1070 result:

```text
classification: coupled proof_washout
training_instability: false
actor_contract_violation: false
broad_generalization_regression: false
behavior_regression: false
exact_active_set_failed: true
old_public_replay_failed: true
family_intersection_failed: true
source_diverse_failed: true
decision: route to post-PPO repair/projection design
next: m1071-v4-public-base-medium-ppo-repair-projection-design
```

M1071 result:

```text
design: projection-first repair
base_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
proposal_checkpoint: runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
requires_failed_row_corpus_export: true
ppo_used: false
training_started: false
promoted: false
private_holdout_used: false
next: m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export
```

M1072 result:

```text
result_class: medium_ppo_failed_row_projection_corpus_pass
rows: 22
surfaces: 8
source_policy_count: 4
source_checkpoint_count: 3
corpus_npz: runs/m1072_medium_ppo_failed_row_projection_corpus/current_family_conflict_corpus.npz
failed_row_map_csv: runs/m1072_medium_ppo_failed_row_projection_corpus/failed_row_map.csv
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe
```

M1073 result:

```text
result_class: candidate_b_combined_active_set_projection_first_replay_candidate
selected_candidate_label: m1031_line_row16x4_s40_a1
selected_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
temporal_exact_pass_count: 30
temporal_and_exact_pass_count: 30
m267_m264_first_replay_pass: true
m183_m170_first_replay_pass: true
m267_m264_row15_retained: true
ppo_used: false
promoted: false
private_holdout_used: false
next: m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate
```

M1074 result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_contract_artifact
candidate_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
actor_inputs_changed: false
allowed_surface_contract_pass: false
exact_pass: false
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
next: m1075-v4-public-base-medium-ppo-contract-clean-candidate-audit
```

M1075 result:

```text
result_class: medium_ppo_contract_clean_candidate_audit_pass
projection_rows: 39
exact_pass_contract_clean_rows: 13
selected_candidate_label: m1031_base_row16x4_s40_a1
selected_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
changed_parameter_count: 4
changed_parameter_names: actor_mean.bias actor_mean.weight response_context_fusion.0.bias response_context_fusion.0.weight
exact_gate_pass: true
exact_m297_delta_vs_base: -0.0000852346420288086
exact_m270_delta_vs_base: -0.00006854534149169922
eligible_for_first_replay: true
movement_retained_pass: true
ppo_used: false
actor_training_started: false
promoted: false
private_holdout_used: false
next: m1076-v4-public-base-medium-ppo-contract-clean-full-public-gate
```

M1076 result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
candidate_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
proof_replay_gates_passed: 6 / 6
family_intersection_replay_gates_passed: 3 / 3
source_diverse_replay_gates_passed: 3 / 3
fresh_success_delta_min: 0.0
ood_success_delta: 0.0
behavior_success_delta_min: 0.0
ppo_used: false
actor_training_started: false
promoted: false
private_holdout_used: false
next: m1077-v4-public-base-medium-ppo-readiness-synthesis
```

M1077 result:

```text
result_class: medium_ppo_readiness_synthesis_promote_to_next_branch
synthesis_decision: promote_to_next_branch
closed_branch: expanded_gate_medium_ppo_readiness
opened_branch: contract_clean_projection_promotion
supported: expanded proof stack catches PPO self-ID proof washout; failed-row projection can produce a contract-clean full-gate candidate
falsified: current 8192-step PPO recipe can be repeated directly; broad gates alone are sufficient; M1076 proves medium-PPO performance lift
ppo_used: false
training_started: false
promoted: false
private_holdout_used: false
next: m1078-v4-public-base-contract-clean-projection-promotion-audit
```

M1078 result:

```text
result_class: contract_clean_projection_promoted_public_gate_base
new_public_gate_base: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
previous_public_gate_base: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
scope: public_gate_base_only proof_hardening
medium_ppo_performance_claim: false
long_run_ppo_stability_claim: false
paper_level_generalization_claim: false
training_started: false
ppo_used: false
promoted: true
private_holdout_used: false
next: m1079-v4-public-base-contract-clean-post-promotion-synthesis
```

M1079 result:

```text
result_class: contract_clean_post_promotion_synthesis_promote_to_next_branch
synthesis_decision: promote_to_next_branch
closed_branch: contract_clean_projection_promotion
opened_branch: proof_hardened_base_surface_refresh
current_public_gate_base: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
supported: M1078 promoted a proof-hardened public-gate base; future public-gate work should use that base
falsified: M1078 proves medium-PPO performance improvement or private-holdout evidence
ppo_used: false
training_started: false
promoted: false
private_holdout_used: false
next: m1080-v4-public-base-proof-hardened-surface-refresh-design
```

M1080 result:

```text
result_class: proof_hardened_surface_refresh_design_complete
current_public_gate_base: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
refresh_family: proof_current short61049 short61050 short61051
primary_margin_bucket_width: 0.005
diagnostic_margin_bucket_widths: 0.01 0.0025
min_accepted_wrong_rows: 80
min_physical_pairs: 10
min_left_steps: 5
min_checkpoints: 3
min_targets: 2
training_started: false
ppo_used: false
mining_started: false
promoted: false
private_holdout_used: false
next: m1081-v4-public-base-proof-hardened-surface-refresh
```

M1081 result:

```text
result_class: proof_hardened_surface_refresh_duplicate_dominated
matched_current_accepted_pairs: 3129
matched_current_physical_pairs: 220
boundary_accepted_wrong_history_rows: 252
boundary_wrong_history_success_drop_count: 192
primary_w005_passed: false
primary_w005_decision: reject_duplicate_dominated_boundary_surface
primary_w005_physical_pairs: 9
primary_w005_success_drop_fraction: 0.7619047619
primary_w005_max_rows_per_physical_pair_fraction: 0.253968254
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1082-v4-public-base-proof-hardened-surface-retarget-design
```

M1082 result:

```text
result_class: proof_hardened_surface_retarget_design_complete
retarget_probe_seed_count: 8
retarget_episodes: 60
retarget_max_samples: 2200
retarget_max_pairs_per_left_step: 12
retarget_max_pairs_per_source_obstacle_bucket: 25
retarget_min_base_margin_gap: 0.005
retarget_min_margin_gap: 0.04
retarget_max_normal_margin: 0.04
primary_margin_bucket_width: 0.005
robustness_thresholds_weakened: false
training_started: false
ppo_used: false
mining_started: false
promoted: false
private_holdout_used: false
next: m1083-v4-public-base-proof-hardened-surface-retarget-refresh
```

M1083 result:

```text
result_class: proof_hardened_surface_retarget_duplicate_dominated
matched_current_accepted_pairs: 7257
matched_current_physical_pairs: 371
boundary_accepted_wrong_history_rows: 626
boundary_wrong_history_success_drop_count: 626
primary_w005_passed: false
primary_w005_decision: reject_duplicate_dominated_boundary_surface
primary_w005_physical_pairs: 6
primary_w005_success_drop_fraction: 1.0
primary_w005_max_rows_per_physical_pair_fraction: 0.3067092652
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1084-v4-public-base-proof-hardened-surface-refresh-synthesis
```

M1084 result:

```text
result_class: proof_hardened_surface_refresh_synthesis_promote_to_next_branch
synthesis_decision: promote_to_next_branch
closed_branch: proof_hardened_base_surface_refresh
opened_branch: source_balanced_boundary_tooling
supported: wrong-history sensitivity still exists; M1083 fixed success-drop quality; remaining blocker is source diversity after boundary relocation
falsified: increased matched-current coverage alone fixes robustness; M1083 is directly convertible; physical-pair thresholds should be weakened
training_started: false
ppo_used: false
mining_started: false
promoted: false
private_holdout_used: false
next: m1085-v4-public-base-source-balanced-boundary-tooling-design
```

M1085 result:

```text
result_class: source_balanced_boundary_tooling_design
designed: pre-boundary source budget report; source-balanced candidate selection; relocation-time physical-pair budget accounting; raw plus balanced accepted-row exports; fail-closed robustness classification
preserved_thresholds: true
rejected: post-filtering M1083's six accepted physical pairs; weakening physical-pair or dominance thresholds; another sampling-only retarget before source-balanced export tooling
training_started: false
ppo_used: false
mining_started: false
promoted: false
private_holdout_used: false
next: m1086-v4-public-base-source-balanced-boundary-tooling-implementation
```

M1086 result:

```text
result_class: source_balanced_boundary_tooling_implementation
implemented: source-budget report; physical-pair round-robin candidate selection; balanced export marking; artifact writer; existing-artifact smoke CLI
focused_tests: 20 passed
training_started: false
ppo_used: false
full_new_mining_run: false
promoted: false
private_holdout_used: false
next: m1087-staged-training-discipline-harness-rule
```

M1087 result:

```text
result_class: process_v4_training_stage_rule
added_doc: docs/training-stage-discipline.md
validator_rule: training_stage required from priority 10820; train_ppo requires guarded_rl
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
```

M1088 result:

```text
result_class: source_budget_ready_but_existing_boundary_export_limited
source_budget_ready: true
candidate_wrong_history_rows: 7257
eligible_physical_pairs: 371
selected_candidates: 512
selected_physical_pairs: 370
balanced_exportable_rows: 102
accepted_wrong_physical_pairs: 6 / 10 required
accepted_wrong_success_drop_fraction: 1.0
decision: source_balanced_existing_artifact_smoke_export_limited_route_to_relocation_run_design
training_started: false
ppo_used: false
full_new_mining_run: false
promoted: false
private_holdout_used: false
next: m1089-v4-public-base-source-balanced-relocation-run-design
```

M1089 result:

```text
result_class: source_balanced_relocation_runner_required
existing_artifact_smoke_only: true
wrong_history_relocation_is_not_source_balanced: true
implementation_needed_before_run: true
decision: source_balanced_relocation_design_route_to_runner_implementation
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1090-v4-public-base-source-balanced-relocation-runner-implementation
```

M1090 result:

```text
result_class: source_balanced_relocation_runner_implementation
implemented: full source-balanced relocation runner; fail-closed source-budget and candidate-selection gates before replay; selected-candidate snapshot collection and boundary relocation replay; process-v5 self-ID evidence discipline
focused_tests: 48 passed
research_validation: passed
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
expensive_relocation_run_started: false
next: m1091-v4-public-base-source-balanced-boundary-relocation-run
```

M1091 result:

```text
result_class: source_balanced_relocation_near_row_count_shortfall
run_dir: runs/m1091_source_balanced_boundary_relocation_seed109100
source_budget_ready: true
selected_rows: 512
selected_physical_pairs: 370
relocation_replay_started: true
accepted_wrong_rows: 76 / 80 required
accepted_wrong_physical_pairs: 18 / 10 required
accepted_wrong_left_steps: 9 / 5 required
accepted_wrong_checkpoints: 4 / 3 required
accepted_wrong_targets: 3 / 2 required
accepted_wrong_normal_margin_buckets: 4 / 2 required
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.1578947368
control_accepted_wrong_rows: 0
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1092-v4-public-base-source-balanced-coverage-expansion-run
```

M1092 result:

```text
result_class: source_balanced_coverage_expansion_pass
run_dir: runs/m1092_source_balanced_coverage_expansion_seed109200
source_budget_ready: true
selected_rows: 1024
selected_physical_pairs: 371
relocation_replay_started: true
accepted_wrong_rows: 146 / 80 required
accepted_wrong_physical_pairs: 18 / 10 required
accepted_wrong_left_steps: 9 / 5 required
accepted_wrong_checkpoints: 4 / 3 required
accepted_wrong_targets: 3 / 2 required
accepted_wrong_normal_margin_buckets: 4 / 2 required
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.1369863014
control_accepted_wrong_rows: 0
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1093-v4-public-base-source-balanced-compact-corpus-conversion-design
```

M1093 result:

```text
result_class: source_balanced_compact_conversion_per_checkpoint_sparsity
source_rows: runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
aggregate_accepted_wrong_rows: 146
aggregate_physical_pairs: 18
cap2 compactability:
  proof_current: 8 rows / 4 physical pairs / 2 targets
  short61049: 13 rows / 8 physical pairs / 2 targets
  short61050: 10 rows / 8 physical pairs / 3 targets
  short61051: 20 rows / 13 physical pairs / 3 targets
direct_conversion_admitted: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
next: m1094-v4-public-base-source-balanced-compactability-audit
```

M1058 result:

```text
objective_pass_count: 3 / 3
compact rows per corpus: 27
physical pairs per corpus: 15
targets per corpus: 3
replay_pass_count: 2 / 3
failed replay: short61049_to_61050
success_drop_count: 27 -> 24
```

M1059 failed rows:

```text
row 0 wrong_history_margin: +0.000086
row 1 wrong_history_margin: +0.000259
row 21 wrong_history_margin: +0.000114
```

M1055 result:

```text
accepted_wrong_history_rows: 315
accepted_wrong_physical_pairs: 15
accepted_wrong_left_steps: 7
accepted_wrong_checkpoints: 3
accepted_wrong_targets: 3
accepted_wrong_success_drop_fraction: 1.0
accepted_wrong_normal_margin_buckets: 1
robustness_passed: false
failure: margin_bucket_sparse
```

M1056 result:

```text
bucket_width 0.0100: failed, margin_buckets 1
bucket_width 0.0050: passed, margin_buckets 2
bucket_width 0.0025: passed, margin_buckets 4
classification: coarse_bucket_artifact
```

Current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Previous public-gate base:

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

Important M1040 contract:

```text
allowed changed parameter prefixes:
  actor_mean.
  response_context_fusion.0.

still forbidden:
  actor input config changes
  response/context encoder changes
  GRU/recurrent changes
  critic changes
  log_std changes
```

M1040 result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_candidate
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
proof replay surfaces: 6 / 6
source-diverse replay diagnostics: 3 / 3
fresh public seeds: 103900, 103901
moderate-OOD seed: 103920
behavior seeds: 9505, 9506, 103930, 103931
```

M1044 constraints:

```text
result_class: combined_active_set_guarded_ppo_raw_candidate
raw checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
promoted: false
private_holdout_used: false
```

M1047 result:

```text
base checkpoint: current public-gate base
seeds: 61045, 61046
total_steps per seed: 1024
raw_candidate_pass_count: 2 / 2
training_metrics_finite_count: 2 / 2
actor_inputs_changed_count: 0 / 2
exact_pass_count: 2 / 2
proof_pass_count: 2 / 2
source_diverse_pass_count: 2 / 2
generalization_pass_count: 2 / 2
behavior_pass_count: 2 / 2
promoted: false
private_holdout_used: false
```

M1048 is design only. It should choose a short PPO escalation step count, seed
count, gate stack, and row15/row16 rollback rules. It must not run PPO or use
private holdout.

M1048 result:

```text
short_escalation_total_steps: 4096
short_escalation_seed_count: 1
seed: 61049
promotion: blocked
private_holdout: blocked
next: m1049-v4-public-base-guarded-ppo-short-escalation-smoke
```

M1049 rollback rows:

```text
M267/M264 row15:
  wrong_history_success must remain false
  wrong_history_margin must remain < 0
  success_drop_count must remain 17 / 17

M183/M170 row16:
  normal_success must remain true
  normal_margin must remain > 0
  success_drop_count must remain 17 / 17
```

M1049 result:

```text
result_class: combined_active_set_guarded_ppo_raw_candidate
raw checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
total_steps: 4096
seed: 61049
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
promoted: false
private_holdout_used: false
```

M1050 result:

```text
seeds: 61050, 61051
total_steps per seed: 4096
raw_candidate_pass_count: 2 / 2
training_metrics_finite_count: 2 / 2
actor_inputs_changed_count: 0 / 2
exact_pass_count: 2 / 2
proof_pass_count: 2 / 2
source_diverse_pass_count: 2 / 2
generalization_pass_count: 2 / 2
behavior_pass_count: 2 / 2
promoted: false
private_holdout_used: false
```

M1052 candidate set:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

M1052 promoted:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

### Historical Trace

The branch trace below is retained for context; the live blocker is the M1040
full public gate above.

M927 ran the no-training residual-direction feasibility sweep and found no
alpha/mix candidate. M928 audits this as a residual-bridge trust-region
conflict and routes to policy-level trust-region design. M929 designs an
actor_mean-only objective sanity probe. M930 updates only the policy mean head,
freezes feature/recurrent encoders, critic, and log_std, and finds no
tail-lift candidate inside the conservative alpha window. M931 routes to a
no-training extended-alpha audit of the saved M930 raw actor_mean direction.
M932 finds weak normal-safe low-tail movement but no tail-lift rows. M933
designs one more actor_mean-only low-tail pressure pass, and M934 confirms that
tail lift requires leaving the normal-retention trust region. M935 closes the
actor_mean-only branch. M936 designs a controlled fusion-plus-head surface:
train `actor_mean` plus `response_context_fusion.0`, while keeping
response/context encoders, GRU, critic, log_std, replay, PPO, and promotion
blocked. M937 validates the trainable-surface contract and finds strong
low-tail leverage, but only outside normal retention on the coarse alpha grid.
M938 fine alpha-boundary audit finds no exact overlap, but alpha `0.15` is a
normal-retained near miss. M939 designs a boundary-aware controlled-fusion
objective using differentiable interpolation at alphas `0.125`, `0.150`, and
`0.175`. M940 implements that objective. It reconstructs all rows and changes
only `actor_mean` plus `response_context_fusion.0`, but still finds no strict
candidate: alpha `0.05` is a normal-safe low-tail trend, while alpha `0.075`
tail-lifts just outside normal retention. M941 synthesizes the branch and
allows exactly one no-training micro-alpha audit before any broader actor
update. M942 runs that audit and finds strict objective-level candidates at
alphas `0.0675`, `0.0700`, and `0.0725`. M944 materializes these candidates
and confirms all three remain exact candidates from ordinary checkpoint
loading. M946 then rejects the primary alpha `0.0725` candidate at closed-loop
proof-gate level: five public replay surfaces pass, but M267/M264 regresses
success-drop count `17 -> 13` because rows `6`, `13`, `15`, and `16` become
wrong-history successes. Behavior seeds `9505` and `9506` still pass, so the
blocker is proof washout, not broad behavior regression. M947 audits the
failure and shows all known M944 candidate alphas `0.0675`, `0.0700`, and
`0.0725` fail the same M267/M264 rows. The next route is therefore explicit
rejected-history branch retention, not direct lower-alpha replay. M948 designs
that route as an objective-only controlled-fusion repair: keep only
`actor_mean` and `response_context_fusion.0` trainable, add rejected-branch
action-retention proxies, and require M267/M264 row `6/13/15/16` preflight
before any full replay, PPO, or promotion. M949 implements that probe. It
recovers M267/M264 preflight at alphas `0.005`, `0.010`, and `0.200`, but has
zero exact candidates because low alphas lack tail lift and higher alphas break
normal retention or M267 proof. The current blocker is the M950 objective
conflict audit. M950 classifies this as a real alpha-boundary conflict and
admits exactly one bounded lower-boundary retune before synthesis or trajectory
target export. M951 runs that retune and improves M267 preflight to `13` pass
alphas, but exact candidates remain `0`: proof retention is now mostly solved,
while normal-retention and low-tail lift still do not overlap. The branch must
synthesize before any further local objective or trainable-surface change.
M952 completes that synthesis and pivots to a new branch: first prove that
replay-constrained targets exist inside the current trust region before
widening the actor or training again. M953 designs that no-training audit:
evaluate candidate target actions or short target sequences first through
offline exact low-tail metrics, then through M267/M264 active-row target
preflight, and accept only target families that jointly preserve normal
retention, produce low-tail lift, and keep wrong-history proof rows failing.
M954 should implement this target-space audit before any actor update, PPO, or
promotion. M954 implements the audit and finds zero joint one-step target
candidates. The result is not a wrong-history blocker: M267 target preflight
passes for `55/56` families. The blocker is one-step exact low-tail
feasibility: `exact_target_candidate_count=0`, with the same normal-retention
versus low-tail boundary appearing in target space. M955 should design a
short-horizon low-tail sequence target audit, with threshold sensitivity as a
fallback, before actor training or threshold changes. M955 designs that audit:
retain the first action under M954 thresholds, distribute maneuver intent over
`K in {2,4,6}` prefix actions, evaluate sequence-level low-tail and terminal
margin effects, and keep M267 branch-separated sequence proof retention
mandatory. M956 should implement the no-training sequence audit.
M956 implements it and finds no sequence candidate: all `9/9` sequence
families retain the first action and pass M267 proof preflight, but
`terminal_margin_positive_family_count=0` and every delayed projection slightly
worsens terminal margin. The next blocker is therefore metric grounding: audit
whether the low-tail action-gap target is a target-metric artifact before
relaxing thresholds or training. M957 designs that audit: compare proxy changes
against closed-loop terminal margin effects across away/toward intervention,
simple action-axis, and existing-direction families; separately classify
target-metric artifact, direction-sign suspicion, threshold-only issue, or
target-source refresh. M958 implements it and finds direction-sign suspicion:
away-from-intervention improves the proxy but worsens terminal margin, while
toward-intervention and several action-axis directions improve terminal margin.
M959 should design a no-training target audit for behavior-improving direction
families before any actor training. M959 completes that design. It makes
`throttle_minus`, `brake_plus`, `toward_intervention`, and
`steer_minus_brake_plus` primary target families; keeps `steer_minus` and
`steer_plus_brake_plus` secondary; and marks anti-aligned families such as
`away_from_intervention` diagnostic-only. M960 should implement the no-training
direction-family target audit and require normal retention, terminal-margin
behavior grounding, and M267/M264 proof retention before any actor update.
M960 implements that audit and finds `20` joint direction-target candidates, all
from primary behavior-improving families. The best candidate is
`throttle_minus_amp_0_0080`. M961 should design a branch-separated target export
and actor-fit objective before any training. M961 completes that design: export
accepted primary target rows, branch-separated proof anchors, and retention
anchors before any actor fitting. M962 implements the no-training export:
`1280` accepted direction targets, `160` branch-separated proof targets, `1149`
retention anchors, diagnostic target count `0`, and max direction-family
fraction `0.25`. Because M953-M962 reaches the branch synthesis cadence, M963
should synthesize this branch before actor-fit continuation. M963 completes the
synthesis and promotes to a new branch,
`v4_public_base_direction_target_actor_fit`. M964 should run the first
objective-only actor-fit probe on the exported M962 targets while keeping PPO,
promotion, private holdout, and actor-input changes blocked. M964 completes
that probe and finds `5` objective-level candidate alphas. It changes only
`actor_mean`; direction-target MSE improves, M267/M264 active preflight passes,
and retention/proof anchors remain within tolerance. M965 should design the
public replay gate before any PPO or promotion. M965 completes that design:
rank `alpha_1_0` primary, run M267/M264 full-surface preflight over candidate
alphas, then run six public replay surfaces, behavior seeds `9505/9506`, and
diagnostics before any PPO or promotion. M966 should implement that no-training
gate. M966 implements it and passes: all `5/5` M964 alphas pass M267/M264
full-surface preflight, the highest-ranked `alpha=1.0` candidate is selected,
all six public replay surfaces pass, source-diverse protected diagnostics pass,
behavior seeds `9505/9506` retain baseline success, and reset/zero-all ordering
is retained. Training, PPO, promotion, private holdout, and actor-input changes
remain blocked. M967 should design the promotion/generalization protocol before
alpha `1.0` can replace the public-gate base or be used for PPO continuation.
M967 completes that design and separates proof retention, fresh public
randomized generalization, behavior/ablation retention, holdout discipline, and
promotion decision. M968 should implement the no-training comparison gate before
any PPO or promotion. M968 implements the gate and classifies alpha `1.0` as a
promotion-gate candidate: public proof replay passes `6/6`, source-diverse
diagnostics pass, fresh public eval and moderate OOD eval show no material
regression, and behavior seeds `9505/9506/96730/96731` retain reset/zero-all
ordering. M969 should audit whether alpha `1.0` becomes the new public-gate base.
M969 promotes alpha `1.0` as the new public-gate base and routes to M970
post-promotion synthesis before any PPO continuation. M970 synthesizes
M964-M969, keeps the public-gate overfit risk at moderate, and opens
`v4_public_base_post_promotion_guarded_ppo_readiness`. M971 should design the
guarded PPO readiness protocol before any smoke PPO from alpha `1.0`. M971
completes that design and registers a `1024` step low-LR guarded PPO smoke
proposal initialized and anchored to alpha `1.0`. M972 should run exactly one
smoke proposal and gate it before any promotion or longer PPO. M972 completes
that smoke PPO proposal. PPO runs, training metrics are finite, actor inputs are
unchanged, fresh public/moderate-OOD generalization gates pass, and
behavior/ablation seeds pass. The raw checkpoint is rejected because
M267/M264 proof retention fails: success-drop count regresses `17 -> 15` when
wrong-history rows `6` and `15` become successful. M973 should design exact
post-PPO repair/projection before any longer PPO, scalar auxiliary escalation,
private holdout, or promotion. M973 completes that design: PPO is treated as a
noisy proposal, M297/M270 exact full-corpus no-regression becomes lexicographic
before replay, and M974 should run raw-start, base-start, and line-boundary
repair candidates before first replay gates. M974 completes the no-PPO exact
repair probe. Raw-start repair only restores M267/M264 to `16/17`, with row
`15` still wrong-history-safe. Base-start and line-boundary candidates pass
exact M297/M270 with stronger deltas; the base-start candidate passes
M267/M264 and M183/M170 first replay gates with `17/17` success drops. M975
should design the full public gate before any promotion audit. M975 completes
that design. M976 should run the no-training full public proof/generalization/
behavior gate for the M974 selected candidate and must not promote directly.
M976 passes all public proof, source-diverse diagnostic, fresh/OOD, and
behavior/ablation gates. M977 promotes
`runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt` as the
new public-gate base, with PPO, private holdout, paper-level, and real-vehicle
claims still blocked. M978 should synthesize M972-M977 before any further PPO
continuation or repair branch. M978 completes that synthesis: M972 raw PPO is
classified as proof-washing, exact repair is useful but raw-start repair remains
partial, and public-gate overfit risk is moderate. The next branch is fresh
post-repair surface refresh before any new PPO continuation. M979 designs that
refresh using the current M974 public-gate base, fresh public seed ranges, and
the no-PPO `normal_success_boundary_source_miner`. M980 should run the refresh
and route by accepted-row/source-diversity results. M980 finds a narrow positive
surface: `301` near-boundary preferred snapshots and `30` accepted wrong-history
success-drop rows, but all accepted rows come from one OOD left seed and two
physical pairs. M981 expands source coverage with thresholds unchanged and
finds no accepted rows: `465` near-boundary preferred snapshots, `30000`
candidate rows, `29959` all-action-threshold rows, but
`candidate_wrong_success_rate=1.0` and `candidate_max_margin_gap=0.004490`.
M982 should return to the original M980 OOD seed range with higher candidate
coverage to distinguish a candidate-limit artifact from an isolated OOD pocket.
M982 does that and reproduces the same `30` accepted rows, still one left seed
and two physical pairs. M983 synthesizes M979-M982 and pivots away from
same-family seed mining. The next branch is extreme scenario-family generation:
use currently supported global hidden-dynamics knobs first, and explicitly keep
split-mu, single-tire puncture, half-shaft failure, and corner-specific brake
loss as future simulator extensions rather than current single-track claims.
M984 creates five configs (`low_mu`, `brake_loss`, `lateral_loss`,
`heavy_cg_delay`, `high_speed_close`) and smoke-runs them successfully with
`211` snapshots and `57` near-boundary preferred rows. M985 should run the first
larger source-mining pass across those five families before any training. M985
runs that pass and finds zero accepted rows despite `1137` snapshots, `246`
near-boundary preferred rows, and strong action separation. The next step is
near-cliff mining with `normal_margin_max=0.20`, not training or threshold
relaxation. M986 runs that near-cliff pass and still finds zero accepted rows;
wrong-history continuations remain successful over the 9-step outcome horizon.
M987 should keep the near-cliff filter and increase continuation horizon to 20
steps before deciding whether to recalibrate scenarios or extend simulator
fault modeling. M987 runs the long-horizon audit and still finds zero accepted
rows. M988 synthesizes M984-M987 and pivots to hidden capability-step/fault
event design. M989 completes that design. It reuses the existing
`extreme_dynamics_scenario_corpus` fault-event harness for the M974 public-gate
base, keeps hidden event labels out of actor observations, and keeps per-wheel
or asymmetric faults as future dynamics extensions. M990 creates that small
current-base capability-step config and smoke-runs the existing cross-fault
corpus harness on M974. The smoke passes compatibility with `832` scenarios,
`3289` snapshots, `768` matched pairs, `2` accepted wrong-history rows, and
`132` reset-only rows. This is nonzero but source-narrow signal. M991 scales
the no-training source wave to `3328` scenarios, `16393` snapshots, and `4096`
matched pairs. It finds `0` accepted wrong-history rows and `1380` reset-only
rows, so the M990 wrong-history signal does not repeat under fresh larger
coverage. M992 audits the reset-only rows: wrong-history first-action gaps are
mostly near zero while reset-hidden action and margin gaps are large. The next
task is M993: design a no-training sequence-level action-response mismatch
intervention before implementation. M993 completes that design and admits M994:
implement/run a trace-window sequence intervention probe using M991 reset-only
rows. M994 implements and runs that probe. The corrected result is
`sequence_temporal_history_positive`: `277` accepted temporal sequence rows
across `9` fault pairs and `17` seeds, but `0` accepted cross-fault sequence
rows. M995 audits the claim scope: M994 is temporal-history positive but not
cross-fault wrong-history positive. M996 designs an exact-auditable temporal
sequence corpus export. M997 implements it and exports `277` temporal positive
rows with replay, exact no-update, tensor, and source-diversity sanity passing.
M998 synthesizes M989-M997, closes the capability-step fault generation branch,
and opens `v4_public_base_temporal_sequence_objective` while blocking
cross-fault overclaims. M999 designs the exact temporal sequence objective:
normal-sequence retention, temporal preference separation, and a base-logp
anchor, with disrupted histories used only as contrast conditions. M1000
implements the no-update evaluator and passes exact objective, replay, mask,
weight, and actor-checksum sanity. M1001 designs a tiny exact-gated
actor_mean-only update probe with interpolation and strict trust-region gates.
M1002 implements it and finds `5` exact candidates, with best alpha `0.2`, while
changing only `actor_mean`. M1003 designs the no-training public replay/proof
gate: M267/M264 preflight, six public replay surfaces, behavior seeds, temporal
exact retention, and diagnostics. M1004 implements the gate and rejects all
M1002 candidates at M267/M264 preflight. All `5/5` candidates still pass
exact/contract retention, but `0/5` retain success-drop count. The best exact
candidate alpha `0.2` regresses M267/M264 success-drop count `17 -> 6`; the
smallest alpha `0.01` still regresses `17 -> 15` because rows `6` and `15`
become wrong-history successes. The next task is M1005: audit this proof
washout and decide whether to design a branch-preserving temporal objective
repair or synthesize the branch. M1005 completes that audit and classifies the
failure as localized wrong-history branch lift: normal success and actor
contract are intact, but the exact temporal update makes wrong-history
near-threshold rows safer. The next task is M1006: design a
branch-preserving temporal repair objective before any new actor update. PPO
remains blocked. M1006 completes the design: keep M997 normal temporal sequences
as the only direct behavior target, keep disrupted temporal histories
contrast-only, and add M267/M264 branch-ceiling plus first-action separation
terms for rows `6`, `15`, `11`, and `16`. The next task is M1007: implement a
no-update evaluator for these branch-retention terms before any repaired actor
update. M1007 implements that evaluator, but the result is negative: it is
finite, base-safe, and reproduces M1000, yet the fixed one-step logp/separation
proxy is not sensitive to the smallest proof-washing candidate. Alpha `0.01`
gets branch loss `0.0` despite M1004 showing rows `6` and `15` become
wrong-history successes. The next task is M1008: audit this evaluator
sensitivity failure against closed-loop margin evidence and design a replacement
residual or synthesize the branch. M1008 completes that audit and classifies
M1007 as a margin-slack mismatch: rows `6` and `15` have near-zero wrong-history
margins, so alpha `0.01` action shifts of only `1e-4` can flip closed-loop
terminal margin while fixed one-step logp/separation penalties stay zero. The
harness cadence check now requires synthesis, so the next task is M1009:
temporal sequence objective branch synthesis. It should decide whether the next
ordinary milestone is margin-weighted trust-region design, trajectory-target
export, or stopping the branch. M1009 completes that synthesis and chooses to
continue the branch with margin-weighted rejected-branch trust-region design.
PPO and promotion remain blocked.
M1010 completes the margin-weighted branch trust-region design: rows `6` and
`15` are primary, rows `11` and `16` are secondary, and `margin_floor=1e-4`.
M1011 implements the no-update evaluator and passes: M974 base trust loss is
`0.0`, alpha `0.01` trust loss is `3.529714`, alpha `0.2` trust loss is
`1407.006193`, and rows `6` and `15` contribute `66.45%` of the alpha `0.01`
loss. Row `16` still contributes materially, so the next design should keep it
in the active proof-retention set. The next task is M1012: design an
actor_mean-only repaired temporal update that combines M997 exact temporal
progress with M1011 margin-weighted branch trust retention before any replay,
PPO, or promotion. M1012 completes that design. M1013 should implement the
objective-only actor_mean repair probe with `lambda_wrong_trust` sweep
`{0.001, 0.003, 0.01, 0.03}` and require strict M1011 branch-trust gates before
any M267/M264 replay preflight.
M1013 implements that probe and returns a clean negative result: `10`
interpolated candidates pass exact temporal gates, but `0` pass both exact and
M1011 branch-trust gates. Only `actor_mean.bias` and `actor_mean.weight`
change. PPO and promotion remain unused. The next task is M1014: audit whether
this is a strict-threshold conflict, actor_mean capacity conflict, optimizer
instability, or a sign that the next repair should use projection/line-search
rather than scalar joint training.
M1014 classifies the result as `proof_washout` /
`exact_branch_active_set_conflict`, not contract violation. It chooses a
minimal replay-calibrated trust audit next: materialize selected exact-but-
branch-unsafe M1013 candidates and run only M267/M264 preflight before any
threshold relaxation or new update.
M1015 completes that design. M1016 should materialize Candidate A
`lambda=0.001, alpha=0.2`, Candidate B `lambda=0.03, alpha=0.5`, and Candidate
C `lambda=0.001, alpha=0.5`, then run only M267/M264 preflight as calibration.
M1016 runs that preflight. Candidate A fails rows `6` and `15`; Candidate C
fails rows `6`, `11`, and `15`; Candidate B passes M267/M264 with `17/17`
success drops. Because Candidate B has higher unsigned branch trust loss than
failing Candidate A, the next task is M1017: audit signed/outcome-aware branch
metrics before full replay, threshold relaxation, or another update.
M1017 audits that result and concludes unsigned branch L2 is a detector, not an
ordering gate. Candidate B passes because it moves active wrong-history margins
negative; Candidate A/C fail because they move rows across zero. Candidate B is
not promoted, but it should advance to full public replay design.

## Recent Evidence Line

- M1017 downgrades unsigned branch L2 from ordering gate to diagnostic detector
  and routes Candidate B to full public replay design.
- M1016 shows unsigned branch action L2 is not a reliable ordering metric:
  Candidate B has larger branch-trust loss than Candidate A but passes
  M267/M264 because it moves wrong-history margins in the safe direction.
- M1015 designs the replay-calibrated trust audit: materialize three selected
  M1013 exact candidates and run only M267/M264 preflight, not full replay or
  promotion.
- M1014 audits M1013 and routes to replay-calibrated trust-threshold evidence:
  test selected exact-but-branch-unsafe M1013 candidates on M267/M264 preflight
  before relaxing trust gates or changing the objective.
- M1013 finds `10` exact temporal candidates but no candidate that also stays
  inside the M1011 branch trust region. The failure is `proof_washout`, not
  contract violation, and must be audited before changing thresholds.
- M1012 designs the repaired update: actor_mean-only, M999/M1002 temporal exact
  objective plus M1011 wrong-branch trust residual, with strict trust gates
  before replay. PPO and promotion remain blocked.
- M1011 implements the margin-slack-weighted no-update evaluator. It is
  sensitive to the known alpha `0.01` proof washout while leaving the M974 base
  loss at zero, so the branch can move to repaired actor_mean-only update
  design before replay preflight.
- M1010 designs the margin-slack-weighted rejected-branch trust-region residual
  and explicitly frames it as proof-retention, not deployable wrong-history
  behavior imitation.
- M1009 synthesizes M999-M1008. The branch has real exact temporal-objective
  movement, but public replay retention fails; unweighted fixed one-step branch
  proxies are stopped. The next ordinary task is margin-weighted branch
  trust-region design.
- M1008 audits the failed branch-preserving evaluator. The issue is not row
  reconstruction or actor mutation; the proxy scale is mismatched to near-cliff
  terminal margins. Cadence now requires branch synthesis before the next repair
  design.
- M1007 implements the branch-preserving no-update evaluator. It changes no
  actor parameters and keeps M974 branch loss at zero, but it fails as a repair
  objective proxy: alpha `0.01` remains branch-loss zero despite known
  closed-loop M267/M264 proof washout.
- M1006 designs the branch-preserving temporal repair route. First repair keeps
  only `actor_mean` trainable, requires a no-update evaluator first, and keeps
  wrong-history branches as proof-retention constraints rather than degraded
  behavior targets.
- M1005 audits M1004 as localized wrong-history branch lift proof washout. It
  rejects contract violation, training instability, and broad normal-regression
  explanations, and routes to branch-preserving temporal repair design.
- M1004 implements the public replay gate for M1002 temporal candidates. It
  rejects all candidates before full replay: exact/contract pass count is `5/5`,
  but M267/M264 preflight pass count is `0/5`; alpha `0.01` still loses rows
  `6` and `15`.
- M1003 designs public replay validation for M1002 exact candidates. Candidate
  order is `0.2`, `0.1`, `0.05`, `0.02`, `0.01`; M267/M264 preflight comes
  before six-surface replay.
- M1002 runs the actor_mean-only temporal objective update probe. It changes
  only `actor_mean`, finds five exact candidates, and selects alpha `0.2` as the
  best exact candidate. Public replay and promotion have not run.
- M1001 designs the first temporal objective update probe. It is actor_mean-only
  and exact-gated; public replay, PPO, and promotion remain blocked until a
  candidate passes interpolation trust-region gates.
- M1000 implements the temporal sequence objective evaluator. Exact no-update
  sanity passes on M997: weighted normal NLL `-1.373014`, weighted preference
  loss `0.491601`, weighted logp gap `0.640106`, replay L2 max `0.0`.
- M999 designs the temporal sequence objective. Normal uninterrupted history is
  the only direct behavior target; disrupted temporal histories are contrast-
  only and must not be trained toward degraded actions.
- M998 synthesizes M989-M997 and opens the temporal sequence objective branch.
  Supported: M997 corpus is usable. Blocked: source-diverse cross-fault
  wrong-history self-ID remains unproven.
- M997 exports M994 temporal positives into
  `runs/m997_v4_public_base_temporal_sequence_corpus_export`: `277` positive
  rows, `9` fault pairs, `17` seeds, replay/action sanity exact (`0.0` max
  L2), exact no-update sanity pass, and source-diversity pass. No actor/PPO/
  promotion change occurs.
- M996 designs the M994 temporal sequence corpus export. It requires tensor
  replay sanity, source-diversity gates, row weighting, and exact no-update
  temporal preference diagnostics before any objective update.
- M995 audits M994 and routes to temporal sequence corpus export design. The
  allowed claim is temporal-history dependence in capability-step scenarios;
  the blocked claim remains source-diverse cross-fault wrong-history self-ID.
- M994 implements the trace-window sequence probe. Result:
  `sequence_temporal_history_positive`, not cross-fault positive. Accepted rows
  come from `reset_then_warm_history` and `delayed_capability_history`; cross-
  fault/action-response mismatch variants still have zero accepted rows.
- M993 designs the next no-training probe: trace-window sequence interventions
  over M991 reset-only rows, with delayed history, cross-fault response window,
  action-response mismatch, zero-command history, and reset-then-warm variants.
- M992 shows the reset-only issue is structural: wrong matched histories are
  too compatible (`action_l2 p50=0.0`, wrong margin gap near zero), while
  reset-hidden is a large disruption. Route: sequence-level action-response
  mismatch design.
- M991 scales the capability-step source wave and gets `cross_fault_reset_only`:
  `0` accepted wrong-history rows, `1380` reset-only rows. This blocks training
  and routes to reset-only/sequence-intervention audit.
- M990 passes the hidden capability-step smoke: M974 is compatible with the
  existing fault-event harness, and the run finds `2` accepted wrong-history
  rows plus `132` reset-only rows. This admits a larger no-training source wave,
  not training.
- M989 designs the hidden capability-step route. The current repo already has a
  no-training fault-event harness; the next step is a small M974 current-base
  smoke, not PPO or a new simulator claim.
- M988 synthesizes M984-M987 and pivots to
  `v4_public_base_capability_step_fault_generation`. Config-only global
  extreme mining creates action separation but not outcome-sensitive proof rows.
- M987 extends near-cliff continuation horizon to 20 steps and still finds zero
  accepted rows. This rules out the short-horizon explanation for M986.
- M986 narrows source mining to `normal_margin <= 0.20`. It still finds no
  accepted rows; action separation is live but wrong-history rollouts remain
  successful over 9 continuation steps. Next: long-horizon outcome audit.
- M985 mines all five M984 families at larger scale. The scenario families
  produce broad coverage and action separation, but no wrong-history outcome
  degradation under the broad normal-margin window. Next: terminal-margin
  near-cliff mining.
- M984 creates and smokes five extreme scenario-family configs. All families
  sample valid scenarios and produce artifacts; no actor/PPO/promotion changes
  occur. Next: multi-family source mining.
- M983 synthesizes M979-M982 and pivots to
  `v4_public_base_extreme_scenario_family_generation`. Same-family fresh/OOD
  seed mining found a real but isolated OOD pocket, not a source-diverse proof
  surface.
- M982 returns to the M980 OOD seed range with higher candidate coverage and
  still finds only the same isolated 30 accepted rows. Candidate-pair cap is not
  the main blocker.
- M981 expands fresh/OOD source coverage and finds zero accepted rows under
  unchanged thresholds. Action separation is live, but wrong histories remain
  successful, so the M980 pocket is not broadly reproduced. Next: targeted OOD
  pocket expansion before any training or threshold relaxation.
- M980 finds real wrong-history outcome sensitivity under the M974 public base,
  unlike the old BC5660 M667 run, but the accepted surface is source-narrow.
  Next: expand source coverage without lowering thresholds.
- M979 designs the fresh post-repair surface refresh. It keeps PPO and
  promotion blocked, uses fresh public seed ranges, and requires accepted
  source-diverse wrong-history/preference rows before another PPO branch.
- M978 synthesizes M972-M977 and pivots to
  `v4_public_base_post_repair_surface_refresh`. Next: design fresh current-base
  wrong-history, preference, and source-diverse proof surface refresh before
  more PPO.
- M977 promotes the M974 exact-repaired candidate as the current public-gate
  base after M976 passes full public proof/generalization/behavior gates. This
  is not a private-holdout, paper-level, or real-vehicle claim. Next:
  synthesize M972-M977 before any further PPO continuation.
- M976 runs the no-training full public gate for the M974 candidate. Six public
  replay surfaces pass, source-diverse diagnostics pass, fresh/OOD comparisons
  pass, and behavior ablations retain reset/zero-all ordering.
- M975 designs the full public gate for the M974 exact-repaired candidate.
  M976 must run six public replay surfaces, source-diverse/old-key diagnostics,
  fresh public/moderate-OOD eval, and behavior ablations before any promotion
  audit.
- M974 runs no-PPO exact repair/projection on the M972 raw PPO proposal.
  Raw-start repair is only partial, but the base-start exact repair candidate
  passes exact M297/M270 and first replay gates on M267/M264 and M183/M170.
  Next: design full public proof/generalization/behavior gate before promotion.
- M973 designs exact post-PPO repair/projection for the M972 raw PPO proposal.
  The next probe must run no PPO, generate raw/base/line-boundary candidates,
  require exact M297/M270 no-regression, and only then run M267/M264 plus
  M183/M170 first replay gates.
- M972 runs the first smoke-scale guarded PPO proposal from alpha `1.0`. The
  PPO run completes and fresh/behavior gates pass, but M267/M264 proof
  retention fails because wrong-history rows `6` and `15` become successful;
  success-drop count regresses `17 -> 15`. No checkpoint is promoted. Next:
  design exact post-PPO repair/projection.
- M971 designs guarded PPO readiness from the promoted alpha `1.0` public-gate
  base. It registers `configs/ppo_m972_post_promotion_guarded_smoke.json` and
  requires M972 to run only one smoke PPO proposal, then proof/fresh
  generalization/behavior gates. No promotion or private holdout is allowed.
- M970 synthesizes M964-M969 after alpha `1.0` public-base promotion. It
  supports alpha `1.0` as the current public-gate base, explicitly rejects
  paper-level/private-holdout/real-vehicle claims, and opens
  `v4_public_base_post_promotion_guarded_ppo_readiness`. Next: design guarded
  PPO readiness before any PPO.
- M969 audits M966/M968 evidence and promotes M964 alpha `1.0` as the new
  public-gate base. This supersedes M399 alpha `0.05` for subsequent public-base
  research. PPO, private holdout, paper-level generalization, and real-vehicle
  claims remain blocked. Next: M964-M969 post-promotion synthesis.
- M968 implements the no-training proof/generalization/behavior comparison gate
  for alpha `1.0`. Result:
  `direction_target_actor_fit_promotion_gate_candidate`. It passes public proof
  replay, source-diverse diagnostics, fresh public eval, moderate OOD eval, and
  behavior ablations without training, PPO, private holdout, or promotion. Next:
  promotion audit.
- M967 designs the promotion/generalization layer for the M966
  replay-gate-passing `alpha=1.0` candidate. It keeps PPO and promotion blocked
  and requires M968 to compare the M399 base against alpha `1.0` through proof
  retention, fresh public randomized eval, moderate OOD eval, behavior seeds,
  and reset/zero-all ablations before any promotion audit.
- M966 implements the no-training public replay gate for M964 direction-target
  actor-fit candidates. Result: `direction_target_actor_fit_replay_gate_pass`.
  All `5/5` candidate alphas pass M267/M264 preflight; selected `alpha=1.0`
  passes all six public replay surfaces, source-diverse protected diagnostics,
  and behavior seeds `9505/9506`. The checkpoint is not promoted. Next: design
  proof/generalization/promotion protocol.
- M965 designs the no-training replay gate for M964 candidates. It requires
  M267/M264 full-surface preflight, six public replay surfaces, behavior seeds
  `9505/9506`, reset/zero-all ordering, source-diverse diagnostics, old-key
  diagnostic-only reporting, and actor input contract checks. M966 should
  implement this gate before PPO or promotion.
- M964 runs objective-only actor_mean fitting on M962 targets. Result:
  `direction_target_actor_fit_candidate`, with candidate alphas `0.05`, `0.10`,
  `0.20`, `0.50`, and `1.00`. `alpha=1.00` gives the best target-fit MSE among
  evaluated alphas. M267/M264 active preflight and retention anchors pass at
  all alphas; feature backbone, critic, log_std, and actor inputs are
  unchanged. Next: design no-training public replay gate.
- M963 synthesizes M953-M962 and opens
  `v4_public_base_direction_target_actor_fit`. Supported: corrected
  terminal-margin-improving target directions yield exportable targets; old
  away-from-intervention target directions are behaviorally wrong; proof
  anchors and retention anchors are available. Public-gate overfit risk remains
  moderate to high because the target rows are public and limited. M964 should
  test objective-only actor fit before any PPO or promotion.
- M962 implements the direction-target export. Result:
  `direction_target_export_pass`, with `1280` accepted direction target rows,
  `20` accepted families, `160` branch-separated proof targets, `1149`
  retention anchors, diagnostic target count `0`, and max direction-family
  fraction `0.25`. M963 should synthesize M953-M962 before actor fitting.
- M961 designs direction-target export and actor-fit objective. It keeps
  training, PPO, promotion, private holdout, and actor-input changes blocked.
  The next implementation must export accepted primary M960 target rows,
  branch-separated M267/M264 proof anchors, and retention anchors before actor
  fitting.
- M960 implements the direction-family target audit. It evaluates `50` target
  families from `10` direction families over `64` low-tail rows and active
  M267/M264 rows `6/13/15/16`. Result:
  `low_tail_direction_family_target_audit_joint_candidate`, with `20` joint
  candidates and `20` primary candidates. Best candidate:
  `throttle_minus_amp_0_0080`. Anti-aligned diagnostic-only families are not
  accepted. M961 should design target export and actor-fit objective before
  training.
- M959 designs the low-tail direction-family target audit. It blocks training,
  PPO, promotion, private holdout, threshold relaxation, and actor-input
  changes. Primary target families are `throttle_minus`, `brake_plus`,
  `toward_intervention`, and `steer_minus_brake_plus`, with `steer_minus` and
  `steer_plus_brake_plus` secondary. M960 must implement a no-training audit
  that accepts a direction target only if it passes normal retention,
  terminal-margin behavior grounding, and M267/M264 branch-separated proof
  retention.
- M958 implements the low-tail target metric artifact audit. It evaluates `10`
  direction families over `64` low-tail rows and `1920` row/action cases.
  Result: `low_tail_metric_artifact_audit_direction_sign_suspicion`.
  `away_from_intervention` has `proxy_improved_fraction=1.0` and
  `behavior_improved_fraction=0.0`, while `toward_intervention` has
  `proxy_improved_fraction=0.0` and `behavior_improved_fraction=1.0`.
  Behavior-improving families include `throttle_minus`, `brake_plus`,
  `steer_minus_brake_plus`, `steer_minus`, and `steer_plus_brake_plus`.
  M959 should design a direction-family target audit instead of training on the
  old away-from-intervention target.
- M957 designs the low-tail target-metric artifact audit. It blocks training,
  PPO, promotion, threshold relaxation, and actor-input changes. The audit will
  compare action-gap proxy improvement with terminal-margin improvement across
  away/toward intervention directions, simple action axes, and existing M951
  directions. M958 should implement it and classify whether the current
  low-tail proxy is ungrounded, sign-wrong, threshold-only, or source-limited.
- M956 implements the no-training low-tail sequence target audit. It evaluates
  `9` delayed projection sequence families over `64/498` low-tail rows, with
  horizons `2/4/6` and amplitudes `0.004/0.006/0.008`. All families retain the
  first action and pass M267 proof preflight, but
  `sequence_low_tail_candidate_count=0`,
  `terminal_margin_positive_family_count=0`, and
  `joint_sequence_candidate_count=0`. Delayed action-gap movement worsens
  terminal margin, so M957 should audit low-tail target-metric grounding before
  threshold relaxation or actor training.
- M955 designs the low-tail sequence target audit after M954. It blocks actor
  training, PPO, promotion, actor-input changes, and output-contract changes.
  The design tests whether M954's zero joint one-step candidates are a
  first-action under-specification: `u_0` must still pass M954 first-action
  retention, while `u_1..u_{K-1}` may carry delayed maneuver intent over
  horizons `2/4/6`. M267/M264 proof retention remains branch-separated and
  mandatory. M956 should implement this no-training sequence audit.
- M954 implements the no-training replay-constrained target feasibility audit.
  It reconstructs `1213/1213` rows, keeps training/PPO/promotion off, and
  preserves the P0 actor-input contract. Result:
  `joint_feasible_target_count=0`,
  `exact_target_candidate_count=0`,
  `m267_target_preflight_pass_count=55/56`, and
  `normal_safe_low_tail_trend_count=27`. This shows M267 proof retention is not
  the current target-space bottleneck; one-step target families cannot pass the
  exact low-tail gate under normal retention. M955 should design a short-horizon
  sequence target audit before changing actor parameters or relaxing thresholds.
- M953 designs the replay-constrained target feasibility audit. It explicitly
  blocks training, PPO, promotion, actor-input changes, and encoder/GRU changes.
  The next implementation should compare existing-direction targets, low-tail
  projection targets, branch-separated proof targets, and optional short-horizon
  sequence targets. A target family is only accepted if the same construction
  passes both offline exact target metrics and M267/M264 active-row closed-loop
  target preflight. M954 should implement that no-training audit and classify
  whether joint feasible targets exist.
- M952 synthesizes M942-M951 and closes the local controlled-fusion retuning
  loop. Supported: controlled-fusion has low-tail leverage, M267 preflight is
  live, and rejected-branch retention can protect proof rows. Falsified: exact
  compatibility alone is replay proof; backup alphas are sufficient; one-step
  rejected retention plus one bounded retune can create exact/preflight overlap.
  The branch pivots to `v4_public_base_replay_constrained_target_feasibility`.
  M953 should design a no-training feasibility check for targets satisfying
  normal retention, low-tail lift, and M267 proof retention before any more
  actor updates.
- M951 runs the one bounded lower-boundary retune allowed by M950. M267/M264
  preflight improves to `13` pass alphas, including all alphas `0.005` through
  `0.150`, while forbidden parameters remain unchanged. Exact candidate count
  is still `0`: alphas up to `0.050` retain normal behavior but do not tail-lift,
  and alphas `0.0675+` tail-lift but fail normal retention. This exhausts local
  controlled-fusion objective retuning; M952 must synthesize M942-M951 before
  any further objective, wider trainable surface, full replay, PPO, or
  promotion.
- M950 audits M949 and admits one bounded retune. The rejected-branch proxy is
  live, but M949 trained at inherited high alphas `0.125/0.150/0.175`. Low
  alphas `0.005/0.010` preserve M267 proof but are too small for low-tail lift;
  alphas `0.100+` lift low-tail metrics but fail normal retention. M951 should
  train at `0.0675/0.075/0.090/0.100`, record coefficients, keep M267 preflight
  mandatory, and if it still fails, route to synthesis or trajectory-target
  export rather than another local tweak.
- M949 implements the no-PPO rejected-branch retention probe. It reconstructs
  `1213/1213` objective rows and `4/4` active rejected rows, changes only
  `actor_mean` plus `response_context_fusion.0`, and keeps the P0 actor-input
  contract. M267/M264 preflight passes at alphas `0.005`, `0.010`, and `0.200`,
  proving the rejected-branch retention signal is live. However,
  `exact_candidate_alpha_count=0`: alphas through `0.075` retain normal behavior
  but do not pass tail lift, while alphas `0.100+` pass tail lift but fail
  normal retention. M950 must audit this objective conflict before more local
  tweaks, full replay, PPO, or promotion.
- M948 designs the rejected-branch retention route. It keeps the existing
  controlled-fusion trainable surface only and blocks actor-input changes, GRU
  updates, PPO, and promotion. The active rejected set is M267/M264 rows `6`,
  `13`, `15`, and `16`, with source-diverse rows `15/16` as overlap checks and
  old key `9944` diagnostic-only. M949 should implement a no-PPO objective-only
  probe with wrong-action anchor, wrong-vs-normal separation floor, and
  wrong-direction anchor proxies, then require M267/M264 preflight before full
  replay.
- M947 audits the M946 failure. It confirms a rejected-history branch washout:
  rows `6`, `13`, `15`, and `16` of M267/M264 keep normal success but their
  wrong-history margins cross positive. No-training checks of backup alpha
  `0.0675` and alpha `0.0700` also fail M267/M264 with success-drop count
  `17 -> 13` on the same rows. Source-diverse diagnostics overlap on rows `15`
  and `16`; old key `9944` remains diagnostic-only. M948 should design
  rejected-history branch retention and an M267/M264 preflight gate before any
  repair probe, PPO, or promotion.
- M946 implements the M945 no-training replay/proof gate for M944 alpha
  `0.0725` versus M399. Actor inputs remain unchanged; no training, PPO, or
  promotion occurs. Behavior seeds `9505` and `9506` pass with success delta
  `0.0` and retained `normal >= reset >= zero-all` ordering. Public replay
  surfaces pass `5/6`; M267/M264 fails with success-drop count `17 -> 13`
  because rows `6`, `13`, `15`, and `16` move wrong-history margins positive.
  Source-diverse diagnostics fail on the row `15/16` family and old key `9944`
  stays diagnostic-only. The result class is
  `public_base_controlled_fusion_candidate_replay_gate_proof_washout`, so M947
  must audit the failing surface before any lower-alpha replay, repair
  objective, PPO, or promotion.
- M944 materializes the M942 candidate alphas as ordinary checkpoints and
  re-runs exact metrics from checkpoint loading. `materialized_checkpoint_count=3`,
  `exact_candidate_count=3`, `primary_candidate_exact_pass=true`,
  `backup_candidate_exact_pass_count=2`, and
  `forbidden_parameter_changed=false`. The primary candidate is
  `runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt`.
  M945 designs closed-loop replay/proof retention before any PPO or promotion.
- M945 designs a no-training replay/proof-retention gate for the materialized
  alpha `0.0725` candidate. M946 should evaluate six public replay surfaces,
  source-diverse/old-key diagnostics where compatible, behavior seeds `9505`
  and `9506`, and input-contract retention. PPO and promotion remain blocked.
- M943 designs exact no-update compatibility for the M942 candidates. The
  primary alpha is `0.0725`, with `0.0675` and `0.0700` as backups. M944 should
  materialize all three checkpoints, re-run exact objective metrics from normal
  checkpoint loading at alpha `1.0`, and aggregate whether the primary remains
  an exact candidate. Replay, PPO, private holdout, and promotion remain
  blocked.
- M942 runs the no-training micro-alpha audit of the M940 raw direction.
  It finds `strict_candidate_count=3` at alphas `0.0675`, `0.0700`, and
  `0.0725`, with forbidden parameters unchanged and training/replay/PPO/
  promotion blocked. The primary candidate is alpha `0.0725`
  (`normal_anchor_mse_mean=0.0000038589`,
  `gap_deficit_mean=0.0129708514`, `low_tail_fraction=0.3264633119`).
  M943 should design materialized candidate checkpoints and exact no-update
  compatibility before any replay.
- M941 synthesizes M936-M940 and decides to continue exactly one no-training
  micro-alpha audit of the M940 raw direction. The justification is narrow:
  alpha `0.05` is normal-retained with low-tail trend, while alpha `0.075`
  tail-lifts but barely exceeds the normal-anchor MSE mean threshold. If M942
  finds no strict candidate, the controlled-fusion branch should close before
  touching encoders or GRU.
- M940 implements boundary-alpha controlled-fusion training. It preserves the
  actor-input and trainable-surface contract, but `candidate_alpha_count=0`,
  `boundary_near_miss_count=0`, and result class is
  `public_base_controlled_fusion_boundary_objective_trust_region_conflict`.
  The useful transition is now narrow: alpha `0.05` is normal-retained but not
  tail-lift, while alpha `0.075` tail-lifts but misses normal retention only on
  mean normal-anchor MSE. M941 should synthesize the controlled-fusion branch
  and decide whether a no-training micro-alpha audit is justified.
- M939 designs the boundary-aware controlled-fusion objective. M940 should
  train with differentiable interpolation at boundary alphas `0.125`, `0.150`,
  and `0.175`, keep the trainable surface unchanged, and report strict
  candidate plus boundary near-miss diagnostics. Replay, PPO, and promotion
  remain blocked.
- M938 runs a no-training fine alpha-boundary audit of the M937 raw direction.
  It confirms no exact normal-retained tail-lift overlap, but alpha `0.15`
  is a near miss: normal retention passes, p10/fraction move strongly, and the
  remaining issue is mainly gap-deficit mean. Next route: boundary-aware
  controlled-fusion objective design.
- M937 implements controlled fusion-plus-head training. It reconstructs
  `1213/1213`, changes only `actor_mean` and `response_context_fusion.0`, and
  keeps response/context encoders, GRU, critic, and log_std unchanged. It gets
  strong tail lift at high alpha (`low_tail_fraction` about `0.045` at
  alpha `1.0`) but no coarse-grid alpha satisfies normal retention and
  tail lift together.
- M936 designs the controlled fusion surface. M937 may update only
  `actor_mean` and `response_context_fusion.0`; it must reconstruct
  observation/hidden samples instead of using cached final features, because
  gradients must pass through the fusion layer. Encoders and GRU remain frozen.
- M935 synthesizes M929-M934 and closes the actor_mean-only branch. Supported:
  actor_mean-only tooling is valid and has some low-tail leverage. Falsified:
  conservative actor_mean-only training, larger alpha on M930 raw direction,
  and stronger actor_mean-only pressure are sufficient to produce an admissible
  candidate. Next branch: `v4_public_base_controlled_fusion_surface`.
- M934 implements the stronger actor_mean-only low-tail pressure probe. It
  reconstructs `1213/1213`, joins `122/122`, changes only `actor_mean`, and
  keeps all non-head checksums unchanged. It gets normal-safe low-tail trend at
  alphas `0.05`, `0.10`, and `0.20`, but tail lift appears only at alpha `1.0`
  where normal retention fails. Result:
  `public_base_policy_head_trust_region_probe_trust_region_conflict`.
- M933 designs a stronger actor_mean-only low-tail pressure implementation.
  The trainable surface remains only `actor_mean`; feature/recurrent encoders,
  critic, log_std, replay, PPO, and promotion stay blocked. M934 should report
  strict candidate, low-tail-effect candidate, target-tolerance candidate, and
  normal-safe trend diagnostics.
- M932 audits the saved M930 raw actor_mean direction through alpha `1.0` with
  no training. The raw direction remains normal-safe and weakly improves
  low-tail metrics (`low_tail_fraction` from about `0.41055` to `0.39736`),
  but `tail_lift_rows=0`, `candidate_alpha_count=0`, and strict target MSE
  worsens slightly. Next route: stronger actor_mean-only low-tail pressure
  design before any broader actor update.
- M931 audits M930 and blocks a premature broader actor update. The key
  distinction is that M930 proves no admissible tail lift inside the registered
  conservative alpha window, but does not yet prove the raw actor-head direction
  lacks tail-lift leverage. This routed to M932's saved-raw-direction audit.
- M930 implements the actor_mean-only trust-region probe. It reconstructs
  `1213/1213`, joins `122/122` targets, changes only `actor_mean`, and keeps
  feature backbone, critic, log_std, and all non-head checksums unchanged.
  Result: `candidate_alpha_count=0` and
  `public_base_policy_head_trust_region_probe_no_tail_lift`. No exact
  compatibility, replay, PPO, or promotion occurred.
- M929 designs the policy-level trust-region route. M930 may update only
  `actor_mean` while freezing feature/recurrent encoders, critic, and log_std.
  It must use objective sanity and interpolation gates before any replay, PPO,
  or promotion. The P0 human-view no-wheel input contract remains unchanged.
- M928 audits M927 as `promotion_gate_failure`: existing residual directions
  can produce tail lift or normal retention, but not both at the same alpha/mix
  point. The next route is `v4_public_base_policy_level_trust_region`, not
  another residual-head objective variant.
- M927 implements no-training residual direction feasibility. It reconstructs
  `1213/1213`, joins `122/122` targets, evaluates `121` alpha/mix rows, and
  finds `feasible_candidate_count=0`. There are `22` tail-lift rows but
  `0` normal-retained tail-lift rows. No training, exact compatibility, replay,
  PPO, or promotion occurred.
- M926 designs no-training residual-direction feasibility. M927 should load the
  existing M921 and M924 residual heads, evaluate mixtures
  `(1-w) * residual_M921 + w * residual_M924` across alpha values, and decide
  whether any existing direction can satisfy normal-retention, low-tail lift,
  and target-action gates before more training.
- M925 synthesizes the `v4_public_base_target_regeneration` branch. Supported:
  M399-rooted source-expanded target generation works and joins cleanly.
  Falsified: strict low-tail-only mining, target-action imitation alone, and
  direct low-tail objective pressure alone are sufficient to admit a
  normal-retaining residual candidate. Next branch:
  `v4_public_base_trust_region_feasibility`.
- M924 implements alpha-aware low-tail residual training. It reconstructs
  `1213/1213`, joins `122/122` targets, preserves the M399 actor checksum, and
  trains only a `feature_dim=128` residual head. Result:
  `candidate_alpha_count=0`. Low-tail metrics improve strongly, but useful
  alphas violate normal retention and target-action MSE worsens. No exact
  compatibility, replay, PPO, or promotion occurred.
- M923 designs an alpha-aware low-tail objective. M924 should train at
  normal-retaining alphas `0.20` and `0.35`, target low-tail gap floor,
  low-tail deficit, and soft low-tail fraction directly, and keep M919 target
  action imitation as an auxiliary rather than the only main objective. Exact
  compatibility, replay, PPO, and promotion remain blocked.
- M922 audits M921 as an objective-gate negative. The residual direction
  improves target-action MSE and moves low-tail metrics in the right direction
  at larger alphas, but normal-retaining alphas do not produce enough tail
  lift. The failure is classified as `objective_overfit`, not reconstruction,
  target-join, actor-contract, or training-instability failure. Route:
  alpha-aware low-tail objective design.
- M921 implements regenerated-target residual-head training. It reconstructs
  `1213/1213`, joins `122/122` M919 targets, trains a `feature_dim=128`
  residual head, and keeps the M399 actor checksum unchanged. Result:
  `candidate_alpha_count=0`. Alpha `1.0` improves target MSE and low-tail
  metrics but fails normal retention; alpha `0.35` keeps normal retention but
  fails tail lift. No exact compatibility, replay, PPO, or promotion occurred.
- M920 designs the regenerated-target residual objective. M921 may train only a
  `feature_dim=128` residual head on frozen M399 features using M919 target
  actions, while measuring normal-retention over the full `1213` reconstructed
  rows. Candidate alphas must improve M912 low-tail p10/deficit/fraction and
  target-action MSE while keeping normal action drift inside registered bounds.
- M919 implements expanded target regeneration. It joins M909 near-base
  objective rows with M912 low-tail labels, adds near-tail source coverage, and
  passes all registered target gates: `accepted_targets=122`,
  `strict_low_tail_accepted_targets=103`, `distinct_seeds=26`,
  `distinct_fault_family_pairs=14`, and
  `max_fault_family_pair_fraction=0.19672131147540983`. Actor checksum remains
  unchanged, with no training, exact compatibility, replay, PPO, or promotion.
- M918 designs target source expansion. M919 should join M909 near-base
  objective rows with M912 strict low-tail labels, add near-tail source
  coverage from the full M755 corpus, and accept a regenerated target corpus
  only if it reaches at least `96` accepted targets, at least `60` strict
  low-tail accepted targets, at least `24` seeds, at least `10`
  fault-family pairs, and `max_fault_family_pair_fraction <= 0.25`.
- M917 implements no-training M399 target regeneration over the strict M912
  low-tail source. It reconstructs `67/67` selected sources and accepts
  `67/67` local targets, with no actor parameter change and no training,
  replay, PPO, or promotion. It fails the pre-registered source gates:
  `accepted_targets=67 < 80`, `distinct_seeds=19 < 24`, and
  `max_fault_family_pair_fraction=0.3582089552238806 > 0.25`. The strict
  low-tail input itself has only `21` distinct seeds, so the next route is
  source expansion rather than residual training.
- M916 designs target regeneration. M917 should select up to `256`
  source-diverse low-tail states, search bounded local action overrides around
  the M399 base action, accept only targets with bounded action drift and
  low-tail/deficit improvement, and require at least `80` accepted targets
  across at least `8` fault-family pairs before any residual objective design.
- M915 synthesizes M905-M914 and opens `v4_public_base_target_regeneration`.
  Supported: direct M761 residual reuse is invalid for M399; M399 can train a
  128-dim residual head; M755/M758/M761 targets do not yield a normal-retaining
  public-base residual candidate; low-tail deficit is broad. Next is M399-rooted
  target regeneration design.
- M914 implements tail-weighted residual probe. It reconstructs `1213/1213`
  rows, joins all low-tail keys, keeps M399 actor checksum unchanged, and trains
  a `feature_dim=128` residual head. `candidate_alpha_count=0`: alpha `1.0`
  passes tail-lift and reduces low-tail fraction to `0.317395`, but normal
  retention fails; all normal-retaining alphas fail tail-lift. Route:
  target regeneration design.
- M913 designs M399 tail-weighted residual objective. The next probe must join
  M912 low-tail rows back to M755 rows, train residual head only, keep M399
  actor checksum unchanged, and admit a candidate only if gap p10 improves by
  at least `0.004`, deficit mean improves by at least `0.002`, and low-tail
  fraction drops by at least `0.05` while normal retention passes.
- M912 implements and runs deterministic recalibration audit. It does not load
  model checkpoints or train. At near-base alpha `0.02`, M399 has `498/1213`
  low-tail rows, low-tail fraction `0.4105523495465787`, and `17` distinct
  fault-family pairs. Route decision:
  `public_base_tail_weighted_objective_design`.
- M911 designs deterministic public-base sequence recalibration. It uses M909
  alpha `0.02` only as a near-base diagnostic, exports low-tail rows where
  `normal_intervention_gap < 0.021141` or `gap_deficit > 0.02`, summarizes
  fault/variant/source groups, and chooses one route: tail-weighted objective,
  target regeneration, or residual-free sanity. No training or exact execution.
- M910 audits M909 no-gap-lift. Compared with M761, M909 has no admitted alpha:
  its mean gap is already large (`~0.144-0.150`), but low-tail p10 remains low
  (`~0.007-0.012`) and larger alphas break normal retention before fixing the
  deficit. The route is M399-specific sequence objective recalibration, not
  direct M880 exact use of the M909 residual head.
- M909 trains only a residual head on frozen M399 features. Compatibility
  succeeds: `1213/1213` rows reconstruct, metadata missing is `0`, residual
  `feature_dim=128`, residual parameters `8451`, and actor checksum is
  unchanged. Objective admissibility fails with `candidate_alpha_count=0`;
  small alphas keep normal retention but fail gap lift, while large alphas
  break normal retention. No replay/PPO/actor update/promotion occurred.
- M908 designs the public-base-compatible residual-head route. It reuses the
  M761-style sequence objective probe with M399 frozen, expects a new
  `feature_dim=128` residual head with `8451` parameters, and requires exact
  no-update M880 compatibility only after M909 passes. Force-loading M761,
  padding/truncation, actor-input edits, replay, PPO, and promotion are
  rejected.
- M907 audits the M906 mismatch. M399 public base and M568 diagnostic BC both
  use `human_view_online_gru`, `obs_dim=72`, `response_dim=12`, and
  `context_dim=60`, but M399 actor_feature_dim is `128` while M568/M761 are
  `64`. M761 is therefore M568-feature-specific. Force-loading, padding,
  truncation, or actor-input edits are rejected; next is a 128-dim public-base
  residual-head design.
- M906 attempts exact no-update pair-delta sanity on M399 public base and fails
  before reconstruction: `residual feature_dim=64 does not match actor
  feature_dim=128`. No training/replay/PPO/promotion occurred. Direct
  public-base use of the M761 residual head is blocked; next is feature-dim
  compatibility audit.
- M905 designs public-base integration readiness. It keeps current public-gate
  base `runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt` separate from
  M568 diagnostic BC and M568-rooted raw candidates. M906 is exact no-update
  compatibility only: reconstruct `247/247` objective rows, finite exact
  losses, no actor parameter changes, no replay, no PPO, no promotion.
- M904 synthesizes M895-M903. Raw objective-only movement is repeatable,
  proof-safe versus M568, and margin-positive on public proof, m121-style fresh,
  and robust challenge-family diagnostics without success/termination
  regression. Unsupported claims remain success improvement, PPO, direct
  promotion, and public-base integration. Next branch: public-base integration
  readiness.
- M903 passes robust challenge-family benchmarks. Near-threshold robust keeps
  raw success `0.843750` and termination `0.156250`, with clearance deltas
  about `+0.00370`. Late high-energy robust keeps raw success `0.781250` and
  termination `0.218750`, with clearance deltas about `+0.00337`. Seed-delta
  audit shows no success flips. This is a second margin-only public
  generalization positive, not PPO or promotion.
- M902 designs M903 challenge-family benchmark on
  `m451_challenge_near_threshold_robust_zero_relvel` and
  `m451_challenge_late_high_energy_robust_zero_relvel`, `128` episodes each.
  Raw candidates must retain success/termination within `0.01` on each family,
  keep nonnegative clearance on each family, and achieve combined clearance
  delta at least `+0.001`. No PPO or promotion.
- M901 audits M900 as margin-only fresh evidence. Raw candidates retained
  success/termination and exceeded the fresh clearance threshold, but seed-delta
  audit showed no success flips. The next route is a second scenario-family
  design using robust near-threshold and late high-energy challenge configs,
  not public-base integration or PPO.
- M900 runs the no-training fresh benchmark on seeds `9705`/`9706`, `256`
  episodes each. Raw candidates retain success `0.761719` and termination
  `0.238281` versus M568 and pass the clearance threshold: `m886_raw`
  `+0.003236`, `m891_raw` `+0.003250`. Alpha `0.1` movement is about
  `+0.000425`. Seed-delta audit shows no success flips, so this is a
  margin-only fresh public diagnostic pass, not promotion or PPO admission.
- M899 designs M900 fresh/generalization benchmark: seeds `9705`/`9706`,
  `256` episodes each, `configs/m121_human_view_zero_obstacle_relvel.json`,
  and seed-delta audit. Raw candidates must retain success within `-0.005`,
  termination within `+0.005`, and clearance delta at least `+0.002` versus
  M568 to count as useful fresh-distribution movement. No PPO or promotion.
- M898 audits M897 as proof-safe raw scaling evidence and routes to fresh
  generalization design. Supported: raw candidates preserve exact/replay/
  behavior-retention gates while producing about `10x` the alpha `0.1`
  clearance movement. Unsupported: success improvement, broad generalization,
  public-base integration, and PPO safety.
- M897 passes the controlled raw-candidate scaling gate. Both raw candidates
  reconstruct `247/247` exact rows, first replay gates pass `4/4`, full replay
  gates pass `12/12`, and behavior seeds `9505`/`9506` retain success `0.8125`
  and termination `0.1875`. Raw candidates increase clearance by about
  `+0.00488` versus M568, roughly `10x` alpha `0.1`, but still do not improve
  success and slightly reduce return. PPO and promotion remain blocked.
- M896 designs controlled raw-candidate scaling gates. M897 must first run
  exact objective recheck for both raw candidates, then the sensitive replay
  gates `M183/M170` and `M267/M264`, then all six replay/proof surfaces only if
  first gates pass. Behavior seeds `9505`/`9506` are allowed only after full
  replay passes. PPO and promotion remain blocked.
- M895 audits effect size from existing M886/M891/M889/M893 artifacts. Accepted
  alpha `0.1` is repeatable and proof-safe but too small for performance claims:
  action L2 mean is about `1.2e-4`, success and termination are retention ties,
  and behavior clearance movement is about `+0.00049`. Raw candidates are about
  `10x` larger in action movement and keep negative exact holdout deltas, but
  they have no replay evidence and require controlled scaling gates first.
- M894 synthesizes M885-M893 and opens `v4_pair_delta_objective_effect_size`.
  The supported claim is narrow: the no-PPO enriched pair-delta objective-only
  update repeats across two optimizer/minibatch seeds, selects alpha `0.1` both
  times, and preserves exact/replay/behavior proof gates versus M568 for both
  candidates. PPO, promotion, generalization claims, and meaningful driver
  improvement remain blocked because the movement is tiny and all gates are
  public workflow artifacts.
- M893 passes exact recheck, six replay/proof surfaces, and behavior seeds
  `9505`/`9506` for M891 `alpha_0_1` versus M568. Exact recheck reconstructs
  `247/247` rows; all six replay surfaces pass with zero candidate success-drop
  regression. Behavior retention stays at success `0.8125` and termination
  `0.1875`, with aggregate clearance delta `+0.0004909103515290392`. Together
  with M889, this supports two-seed proof retention for the no-PPO
  objective-only recipe, not promotion or PPO safety.
- M892 audits M891 as a clean fresh-seed repeat of the M886 no-PPO
  objective-only result. Both seeds reconstruct `247/247` rows, find `7`
  nonzero exact-admissible interpolation candidates, and select alpha `0.1` as
  the best exact-admissible candidate. This supports objective-level
  repeatability only; replay retention for the M891 repeat is routed to M893.
- M891 repeats the M886 objective-only recipe with seed `10887` and otherwise
  identical settings. It reconstructs `247/247` rows, keeps actor input and M761
  residual head unchanged, and again finds `7` nonzero exact-admissible alphas.
  Best alpha is `0.1` with train weighted-loss delta
  `-0.00008399784564971924`. This supports objective seed repeatability but not
  replay retention for the repeat yet.
- M890 audits M889 as clean but single-seed proof evidence. The supported claim
  is limited to M886 seed-10886 `alpha_0_1` preserving M568-relative exact,
  replay, and behavior-retention gates. Unsupported claims include repeat
  stability, meaningful driver improvement, generalization, PPO safety, and
  public-base promotion. Next is an identical no-PPO objective-only repeat with
  seed `10887`.
- M889 passes the exact/replay/behavior proof-gate stack for M886
  `alpha_0_1.pt` versus M568. Exact recheck reconstructs `247/247` rows and
  keeps exact deltas nonpositive. All six replay/proof surfaces pass with zero
  candidate success-drop regression. Behavior seeds `9505` and `9506` retain
  success `0.8125` and termination `0.1875`; aggregate clearance margin delta
  is `+0.0004892324201435372`. This is proof retention from the M568 diagnostic
  branch, not public-base promotion.
- M888 designs the M889 replay/proof gate stack for
  `runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt`
  versus M568. The order is exact objective recheck, first replay gates
  `M183/M170` and `M267/M264`, all six public replay surfaces, then behavior
  seeds `9505` and `9506` only if replay passes. `alpha_0_05.pt` is the
  fallback. PPO and promotion remain blocked.
- M887 audits the M886 objective-only result as clean exact-objective evidence
  and admits replay/proof gate design. It selects
  `runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt`
  because it is the largest exact-admissible interpolation, has the best train
  objective delta, and keeps exact holdout deltas nonpositive. `alpha_0_05.pt`
  is the fallback. This is still not replay success, PPO admission, or
  promotion.
- M886 implements the first no-PPO enriched pair-delta objective-only probe. It
  reconstructs all `247/247` actor-state tensor rows with `0` missing rows,
  keeps M761 residual-head parameters unchanged, trains only actor-coupling
  parameters for `32` Adam steps, and finds `7` nonzero exact-admissible
  interpolation candidates. The best exact-admissible alpha is `0.1` with train
  weighted-loss delta `-0.00008386037042074079`; raw train delta is
  `-0.0008391377425962521`, but raw is not accepted directly. This is exact
  objective evidence only, not closed-loop replay evidence or promotion.
- M885 designs the first no-PPO objective-only probe. It limits the update to a
  narrow actor-coupling scope, requires exact M883 objective metrics before and
  after update, uses interpolation from base to raw candidate, rejects exact
  holdout regression, and explicitly forbids PPO or promotion.
- M884 synthesizes M875-M883 and promotes to the next branch:
  `v4_pair_delta_objective_probe`. The previous branch successfully transformed
  raw M873 pair-delta rows into deduped splits, enriched action targets, and
  exact no-update objective sanity with full tensor reconstruction. Remaining
  caveats are public-gate overfit risk, no new source holdout, degradation-only
  eval/new-signature splits, and 78055 still absent from new accepted rows.
- M883 implements exact no-update enriched pair-delta objective sanity and
  passes. It reconstructs all `247` expected actor-state rows with `0` missing
  tensors and `0` snapshot rejections, computes finite improvement/degradation
  preference losses, and leaves actor parameters unchanged. This is still not an
  update result, so the next step is M884 branch synthesis before objective-only
  probe work.
- M882 designs exact no-update pair-delta objective sanity. Improvement rows
  should prefer the override action over the normal action under the same
  normal observation/hidden state; degradation rows should prefer the normal
  action over the harmful override. The design requires deterministic actor
  observation and recurrent-hidden reconstruction before logprob losses can be
  computed. No update or PPO is admitted.
- M881 audits M880 enriched corpus as complete enough for design-only objective
  work. The action target blocker is resolved, but the next design must define
  how implementation will recover actor observations and recurrent hidden
  states for exact log-probability objectives. New source holdout remains
  unavailable and the 78055 caveat remains, so actor update, PPO, promotion,
  and learned self-ID claims are still blocked.
- M880 implements no-training target-action enrichment and passes. It enriches
  `247` dedup rows plus all four split files, with `494/494` identity-unique
  joins, zero missing joins, zero ambiguous joins, preserved split labels,
  preserved duplicate metadata, and restored target action fields. The result
  is corpus infrastructure only: new source holdout is still unavailable and
  the 78055 caveat remains, so objective training, actor update, PPO, and
  promotion remain blocked pending M881 audit.
- M879 designs the no-training target-action enrichment route. The important
  correction is that M877's `existing_m867_or_m870` rows recover action targets
  from M867 sequence rows, while `new_m873` rows recover action targets from
  M873 sequence rows. A live identity-key check gives `247/247` unique sequence
  matches, but this is still corpus infrastructure only. Objective training,
  actor update, PPO, and promotion remain blocked until M880 implements and
  audits the enriched artifacts.
- M878 audits M877 transformed corpus as structurally cleaner but not ready for
  loss design. M877 fixed duplicate-axis pressure and split coverage, but
  deduplicated accepted rows do not carry the action target fields needed for a
  future objective, such as normal first action, right first action, and first
  override action. Those fields exist in M873 sequence rows, so the next step is
  no-training target enrichment by joining M877 dedup signatures back to M873
  sequence rows. Objective training, PPO, and promotion remain blocked.
- M877 implements the no-training dedup/resplit transformation. It reduces the
  corpus from `273` raw accepted rows to `247` deduplicated rows and collapses
  new M873 evidence from `39` rows to `13` closed-loop signatures, reducing new
  duplicate factor from `3.0` to `1.0`. The transformed objective train split
  has `124` rows including `8` new rows, eval has `22` rows including `2` new
  rows, source holdout has `98` existing-only rows, and new-signature holdout
  has `3` rows. The `78055` caveat remains and new source holdout is
  unavailable, so objective training, PPO, and promotion remain blocked pending
  audit.
- M876 designs a no-training corpus transformation before objective design. The
  plan deduplicates by closed-loop signature, explicitly excludes retarget-axis
  labels from the dedup key, preserves duplicate metadata, separates existing
  M867/M870 evidence from new M873 evidence, and writes purpose-specific
  objective train/eval/source-holdout plus new-signature holdout splits. The
  design keeps the `78055` caveat visible and makes objective training, PPO,
  and promotion remain blocked until the transformed corpus is implemented and
  audited.
- M875 audits M873 corpus objective readiness and rejects direct objective
  design from the raw split. M873 remains a positive corpus result, but the
  `39` new accepted rows compress to `13` unique closed-loop signatures, all
  have `retarget_delta = 0.0`, and axis labels create a `3.0x` duplication
  factor. The current split is not objective-ready: train has `28` rows and
  `0` new M873 rows, eval has `16` rows all from new M873 rows, and holdout has
  `12` rows and `0` new M873 rows. The `78055` caveat remains. Objective
  training, PPO, and promotion stay blocked.
- M874 synthesizes M864-M873 and closes the
  `v4_pair_delta_boundary_expansion` branch. The branch supports that
  no-training generated boundary data can be converted into real pair-delta
  outcome evidence, and that M873's boundary-preserving normal-window search
  materially improves coverage to `56` balanced rows across `4` left seeds. It
  does not support learned self-ID or promotion, and the `78055` caveat remains.
  Public-gate overfit risk is moderate because all evidence is still corpus
  construction on public surfaces. Objective training, PPO, and promotion
  remain blocked until the new objective-readiness branch audits duplicate
  pressure, source split quality, and caveats.
- M873 implements the no-training boundary-preserving refresh and passes the
  registered coverage gates. Normal-boundary search produces `48`
  accepted-window candidates across all `3` missing seeds and all `3` retarget
  axes. Pair-delta replay over `48` candidates produces `864` sequence rows and
  `39` new accepted pair-delta rows. Combined with existing accepted rows, the
  balanced corpus reaches `56` rows across `4` left seeds, `11` source groups,
  `8` fault families, `27` fault pairs, `2` directions, and `2` axis pairs;
  seed/direction/axis dominance gates pass. Caveat: new accepted rows cover
  `78048` and `78057` but not `78055`, so this is not a complete missing-seed
  solution and not a promotion claim. Actor and M761 checksums are unchanged;
  no training, PPO, or promotion occurs. M874 must synthesize before more work.
- M872 designs a no-training two-stage refresh for missing seeds. Stage A must
  run normal-only boundary search, include the original target point, classify
  wide-safe vs collision/negative vs accepted-window rows, and refine adjacent
  brackets until normal branch satisfies `normal_success == true`,
  `normal_collision == false`, and `0.0 <= normal_margin <= 0.03`. Stage B may
  run pair-delta sequence replay only on accepted normal-window candidates.
  Thresholds remain unchanged, component controls stay diagnostic-only, and
  objective training, PPO, actor mutation, M761 mutation, and promotion remain
  blocked. M873 is admitted as the final targeted implementation before branch
  synthesis.
- M871 audits M870 as clean but not objective-ready. Construction worked and
  targeted all missing seeds, but accepted-row failure is explained by normal
  branch window miss: `0/1728` retarget replay rows satisfy the accepted normal
  branch condition, while `1152` rows are already colliding and `576` rows are
  too safe (`normal_margin > 0.03`). The largest missing-seed margin deltas are
  real diagnostics but occur on non-primary rows, so they cannot become
  objective data. Objective training, PPO, and promotion remain blocked. M872
  should design boundary-preserving missing-seed refresh.
- M870 implements the no-training accepted pair-delta coverage expansion.
  Construction gates pass with `24` target weak-seed rows across missing seeds
  `78048`, `78055`, and `78057`, `96` retarget candidates, and `1728`
  pair-delta sequence replay rows. Actor and M761 checksums are unchanged; no
  training, PPO, or promotion occurs. The result remains source-limited:
  `new_accepted_pair_delta_rows` is `0`, accepted coverage remains the
  original `234` rows, and the balanced corpus has `40` rows but only `2` left
  seeds. Existing accepted rows rebalance better on direction and axis
  dominance (`0.525` each), but missing-seed retargets mostly produce high
  margin deltas only after the normal branch is already colliding, so they
  cannot count as accepted primary pair-delta evidence. M871 should audit
  before more implementation.
- M869 designs a no-training accepted pair-delta coverage expansion route. The
  next implementation should first compute a stronger direction/axis-aware
  rebalance diagnostic over existing M867 accepted rows, then target missing
  accepted seeds `78048`, `78055`, and `78057` by selecting their strongest
  weak pair-delta rows and applying bounded obstacle retargeting plus extended
  pair-delta replay (`hold_steps` `6,8,10`, epsilon L2 `0.075,0.10,0.125`).
  Primary gates require at least `60` accepted rows, `36` balanced rows, at
  least `3` left seeds, at least `2` directions and axis pairs, and dominance
  limits on seed, direction, and axis-pair. Component controls remain
  diagnostic-only; objective training, PPO, and promotion stay blocked.
- M868 audits M867 as real pair-delta outcome evidence but not objective-ready.
  Candidate selection passed, so pair construction is not the active blocker.
  The blocker is accepted outcome sensitivity concentration: accepted rows
  appear only for left seeds `78058` and `78050`; seeds `78048`, `78055`, and
  `78057` have no flips and max absolute margin deltas below `0.003`. The
  balanced corpus has `32` rows but only `2` left seeds, direction dominance
  `0.75`, and axis-pair dominance `0.96875`. M869 should design targeted
  accepted-coverage expansion; objective training, PPO, and promotion remain
  blocked.
- M867 implements the no-training generated-boundary pair-delta refresh.
  Candidate selection passes design gates with `1332` raw pair candidates,
  `118` selected replay pairs, `27` left source groups, `5` left seeds, and
  `9` left fault families. Actual pair-delta replay produces real outcome
  signal: `1416` pair-delta sequence rows, `234` accepted pair-delta rows, and
  `97` success/collision flips. The result is still source-limited because
  the balanced corpus has only `32` rows across `2` left seeds, with direction
  dominance `0.75` and axis-pair dominance `0.96875`. Actor and M761 checksums
  are unchanged; no training, PPO, or promotion occurs. M868 must audit before
  objective design.
- M866 designs the source-aware no-training pair-delta refresh over M864
  combined generated-boundary rows. M867 should convert pairability projection
  into actual sequence outcome evidence by replaying only pair-delta directions
  first, then selecting a balanced pair-delta corpus. Component controls cannot
  satisfy primary gates. Objective training, PPO, actor mutation, M761 mutation,
  and promotion remain blocked.
- M865 audits M864 as clean sparse-useful generated-boundary coverage. Strong
  gates still fail and the surface is axis-concentrated, but sparse gates pass
  with `59` combined boundary-new-to-M844 rows, `27` source groups, `5` seeds,
  `9` fault families, and `365` primary pairability projections. The next route
  is a limited pair-delta refresh design that converts pairability projections
  into actual sequence outcome evidence. PPO, objective training, actor
  mutation, M761 mutation, and promotion remain blocked.
- M864 implements no-training generated-boundary refinement from M860 brackets.
  It selects `25` bracket seeds, including `13` no-M860-boundary brackets,
  reconstructs all `25` snapshots, and produces `42` accepted refined rows.
  Combined M860+M864 coverage reaches `59` boundary-new-to-M844 rows across
  `27` source groups, `5` seeds, and `9` fault families; primary pairability
  projection rises to `365`. This passes sparse generated-boundary gate but not
  strong gate because rows/source groups/seeds remain below strong thresholds.
  Pair-delta replay and PPO remain blocked until audit.
- M863 synthesizes the M853-M862 branch and continues it into one
  generated-boundary refinement implementation. Supported claims are limited to
  no-training data construction: source targeting and snapshot reconstruction
  work, trace diagnostics identify all-safe-wide blocker, closer obstacle
  generation opens `17` new boundary rows, and M860 contains `13`
  refinement-ready wide/negative bracket groups. Unsupported claims remain
  pair-delta outcome evidence, objective-ready self-ID corpus, PPO admission,
  learned policy improvement, or promotion.
- M862 designs the no-training generated-boundary refinement route. The next
  implementation should select M860 same-source same-axis generated
  wide/negative brackets, prioritize groups with no M860 accepted boundary row,
  reconstruct the original M825 temporal snapshot, and replay bounded
  bisection/refinement between endpoint parameters. It must report both
  refined-only accepted rows and combined M860+refined coverage. Pairability
  remains a cheap projection only; pair-delta replay, objective training, PPO,
  actor mutation, M761 mutation, and promotion remain blocked. However, the
  branch has reached the 10-milestone synthesis cadence, so M863 must synthesize
  M853-M862 before another implementation.
- M861 audits M860 as source-limited but refinement-ready. Sparse gates still
  fail (`17 < 32` accepted generated boundary rows, `38 < 40` primary
  pairability rows, `4 < 5` seeds), so pair-delta replay is still blocked. But
  M860 generated replay contains `13` same-source same-axis groups with
  wide/negative brackets and no accepted boundary row, plus `17` groups with
  accepted rows. The next route is therefore no-training generated-boundary
  refinement, not direct pair-delta replay or broad source generation.
- M860 implements the no-training closer obstacle/source generation runner. It
  generates `660` candidate plans from M857 traces across `44` primary source
  groups, `8` seeds, and `9` fault families, reconstructs all requested
  snapshots, and preserves actor/M761 checksums. The run opens `17` accepted
  boundary-new-to-M844 rows and `38` primary pairability projection rows. This
  improves over M857's zero generated boundary rows but remains below sparse
  gate (`32` accepted rows and `40` pairability rows). Accepted rows come only
  from `all_safe_closer_obstacle`; `all_collision_safer_side` and
  half-width-only generation contribute zero accepted rows. M860 is
  `v4_closer_obstacle_source_generation_source_limited`, not pair-delta
  outcome evidence and not PPO admission.
- M859 designs the closer obstacle/source generation route. All-safe-wide
  source axes should generate bounded closer-obstacle extrapolations from their
  closest wide-safe trace rows, with combined tightening for very wide margins.
  All-collision axes should use safer-side candidates and source-step
  neighborhood shifts. M860 may only run normal closed-loop generated candidate
  replay and must not run pair-delta sequence replay.
- M858 audits M857 as valid no-training trace evidence and confirms the primary
  blocker is scenario sampling: boundary-new-to-M844 rows are mostly too
  safe/wide under the tested grids. Recovered controls validate the trace
  runner but cannot count as new-source evidence. The next route is closer
  obstacle/source generation, not wider same-axis replay, objective training, or
  PPO.
- M857 implements the no-training trace diagnostic. It traces `44` primary
  boundary-new-to-M844 sources and `8` recovered controls, reconstructs all
  `52` snapshots, writes `1924` bracket trace rows, and classifies `132`
  primary source-axis rows. The primary cause is `all_safe_wide`:
  `114/132 = 0.863636`; `18/132 = 0.136364` are
  `all_collision_or_negative`; accepted extended boundary axes are `0`. This
  rules out simple same-source axis widening as the best next route and points
  toward closer obstacle/source generation after audit.
- M856 designs a full parameter/outcome trace diagnostic for
  boundary-new-to-M844 source axes. The next implementation must preserve every
  initial and extended grid evaluation over obstacle lateral offset, timing, and
  half-width, then classify no-bracket causes such as all-safe wide margins,
  all-collision traces, extended bracket discovery, mixed/no-adjacent brackets,
  ambiguous/non-finite results, or reconstruction errors. The result is allowed
  to choose a no-training next route only; it is not pair-delta outcome
  evidence and does not admit PPO or promotion.
- M855 audits M854 as a clean source-limited boundary expansion rather than a
  contract failure. Target selection and snapshot reconstruction work, and M854
  expands beyond the M850 active pair-delta source groups. But accepted
  boundary rows are still all from existing M844 boundary sources, while
  boundary-new-to-M844 targets produce only `no_collision_safe_bracket`
  failures. Because M854 did not persist full initial/expansion evaluation
  traces for rejected axes, the next step is trace-first no-bracket diagnosis
  rather than pair-delta replay or PPO.
- M854 implements the no-training pair-delta boundary expansion. Target
  selection is broad: `61` source groups, `12` seeds, and `9` fault families,
  with all `61` requested snapshots reconstructed. Actor and M761 residual-head
  checksums are unchanged and no training, PPO, promotion, or pair-delta
  sequence replay occurs. Boundary bracketing remains source-limited:
  `73` expanded rows produce only `32` accepted successful non-collision
  low-margin rows, covering `17` source groups, `4` seeds, `7` fault families,
  and all `3` boundary axes. Pairability projection is close to sparse-useful
  but below gate with `77` primary rows. The key blocker is that all accepted
  rows are `existing_boundary_recovered`; the `boundary_new_to_m844` targets
  produced only `no_collision_safe_bracket` failures.
- M853 designs the first step of the `v4_pair_delta_boundary_expansion` branch.
  It targets the M850 coverage gap by selecting sources absent from the M850
  balanced pair-delta left side, prioritizing absent seeds and missing fault
  families such as brake/drive authority drops, front/rear lateral authority
  drops, steering fault, and combined fault. M853 explicitly blocks PPO,
  promotion, actor/residual training, and pair-delta sequence replay until
  boundary coverage is audited.
- M806 designs the next no-training boundary-axis expansion. It preserves the
  M804 closed-loop replay discipline but adds obstacle lateral offset,
  source-step neighborhood replay, fault activation micro-sweeps, fault
  severity micro-sweeps, and bracketed distance/width bisection. M806 also adds
  axis-balance gates: at least `3` retarget axes, max axis dominance `0.60`,
  and at least `10` accepted rows from at least `3` axes, while keeping the
  primary `0.0 <= margin <= 0.00005`, alpha `0.2`, source-dominance, checksum,
  no-training, no-PPO, and no-promotion constraints unchanged.
- M805 audits M804 as a clean geometry-only diagnostic. M804 proves the primary
  low-margin window is reachable by closed-loop public geometry retargeting and
  preserves intervention sensitivity, but it is not source-diverse or
  axis-diverse enough for the active-steer guard corpus. M805 rejects
  calibration, PPO, promotion, and threshold weakening, and routes next to
  source-diverse boundary-axis expansion design.
- M804 implements and runs the no-training boundary-window retarget tool.
  Closed-loop retargeting creates `252` accepted primary-window rows with
  margins from `0.000004953` to `0.000046264`, no reconstruction failures, and
  unchanged actor/residual checksums. However every accepted row comes from
  `obstacle_half_width` retargeting; obstacle-distance retargeting produces
  `0` accepted rows. Accepted rows cover only `3` seeds, have max seed
  dominance `0.428571`, and max fault-pair dominance `0.714286`, so M804 is
  classified as `v4_low_margin_boundary_window_geometry_only_diagnostic`, not a
  source-diverse guard pass. Intervention branches on accepted rows still all
  collide, so the local proof mechanism is present but too source/axis
  concentrated for calibration.
- M803 designs the next no-training boundary-window retarget step. It fixes the
  target anchors from M801: `60` collision rows at alpha `0.2` with margins from
  `-0.000572` to `-0.000173` across `2` seeds and `5` source indices, plus the
  nearest `24` successful non-collision diagnostic rows with margins from
  `0.005243` to `0.005768` from `1` seed and `4` source indices. M803 requires
  M804 to rerun closed-loop candidates under public retarget axes such as
  obstacle width, obstacle timing, fault activation step, fault severity, and
  neighboring source step. It keeps alpha `0.2`, the primary
  `0.0 <= margin <= 0.00005` gate, source-diversity requirements, checksum
  invariants, and no-training/no-PPO/no-promotion constraints unchanged.
- M802 audits M801 as a clean no-training diagnostic-band-only result. M801 is
  a broad coverage positive but not a primary low-margin corpus pass: positives
  increased to `4825` across `108` seeds and `18` fault-family pairs, while the
  primary successful non-collision low-margin band `<= 0.00005` remains empty
  and all rows through `<= 0.001` are collisions. M802 classifies the blocker
  as a boundary-window miss and rejects both threshold relaxation and another
  generic broad wave. M803 should design targeted collision/success boundary
  retargeting.
- M801 implements the low-margin refresh config and selector, then runs the
  no-training data pipeline. The source wave expands to `49152` matched pairs
  and `3552` reset-only rows. Sequence intervention exports `4825`
  outcome-critical positives across `108` seeds and `18` fault-family pairs
  with sentinel false positives `0`. Reference residual replay reconstructs
  `4805/4825` rows with actor checksum unchanged and no training/PPO, but raw
  residual alpha `0.2` has normal success `0.987513` and collision `0.012487`.
  The low-margin selector finds `76` collision-free successful diagnostic rows
  at margin `<= 0.2`, but `0` rows in the primary `<= 0.00005` band and `0`
  through `<= 0.001`; all rows at margin `<= 0.001` are collisions. Result
  class is `v4_low_margin_guard_refresh_diagnostic_band_only`. M802 audit is
  required before retargeting or calibration.
- M800 designs the required low-margin corpus refresh after M799 accepted the
  M798 source-diversity blocker. A direct M795 parent replay margin-distribution
  check shows alpha `0.2` normal rows have only `12` rows at margin
  `<= 0.00005`, still `12` at `<= 0.00010`, and only `36` through
  `<= 0.10000`, all from one seed, before the next distinct rows jump to about
  `0.201 m`. M800 therefore rejects a threshold-only fix and requires M801 to
  run a no-training boundary-retargeted source wave, reference residual replay,
  and strict low-margin guard export with at least `80` accepted rows, `8`
  seeds, `8` source indices, `4` fault-family pairs, max seed dominance
  `0.25`, no actor/residual mutation, no PPO, and no promotion.
- M799 audits M798 as a valid process-positive blocker. The low-margin guard
  corpus has only `12` rows and all are variants of one public active source:
  `seed 77025`, `source_index 12`, `step 24`, one fault-family pair, with
  normal margin `+0.000003618`. Diversity is `1` unique seed, `1` unique source
  index, `1` unique fault-family pair, and max seed dominance `1.0`, versus
  required `8`, `8`, `4`, and `0.25`. The audit rejects weakening the
  diversity thresholds or tuning only that active source. It routes next to
  `m800-v4-low-margin-source-diverse-corpus-refresh-design`; residual
  calibration, PPO, and promotion remain blocked.
- M798 extends `v4_normal_margin_residual_calibration.py` with
  `--objective-mode active_steer_guard`, source-diverse low-margin guard row
  selection, low-margin guard artifacts, separability artifacts, and focused
  tests. The run stops before training because the M795 parent replay contains
  only `12` low-margin guard rows, all from the same public active source
  (`seed 77025`, `source_index 12`, `step 24`, one fault-family pair).
  Diversity is `1` unique seed, `1` unique source index, `1` unique
  fault-family pair, and max seed dominance `1.0`, versus required `8`, `8`,
  `4`, and `0.25`. No optimizer, closed-loop replay, PPO, or promotion occurs;
  actor and residual checksums remain unchanged. Result class is
  `v4_active_steer_guard_low_margin_corpus_blocked`.
- M797 designs a no-PPO active steer guard calibration after M795's near miss.
  The design keeps the M568 actor and M761 residual head frozen, keeps the M795
  steer/brake gate with fixed-zero throttle, and adds a stronger workflow:
  source-diverse low-margin guard-row selection, supervised gate separability
  probe, active-steer feasibility projection, then gap retention under the
  guard. It requires exact alpha `0.2` closed-loop gates, M786/M780 references,
  active/source-diverse low-margin steering safety, and steer selectivity
  before any candidate claim. It also adds explicit stop conditions for
  low-margin corpus block and deployable feature separation failure. M798 is
  admitted as implementation diagnostic only; PPO and promotion remain blocked.
- M796 audits M795 as a clean near-miss negative. M795 is not a candidate and
  does not justify PPO because active-source margin and steer selectivity fail.
  However, alpha `0.2` is collision-free and reaches the strong gap reference,
  so the branch is not exhausted. The audit concludes that the next design must
  make active/source-diverse low-margin steering safety lexicographic before
  gap optimization, rather than simply tuning the same objective coefficients.
  M797 is admitted as design-only; PPO and promotion remain blocked.
- M795 extends `v4_normal_margin_residual_calibration.py` with
  `--objective-mode steer_attributed_gate`, a 2146-parameter
  `SteerAttributedResidualGate` that learns steer/brake gates and fixes
  throttle residual to zero, plus focused tests and component gate artifacts.
  The no-PPO run reconstructs `2640/2652` rows, writes `21120` replay rows and
  `10560` objective rows, and confirms M568 actor and M761 residual-head
  checksums unchanged. Result class is
  `v4_steer_attributed_calibration_component_collapse`: alpha `0.2` passes
  strict normal retention and reaches gap mean `0.044080`, slightly above the
  M780 alpha `0.125` gap reference, but active-source margin is only
  `+0.000003618`, below the M786 alpha `0.15` active-margin reference
  `+0.000028246`. Gate evidence explains the miss: active normal steer gate is
  `0.668225`, active intervention steer gate is `0.665187`, so active steer
  contrast is negative instead of selective. M795 is a clean negative and
  admits M796 audit only.
- M794 designs the next no-PPO residual calibration probe around M792's
  component attribution. The design keeps the M568 actor and M761 residual head
  frozen and adds only a deployable-feature
  `SteerAttributedResidualGate(feature) -> [g_steer, g_brake]`, with throttle
  fixed to zero in the primary mode because M792 found no throttle role. The
  objective makes high residual retention the default, applies
  steering-specific suppression to low-normal-margin normal rows and the active
  source, retains steering on intervention-sensitive rows, retains brake as a
  useful-only component, and adds a steer contrast term between low-margin
  normal and intervention rows. Candidate rules keep the M786 alpha `0.15`
  active-margin and gap references plus the M780 alpha `0.125` strong-gap
  reference, and require component selectivity to avoid another scalar/vector
  collapse. M795 is admitted as implementation diagnostic only; PPO and
  promotion remain blocked.
- M793 audits M792 as a clean attribution-only result, not an actionable mask
  or promotion result. M792 preserves no-training invariants, reconstructs
  `2640/2652` rows, and reports no actor or residual-head mutation. The audit
  accepts the main component finding: steering residual is both useful and
  harmful, because it carries intervention gap but also drives the active-source
  alpha `0.2` normal collision; brake is useful-only and throttle is inactive
  on this diagnostic. M793 blocks generic vector-gate continuation, PPO, and
  promotion. It selects a new design-only blocker: steer-attributed
  normal-boundary residual calibration that can suppress harmful steering
  residual on low-normal-margin branches while retaining steering and brake
  contribution where intervention separation is needed.
- M792 adds `src/autodrift/v4_residual_component_sensitivity.py` and focused
  tests, then runs the no-training fixed-mask component sensitivity probe over
  the M773 broader source-holdout corpus. It reconstructs `2640/2652` rows with
  `0` metadata misses and the same `12` unsupported `command_shift_obs`
  rejects, writes `168960` replay rows, `84480` objective rows, `384`
  active-source rows, and confirms the M568 actor and M761 residual-head
  checksums unchanged. No optimizer, PPO, or promotion is used. Result class is
  `v4_residual_component_sensitivity_attribution_found`: no fixed mask is
  actionable, but component roles are identifiable. Steer is both useful and
  harmful: at alpha `0.2`, `steer_only` reaches gap mean `0.044286` but
  collides on the active source with margin `-0.000049`, while
  `throttle_brake` / no-steer stays safe with margin `+0.000112` but gap mean
  only `0.042545`. Brake is useful-only with lower gap, and throttle has no
  meaningful role. M792 therefore blocks PPO/promotion and admits M793 audit
  before any steer-specific objective.
- M791 designs a no-training fixed-mask component sensitivity probe for the
  frozen M761 residual head. The design keeps the M568 actor frozen, keeps the
  M761 residual head frozen, and evaluates masks over steer/throttle/brake
  residual components: none, all, single components, no-component ablations,
  and two-component combinations. It uses alpha ladder `0.0`, `0.125`, `0.15`,
  `0.2`, with alpha `0.2` as the primary diagnostic because it has strong
  intervention gap but active-source normal collision. Required outputs include
  per-mask aggregate metrics, active-source metrics, component replay rows, and
  checksums. Actionable evidence requires strict normal retention plus
  better-than-M786 alpha `0.15` gap and active-source margin; attribution
  evidence can also identify harmful/useful components without producing a
  candidate. M792 is admitted as a no-training implementation only; training,
  PPO, and promotion remain blocked.
- M790 audits M789 as a clean negative. The vector-gate implementation
  preserved actor and residual checksums, trained only the 2179-parameter
  calibrator, and wrote complete artifacts, so the negative is not a tooling
  artifact. The audit confirms that M789 did not beat M786 alpha `0.15`: gap
  mean improved by only about `5e-6`, while active-source margin dropped
  slightly from `+0.000028246` to `+0.000027881`; alpha `0.2` still collides on
  the same active source. The decisive failure is component collapse: final
  normal gates are `0.671292/0.671167/0.671190`, final intervention gates are
  `0.684914/0.684800/0.684820`, and `gate_component_std_mean` is only
  `0.000066`. M790 classifies the primary issue as `objective_overfit`: without
  component attribution, the vector gate found another scalar-like moderate
  scaling solution. It blocks PPO/promotion and selects a no-training residual
  component sensitivity design before another vector objective.
- M789 extends the residual calibration tool with `objective_mode=vector_gate`,
  a 3-output steer/throttle/brake gate, component gate metrics, and vector
  candidate classification, then runs the registered no-PPO probe. It
  reconstructs `2640/2652` rows with `0` metadata misses and the same `12`
  unsupported `command_shift_obs` rejects, writes `21120` replay rows and
  `10560` objective rows, and confirms base actor and M761 residual-head
  checksums unchanged. Only the 2179-parameter vector calibrator is trained.
  Result class is `v4_vector_residual_calibration_component_collapse`:
  candidate count is `0`, strong candidate count is `0`, and limited candidate
  count is `0`. Alpha `0.15` passes strict normal retention and has gap mean
  `0.043403`, but active-source margin `+0.000027881` is slightly below M786
  alpha `0.15`'s `+0.000028246`, so it is not a Pareto improvement. Alpha
  `0.2` has gap mean `0.044438` but still collides on the active source with
  margin `-0.000005`. Final component gates are nearly identical (`normal
  0.671292/0.671167/0.671190`, `intervention
  0.684914/0.684800/0.684820`), with `gate_component_std_mean 0.000066`, so
  the vector gate collapsed to scalar-like behavior. M790 must audit before
  further vector objective, PPO, or promotion.
- M788 designs the next no-PPO residual calibration probe after M787 found
  scalar gating too close to alpha scaling. The design keeps the M568 actor
  frozen, keeps the M761 residual head frozen, and replaces scalar `g(feature)`
  with a per-action-dimension vector gate `g(feature) in [0,1]^3` over
  steer/throttle/brake residual components. It preserves the human-view
  deployable input contract and uses terminal margins/source labels only as
  training-time weights and audit metadata. The primary target is alpha `0.2`:
  a strong candidate must pass strict normal retention, keep active-source
  margin at least M786 alpha `0.15`'s `+0.000028`, and reach intervention gap
  mean at least M780 alpha `0.125`'s `0.044047`. A limited candidate must
  Pareto-improve M786 alpha `0.15`; merely reproducing scalar-gate behavior
  does not count. M789 is admitted as implementation diagnostic only, with PPO
  and promotion blocked.
- M787 audits M786 alpha `0.15` as a valid limited diagnostic positive, not a
  promotion-ready scalar-gate breakthrough. M786 is clean and produces one
  candidate: alpha `0.15` passes strict normal retention and the registered gap
  gate with intervention gap mean `0.043397` and active-source margin
  `+0.000028`. However, alpha `0.2` still fails on the same active source
  (`seed 77025`, `source_index 12`) with margin `-0.000005`, and M786 does not
  outperform M780 alpha `0.125` on intervention gap or margin gap. Gate means
  move from M783's near-half `0.499727/0.499986` to `0.670088/0.683384`, which
  is an improvement but still far from the intended high-default `0.85`
  asymmetric behavior. M787 therefore blocks PPO and promotion and pivots from
  scalar gate tuning to vector residual calibration design.
- M786 extends the frozen-actor frozen-residual calibrator with a high-default
  asymmetric scalar-gate objective and runs the registered no-PPO probe. It
  reconstructs `2640/2652` rows with `0` metadata misses and the same `12`
  unsupported `command_shift_obs` rejects, writes `21120` replay rows and
  `10560` objective rows, and confirms base actor and M761 residual-head
  checksums unchanged. Only the 2113-parameter calibrator is trained. Result
  class is `v4_normal_margin_calibration_candidate` with one candidate alpha:
  `0.15`. Alpha `0.15` keeps normal success `1.0`, collision `0.0`, improves
  intervention action gap mean/p10 to `0.043397/0.026649` versus base
  `0.040348/0.025782`, and keeps active source margin `+0.000028` versus M780
  alpha `0.125` reference `+0.000009`. Alpha `0.2` still fails strict normal
  retention with normal success `0.995455`, collision `0.004545`, and the same
  active source margin crossing to `-0.000005`. Final gate means are
  `0.670088` normal and `0.683384` intervention, so M786 partially escapes
  M783's global half-gate but does not achieve the intended high-default
  asymmetric behavior. M787 must audit before repair, PPO, or promotion.
- M785 designs the second scalar-gate calibration probe. It keeps the M568
  actor and M761 residual head frozen, keeps deploy-time inputs clean, and
  changes the objective so high gate is the default rather than a value the
  optimizer must discover from a `0.5` start. The proposed M786 gate initializes
  at about `0.85`, applies strong suppression only to low-margin normal rows
  and the active boundary source, adds high-default priors for non-low-margin
  normal and intervention rows, requires active/outcome intervention gate
  retention, adds a low-margin gate contrast term, and keeps the original
  intervention gap threshold instead of weakening the M783 near miss. M786
  should evaluate alphas `0.0`, `0.125`, `0.15`, `0.2` and explicitly report
  whether the gate escaped global half-scaling.
- M784 audits M783 as a clean negative. The first calibrator successfully fixed
  normal retention, including active source alpha `0.2` margin `+0.000033`,
  while preserving actor and residual-head checksums. It failed because the
  objective found an almost global half-gate solution (`gate_normal_mean
  0.499727`, `gate_intervention_mean 0.499986`) that under-shot intervention
  signal: alpha `0.2` gap lift is `0.002950`, just below the required `+0.003`,
  and candidate count remains `0`. M784 classifies the issue as
  `objective_overfit` / objective misalignment rather than contract or metric
  artifact, and admits only a high-default asymmetric residual gate design. PPO
  and promotion remain blocked.
- M783 adds `src/autodrift/v4_normal_margin_residual_calibration.py` and focused
  tests, then runs the no-PPO calibrator probe. It reconstructs `2640/2652`
  rows with `0` metadata misses and the same `12` unsupported
  `command_shift_obs` rejects, writes `21120` replay rows and `10560` objective
  rows, and confirms base actor and M761 residual-head checksums unchanged.
  Only the 2113-parameter calibrator is trained. Result class is
  `v4_normal_margin_calibration_no_gap_lift`: the calibrator fixes the active
  normal boundary, with alpha `0.2` normal success `1.0`, collision `0.0`, and
  active source margin `+0.000033`, but no alpha passes the intervention gap
  candidate threshold. Final gates are almost global half-scale
  (`gate_normal_mean 0.499727`, `gate_intervention_mean 0.499986`), so alpha
  `0.2` gap mean improves only to `0.043298` versus base `0.040348`, just below
  the required `+0.003` lift. This is a clean negative for the first gate-only
  objective; no PPO or promotion occurred.
- M782 designs a no-PPO normal-margin-aware residual calibration branch. The
  design keeps the M568 actor frozen, keeps the M761 residual head frozen for
  the first probe, and adds a small deployable-feature gate
  `g(feature) in [0, 1]` so executed residual action becomes
  `base_action + alpha * g(feature) * delta_m761`. Terminal margins, source
  labels, and fault metadata may be used only as training-time weights and
  audit metadata, not deploy-time inputs. The objective combines low-margin
  normal suppression, an explicit `seed 77025/source_index 12` boundary guard,
  intervention gap retention, an intervention gate floor, optional
  hard-negative calibration, and parameter regularization. M783 should evaluate
  alpha `0.0`, `0.125`, `0.15`, `0.2`, verify base actor and M761 residual
  checksums remain unchanged, train only calibrator parameters, and keep
  PPO/promotion blocked.
- M781 audits M780 as a limited lower-alpha feasibility positive. Alpha
  `0.125` preserves strict normal retention and improves intervention
  action-gap and margin-gap metrics on M773, showing that M777's alpha `0.2`
  failure was a narrow residual-scale boundary rather than broad normal
  collapse. The audit blocks promotion and PPO because the active normal source
  margin at alpha `0.125` is only about `9e-6`, and alpha `0.15` already
  crosses into collision on the same source. M781 concludes that more dense
  alpha sweeps would only refine the crossing point; the next scientific
  blocker is how to preserve intervention-sensitive residual corrections while
  explicitly protecting low-margin normal branches.
- M780 runs the pre-registered no-training alpha ladder `0.0`, `0.05`, `0.1`,
  `0.125`, `0.15`, `0.175`, `0.2` on the broader M773 corpus. It reconstructs
  `2640/2652` rows with `0` metadata misses and `12` rejected
  `unsupported_variant:command_shift_obs` rows, writes `36960` replay rows and
  `18480` objective rows, and keeps actor checksum unchanged. Alpha `0.125` is
  the best script-level candidate and the only tested alpha that both passes
  strict normal retention and script closed-loop candidate criteria: normal
  success `1.0`, normal collision `0.0`, intervention action gap mean/p10
  `0.044047/0.026886` versus base `0.040348/0.025782`, margin gap mean
  `0.032352` versus base `0.029796`, and outcome sensitivity retention `1.0`.
  Alphas `0.15`, `0.175`, and `0.2` all collide on the same `seed 77025`,
  `source_index 12` source; the source margin crosses from `+0.000009` at
  alpha `0.125` to `-0.000014` at alpha `0.15`. This supports a narrow
  alpha-boundary interpretation, but alpha `0.125` remains a tiny-margin
  diagnostic candidate, not a promotion result. M781 must audit before repair,
  PPO, or promotion.
- M779 designs the pre-registered no-training alpha-boundary probe admitted by
  M778. It fixes inputs to the M568 diagnostic actor, M761 residual head, M773
  positive/contrast rows, and broader scenario config, and registers alpha
  ladder `0.0`, `0.05`, `0.1`, `0.125`, `0.15`, `0.175`, `0.2`. Alpha `0.2`
  remains the failed reference; lower alphas are not a retroactive pass. M780
  must require strict normal retention (`normal_success_rate == 1.0`,
  `normal_collision_rate == 0.0`), intervention action-gap and margin-gap
  improvement over base, outcome sensitivity retention `1.0`, no metadata
  misses, and no actor/training/PPO/promotion mutation. It must stratify `seed
  77025`, `source_index 12`, `step 24` to decide whether M777 is a narrow
  alpha-boundary issue or requires explicit normal-margin retention/objective
  repair.
- M778 audits M777 as mechanism-positive but strict-normal-retention-failed.
  Alpha `0.2` improves intervention action gap mean/p10 from base
  `0.040348/0.025782` to `0.046317/0.027627`, improves margin gap mean from
  `0.029796` to `0.033918`, and keeps outcome sensitivity retention at `1.0`;
  reconstruction is `2640/2652` with `0` metadata misses and no
  actor/training/PPO/promotion mutation. The stricter M775 gate still fails
  because normal success drops to `0.995455` and normal collision rate becomes
  `0.004545`. All 12 normal collision rows come from one unique source (`seed
  77025`, `source_index 12`, `step 24`, `halfshaft_torque_loss_proxy`,
  `drive_authority_drop->rear_lateral_authority_drop`) duplicated across three
  intervention variants and four horizons. The source has only `+0.000124`
  base margin, so alpha `0.2`'s small first-action drift `0.000380` flips it
  to `-0.000062`. M778 classifies this as `behavior_regression` with
  `scenario_sampling_failure` risk, not a metric artifact or contract
  violation, and admits only a pre-registered lower-alpha normal-boundary probe
  design. PPO and promotion remain blocked.
- M777 runs no-PPO residual replay on the broader M773 corpus. It reconstructs
  `2640/2652` rows with `0` metadata misses and `12` rejected
  `unsupported_variant:command_shift_obs` rows, writes `21120` replay rows and
  `10560` objective rows, and keeps actor checksum unchanged. Script-level
  result_class is `v4_residual_closed_loop_replay_candidate` with candidate
  alphas `0.2`, `0.5`, and `1.0`. Alpha `0.2` improves intervention action gap
  mean from base `0.040348` to `0.046317` and margin gap mean from `0.029796`
  to `0.033918`, with outcome sensitivity retention `1.0`. However, M775's
  stricter normal-retention gate fails: alpha `0.2` normal success is
  `0.995455` and normal collision rate is `0.004545`, caused by one unique
  concentrated normal collision source (`seed 77025`, `source_index 12`,
  `halfshaft_torque_loss_proxy`,
  `drive_authority_drop->rear_lateral_authority_drop`). This is
  mechanism-positive but strict-normal-retention-failed; no training, PPO, or
  promotion occurred. M778 must audit before repair, alpha retuning, PPO, or
  promotion.
- M776 performs the required workflow synthesis for the
  `v4_residual_source_holdout_replay` branch after validation blocked direct
  implementation. The synthesis records that M761-M775 support limited
  continuation: the residual mechanism survived public closed-loop replay and
  sparse fresh-holdout replay, and broader M773 source mining materially
  expanded positives from `995` to `2652` while reducing concentration.
  Unresolved risks remain: M773 misses strict broad gates on fault-family-pair
  count (`17 < 18`) and seed dominance (`0.171569 > 0.15`), hard negatives are
  sparse, and current faults remain `current_model_or_proxy` rather than true
  per-wheel physics. Synthesis decision is `continue`, but only to one limited
  no-PPO broader residual replay implementation. PPO, promotion, and broad
  generalization remain blocked.
- M775 designs a limited no-PPO residual replay on the broader M773 corpus. It
  fixes inputs to the M568 actor checkpoint, the M761 residual head, M773
  `2652` positive rows and contrast rows, and
  `configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json`.
  Alpha `0.2` is pre-registered as the primary conservative candidate, with
  `0.5` and `1.0` diagnostic. M776 must report reconstruction, normal
  retention, intervention action-gap and margin-gap changes, seed/fault-family
  pair/variant/horizon stratification, hard-negative sparsity, and
  `current_model_or_proxy` claim boundary. Alpha retuning, training, PPO,
  residual retraining, actor mutation, and promotion remain blocked. Research
  validation required workflow synthesis before another implementation
  milestone, so M775 now admits M776 synthesis rather than direct replay.
- M774 audits M773 as materially supporting the coverage-limited hypothesis.
  M773 is much broader than M767: `2652` positives versus `995`, `49` positive
  seeds versus `25`, `17` positive fault-family pairs versus `13`, and max seed
  dominance `0.171569` versus `0.247236`. Artifact gates are clean: no
  sentinel positives, no missing normal matches, no missing metadata, and no
  mutation/training/PPO flags. The audit preserves caveats: strict broad gates
  still miss by one fault-family pair (`17 < 18`) and seed dominance
  (`0.171569 > 0.15`), and hard negatives remain incomplete (`2134` hard
  negatives for `2652` positives, `872` positives without hard negatives).
  Because ordinary corpus validity is clean and the strict misses are small
  relative to the coverage improvement, M774 admits only limited no-PPO
  residual replay design on M773 with alpha `0.2` primary. PPO, training, and
  promotion remain blocked.
- M773 runs the broader disjoint-seed source wave from M772. Stage 1 reaches
  `24576` matched pairs and `1389` reset-only rows with result_class
  `cross_fault_reset_only`, compared with M767's `390` reset-only rows. Stage 2
  selects `1024` source rows across `63` seeds and `22` source fault-family
  pairs, finding `2652` sequence outcome-critical rows with `0` sentinel false
  positives and result_class `v4_reset_sequence_outcome_positive`. Stage 3
  exports `2652` clean positives, `2652` normal rows, and `2134` hard-negative
  rows with no sentinel positives, no missing normals, no missing metadata, and
  `current_model_or_proxy` claim boundary. This materially supports the
  coverage-limited hypothesis: M767 had `995` positives, `25` positive seeds,
  `13` positive fault-family pairs, and max seed dominance `0.247236`; M773
  has `2652`, `49`, `17`, and `0.171569`. The ordinary positive corpus gate
  passes, but the result is `v4_sequence_outcome_corpus_hard_negative_sparse`.
  Strict M772 broad gates still miss by one pair (`17 < 18`) and by seed
  dominance (`0.171569 > 0.15`). No residual replay, training, PPO, actor
  mutation, or promotion occurred. M774 must audit before choosing limited
  residual replay versus more source-balancing work.
- M772 designs a broader source-holdout wave to test whether sparse
  extreme-scenario coverage is limiting self-ID evidence. It adds
  `configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json`,
  preserves the v4 fault families and pairing rules, increases `max_pairs` from
  `12288` to `24576`, registers fresh seed range `77024..78047`, and sets M773
  `max_source_rows=1024`. The stricter broader gates are `positive_rows >=
  1500`, `unique_positive_seeds >= 40`,
  `unique_positive_fault_family_pairs >= 18`, `max_positive_seed_dominance <=
  0.15`, and `max_positive_fault_family_pair_dominance <= 0.22`. M772 also
  keeps the model-fidelity boundary explicit: wheel blowout, single-corner
  grip collapse, split-mu, stuck caliper, halfshaft, suspension, and per-wheel
  sensor faults are current-model proxies or future high-fidelity faults, not
  true per-wheel physics claims in the single-track model. It admits M773
  broader corpus generation only; residual replay, PPO, training, and promotion
  remain blocked until audit.
- M771 audits M770 as a limited source-holdout mechanism positive. It supports
  the coverage-mining hypothesis: v4 coverage produced source rows, sequence
  outcome rows, residual objective signal, public closed-loop replay, and now a
  limited disjoint-seed holdout replay where primary alpha `0.2` passes while
  normal branch success remains `995/995`. The audit also preserves caveats:
  the holdout corpus is sparse/source-concentrated and intervention collisions
  concentrate in a few seeds/fault pairs. It selects broader source-holdout
  coverage before stronger generalization, PPO, or promotion claims.
- M770 runs limited no-PPO residual replay on the sparse fresh M767 holdout
  corpus. It reconstructs `995/995` rows with `0` metadata misses and `0`
  rejected rows, writes `7960` replay rows and `3980` objective rows, and keeps
  the base actor checksum unchanged. Result class is
  `v4_residual_closed_loop_replay_candidate`: alpha `0.2`, `0.5`, and `1.0`
  pass. Normal branch success is `995/995` and normal collision rate is `0` for
  all alphas. Primary alpha `0.2` raises intervention action gap mean/p10 from
  base `0.043862/0.039491` to `0.050473/0.045717` and margin gap mean from
  `0.026641` to `0.030329`, with normal first-action drift mean/p95
  `0.000553/0.001208`. Base intervention branch already has `20/995`
  collisions; alpha `0.2` has `23/995`, alpha `1.0` has `31/995`, concentrated
  in a few seeds/fault pairs. No optimizer, training, PPO, promotion, or actor
  mutation occurred.
- M769 designs limited no-PPO residual replay on the sparse fresh M767 corpus.
  It fixes the replay inputs to the M761 residual head and M767
  positive/contrast rows, sets alpha `0.2` as the primary conservative holdout
  alpha, keeps `0.5` and `1.0` diagnostic, and requires M770 to preserve
  sparse-holdout caveats. Residual retraining, alpha tuning from holdout
  results, PPO, and checkpoint promotion remain blocked.
- M768 audits M767 as fresh, clean, but sparse. The corpus fails strict
  exporter gates, but passes M766 limited-holdout minimums: `995` positives,
  `25` seeds, `13` fault-family pairs, max seed dominance `0.247236 <= 0.25`,
  no sentinel positives, no missing normal matches, no metadata misses, and
  `current_model_or_proxy` claim boundary. The audit admits only limited
  residual holdout replay design with caveats; it does not admit broad
  generalization, PPO, or promotion.
- M767 runs the disjoint-seed source-holdout pipeline for seed range
  `76512..77023`. Stage 1 produces `390` reset-only rows with result_class
  `cross_fault_reset_only`. Stage 2 selects `441` source rows and finds `995`
  sequence outcome-critical rows with `0` sentinel false positives, but
  result_class is `v4_reset_source_balance_blocked`. Stage 3 exports `995`
  clean positives, `995` normal rows, and `1028` hard-negative rows with no
  missing metadata, no sentinel positives, and no missing normal matches. The
  fresh corpus gate fails as `v4_sequence_outcome_corpus_sparse`: positive rows
  `995 < 1000`, fault-family pairs `13 < 16`, and max seed dominance
  `0.247236 > 0.2`. No residual replay, training, PPO, promotion, or actor
  mutation occurred.
- M766 designs the fresh source-holdout path. Precheck shows existing artifacts
  are not enough for unbiased residual holdout: M752 has `1213` non-sentinel
  outcome positives, M755 exports all `1213`, and there are `0` extra positives
  not used by M761. Although M752 has `60` unused source rows, they are not
  clean positive holdout rows. The design therefore selects a disjoint seed
  range `76512..77023` and admits a no-training fresh v4 source wave,
  reset-source sequence intervention, and corpus export before any residual
  replay.
- M765 audits M764 as a clean public-corpus closed-loop mechanism positive. It
  supports alpha `0.2` as the conservative next candidate and treats alpha
  `1.0` as aggressive diagnostic because its `4/1213` intervention collisions
  are concentrated in seed `76030`, variant `zero_command_obs`, horizons `6/8`,
  and fault pair `front_lateral_authority_drop->combined_fault`. The audit
  records that M755's `assigned_split=heldout` is contaminated for residual
  evaluation because M761 trained on all M755 positives. The next branch must
  design fresh source-holdout replay or fresh source mining, not PPO or
  promotion.
- M764 implements and runs the no-PPO closed-loop residual replay evaluator.
  It reconstructs `1213/1213` source rows with `0` metadata misses and `0`
  rejected rows, writes `9704` replay rows and `4852` objective rows, and keeps
  the base actor checksum unchanged. Result class is
  `v4_residual_closed_loop_replay_candidate`: alpha `0.2`, `0.5`, and `1.0`
  pass closed-loop candidate gates. Normal success is `1213/1213` and normal
  collision rate is `0` for all alphas. Alpha `0.2` raises intervention action
  gap mean/p10 from base `0.041716/0.026395` to `0.047937/0.028594` with normal
  first-action drift mean/p95 `0.000480/0.000939`; alpha `1.0` raises gap to
  `0.074868/0.038011` but creates `4/1213` intervention-branch collisions. No
  optimizer, PPO, promotion, or actor mutation occurred.
- M763 designs a no-PPO closed-loop replay evaluator for the M761 residual
  head. It compares base alpha `0.0` with residual alphas `0.2`, `0.5`, and
  `1.0`, reconstructs M755/M761 source snapshots, applies the residual wrapper
  at every rollout step, and reports normal retention separately from
  intervention action/outcome sensitivity. Required metrics include success,
  collision, road departure, spin, terminal reason, clearance margin,
  first-action drift, sequence-action drift, variant/horizon/fault-family
  stratification, and hard-negative/sentinel diagnostics. Training, PPO, and
  promotion remain blocked.
- M762 audits M761 as a clean objective-only positive, not a promoted driver.
  It supports that the v4 sequence corpus has residual actor-coupling signal:
  alpha `0.2`, `0.5`, and `1.0` improve exact gap metrics while keeping normal
  first-action drift inside gates. It keeps `scenario_sampling_failure` visible
  because hard-negative availability remains `0.721352` and rows are dominated
  by `zero_command_obs` and long horizons. The next admitted step is only a
  no-PPO closed-loop residual replay design.
- M761 implements and runs the no-PPO frozen-backbone residual objective probe.
  It reconstructs `1213/1213` M755 positive rows with `0` metadata misses and
  `0` rejected rows, trains only a `4355`-parameter residual head for `40`
  epochs, and keeps the base actor checksum unchanged. Result class is
  `v4_sequence_objective_probe_candidate`: alpha `0.2`, `0.5`, and `1.0` pass
  exact candidate gates. At alpha `0.2`, normal first-action drift mean/p95 is
  `0.000480/0.000939`, gap mean/p10 is `0.029079/0.023874`, and gap deficit
  mean is `0.012637`. At alpha `1.0`, gap mean reaches `0.047347` and gap
  deficit mean drops to `0.000000337` while normal drift remains within gates.
  No PPO or checkpoint promotion occurred.
- M760 designs a conservative no-PPO objective-only probe: frozen BC5660 actor
  backbone, bounded residual head, normal residual target zero, existing
  intervention direction preservation/amplification, optional sparse
  hard-negative calibration, and alpha ladder `0.02,0.05,0.10,0.20,0.50,1.00`
  with exact M758 metrics. No PPO or promotion is allowed.
- M759 audits M758 as a clean no-training exact objective sanity result, not a
  trained-driver improvement. It admits only objective-only probe design with
  exact before/after metrics and normal-retention gates. PPO/promotion remain
  blocked.
- M758 implements and runs the no-training exact/offline v4 sequence objective
  sanity evaluator. It reconstructs `1213/1213` M755 positive groups with no
  metadata misses, no missing normals, no missing snapshots, and no rejected
  rows. Exact metrics are finite: gap mean `0.024908`, gap p10 `0.021141`,
  target gap mean `0.041716`, gap deficit mean `0.016809`. The result is
  `v4_sequence_objective_hard_negative_sparse` because hard-negative
  availability is `0.721352`.
- M757 designs a constrained v4 sequence objective from the M755 corpus. It
  treats M755 as an index/evidence corpus, not a tensor dataset, and requires
  M758 to reconstruct samples by replay. The objective keeps normal behavior
  retention, an intervention branch anchor, outcome-weighted gap preservation,
  and optional hard-negative calibration. Actor update/PPO/promotion remain
  blocked.
- M756 audits M755 as a valid v4 positive corpus export with sparse hard
  negatives. It admits only constrained objective design: use positives and
  matched normals as required contrast, treat hard negatives as optional sparse
  contrast, preserve claim-boundary metadata, and keep PPO/promotion blocked.
- M755 implements the deterministic v4-aware sequence-outcome corpus exporter
  and runs the registered export. It writes `1213` clean positive rows, `1213`
  matched normal rows, `1009` hard-negative action-only rows, and balance
  artifacts. Positive corpus gates pass with `0` sentinel positives, `0`
  missing normals, `0` missing metadata rows, `27` seeds, `17` fault-family
  pairs, max seed dominance `0.171476`, and
  `claim_boundary_level=current_model_or_proxy`. Hard-negative contrast remains
  sparse, so objective work remains blocked pending M756 audit.
- M754 designs a v4-aware deterministic corpus export for M752's non-sentinel
  outcome positives. Precheck values are `1213` positives, `0` positive
  sentinels, `27` positive seeds, `17` fault-family pairs, max seed dominance
  `0.171476`, `0` missing normal matches, `source_kind=v4_reset_source`, and
  `claim_boundary_level=current_model_or_proxy`. Hard negatives are useful but
  sparse: `1009` capped hard negatives for `1213` positives.
- M753 audits M752 as a clean diagnostic positive, not trained-driver
  improvement. It supports the coverage-mining hypothesis and promotes only to
  a v4-aware corpus export design. Objective training, PPO, promotion, and true
  per-wheel/four-wheel fault claims remain blocked.
- M752 implements and runs v4 reset-source sequence interventions over M749
  reset-only rows. It selects `512` source rows with `461` primary rows and
  `51` sentinels across `31` seeds, `9` preferred fault families, `7` wrong
  fault families, and `21` fault-family pairs. It evaluates `12288` rollout
  rows and finds `5429` action-critical rows plus `1213` outcome-critical rows
  across `27` seeds and `17` fault-family pairs. Outcome rows are dominated by
  `zero_command_obs` (`1044`) and grow with horizon (`H=2:25`, `H=4:168`,
  `H=6:455`, `H=8:565`). Actor parameters are unchanged, sentinel
  false-positive rate is `0.0`, and no training/PPO/promotion occurs.
- M751 designs the v4 reset-source sequence intervention branch over M749
  reset-only rows. It requires source-balanced selection, `10%` sentinels,
  preserved `source_kind=v4_reset_source`, and `current_model_or_proxy` claim
  boundary metadata before any source export or objective design.
- M750 audits M749 as broad, clean reset-only v4 evidence rather than
  wrong-history proof. V4 source generation increases reset rows from M740's
  `744` to M749's `1171`, but wrong-history action-critical rows remain `0`.
  The audit selects source-balanced v4 sequence intervention as the next
  branch.
- M749 runs the no-training v4 extreme-fault coverage wave with `28`
  executable current/proxy faults and `14` future-only fault labels. It
  generates `14848` scenarios, `100624` snapshots, `12288` matched pairs, and
  `1171` reset-only rows. Actor parameters are unchanged and no training/PPO
  occurs.
- M689 implements gate-margin response amplification and passes exact
  actor-coupling gates for `3/3` seeds at `alpha=1.0`. Source-holdout selected
  metrics: normal mean `0.001380-0.001461`, gap mean `0.010731-0.011165`, gap
  ratio `3.734864-3.885905`, wrong-target improvement `0.782311-0.795998`,
  first drift p95 `0.003748-0.004017`; actor checksum unchanged, no base actor
  checkpoint, no PPO, no promotion. Caveat: normal gate remains moderately open,
  so this is an exact diagnostic pass, not a clean gate-factorization claim.
- M688 designs gate-margin response amplification after M686 gate collapse. It
  keeps the split/gated head and exact gates, but adds detached-normal
  wrong-vs-normal gate margin, hard low-gate wrong rows, stronger wrong
  gate-open pressure, and gate-margin diagnostics. PPO and promotion remain
  blocked.
- M687 audits M686 as `gate_collapse`, not amplifier capacity failure. The raw
  wrong amplifier is large, but wrong gates stay near normal gates and do not
  open toward target `0.50`. The next branch should add explicit gate-margin
  and hard low-gate wrong-row pressure.
- M686 implements split/gated response amplification. It is implementation-clean
  with gated residual heads active and actor checksum unchanged. Normal
  retention is strong (`alpha=1.0` normal mean `0.001097-0.001159`), but gates
  collapse (`normal_gate_mean` about `0.098`, `wrong_gate_mean` about
  `0.102-0.105`) and wrong gap stays around `0.0064`, so no seed/alpha passes.
- M685 designs a split/gated residual head after the M680/M683 scalar-loss
  tradeoff. The proposed head factors output into `gate(feature) *
  amplifier(feature)`, adds normal gate close and wrong gate open losses, keeps
  normal sequence/first-step safety and detached-normal wrong-history gap
  losses, and reports gate diagnostics without using them as promotion
  evidence.
- M684 audits M683 as `wrong_gap_suppressed_by_normal_sequence_anchor`. M680 and
  M683 now bracket the scalar-loss conflict: wrong pressure can restore gap but
  moves normal sequence residuals; normal sequence pressure improves retention
  but suppresses wrong-history gap. The next design target is a split/gated
  residual response amplifier, not PPO, gate weakening, or input changes.
- M683 implements normal-sequence-safe branch-specific response amplification.
  It is implementation-clean: `648` rows, `216` sources, `3` residual heads,
  actor checksum unchanged, no base actor checkpoint, no PPO, and no promotion.
  It improves normal retention versus M680 (`alpha=1.0` best normal mean
  `0.002769` versus `0.003753`) but suppresses wrong-history gap (`alpha=1.0`
  best gap mean `0.008320`, ratio `2.895718`, wrong-target improvement
  `0.438964`), so no seed/alpha passes.
- M682 designs normal-sequence-safe branch-specific response amplification. It
  preserves M680's detached-normal wrong-history pressure and adds full
  normal-sequence mean/top-k retention losses with initial thresholds `0.0020`
  mean and `0.0045` top-k. This targets M680's normal full-sequence mean
  failure without weakening exact gates.
- M681 audits M680 as
  `branch_specific_gap_partial_normal_sequence_retention_failure`. M680's
  branch-specific wrong-history pressure is useful, but normal full-sequence
  retention is now the blocker. The next design should add normal sequence
  mean/top-k pressure while keeping wrong-history pressure and first-step
  safety.
- M680 implements branch-specific response amplification. It is a clean negative
  result with progress: branch-specific pressure restores wrong-history gap
  enough for seed `6801` at `alpha=1.0` to pass gap, p10, ratio, wrong-target,
  and first-drift gates, but normal full-sequence mean is `0.003753`, above the
  `0.0025` retention gate. The next blocker is normal sequence retention, not
  first-step safety or missing wrong-history signal.
- M679 designs branch-specific response amplification. It keeps frozen BC5660,
  fused-plus-next-hidden features, first-residual execution, alpha ladder,
  exact-first evaluation, no PPO, no promotion, and no input changes, while
  adding detached-normal gap losses, stronger wrong-history branch pressure,
  wrong first/sequence gap hinges, and hard low-gap row pressure.
- M678 audits M677 as `first_step_safety_positive_wrong_gap_suppressed`.
  First-step normal safety is now controllable, but wrong-history gap collapses.
  The next design target is branch-specific wrong-history pressure with
  detached-normal gap losses, not more normal anchoring, PPO, or gate weakening.
- M677 implements the first-step-safe residual objective. It is a clean negative
  result: actor checksum unchanged, no base actor checkpoint, no PPO, no
  promotion, but `0` seed/alpha candidates pass. It fixes first-step normal
  drift (`alpha=1.0` p95 down to `0.0025-0.0033`) but suppresses wrong-history
  sequence gap (`alpha=1.0` gap mean `0.0036-0.0069`, ratio `1.25-2.40`). The
  next step is an audit and branch-specific redesign.
- M676 designs the first-step-safe residual objective. It keeps frozen BC5660,
  fused-plus-next-hidden features, residual sequence head, first-residual
  execution, alpha ladder, and exact-first evaluation, but adds
  `L_normal_first_zero`, top-k/p95 normal first-residual hinge
  (`threshold=0.004`, fraction `0.10`), and wrong-history first-gap target
  `0.006` while preserving the M671 sequence target. PPO and promotion remain
  blocked.
- M675 audits M674 as `first_action_drift_vs_sequence_gap_conflict`, not a
  representation failure. The next step is a first-step-safe residual objective
  with strong normal first-action anchoring, top-k/p95 first residual penalty,
  wrong-history sequence target, and wrong-history first-gap objective. Frozen
  backbone, fused-plus-next-hidden view, alpha ladder, exact-first evaluation,
  no PPO, no promotion, and no actor-input changes remain required.
- M674 implements the frozen-backbone residual sequence-head actor-coupling
  exact probe. It is a clean negative result: actor checksum unchanged, no base
  actor checkpoint, no PPO, no promotion, but `0` seed/alpha candidates pass.
  The blocker is an alpha conflict: `alpha=1.0` has enough sequence gap but
  first-action normal drift p95 fails; `alpha=0.5` is mostly safe but sequence
  gap and gap ratio are below threshold. The next step is an audit and a
  first-step-safe redesign, not PPO.
- M673 designs the first conservative actor-coupling probe after the positive
  M671 shadow result. The probe freezes the BC5660 actor backbone and trains
  only a residual sequence head on fused-plus-next-hidden features. It predicts
  a short residual sequence but executes only the first residual in closed loop,
  with alpha ladder `0.02,0.05,0.10,0.20,0.50,1.00`. Exact source-heldout
  metrics must pass before replay; PPO, promotion, actor-input changes, and
  base actor checkpoint writing remain forbidden.
- M672 audits M671 as
  `shadow_positive_representation_action_boundary_evidence`, not closed-loop
  self-ID proof. Fused-plus-next-hidden supports source-heldout wrong-history
  sequence amplification in `2/3` seeds; fused alone fails and next-hidden
  alone misses normal-retention mean. PPO, promotion, and actor-input changes
  remain blocked. The next admitted step is a design-only exact-gated
  actor-coupling milestone.
- M671 implements and runs the frozen-actor response-amplification shadow
  objective. It reconstructs `648` source-balanced rows from M667 candidates
  across `216` sources and `100` physical pairs. The fused view fails, the
  next-hidden view has enough wrong-history gap but slightly too much normal
  residual, and fused-plus-next-hidden passes in `2/3` seeds with source-heldout
  gap ratios above `4.22` and wrong-target MSE improvements around `0.90`.
  Actor checksum is unchanged, no actor checkpoint is written, no PPO is used,
  and no checkpoint is promoted. The result is shadow-positive but not
  closed-loop proof.
- M670 designs the concrete frozen-actor response-amplification shadow
  objective. M671 should reconstruct source-heldout shadow data from M667
  candidates, anchor normal residuals to zero, amplify existing wrong-normal
  action-delta directions to a bounded target gap, compare fused/next-hidden/
  fused-plus-hidden views, and require exact source-heldout metrics before any
  actor coupling is considered.
- M669 designs a conservative no-PPO action-boundary response-amplification
  ladder. The next step is a frozen-actor shadow objective over fused,
  next-hidden, and fused-plus-hidden feature views with normal-history anchors,
  wrong-history sequence-separation targets, source-heldout exact evaluation,
  and no actor mutation.
- M668 audits M667 as `near_boundary_exists_but_wrong_history_outcome_insensitive`.
  Valid near-boundary preferred windows exist and first-action differences are
  common, but short-horizon action separation is weak and outcome gaps are
  absent. The next branch should address the action boundary directly through a
  no-PPO response-amplification design with exact/replay gates before any actor
  coupling.
- M667 implements and runs the normal-success near-boundary source miner. It
  finds `204` valid near-boundary preferred windows, so source-window coverage
  is not the active blocker. It still accepts `0` rows: wrong history changes
  first actions often, but only `4` rows pass the sequence threshold, `0` pass
  preferred-vs-rejected `0.010`, `0` pass margin threshold, and success-drop
  rate is `0.000`. Normal and wrong-history branches both succeed at rate
  `1.000`.
- M666 designs a normal-success near-boundary source miner. The source order is
  now: wider obstacle decision-window bank, normal-history prepass, margin-band
  classification, then wrong-history pairing only for
  `near_boundary_preferred` windows. This directly addresses M664's issue where
  action-sensitive rows were already failed under normal history.
- M665 audits M664 as `action_gap_positive_outcome_gap_negative`. M664 found
  wrong-history action gaps, but the rows that crossed all action thresholds
  were already failed under normal history and had no success-drop or
  margin-gap evidence. The likely root cause is source-window quality:
  close-obstacle windows expose action sensitivity too late. The next branch is
  a normal-success near-boundary source filter before wrong-history pairing.
- M664 implements and runs the broader no-training action-critical
  wrong-history source miner. It builds `473` snapshots and scores `7200`
  candidate sequence rows. The result is still negative: `0` accepted rows.
  Compared with M661, action sensitivity improved (`5352` first-action
  threshold rows, `60` sequence-threshold rows, `3` all-action-threshold rows,
  max sequence mean L2 `0.010464`), but outcome sensitivity is absent: `0`
  margin-threshold rows and success-drop rate `0.000`. The all-action-threshold
  rows are already failed under normal history, so they are not usable
  self-ID supervision.
- M663 designs the action-critical wrong-history source miner. The key change
  is to invert source selection: first build a broader snapshot bank and test
  many compatible wrong-history candidates, then accept rows only when wrong
  history creates explicit short-horizon action-sequence divergence plus
  margin/success sensitivity. Hidden distance may rank proposals but cannot be
  an acceptance criterion.
- M662 audits M661 as implementation pass but corpus gate fail. M661 evaluated
  `3207` candidates and wrote valid preferred/rejected artifacts, but the
  existing matched-current surfaces produce neither meaningful wrong-history
  action sequence divergence nor margin divergence. The next branch is
  action-critical wrong-history source mining, not threshold weakening,
  objective tuning, actor coupling, or PPO.
- M661 implements and runs the no-training action-divergent wrong-history corpus
  miner. It is a clean negative result: `0/3207` candidates accepted. The max
  wrong-history sequence mean L2 is only `0.001850` versus the `0.006`
  threshold, max preferred-vs-rejected sequence mean L2 is `0.001850` versus
  `0.010`, max margin gap is `0.000031` versus `0.010`, and both normal and
  wrong-history success rates are `1.000`. Actor checksum is unchanged and no
  actor checkpoint is written. This means the existing M586/M636
  matched-current surfaces are hidden/feature-different but not usable
  action-divergent wrong-history supervision.
- M660 designs the action-divergent wrong-history corpus. The next miner should
  stop accepting hidden-difference-only rows and require explicit
  preferred/rejected action sequences, first-action divergence, short-horizon
  action divergence, margin gap, and source-heldout split coverage before any
  new objective is considered.
- M659 audits M658 as
  `partial_relative_signal_but_absolute_wrong_history_gap_negative`.
  `next_hidden` carries more wrong-history signal than fused features, but not
  enough: wrong-history L2 remains below threshold and mean gap MSE is negative.
  The next blocker is corpus/target design, not actor coupling or more fused
  contrast tuning.
- M658 implements the frozen feature-view comparison probe. It is negative:
  `diagnostic_passed=false`, with no passed views. `next_hidden` improves
  wrong-history prediction L2 by about `3.71x` over fused on average, but only
  reaches `0.001732`, below the `0.005` threshold, and wrong validation gap MSE
  remains negative on average. Actor checksum is unchanged and no actor
  checkpoint is written.
- M657 designs the fusion-boundary probe. The implementation should evaluate
  three frozen feature views: fused actor features, next recurrent hidden state,
  and their concatenation. The decision rule is diagnostic: if next-hidden or
  fused-plus-hidden creates source-heldout wrong-history separation while fused
  remains weak, the fusion boundary becomes the next design target; no actor
  checkpoint may be written.
- M656 audits M655 and admits a fusion-boundary probe design. The strongest
  interpretation is that wrong-history information exists in recurrent state
  and survives the current-response GRU update, but is too weak at the fused
  feature and actor-action boundary. The next branch should compare fused,
  next-hidden, and fused-plus-hidden diagnostic heads before actor coupling or
  PPO.
- M655 implements and runs the no-training feature separability audit. The
  result is `fusion_washout`: wrong-history raw hidden L2 is `0.097340` and
  next-hidden retention is `0.409547`, so the signal is not absent, but fused
  feature L2 is only `0.014905` and actor action L2 is only `0.000685`.
  Wrong-history feature/action gaps are only `20.27%` and `5.12%` of the
  delayed-history gaps. Actor checksum is unchanged and no checkpoint is
  written.
- M654 designs the wrong-history feature separability audit. The next diagnostic
  should measure raw hidden, next hidden, fused feature, actor mean, and tanh
  action distances for normal versus variant histories, with group summaries by
  variant, split, source, target, and surface. Actor coupling, contrast tuning,
  PPO, and promotion remain blocked until M655 localizes where the
  normal-vs-wrong signal collapses.
- M653 audits M652 as `normal_retention_positive_wrong_history_gap_negative`.
  Normal validation retention is good, but wrong-history gap MSE/L2 are one to
  two orders of magnitude below threshold. The likely blocker is weak
  normal-vs-wrong separability in frozen BC5660 recurrent features. M653 rejects
  actor coupling and rejects increasing contrast coefficients before a feature
  separability audit.
- M652 implements and runs the frozen-head wrong-history contrast smoke. It is
  a clean negative result: `0/3` seeds pass. Normal validation MSE remains good
  (`0.000491`, `0.000508`, `0.000509`), but wrong-history gaps stay near zero:
  validation gap MSE is negative for all seeds and validation gap L2 is only
  `0.000624-0.000748`, far below the `0.005` threshold. Actor checksum is
  unchanged and no actor checkpoint is written.
- M651 designs the frozen-head wrong-history contrast objective. It keeps actor
  parameters frozen and trains only the auxiliary head. The design uses normal
  target loss plus a wrong-history margin loss on `wrong_matched_history` rows,
  with delayed-history rows reported but not forced into the rejection loss.
  M652 must preserve normal validation MSE `<= 0.0010` while creating
  wrong-history train/heldout gap thresholds.
- M650 audits M649 as `pass_with_wrong_history_limitation`. The 3/3 head-only
  repeat proves frozen-feature sequence-delta learnability, but wrong-history
  sources `30` and `32` have normal/variant prediction gaps around
  `0.0005-0.0007`. This is not self-ID separation. M650 rejects direct adapter
  or actor coupling and admits wrong-history contrast design.
- M649 implements the early-stopped multi-seed frozen-head repeat. All three
  seeds pass best-validation thresholds, all best/final head checkpoints are
  written, and actor checksum remains unchanged. Best validation MSE is
  `0.000486`, `0.000458`, and `0.000502` for seeds `6460`, `6461`, and `6462`.
  The limitation is wrong-history separation: sources `30` and `32` have
  normal/variant prediction gaps only about `0.0005-0.0007`, so actor coupling
  remains blocked pending M650 audit.
- M648 designs the early-stopped multi-seed head-only repeat. The next run
  should use seeds `6460`, `6461`, and `6462`, save best-validation heads, use
  a lower `240` epoch cap, and require at least `2/3` seeds to reach train
  improvement `>= 30%`, validation improvement `>= 50%`, best validation MSE
  `<= 0.00075`, and final-vs-best ratio `<= 3.0`. Actor coupling remains
  blocked.
- M647 audits M646 as `pass_with_overfit_caveat`. The correct best validation
  epoch is `120` with normal delta-MSE `0.000490287`; final epoch `300` is
  `0.001331890`, or `2.72x` the best value. Source-level summaries show
  wrong-history source separation remains weak, especially source `32`, whose
  variant loss is lower than normal loss. M647 admits an early-stopped
  multi-seed head-only repeat, not actor coupling.
- M646 implements and runs the frozen-actor BC-v2 sequence-delta head-only
  smoke. It passes the pre-registered gate: train delta-MSE improves
  `97.28%`, source-heldout validation improves `84.50%`, the actor checksum is
  unchanged, only `sequence_delta_head.pt` is written, and no actor checkpoint
  or promotion occurs. Caveat: validation is best at epoch `120`
  (`0.000490287`) and worsens by epoch `300` (`0.001331890`), so M647 must audit
  before actor coupling.
- M645 designs the frozen-actor head-only smoke. The later implementation may
  train only `SequenceDeltaHead(features) -> delta_action_sequence`; all BC5660
  actor/recurrent/critic parameters remain frozen. The pass criterion is
  train delta-MSE improvement `>= 30%`, source-heldout validation not worse,
  actor checksum unchanged, only a head checkpoint written, and no promotion.
- M644 implements and runs the exact no-update BC-v2 evaluator. Normal-hidden
  first-action loss is `0.002101438`; variant-hidden first-action loss is
  `0.002599709`; sequence-delta target MSE is `0.002039985`; and actor checksum
  is unchanged. Normal actions reconstruct stored base first actions to
  `4.04e-8` weighted mean L2, confirming the evaluator is live and no-update.
  Wrong-history sources still have very small normal/variant action gaps, so
  M644 admits only a frozen-actor head-only smoke design, not an actor update.
- M643 designs the source-balanced BC-v2 objective. The key constraint is that
  M641 has initial observation/hidden plus target sequences, but not the
  closed-loop post-target observation sequence. Therefore the next step is not
  a direct full-actor update. The safe ladder is M644 exact evaluator, then a
  frozen-actor shadow/head-only smoke, then only later a tightly gated adapter
  or actor update. Metadata remains objective-only and cannot enter actor
  inputs.
- M642 runs exact objective sanity on the M641 sequence corpus. The NPZ and
  metadata align for `431` rows; all rows have nonzero target/base deltas;
  `outside_mask_abs_max` is `0.0`; weighted sequence MSE is `0.002039985`; and
  source weights are balanced with max absolute source-weight error
  `8.28e-10`. Train and source-heldout validation objective scales are close:
  weighted MSE `0.002054882` versus `0.002010192`. This admits BC-v2 objective
  design, not training or promotion.
- M641 implements and runs the source-balanced sequence target corpus builder.
  It selects `431` rows across `9` source rows, `8` physical pairs, `6` left
  seeds, `2` surfaces, `3` targets, and `2` variants. It writes
  `balanced_sequence_targets.csv`, `balanced_sequence_target_corpus.npz`,
  source-balance summaries, and top-k diagnostics. The split is group-aware:
  train has `271` rows and source-heldout validation has `160` rows, with
  sources `20` and `32` held out together because they share a physical pair.
  Equal source total weights are written. This is corpus infrastructure only;
  actor training, PPO, and promotion remain blocked pending exact objective
  sanity.
- M640 designs the source-balanced sequence target corpus. M641 should cap M639
  accepted candidates per source/grid/family, use equal source total weights,
  and write both `balanced_sequence_targets.csv` and
  `balanced_sequence_target_corpus.npz`. Source labels and target metadata
  remain training metadata only and must not enter actor input.
- M639 implements and runs the no-training broad source-diversity expansion.
  It selects `9` M627 trust-primary non-collision source rows and all `9` have
  accepted projected candidates. Accepted evidence covers `8` physical pairs,
  `6` left seeds, `2` surfaces, `3` targets, and `2` variants, with trust limits
  preserved. This passes the target-corpus admission-candidate gate, but it does
  not yet admit training because raw accepted candidates are dominated by a few
  high-count sources.
- M638 designs the broader source-diversity expansion. M639 should select the
  M627 trust-primary non-collision near-miss rows, run the combined projected
  shape grids over that expanded set, and classify target-corpus admission only
  if accepted evidence reaches at least `8` source rows, `6` physical pairs,
  `6` left seeds, `2` surfaces, and `2` targets. If the result remains close to
  the four-source M636 footprint, the branch should stop pure sequence-grid
  mining and move to local QP / hidden-to-action forcing / BC-v2.
- M637 audits M636 as strong positive but not source-diverse enough for target
  corpus admission. M636 proves projection plus local shape design can recover
  four focused sources, but accepted candidates still come from only `4` source
  rows, `4` physical pairs, and `3` left seeds. M638 should expand the source
  set before any optimizer or actor-update design.
- M636 implements and runs the two-grid combined projected search. It evaluates
  `7884` candidates, accepts `1424`, preserves trust limits, and produces
  accepted candidates for all four focused sources: source `8` `664`, source
  `30` `430`, source `0` `196`, and source `7` `134`. Accepted targets include
  both `future_braking_deceleration` and `future_yaw_response`.
- M635 designs a two-grid combined projected search. Grid A preserves M633's
  source8/source0/source30 recovery. Grid B restores M630's source7 pattern
  around steer `0.08`, throttle `0.00`, and brake `0.00/0.04`. M636 should
  implement this as a no-training artifact pass with source-level outcomes for
  all four sources.
- M634 audits M633 as strong targeted-positive with sentinel grid regression.
  The source-7 failure is likely coverage, not a fundamental conflict: M633 did
  not include M630's source-7 pattern around steer `0.08`, throttle `0.00`,
  brake `0.00/0.04`. M635 should design a combined grid that merges source8
  recovery and source7 preservation.
- M633 implements and runs the source-8 targeted projected search. It evaluates
  `10080` candidates, preserves trust limits, recovers source `8` with best
  improvement `0.026789`, recovers source `0` with `0.022995`, and improves
  source `30` with `0.029507`. Source `7` regresses from accepted to best
  improvement `0.019965`, just below threshold, so this remains diagnostic and
  requires M634 audit.
- M632 designs a source-8 targeted projected shape search. Source `8` is only
  `0.001248` below the margin threshold after M630. The design focuses a local
  microgrid around K=7 constant-delta signs (`throttle_delta=-0.06`, steer near
  `0.00` to `0.04`, brake near `0.04`) and adds K=5/K7/K9 targeted projected
  shape families. Source `0` is secondary; sources `7` and `30` are sentinels.
- M631 audits M630 as narrow diagnostic-positive but not optimizer-ready.
  Projection preserved all trust limits and recovered one zero-accepted source,
  but accepted evidence still covers only sources `7` and `30`, `2` physical
  pairs, and `1` target. Source `8` is near threshold with best projected
  improvement `0.018752`, so M632 should design a targeted source-8 local shape
  search before any optimizer discussion.
- M630 implements and runs the trust-projected sequence pass. It evaluates
  `7596` candidates on focused sources `0`, `7`, `8`, and `30`, preserves all
  trust limits, accepts `9` projected candidates, and recovers source `30` from
  zero accepted candidates. Source `7` improves from `3` to `5` accepted
  candidates, while sources `0` and `8` remain below the margin threshold. This
  is diagnostic-positive but still source-narrow.
- M629 designs the projected/smoother sequence-shape pass. It specifies a
  focused source filter (`accepted_candidate_count <= 3`, trust-primary best
  failure, no collision near miss), radial projection of raw `delta_sequence`
  into the existing trust limits, and source-level recovery artifacts. M630
  should implement this as another diagnostic-only pass.
- M628 audits M627 and chooses the next branch. The strongest high-count
  near-miss sources already have many accepted candidates, so the diversity
  opportunity is in low/zero accepted trust-primary sources. M628 selects a
  design-only projected/smoother sequence-shape branch focused on sources
  `30`, `7`, `0`, and `8`, while keeping collision-primary sources separate and
  keeping optimizer admission blocked.
- M627 implements and runs the no-training near-miss trust-geometry analyzer on
  M624 candidates. It finds `802` unaccepted-but-useful near-miss candidates
  across `13` source rows: primary failures are mean L2 excess `542`, max L2
  excess `185`, and collision `75`; off-road and spin are `0`. All `13` source
  rows have trust near misses and `4` have collision near misses. This supports
  a projected/smoother candidate-shape audit but does not admit optimizer
  training, PPO, promotion, threshold changes, or trust-region relaxation.
- M626 designs the near-miss trust-geometry analyzer. M627 should filter M624
  unaccepted-but-useful candidates, compute mean/max/delta-delta L2 excess,
  keep collision/off-road/spin flags visible, aggregate by source row, and
  write near-miss candidate/source artifacts. This is still diagnostic-only.
- M625 audits M624. K=7 is useful for stronger candidates but negative for
  source-diversity recovery: accepted sources stay at `6` rows, `5` physical
  pairs, and `4` left seeds. The next signal is near misses: `7` unaccepted rows
  have best margin improvement `>= 0.02`, with `6` blocked by
  `outside_sequence_trust_region` and `1` by collision; `775` trust-blocked
  candidates exceed the margin threshold across `13` source rows. M626 should
  design trust-geometry analysis without relaxing constraints.
- M624 runs the K=3/5/7 low-amplitude sequence diagnostic. It increases
  accepted candidates from `189` to `607` and selected mean margin improvement
  from `0.056784` to `0.068523`, but source-level accepted diversity stays at
  `6` selected rows, `5` physical pairs, and `4` left seeds. K=7 strengthens
  already-accepted source rows but does not solve the source-diversity blocker.
- M623 designs a K=7 low-amplitude sequence diagnostic. M624 should use the
  M616 expanded source table, add `K=7`, add intermediate steer deltas `±0.06`,
  and keep all M621 trust-region and acceptance thresholds unchanged. The run
  remains diagnostic-only and must compare source-level selected/candidate
  diversity against M621 before any optimizer discussion.
- M622 audits M621's `189` accepted candidate rows. They show useful
  candidate-family diversity but not enough source diversity: accepted
  candidates still cover only `5` physical pairs and `4` left seeds, and
  core-boundary evidence is only `2` accepted candidates. Optimizer admission
  remains blocked. M623 should design a longer K=7 low-amplitude diagnostic
  rather than widening trust regions or lowering thresholds.
- M621 formally reruns the tier-aware sequence target miner. It reproduces M617
  selected metrics exactly and writes `accepted_candidate_sequences.csv` with
  `189` accepted candidate rows. Candidate-level family diversity exists
  (decay_pulse `86`, constant_delta `64`, steer_then_brake `22`,
  brake_release_then_steer `17`), but accepted candidates still cover only `5`
  physical pairs and `4` left seeds. M622 should audit before any longer K=7
  diagnostic or optimizer design.
- M620 implements source-tier metadata propagation and
  `accepted_candidate_sequences.csv` in `sequence_target_miner`. A real
  tier-aware smoke on M616 expanded rows reproduces M617's `6` selected
  accepted sequences and exposes `189` accepted candidate rows. Candidate-level
  family diversity exists, but source-level diversity remains narrow: accepted
  candidates still cover only `5` physical pairs and `4` left seeds. Optimizer
  admission remains blocked.
- M619 designs the next no-training sequence diversity step. M617 has `6`
  selected accepted sequences but `189` accepted candidate rows, and accepted
  source-tier interpretation required a manual join to M616. M620 should make
  the sequence miner source-tier and accepted-candidate-set aware before any
  larger search, optimizer design, training, or PPO.
- M618 audits M617 as diagnostic-positive but not optimizer-ready. M617
  increases selected accepted sequences from `1` to `6`, but it still misses
  the pre-registered breadth target: `6 < 8` accepted sequences, `5 < 6`
  physical pairs, `4 < 6` left seeds, and all selected sequences are `K=5`
  `constant_delta` with `+0.08` steer. M619 should design source-tier metadata
  propagation, accepted candidate-set audit, and possibly longer low-amplitude
  sequence families while keeping target thresholds and trust regions intact.
- M617 repeats the unchanged M613 sequence target miner on the M616 expanded
  source table. It evaluates `10440` candidates across `30` source rows and
  selects `6` accepted sequences with mean margin improvement `0.056784` and
  max `0.093048`. This is a clear repeatability improvement over M613's one
  accepted sequence, but it remains diagnostic-only: accepted diversity is `5`
  physical pairs and `4` left seeds, and all selected sequences are `K=5`
  `constant_delta` with `+0.08` steer. M618 should audit before any optimizer
  or training design.
- M616 implements and runs the expanded sequence-source miner. From `33` M609
  source rollout rows it writes `30` expanded rows and `3` rejected rows. The
  expanded set includes all `17` original M609 boundary rows plus `6` near
  boundary and `7` support boundary rows; it covers `27` physical pairs, `15`
  left seeds, `2` surfaces, `2` variants, and `3` targets with max pair
  dominance `0.066667`. Diversity passes, so M617 can rerun the unchanged
  sequence target miner on this expanded source table.
- M615 designs source expansion before another sequence miner run. Lowering
  `min_capability_z_distance` is not useful on the current two-variant source
  pool: z thresholds from `0.10` down to `0.00` deduplicate to the same `33`
  rows. The next implementation should instead tier M609 `source_rollouts.csv`
  by baseline boundary window: core collision/margin `<= 0.50`, near margin
  `<= 1.00`, and support margin `<= 2.00`. This can expand from `17` original
  boundary rows to up to `30` rollout-backed rows while preserving deterministic
  wrong/delayed hidden provenance. Sequence target acceptance thresholds remain
  unchanged.
- M614 audits the M613 result and admits source expansion design. M613 produced
  a real sequence-target signal, but accepted diversity is only one source row,
  one physical pair, one left seed, one surface, one variant, and one target.
  Optimizer admission, training, PPO, and promotion remain blocked; M615 should
  expand source diversity and repeatability criteria before another sequence
  mining run.
- M613 implements and runs sequence target mining on M609 boundary rows. It
  evaluates `5916` sequence candidates and selects one accepted `K=5`
  `constant_delta` sequence on a fresh delayed braking row, with margin
  improvement `0.020817`. `sequence_target_corpus.npz` is written, but accepted
  diversity is one source/physical pair/surface/variant/target, so it is
  diagnostic-only and cannot feed training.
- M612 designs the sequence target miner: structured `K in {3, 5}` action
  prefixes, per-step action L2 `<= 0.10`, sequence mean L2 `<= 0.08`, sequence
  max L2 `<= 0.10`, unchanged `0.02` margin / `0.05` risk acceptance
  thresholds, and diagnostic-only artifacts.
- M611 audits M610 and classifies the blocker as first-action locality / myopia,
  not source-boundary distance or horizon length. A single first-action
  override followed by unchanged BC5660 is too weak; M612 should design
  bounded 3-5 step action-sequence targets before any training.
- M610 runs diagnostic target search on the `17` M609 boundary rows using an
  `80`-step continuation horizon. It evaluates `3332` first-action candidates
  and accepts `0` targets. Max candidate improvement is `0.017662`, and max
  trust-region improvement is `0.015549`, still below the `0.02` threshold.
  No target corpus is written; sequence/trajectory target audit is admitted.
- M609 implements and runs the boundary-conditioned source miner. It selects
  `33` reconstructable full-pool source rows, admits `17` near-boundary rows,
  and rejects `16` far rows. The `17` rows cover `16` physical pairs, `9` left
  seeds, `2` surfaces, `2` variants, and `3` targets, but miss the desired
  `24`-row threshold, so `diversity_pass=false`. A limited diagnostic target
  search is admitted; training and optimizer admission remain blocked.
- M608 designs the next source-screen step. M609 should scan the full
  reconstructable M604 source pool, initially `wrong_matched_history` and
  `delayed_history`, run an `80`-step normal baseline continuation, and admit
  rows only when collision, margin `<= 0.50`, or high baseline risk makes them
  boundary/risk candidates. M609 should write source-rollouts, boundary-source
  rows, rejected/far rows, and summary artifacts, but no action targets.
- M607 audits M606 and classifies the zero-accepted result as primarily
  source-row boundary-distance. Baseline source margins are mostly far from the
  short-horizon boundary: median `2.729036`, mean `2.833607`, only `3 / 23`
  below zero, and `4 / 23` at or below `0.5`. A diagnostic `0.015` margin
  threshold would still accept no rows. The next branch is boundary/risk-
  conditioned source re-mining design; actor training and PPO remain blocked.
- M606 implements and runs the grounded target miner. It selects `23` unique
  wrong/delayed source rows from M604 and evaluates `4508` first-action
  candidate rollouts. Result: `0` accepted targets, `23` unaccepted rows, max
  candidate margin/risk improvement `0.014268`, and max trust-region
  improvement `0.013046`. No target corpus is written; actor training, PPO,
  promotion, and direct use of belief-only gaps as labels remain blocked.
- M605 designs the grounding step. M606 should run a local first-action search
  around M604 candidates and accept targets only when they improve simulator
  margin/risk within a small action trust region. Actor training, PPO, and
  direct use of belief-only gaps as labels remain blocked.
- M604 implements and runs the no-update evaluator. It joins `6776` rows and
  finds `262` real-history `belief_only_gap` candidates: fresh shuffled `84`,
  fresh delayed `24`, fresh wrong-matched `8`, OOD shuffled `77`, OOD
  wrong-matched `49`, and OOD delayed `20`. These are grounding candidates,
  not action labels.
- M603 designs that guarded action-coupling branch. The immediate next step is
  an exact no-update evaluator that joins M591 action distances and M601
  capability z-distances, then classifies `belief_only_gap` rows before any
  grounded recovery/boundary target mining or optimizer step.
- M602 audits M601. The supported diagnosis is belief-level signal without
  action-use proof: hidden capability movement exists, but M591 still shows
  real wrong/delayed histories barely move action. M602 admits a design-only
  guarded action-coupling objective and keeps actor training, PPO, promotion,
  and ungrounded action separation blocked.
- M601 implements and runs that probe. Fresh has `329` pairs and OOD has `287`
  pairs. `shuffled_history` passes the admission rule on both surfaces, and
  `wrong_matched_history` passes on OOD with mean z-distance `0.140707` and
  `49 / 287` above-threshold rows. Fresh `wrong_matched_history` is mixed
  (`0.099081`, `8 / 329`), and `delayed_history` is weak on both surfaces.
  This admits M602 audit but not actor training, PPO, promotion, or a driver
  improvement claim.
- M600 designs the capability-belief intervention probe. It uses the M598
  capability head on recurrent `next_hidden` under M591-style hidden variants
  and measures z-scored capability prediction distance. Actor fine-tuning is
  admitted only if real-history variants show capability movement; random
  hidden remains diagnostic only.
- M599 audits M598: the frozen BC5660 hidden state contains learnable
  capability signal, but this is not driver improvement and does not show action
  use. Before actor fine-tuning, M600 should test whether the learned capability
  belief changes under wrong/delayed hidden interventions on M586/M591-style
  surfaces.
- M598 implements and runs the frozen-actor capability-head smoke. Train/val
  regression losses drop `79%` / `67%`, train rank loss drops `32%`, validation
  rank loss also decreases, action-anchor MSE is `0`, actor parameters are
  unchanged, and no checkpoint is promoted. This proves data/objective signal,
  not driver improvement.
- M597 designs the first capability repair objective smoke as a frozen-actor,
  head-only test. It trains only `CapabilityHead` on `base_next_hidden_seq` and
  M596 capability targets, uses regression plus pair ranking losses, and treats
  action anchor as a near-zero drift metric. It explicitly makes no driver
  improvement or self-ID claim.
- M596 exports train and validation BC capability corpora. Train has `112`
  rows and `240` pair rows; validation has `58` rows and `240` pair rows. Both
  preserve `student_obs_dim = 72`, `target_dim = 3`,
  `labels_enter_actor_input = false`, and
  `contains_privileged_actor_inputs = false`. M597 should design the first
  objective smoke before any training.
- M595 implements `bc_capability_corpus`: closed-loop BC5660 corpus export with
  P0 observations, base action anchors, future-response target labels,
  recurrent hidden diagnostics, and same-corpus matched-current pair rows. A
  real 3-seed smoke produced `24` rows and `18` pair rows with
  `labels_enter_actor_input = false`. M596 should export train/validation
  corpora; still no repair training or promotion.
- M594 designs the real capability corpus/runner. It chooses closed-loop
  BC5660 rollout collection so P0 observation, recurrent hidden diagnostics,
  base action anchor, and future-response label correspond to the same state.
  Matched-current ranking rows should be mined from the new corpus rather than
  blindly reusing M586 indices. M595 should implement exporter and tests only.
- M593 implements the capability-repair objective utilities:
  training-only capability head, z-score regression, matched-current ranking,
  action BC/anchor losses, and metadata preservation. Synthetic tests pass, but
  no real checkpoint training was run. M594 must design the corpus/runner that
  aligns future-response labels with rollout hidden states before smoke
  training.
- M592 selects the first repair direction: train hidden state with
  training-only future-response/capability targets, using regression plus
  matched-current ranking and an action anchor. It explicitly rejects
  ungrounded action separation, PPO continuation, promotion, and any actor
  input expansion. M593 should implement objective infrastructure and tests
  only.
- M591 implements and runs the hidden-action sensitivity probe. Fusion weights
  have non-trivial hidden/context/interaction shares for BC5660/5661/5662, but
  BC5660 real wrong/delayed hidden states remain action-equivalent on fresh and
  OOD matched-current surfaces. Fresh wrong/delayed mean action distances are
  `0.000552` / `0.001658`; OOD values are `0.000764` / `0.001218`. Zero-current
  stays dominant. The next step is hidden-use objective/corpus design, not
  PPO, promotion, or outcome rollout.
- M590 designs the hidden-action sensitivity probe needed after M589. M591
  should measure fusion weight chunk norms, real wrong/delayed hidden variants,
  shuffled/scaled/random hidden variants, positive observation controls, and
  hidden-distance/action-distance correlations. Random-hidden movement is
  diagnostic only and must not be treated as self-ID proof.
- M589 audits the scaled L3 BC objective after the negative M587
  wrong/delayed-history action screen. The `human_view_online_gru` actor has a
  structural hidden-to-action path, but the BC optimizer trains only recurrent
  one-step teacher-action MSE and the corpus lacks matched-current
  history-contrast targets. M590 should design a hidden-action sensitivity
  probe before any repair training.
- M520 valid-offset projected replay produced only a margin-only projected
  history signal: `1` source-narrow wrong-history proof candidate and `0` event
  rows.
- M524 found stronger natural history-value diagnostics: `480` L0 diagnostic
  candidates and `18` obstacle-completion event rows across natural M497/M487
  surfaces.
- M526 audited those event rows as source-diverse diagnostic evidence:
  `18` obstacle-completion drops across `2` surfaces, `5` probe seeds, and
  `2` targets, with projected event rows excluded.
- M527 defined the matched baseline family: L0 feedforward/current observation,
  L1 one-step command-response annotation, L2 finite command-response window,
  and L3 online GRU recurrent belief.
- M528 implemented explicit baseline metadata and an L0 smoke path while
  preserving the P0 no-wheel/no-oracle actor contract.
- M529 pre-registered the staged matched-baseline evaluation ladder so later
  L0/L2/L3 comparisons use shared budgets, seeds, configs, artifacts, and
  holdout discipline.
- M530 repeated the L0 current-observation smoke on seeds `3530` and `3531`.
  Both completed and wrote stable `L0_current_observation` plus
  `P0_human_view_no_wheel_no_oracle` metadata. The smoke returns are not
  interpreted as baseline evidence.
- M531 added machine-checkable L0/L2/L3 short-train configs with shared PPO
  budget, seed, task distribution, and P0 contract checks. L2 is the only config
  with `history_length = 4`; L0 and L3 use `history_length = 1`.
- M532 ran all three short-train configs on seed `3530`. L0 and L2 terminated
  in all eval episodes, while L3 had lower termination rate (`0.6`) and higher
  return on this one seed. This is route/artifact evidence only; repeat seeds
  and natural history-value surface evals are still required.
- M533 repeated the frozen configs on seeds `3531` and `3532`. Across seeds
  `3530`-`3532`, L3 has the best average return/termination (`45.7765`/`0.6`),
  L2 is second (`39.9082`/`0.6667`), and L0 is third (`27.3016`/`0.8667`).
  This is preliminary route evidence only; natural history-value surface eval is
  the next evidence layer.
- M534 designed that next layer. Existing recurrent-only tail gates are not
  enough for matched L0/L2/L3 evaluation, so the next tool must reconstruct
  natural source states with M399, replay L0/L2/L3 from the same frozen
  state/history, keep M526 rows as public diagnostics, and exclude projected
  surfaces from natural claims.
- M535 implemented that evaluator. It supports L0 current-frame replay, L2
  current-first stacked history replay, and L3 hidden construction from source
  observation prefixes. Focused tests pass, and a real 2-pair short-reveal smoke
  produced `6` outcome rows with `0` invalid rows.
- M536 scaled the evaluator to all nine matched short-train checkpoints on
  small short-reveal and warmup natural subsets. It produced `279` valid outcome
  rows total with one diagnosed short-reveal source-tail miss. L0/L2/L3 tied on
  success/completion/collision, while L3 had the best mean clearance margin.
  This is still route evidence only.
- M537 ran the full public frozen-source natural-surface matrix across M497
  short/warmup and M487 near/late splits. It produced `20196` valid outcome rows
  and no metadata or actor-contract failures. L3 leads aggregate success
  (`0.851901`), collision rate (`0.148099`), and mean clearance margin
  (`1.654668`) versus both L0 and L2, and is best on every per-surface success
  and margin table. The public M526 event overlay also favors L3, but this is
  still public diagnostic evidence rather than private generalization or
  checkpoint promotion.
- M538 converted the M537 result into exact paired source-key deltas. The join
  is complete (`6732` triplets, `0` incomplete). L3-L0 is robust across all
  surfaces and all three training seeds, with paired success delta `+0.020351`
  and margin delta `+0.144301`. L3-L2 is aggregate-positive and positive on all
  surfaces, but not seed-uniform: seed `3531` favors L2 with success delta
  `-0.013815` and margin delta `-0.143703`.
- M539 diagnoses the seed `3531` L2-over-L3 counterexample. It is broad rather
  than an event artifact: all four surfaces, all target groups, and all
  tail-offset groups have negative mean L3-L2 margin deltas. The `31` success
  regressions are all `L2 obstacle_completed -> L3 collision`, and non-event
  rows carry the success/collision regression. L3 seed `3531` has a systematic
  first-action shift relative to L2, so the next step should address matched
  training variance rather than promote L3 from public diagnostics.
- M540 designs the matched training-variance escalation. It keeps L2 as a real
  finite-window baseline, defines a staged ladder starting with 4096-step
  matched configs, separates L3-vs-L0 from L3-vs-L2 pass rules, and requires
  public paired diagnostics before any fresh-holdout claim. It also corrects the
  current lineage config paths to `configs/ppo_m531_matched_*_short_train.json`.
- M541 implements the matched 4096-step variance config family:
  `configs/ppo_m541_matched_l0_variance_4096.json`,
  `configs/ppo_m541_matched_l2_variance_4096.json`, and
  `configs/ppo_m541_matched_l3_variance_4096.json`. Tests verify valid P0
  history-baseline metadata, shared task distribution, and that the new configs
  differ from M531 only in `total_steps` and default seed. No training or
  promotion was performed.
- M542 runs the seed-3540 4096-step route pilot for all three levels. All runs
  complete and write valid P0 history-baseline metadata. Route eval strongly
  favors L2 (`return_mean = 77.992665`, `termination_rate = 0.2`) over L0
  (`20.334296`, `1.0`) and L3 (`21.645978`, `1.0`), but this is route evidence
  only and not a stable ranking or promotion claim.
- M543 evaluates those M542 checkpoints on the public M497/M487 frozen-source
  natural surfaces. L2 dominates aggregate success/margin (`0.866310`/`1.777833`)
  while L3 regresses below L0 (`0.670677`/`0.984809`). Paired L3-L2 deltas are
  strongly negative: success `-0.195633`, collision `+0.190731`, margin
  `-0.793024`. L3 is worst on every public surface, so the current recurrent
  recipe should be audited before expanding seeds.
- M544 audits that L3 regression. There is no P0 contract violation: config and
  metadata differences are the intended finite-window versus online-GRU fields.
  The issue is training behavior: L3 peaks early (`best_return = 52.598733` at
  step `1792`) but collapses late (`last4_return_mean = 23.259713`, final return
  `15.771149`), while L2 improves late. M543 failures include `423` L2-completed
  to L3-collision pairs and a large L3-L2 action shift. The next step is L3
  recurrent recipe repair design, not more runs of the same L3 setup.
- M545 designs that repair path. It keeps P0 inputs and L2 as a serious
  finite-window baseline, allows only L3 optimization/checkpoint-selection
  controls, pre-registers interval-checkpoint selection from route artifacts
  before public eval, and admits three M546 diagnostic configs: `fast_select`,
  `lr1e4`, and `lr5e5`. This is design-only and does not promote a checkpoint.
- M546 implements those L3-only repair configs and tests. `fast_select` adds
  `checkpoint_interval_steps = 512` while keeping `learning_rate = 0.0003`;
  `lr1e4` and `lr5e5` lower recurrent update aggressiveness and set
  `max_grad_norm = 0.25`. Tests verify all three keep the M541 L3 environment
  exactly and differ only by approved optimization/checkpoint-selection fields.
- M547 runs the three M546 repair configs and evaluates all saved interval/final
  checkpoints under the route-only selection rule. The result is negative:
  `0/27` saved checkpoints pass route health, and the best saved checkpoint
  (`fast_select` step `1024`) has return `22.941196` with termination `1.0`.
  The useful diagnostic is that all three variants peak in training at step
  `1792`, but that step is unsaved by the 512-step checkpoint cadence.
- M548 adds update-aligned `checkpoint_interval_steps = 256` configs for the
  same three L3 repair variants. Tests verify the only PPO difference from each
  M546 parent is checkpoint cadence, so every PPO update step can be saved and
  evaluated in the next route pilot.
- M549 runs that update-aligned route pilot. The previously missed step `1792`
  is now saved but fails deterministic route health for all variants. One saved
  checkpoint passes the M545 route-health gate: `fast_select_ckpt256` step
  `2816`, with route return `27.858686`, termination `0.8`, and mean clearance
  margin `0.594595`. Public frozen-source diagnostics are now admitted for that
  selected checkpoint, but no checkpoint is promoted.
- M550 runs those public diagnostics. M549 selected L3 improves over original
  M542 L3 (`success +0.053922`, margin `+0.164015`), but it still regresses
  against L0 (`success -0.076203`, margin `-0.235235`) and L2 (`success
  -0.141711`, margin `-0.629009`) on the same public surfaces. The next step is
  to redesign route-health screening, not to promote or matched-repeat this
  checkpoint.
- M551 redesigns the route-health screen. Route-screen v2 must use at least
  `64` public-neutral route episodes, include L0/L2/original-L3 references, and
  rank checkpoints by obstacle success, clearance margin, collision rate, then
  return. A candidate below L0 on route-screen v2 is blocked from public
  frozen-source eval.
- M552 retrospectively validates route-screen v2. It uses level-matched env
  configs so L2 keeps `history_length = 4`, evaluates 64 public-neutral route
  episodes, and rejects M549 selected L3 before public eval: M549 success
  `0.046875` is below L0 `0.062500` and far below L2 `0.609375`.
- M553 implements route-screen v2 as reusable harness infrastructure:
  `autodrift.route_screen_v2` supports named checkpoint policies, per-policy
  level-matched env configs, required L0/L2 references, candidate selection,
  `episodes.csv`, `policy_summary.csv`, `summary.json`, and explicit
  `uses_public_frozen_source_rows = false` provenance. The runner reproduces
  the M552 rejection of M549 selected L3.
- M554 designs the next L3 recurrent repair branch under route-screen v2. It
  freezes P0/env/task boundaries, restricts repair v2 to PPO stability controls,
  and admits exactly three small L3-only variants for M555:
  `epoch1_clip01`, `longseq_epoch1`, and `lowentropy_epoch1`.
- M555 implements those three L3-only configs and tests. All preserve the M548
  L3 env/task distribution, P0 actor contract, and update-aligned
  `checkpoint_interval_steps = 256`; differences are limited to M554-approved
  PPO stability controls.
- M556 trains those configs and evaluates `43` L3 interval/final candidates
  with route-screen v2. No checkpoint is admitted. `35/43` candidates pass L0
  binary success, but `0/43` pass L0 clearance margin and `0/43` pass collision
  tolerance. Public frozen-source diagnostics are blocked.
- M557 classifies that failure as collision-dominated after a small binary
  success gain. The best candidate converts `5` L0 collisions to completions,
  but also converts `7` L0 non-collision terminations and `3` L0 completions to
  collisions. Versus L2, `38` L2 completions become L3 collisions.
- M558 designs a targeted repair branch using existing obstacle collision and
  clearance-margin reward terms. It keeps P0 inputs, rotates the next
  route-screen v2 selection seed to `16560`, and admits exactly three M559
  reward variants.
- M559 implements those three reward configs and tests. P0 L3 actor inputs and
  M555 `epoch1_clip01` PPO controls are unchanged; only M558-approved obstacle
  reward fields differ.
- M560 trains the reward configs and evaluates `51` L3 candidates on fresh
  route-screen seed `16560`. No candidate is admitted. All candidates pass L0
  binary success, but all fail L0 margin and collision tolerance, so public
  frozen-source diagnostics remain blocked.
- M561 designs the pivot from failed from-scratch L3 PPO branches to L2-to-L3
  distillation. L2 remains a training-only teacher using finite-window P0
  observations, while the deployable L3 student remains P0 online-GRU with
  current 72-value frames and recurrent hidden state. The next admitted step is
  M562: export `student_obs_seq`, `teacher_action_seq`, done masks, and terminal
  diagnostics on non-public route seeds without training or promotion.
- M562 implements that exporter in `autodrift.l2_teacher_corpus`. The real
  smoke export on non-public seeds `18000:18001` wrote `116` transitions with
  `student_obs_seq` shape `(116, 72)`, `teacher_action_seq` shape `(116, 3)`,
  done/start masks, and terminal diagnostics. The NPZ does not contain
  `teacher_obs_stack_seq`, and `uses_public_frozen_source_rows = false`.
- M563 implements offline L3 behavior cloning in
  `autodrift.l3_behavior_cloning`. A smoke run trained on the M562 corpus and
  validated on seeds `18128:18129`. It reduced train action MSE from `0.083840`
  to `0.0000705` and validation action MSE from `0.076715` to `0.000131` while
  saving a P0 `L3_online_gru` checkpoint with `ppo_used = false` and
  `promoted = false`. Closed-loop route behavior is still untested.
- M564 runs route-screen v2 on fresh selection seed `17560`. M563_BC is
  admitted for public diagnostics: success `0.656250`, collision `0.343750`,
  and mean margin `0.770803`, matching L2 success/collision and remaining
  within L2 margin tolerance while strongly outperforming L0. No checkpoint is
  promoted from this route-screen smoke.
- M565 evaluates M563_BC on the four public frozen-source natural surfaces from
  M543/M550. M563_BC matches L2 success/collision (`0.866310` / `0.133690`),
  has nearly identical mean margin (`1.770749` vs L2 `1.777833`), and strongly
  repairs original M542 L3 (`+0.195633` paired success, `+0.785940` paired
  margin). This is public diagnostic evidence only; no checkpoint is promoted.
- M566 designs the scaled BC repeat. It freezes the L2-teacher/L3-student
  boundary, assigns fresh non-public train seeds `18200-18327`, validation seeds
  `18328-18391`, BC optimizer seeds `5660/5661/5662`, and fresh route-screen
  seed `18560`. PPO remains blocked until scaled BC route/generalization
  evidence is stable.
- M567 exports the scaled corpora. Train has `128` episodes and `8024`
  transitions; validation has `64` episodes and `3900` transitions. Both corpora
  keep `student_obs_seq` at 72 dimensions, store `teacher_action_seq` plus
  done/start masks, omit `teacher_obs_stack_seq`, and report
  `uses_public_frozen_source_rows = false`.
- M568 trains scaled BC seeds `5660`, `5661`, and `5662`. All three improve
  train and validation MSE and save clean P0 L3 checkpoints. Final validation
  MSEs are `0.00003675`, `0.00000855`, and `0.00001963`; all metadata reports
  `L3_online_gru`, `P0_human_view_no_wheel_no_oracle`, `ppo_used = false`, and
  `promoted = false`.
- M569 runs route-screen v2 with fresh seed `18560`. All three scaled BC seeds
  clear route-screen, match L2 success/collision (`0.671875` / `0.328125`), and
  beat L2 mean margin slightly. `BC5660` is selected with mean margin
  `0.950870`, ahead of L2 `0.936128`. No checkpoint is promoted.
- M570 evaluates selected `BC5660` on the four public frozen-source natural
  surfaces used by M543/M550/M565. It matches L2 success/collision
  (`0.866310` / `0.133690`), has slightly higher mean margin (`1.782199`
  versus L2 `1.777833`), and strongly repairs original M542 L3 (`+0.195633`
  paired success, `-0.190731` paired collision, `+0.797390` paired margin).
  This is public diagnostic evidence only; no checkpoint is promoted.
- M571 designs the next fresh route/generalization gate. M572 will evaluate
  `BC5660` versus L0/L2 on `256` fresh non-public route seeds
  `19560..19815`, excluding prior route-screen seeds `15560`, `16560`,
  `17560`, and `18560`. It must remain L0-safe and L2-competitive under
  pre-registered success/margin/collision tolerances, with no PPO, no public-row
  tuning, and no promotion.
- M572 runs that fresh route/generalization gate. `BC5660` passes: success
  `0.625000`, collision `0.375000`, and mean margin `1.064947`, slightly ahead
  of L2 (`0.621094`, `0.378906`, `1.049135`) and far ahead of L0
  (`0.050781`, `0.867188`, `-0.044399`). The run used `256` fresh seeds
  `19560..19815`, `uses_public_frozen_source_rows=false`, and performs no
  training or promotion.
- M573 designs the next moderate-OOD route layer. M574 should add eval-only
  config copies for L0/L2/L3 with shared wider speed, friction, obstacle, and
  hidden-vehicle randomization ranges while preserving each level's history
  contract. The later M575 OOD eval should use fresh seeds `20560..20815` and
  relaxed L2 competitiveness tolerances (`0.05` success/collision and `0.10`
  margin) because the distribution is deliberately shifted.
- M574 implements those eval-only configs:
  `configs/eval_m574_moderate_ood_l0.json`,
  `configs/eval_m574_moderate_ood_l2.json`, and
  `configs/eval_m574_moderate_ood_l3.json`. Focused tests verify exact parent
  PPO sections, approved OOD env deltas, shared distribution except
  `history_length`, and route-screen loader compatibility. No evaluation,
  training, or promotion is performed.
- M575 runs the moderate-OOD route gate on fresh seeds `20560..20815`.
  `BC5660` passes: success `0.628906`, collision `0.371094`, return
  `61.804108`, and mean margin `1.042773`, matching L2 success/collision and
  slightly improving L2 return/margin (`61.796892`, `1.036858`). This is a
  positive OOD diagnostic but still not promotion evidence by itself.
- M576 audits M570/M572/M575. BC5660 is L2-competitive on public natural
  surfaces, fresh route seeds, and moderate-OOD route seeds, but this is still a
  selected single-BC-seed result. Immediate promotion and PPO remain blocked;
  the next escalation is a BC seed-family repeat for seeds `5660`, `5661`, and
  `5662` on fresh same-distribution and moderate-OOD route blocks.
- M577 designs that repeat. M578 will evaluate `BC5660`, `BC5661`, and
  `BC5662` on fresh route seeds `21560..21815` using M541 configs. M579 will
  use fresh OOD seeds `22560..22815` and M574 configs only if M578 passes.
  Family pass requires BC5660 plus at least one other BC seed to remain L0-safe
  and L2-competitive; no promotion is allowed.
- M578 runs the BC seed-family fresh route repeat. All three BC seeds pass:
  `BC5660` success/collision/margin `0.675781` / `0.324219` / `0.992939`,
  `BC5661` `0.671875` / `0.328125` / `0.982097`, and `BC5662` `0.675781` /
  `0.324219` / `0.991177`, versus L2 `0.671875` / `0.328125` / `0.978128`.
  No checkpoint is promoted.
- M579 runs the BC seed-family moderate-OOD repeat. All three BC seeds pass:
  `BC5660` success/collision/margin `0.582031` / `0.417969` / `0.921253`,
  `BC5661` `0.574219` / `0.425781` / `0.914780`, and `BC5662` `0.582031` /
  `0.417969` / `0.920871`, versus L2 `0.574219` / `0.425781` / `0.913270`.
  This strengthens the scaled BC family but still does not prove recurrent
  dependence.
- M580 audits the BC family evidence. The route/OOD transfer claim is now
  strong, but recurrent self-ID is not yet proven. The next layer should use
  checkpoint ablations such as `reset_recurrent_state`,
  `zero_current_response`, and `zero_action_history` to test whether the L3
  online-GRU policy actually depends on recurrent command-response history.
- M581 designs that ablation layer. M582 will compare `BC5660` normal against
  `reset_recurrent_state`, `zero_current_response`, `zero_action_history`, and
  `zero_all_response` on fresh seeds `23560..23815`. Meaningful degradation is
  pre-registered as success drop `>= 0.02`, margin drop `>= 0.05`, or collision
  increase `>= 0.02`.
- M582 runs that fresh-route ablation. Normal `BC5660` scores success/collision/
  margin `0.691406` / `0.308594` / `1.068165`. `zero_action_history` reaches
  meaningful margin degradation (`0.052959`), while `zero_current_response` and
  `zero_all_response` reach strong margin degradation (`0.144810`) plus success
  drop and collision increase `0.027344`. `reset_recurrent_state` is only weak
  (`0.007812` success drop, `0.017594` margin drop), so the next step is the
  M583 moderate-OOD repeat rather than promotion or PPO.
- M583 repeats the ablation on moderate-OOD seeds `24560..24815`. Normal
  `BC5660` scores success/collision/margin `0.621094` / `0.378906` /
  `0.985368`. `zero_current_response` and `zero_all_response` again degrade
  behavior, with success drop and collision increase `0.035156` and margin drop
  `0.100321`. `reset_recurrent_state` and `zero_action_history` remain below
  meaningful thresholds on OOD. The next step is an audit to separate
  current-response dependence from accumulated hidden-state self-ID claims.
- M584 audits M582/M583. The supported claim is that BC5660 uses the current
  deployable ego/IMU-like response stream on both fresh route and moderate-OOD
  distributions. The unsupported claim is accumulated online-GRU hidden belief:
  reset-hidden remains weak in both runs. M584 blocks promotion/PPO and admits a
  sharper history-intervention design using delayed or wrong recurrent history.
- M585 designs that sharper gate. Existing tooling is sufficient: use
  `matched_current_response_ambiguity` to mine source-diverse pairs,
  `matched_history_intervention_gate` for action-level screening, and
  `persistent_wrong_history_intervention_gate` for outcome degradation. M586
  will mine BC5660 pair surfaces on fresh route seeds `25560..25563` and
  moderate-OOD seeds `25660..25663`.
- M586 mines those pair surfaces. Both pass the pre-registered source-diversity
  thresholds: fresh route yields `666` accepted pairs, `192` physical pairs,
  `15` left steps, and `14` obstacle buckets; moderate-OOD yields `403`
  accepted pairs, `152` physical pairs, `14` left steps, and `14` obstacle
  buckets. M587 action screening is admitted; no checkpoint is promoted.
- M587 runs action-level delayed/wrong-history screens on both M586 surfaces.
  The result is negative for hidden-history action sensitivity:
  `wrong_matched_history` and `delayed_history` have `0` above-threshold rows on
  both fresh and OOD surfaces. The screen is valid because positive controls are
  strong: `zero_current_response` is above threshold for all rows on both
  surfaces, and `zero_action_history` is often above threshold. Persistent
  outcome rollout is blocked until M588 audits the negative result.
- M588 audits that negative result. The screen is live, so the likely issue is
  not tool failure: BC5660 appears to transfer L2 behavior through current
  response, previous commands, and scene context without materially using
  accumulated hidden state. M588 blocks the persistent outcome gate and admits a
  BC hidden-use/objective audit before any repair training.

## Near-Term Rule

Do not treat reset-hidden diagnostics, M528 smoke return, route eval, or
M537-M570 public diagnostics as private generalization evidence. The L2-to-L3
distillation branch must keep L2 finite-window stacks training-only. Offline BC
may optimize teacher-action MSE only; any checkpoint still needs route-screen v2
before public frozen-source eval. M550 remains public diagnostic evidence and
cannot support a private generalization claim. Any later promotion requires
proof retention, generalization retention, behavior retention, no contract
violation, and clear lineage.

## Sensor Profile Policy

Keep raw wheel, `v_parallel`, steering torque, suspension, and similar channels
as separate profile experiments only. Do not promote them into the main actor
without passing the same frozen-recipe proof gates as P0.

Suggested future profile ladder:

| Profile | Inputs |
| --- | --- |
| P0 | current no-wheel human-view baseline |
| P1 | commands + actuator feedback + `ax/ay/yaw_rate` + scene |
| P2 | P1 + steering torque / EPS current |
| P3 | P2 + raw four-wheel `R omega` |
| P4 | P3 + roll/pitch/vertical acceleration |
| P5 | P4 + suspension / wheel travel |

Every profile must use the same gate sequence: probe, frozen PPO recipe,
matched-current wrong-history, reset/zero-current ablation, and outcome boundary
proof. Do not tune PPO separately for one profile and compare it directly.
