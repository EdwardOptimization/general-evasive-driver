# m1419-paper-route-warmup-gate-invasiveness-retune-source-smoke Research Review

## Summary

- Generated at UTC: 20260529T013942Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: warmup_gate_invasiveness_retune_invasiveness_pass_marginal_source_diversity_fail_route_to_synthesis
- Decision reason: M1419 reduces matched collision share to 0.294 and preserves warmup evidence but misses matched/bucketed unique seed threshold by one so routes to branch synthesis

## Hypothesis

A less invasive warmup gate will preserve M1417 source materialization and warmup evidence while lowering matched/bucketed collision share enough to justify a later outcome probe.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1417_warmup_retarget_sampling_repair_source_smoke/summary.json, docs/m1418-paper-route-warmup-retarget-source-result-audit.md
- parent_config: configs/ppo_m1417_warmup_retarget_sampling_repair_figure_eight.json, configs/m1417_warmup_retarget_sampling_repair_source_wave.json, experiments/manifests/m1418-paper-route-warmup-retarget-source-result-audit.json
- parent_objective: run one focused no-training source smoke with only warmup-gate invasiveness retuned
- derived_from: m1418-paper-route-warmup-retarget-source-result-audit
- blocked_by: M1417 passes source and warmup evidence gates but misses matched/bucketed invasiveness gates narrowly
- supersedes: running outcome probe from M1417 despite failed invasiveness gates, retuning obstacle sampling again before warmup-gate invasiveness is isolated, training from M1417 source rows
- invalidates: None

## Success Criteria

- M1419 retuned source-smoke configs exist
- runs/m1419_warmup_gate_invasiveness_retune_source_smoke/summary.json exists
- source_rows >= 1024
- matched_or_bucketed_reveal_rows >= 240
- matched/bucketed unique_source_seeds >= 28
- matched/bucketed unique_capability_pairs >= 12
- matched/bucketed unique_reveal_buckets >= 64
- finite_metric_rows == source_rows
- matched/bucketed warmup_gate_visible_rows == matched_or_bucketed_reveal_rows
- matched/bucketed warmup_evidence_rows == matched_or_bucketed_reveal_rows
- matched/bucketed warmup_response_history_l2_p95 >= 0.035
- matched/bucketed warmup_action_history_l2_p95 >= 0.008
- matched/bucketed warmup_gate_collision_share <= 0.50
- matched/bucketed clear + clear_low_margin rows >= 120
- actor_parameters_changed == false
- result chooses next route without outcome intervention training PPO promotion private holdout corpus export or actor-input expansion

## Failure Criteria

- source smoke artifact is missing
- source rows are zero or metrics are missing
- source diversity gates fail
- warmup evidence gates fail
- invasiveness gates fail
- result routes directly to training PPO promotion private holdout corpus export or claim expansion

## Evidence Gates

- M1419 must run no-training warmup-gate invasiveness retune source smoke only
- M1419 must preserve M1417 obstacle sampling and retune only warmup_gate distance lateral offset and half width
- M1419 must report source diversity warmup evidence and matched/bucketed invasiveness metrics
- M1419 must not run outcome interventions train run PPO promote use private holdout export a training corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not claim self-identification from source materialization
- do not change obstacle sampling from M1417
- do not tune against private holdout
- do not run another local retune after M1419 without branch synthesis

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1419-paper-route-warmup-gate-invasiveness-retune-source-smoke
- type: infrastructure
- checkpoint: runs/m1419_warmup_gate_invasiveness_retune_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: warmup_gate_invasiveness_retune_invasiveness_pass_marginal_source_diversity_fail_route_to_synthesis
- reason: M1419 reduces matched collision share to 0.294 and preserves warmup evidence but misses matched/bucketed unique seed threshold by one so routes to branch synthesis

## Next Blocker

m1420-paper-route-warmup-reveal-pressure-retune-branch-synthesis
