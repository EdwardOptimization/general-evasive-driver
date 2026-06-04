# M2714 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Panel Materialization Preflight

## Metadata

- status: completed
- decision: route_to_current_m1690_exact_executable_reentry_panel_result_audit
- manifest: `experiments/manifests/m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight.json`
- run dir: `runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel`
- next: `m2715-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m2715-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-result-audit.json`

## Materialized Surface

```text
input source rows: 12
M1690 workload rows read: 864
M2693 anchor task_source_ids: 9
selected profiles per anchor: 4
exact executable candidate rows: 36
profile context rows: 36
missing selected profile rows: 0
candidate rows all existing M1690: True
candidate rows clean schedule: True
```

Selected profiles:

```text
L0_current_masked
L2_window_50_current_tiled
L3_online_gru
L3_reset_control_corrected
```

## Protected Proposal Exclusions

```text
M2710 protected proposal exclusion rows: 12
protected execution-admitted rows: 0
ready-existing protected rows: 0
existing exact protected M1690 matches: 0
fabricated exact protected M1690 matches: 0
protected rows in success denominator: False
```

## Actor And Claim Boundary

```text
actor contract 72/action 3: True
hidden oracle actor input detected: False
target labels actor-visible: False
protected labels actor-visible: False
execution_run: False
validation_run: False
training_run: False
ranking_run: False
driver_performance_claim_made: False
paper_claim_made: False
current_sim_verdict_claim_made: False
level3_self_id_claim_made: False
```

M2714 is materialization only. It does not reset, step, roll out, replay,
validate, train, run PPO, rank profiles, select a winner, promote a checkpoint,
compute success-rate verdicts, or claim repair success, driver performance,
paper evidence, current-sim verdict, high-fidelity validation, full ideal driver
completion, or self-ID evidence.

## Gates

```text
required artifacts present: True
gate matrix pass: True
actor contract guard rows: 12
claim-boundary rows: 28
gate rows: 35
status_pass: True
```

## Follow-Up

If this artifact passes audit, the only admitted continuation is the M2715
materialization result audit. Any later bounded execution preflight must be
separately pre-registered and must keep M2710 proposed protected rows excluded
from execution denominators and performance claims.
