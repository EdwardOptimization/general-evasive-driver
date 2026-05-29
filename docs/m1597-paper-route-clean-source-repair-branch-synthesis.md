# M1597 Paper-Route Clean-Source Repair Branch Synthesis

## Summary

M1597 synthesizes the M1591-M1596 clean-source repair sub-branch.

Decision:

```text
clean_source_repair_synthesis_pivot_to_clean_active_set_contour_mapping
```

The branch should pivot. M1592 showed the clean-source repair objective has real
signal, but M1595 showed that naive source-edge balancing can erase that signal.
Another local cap tweak on the same public rows would be a gate-passing loop.
The next branch should map the clean active-set contour before any new replay or
implementation.

## evidence_summary

M1591 synthesized M1581-M1590 and admitted exactly one bounded clean-source
repair implementation.

M1592 implemented that repair:

```text
selected_source_edge_count: 7
clean_directed_pair_count: 34
clean_source_edge_count: 5
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.35294117647058826
invalid_directed_pair_count: 0
null_result_classification: source_concentrated_clean_surface
```

M1592 was a near-pass. It increased clean directed pairs from 7 to 34 and clean
source edges from 4 to 5, but missed the `0.35` source-share gate by a small
margin.

M1593 audited M1592 as a near-pass and admitted a design-only source-balanced
cap repair without relaxing thresholds.

M1594 designed that repair:

```text
target selected pairs: 96
max selected pairs per source edge: 12
minimum selected source edges: 8
source-edge round-robin selection: true
```

M1595 implemented it:

```text
selected_source_edge_count: 24
clean_directed_pair_count: 10
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.4
invalid_directed_pair_count: 0
null_result_classification: clean_count_shortfall
```

M1595 was negative. Source-edge round-robin selected many pairable but
history-null/control-only edges.

M1596 audited M1595 against M1592 and routed to synthesis before further repair.

## supported_claims

M1597 supports:

```text
the clean-source repair objective is not null;
M1592 is the strongest clean-source diagnostic result in this branch;
clean history-control rows can be generated beyond the original M1588 surface;
the useful clean surface is active-set sensitive;
source-edge balance must be contour-aware, not broad round-robin over all pairable edges;
the current public branch should pivot before further replay.
```

## falsified_claims

M1597 falsifies:

```text
broad pairability is sufficient for clean history-control evidence;
source-diverse intervention plumbing automatically produces clean rows;
lowering per-edge cap and round-robining all pairable edges fixes source concentration;
more selected source-edge diversity monotonically improves clean evidence;
another local cap tweak is a safe next step without synthesis.
```

## unsupported_claims

M1597 does not support:

```text
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
high-speed history sensitivity;
paper-level self-identification;
level3 anticipatory self-identification.
```

## failure_taxonomy_summary

```text
scenario_sampling_failure
objective_overfit
```

`scenario_sampling_failure` covers the M1592 source concentration and M1595
clean-count shortfall. `objective_overfit` is the branch risk: repeated cap
tuning on the same public rows would optimize the harness rather than discover
a robust contour.

## public_gate_overfit_risk

Risk:

```text
high
```

Reasons:

```text
M1588, M1592, and M1595 all reuse the public M1582/M1585 family;
M1592 missed by only 0.00294117647058826 on source share;
M1595 was an immediate local repair based on that miss and failed in the opposite direction;
another cap tweak would be selected using known public outcomes;
no private holdout or distribution-level evidence exists for this contour.
```

Mitigation:

```text
pivot to offline clean active-set contour mapping;
do not run replay or implementation first;
use M1592/M1595 as diagnostic surfaces;
pre-register contour features and stop conditions before any new source-generation run.
```

## next_branch_decision

Pivot to a new branch:

```text
paper_route_clean_active_set_contour_mapping
```

Next milestone:

```text
m1598-paper-route-clean-active-set-contour-mapping-design
```

M1598 should design an offline contour mapper over existing M1588/M1592/M1595
artifacts. It should characterize which combinations of source edge, target
family, donor family, window, selection source, response-action distance,
hidden distance, and normal-margin band produce clean versus dominated/null
rows.

M1598 must not run another replay, simulator smoke, PPO, training, private
holdout, candidate materialization, or threshold relaxation.

## Guardrails

```text
history_interventions_executed: false in M1597
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1598-paper-route-clean-active-set-contour-mapping-design
```
