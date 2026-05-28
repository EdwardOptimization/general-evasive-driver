# M1251 Paper-Route Capability-Separable Trajectory Proposal Near-Miss Audit

## Summary

M1251 audits the M1250 trajectory proposal source smoke.

Decision:

```text
trajectory_proposal_near_miss_admit_targeted_margin_restoration_smoke
```

The M1250 source is not accepted:

```text
accepted_separable_pairs: 0
```

But the failure is actionable. M1250 found a row that satisfies the action
separation and two-sided cross-regret requirements, and fails only because
own-branch best margins remain slightly negative.

Do not lower the source-positive thresholds. Run one targeted no-training
margin-restoration smoke instead.

## Near-Miss Evidence

M1250 key row:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
relocation_stage: coarse
relocation_id: 1
best_action_l2: 0.3979088664
cross_regret_A: 0.2439473105
cross_regret_B: 0.0239608733
pair_min_best_margin: -0.0018868557
margin_A_best_A: -0.0018868557
margin_B_best_B: -0.0004172706
rejection_reason: best_candidate_not_viable
```

Comparison with M1247:

```text
M1247 pair_min_best_margin: -0.0048001855
M1250 pair_min_best_margin: -0.0018868557
```

Trajectory proposals moved the branch closer to an accepted source row while
preserving two-sided regret. This is qualitatively different from M1247's
fixed-lattice result.

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

More precise subtype:

```text
near_positive_nonviable_source_row
```

Not classified as:

```text
proof_washout: no training occurred
objective_overfit: no objective optimization occurred
contract_violation: proposal labels stayed out of actor inputs
promotion_gate_failure: no promotion was attempted
private_holdout_contamination: private holdout was not used
```

## Why Not Lower Thresholds

Lowering `min_cross_regret_margin` or accepting negative own-branch margins
would make the source corpus easier to pass but weaker scientifically. The
paper route needs rows where:

```text
each hidden branch has a viable own maneuver;
the other branch's maneuver is meaningfully worse.
```

M1250 does not satisfy that yet. The right response is to repair source
viability while keeping the acceptance criterion fixed.

## Targeted Repair

Admit one bounded no-training targeted source repair:

```text
m1252-paper-route-capability-separable-proposal-margin-restoration-smoke
```

Targeted repair is allowed to change source-mining parameters:

```text
positive near-zero viability band target
slightly larger proposal count
different proposal seed
same trajectory_proposal candidate mode
same actor checkpoint and config
same no-training/no-promotion guardrails
```

Targeted repair is not allowed to change:

```text
accepted source thresholds
actor inputs
actor checkpoint
training or PPO state
private holdout
```

The proposed M1252 source window should target a small positive band:

```text
target_min_best_margin: 0.005
target_max_best_margin: 0.08
```

This is not a threshold change. The accepted-source viability threshold remains
nonnegative own-branch margin, and the cross-regret threshold remains `0.02`.

## Stop Rule

If M1252 still produces zero accepted rows, do not keep expanding proposal
budget on the same public source. Write a source-variable audit and decide
between:

```text
event-timing/source-state redesign
higher-fidelity dynamics source
teacher/optimization proposal source with stronger search
```

## Decision

Continue with one targeted source repair:

```text
m1252-paper-route-capability-separable-proposal-margin-restoration-smoke
```

Guardrails remain:

```text
no training
no PPO
no promotion
no private holdout
no actor-input expansion
no threshold relaxation
no self-identification claim
```
