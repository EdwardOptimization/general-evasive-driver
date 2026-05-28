# M1181 V4 Public Base Source-Rich Route Compatibility Audit

## Purpose

M1181 audits whether the existing source-rich v4 route tooling can be reused
for the current public-gate base.

This milestone inspects tooling and checkpoint compatibility only. It does not
run mining, run replay, train actor weights, run PPO, promote, use private
holdout, convert rows, or change actor inputs.

## Current Public-Gate Base

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

## Tooling Audit

The existing source-rich v4 route tools all require residual-head inputs:

```text
src/autodrift/v4_extreme_hidden_dynamics_data_route.py
  --checkpoint
  --residual-head
  --scenario-config
  --alpha

src/autodrift/v4_low_margin_new_data_route.py
  --checkpoint
  --residual-head
  --scenario-config
  --alpha

src/autodrift/v4_boundary_preserving_missing_seed_pair_delta_refresh.py
  --checkpoint
  --residual-head
  --scenario-config
  --alpha

src/autodrift/v4_wrong_cross_fault_history_intervention.py
  --checkpoint
  --residual-head
  --scenario-config
  --alpha

src/autodrift/v4_pair_delta_focused_source_balanced_mining.py
  --checkpoint
  --residual-head
  --scenario-config
  --alpha
```

These routes were built around the older M568 + M761 residual-head branch.
They are not directly current-public-base routes.

## Residual-Head Compatibility Check

Read-only loader check:

```text
current base feature_dim: 12
M761 residual_head feature_dim: 64
load result: ValueError
```

The error is:

```text
residual feature_dim=64 does not match actor feature_dim=12
```

This means `alpha=0` is not a sufficient compatibility workaround. The residual
head is loaded before alpha can neutralize the residual action.

## Metadata Support Audit

Existing v4 source-rich tooling already has useful metadata support:

```text
fault_family
fidelity_class
warmup_mode
fault_onset_bucket
boundary_axis
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
source_obstacle_body_x
source_obstacle_body_y
source_obstacle_half_width
matched pair fault/fidelity/warmup fields
```

The useful pieces are the source generation, metadata schema, obstacle
retargeting, boundary-axis balancing, and fault/fidelity accounting. The
problem is the behavior replay path, not the metadata concept.

## Compatibility Decision

Do not run old M568+M761 source-rich tools as current public-base evidence.

Do not run current M1154 base through M761 residual-head routes.

Implement a minimal current-base no-residual source-rich adapter that reuses
the existing scenario/fault/source-generation conventions but evaluates the
current public-gate actor directly.

The adapter should:

```text
load only the current actor checkpoint;
avoid residual-head arguments;
preserve P0 actor inputs;
emit source-rich metadata required by M1180;
start with a small smoke run before any large mining;
write source_rows.csv, candidate_plan_rows.csv, normal_replay_rows.csv,
summary.json, and gate_summary.csv;
not train or promote anything.
```

## Minimal First Implementation Scope

M1182 should implement only enough to answer:

```text
Can the current public-gate actor generate source-rich near-boundary rows
with explicit obstacle geometry and fault/fidelity metadata?
```

M1182 should not implement wrong-history pairing yet. It should first create a
current-base source-rich normal-boundary sampler. Wrong-history intervention
should come only after source-rich near-boundary rows pass diversity gates.

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, row
conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: source_rich_route_compatibility_audit_route_to_no_residual_adapter_implementation
next: m1182-v4-public-base-no-residual-source-rich-adapter-implementation
```
