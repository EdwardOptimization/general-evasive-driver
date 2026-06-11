# 测量 A：滑移起始在 obs72 中的可检测性与检测延迟（threshold-seeking 范式）

## 状态与声明边界

- 范式：self-ID 新范式（辨识嵌入有用动作本身——threshold braking / 增量极限搜索），
  四环结构中的第三环"滑移起始检测贴边"的**信号层测量**。
- 本文件只做信号可检测性 / 检测延迟 / 误报漏报 / 超调深度的测量声明；
  不做 driver 性能、训练、gate 有效性或 self-ID 能力声明。
- 数据：`experiments/feasibility_audit/slip_onset_detectability.json`
  （generated 20260611T081047Z，648 episodes，64.1 s，纯 CPU 零训练）；
  逐 episode 行：`runs/feasibility_audit/slip_onset_detectability/episodes.csv`；
  示例逐步轨迹：`runs/feasibility_audit/slip_onset_detectability/traces/`（8 个 CSV，
  纵/横 × 4 爬坡速率各 1 条）。
- 脚本：`scripts/feasibility_audit/slip_onset_detectability.py`（只新建文件，复用
  B2K2_final 机器；环境族基于 `docs/selfid-task-final-spec-2026-06.md`）。
- 种子流：SEED_BASE=20260616（与 B=20260612 / C=20260613 / final=20260615 不相交）。

## 1. 信号定义："手上感受到略微滑了"在 obs72 里是什么

obs72 布局（history_length=1，`scripts/feasibility_audit/voi_commitment_task_design.py`
OBS_DIM=72 断言）：ch0 vx/20、ch1 vy/12、ch2 yaw_rate/2.5、ch3 ax/15、ch5 转向执行器态
/max_steer、ch8 刹车执行器态（已含一阶迟滞，归一到 max_brake_force）。

**纵向（threshold braking）**：

```
y      = 15*obs[3] − (2.5*obs[2])·(12*obs[1])        # 实际 ax，扣掉 r·vy 离心耦合项
x      = [1, obs[8], (20*obs[0])²/100]               # 偏置、刹车执行器态、气动阻力项
signal = y − θ·x                                      # 减速度 shortfall（m/s²，正=滑）
```

**横向（threshold steering）**：

```
y      = 2.5*obs[2]                                   # 实际 yaw_rate
x      = [1, obs[5]·(20*obs[0])/10]                   # 偏置、steer·vx（线性区增益回归子）
signal = sign(obs[5])·(θ·x − y)                       # yaw_rate deficit（rad/s，正=推头）
```

θ 由**门控 RLS 在线自标定**（遗忘 0.995，warmup 10 步恒更新，之后仅当
signal < 0.5τ 时更新——单边门：响应不足冻结模型，响应过剩继续自适应）。

**为什么必须自标定（M150 教训：capability not parameter）**：brake_scale ∈ [0.80,1.15]、
mass_scale ∈ [0.85,1.20] 随机化使"指令→力→减速度"映射本身未知，actor 无法用固定模型算
期望减速度。shortfall 信号辨识的是**局部增益的塌缩点**，即有效组合极限
0.98·μ·Fz_rear/mass（dynamics.py `tire_forces` 的硬 clamp）/ 前胎 tanh 饱和——
是 capability（"我还能要到多少减速度/横摆"），不是 μ、不是 brake_scale。实测佐证：
纵向拟合增益中位 |θ₁|=3.84 m/s² per 刹车满量程（真值 max_brake_force/mass，base
4.14，随机化下被正确吸收）；横向拟合增益 θ₁=2.016 → dr/dδ_norm = θ₁·v/10 ≈ 1.61
rad/s @8 m/s，对线性单轨理论值 v·max_steer/(L+Kv²)=1.71 偏差 6%（均见 JSON
`*.fitted_gain_median`）。

旧发现的重定位：刹车把 μ 写进速度寄存器，在本范式下不再是缺陷——刹车本来就是任务动作，
写进去的速度损失就是任务要付的探测代价的一部分；K2 紧窗口不可对冲（条件 VoI 的窗口
依赖）反而要求辨识必须嵌在动作里完成，这正是本测量的动机。

## 2. 测量装置（实测条件）

- 环境：B2K2_final 动力学/赛道族（r=900 m 圆弧、dt=0.02、v0=8 m/s、连续 μ∈[0.25,1.15]），
  扩展 brake_scale [0.80,1.15] + mass_scale [0.85,1.20] 随机化。
- 与任务环境的偏差（JSON `env_family.deviations` 全列）：障碍物关闭（爬坡发生在
  pre-reveal 段，pre-reveal 的 obs72 与任务族逐位一致——障碍 slot 在 reveal 前恒零）；
  max_steps 600（慢爬坡需要 >5.7 s，原生 285 步窗口内的覆盖率单独报告）；横向延迟
  测量另用 track_width=30 m 消除 off_track 截断（检测器输入不含赛道宽度，物理不变；
  原生 5 m 赛道保留用于"检测先于冲出"的 lead 测量）。
- 真值（仅 harness 可见，检测器只看 obs72）：纵向 = |drive_force| ≥ 0.98·μ·Fz_rear
  （clamp 生效）；横向 = 前胎利用率 |fy_front|/(μ·Fz_front) ≥ 0.90。
- 刺激：刹车/转向指令爬坡 0.05 / 0.1 / 0.2 / 0.4 满量程每秒；亚极限组（误报测量）用
  truth 构造的上限（纵向 0.6·b_sat，横向稳态利用率 0.5 对应转角）——构造用了特权量，
  但只用于出题，检测器与信号均纯 obs72。
- 阈值标定：每轴 32 条独立种子亚极限 episode，τ = max(1.5×最大信号, floor)。实测亚极限
  残差极小（纵向 max 0.0399 m/s²、横向 max 0.0095 rad/s，JSON `calibration`），两轴均落
  在 floor 上：**τ_long = 0.15 m/s²，τ_lat = 0.03 rad/s**。
- 触发规则：armed（≥15 次更新且激励跨度达标）后 signal > τ 连续 3 步。

## 3. 实测结果

### 3.1 纵向：检测延迟与覆盖（240 ramp episodes）

JSON `longitudinal.per_rate`：

| 爬坡速率 (满量程/s) | n / 真值饱和 / 检出 | 延迟中位 (步=ms) | 延迟 p90 | 超调中位 (满量程) | 超出极限 % 中位 / p90 | 饱和落在 285 步窗内 |
|---|---|---|---|---|---|---|
| 0.05 | 60 / 6 / 4 | 37.5 = 750 ms | 43.6 | 0.038 | 13.4% / 13.7% | 16.7% |
| 0.10 | 60 / 17 / 11 | 20 = 400 ms | 26 | 0.040 | 9.7% / 12.0% | 76.5% |
| 0.20 | 60 / 33 / 31 | 12 = 240 ms | 14 | 0.048 | 8.8% / 15.3% | 100% |
| 0.40 | 60 / 41 / 36 | 7 = 140 ms | 8 | 0.049 | 8.6% / 14.4% | 100% |

- **误报：0/64 亚极限 episode；0/143 未达饱和的 ramp episode**（JSON
  `longitudinal.false_positives`）。
- 信号分离度：真值饱和后 10 步的 shortfall 中位 0.181 m/s²，是饱和前最大信号 p99
  （0.0494）的 **3.67 倍**（JSON `longitudinal.signal_validation`）。
- 漏报 15/97（15.5%）全部是**截断型**：饱和出现后 episode 仅剩中位 8 步（全部 ≤33 步，
  12/15 ≤16 步）即因 speed_too_low 终止——8 m/s 入速下车先停了，不是检测器漏掉持续
  存在的饱和（episodes.csv `post_onset_steps` 列）。
- 覆盖分解（episodes.csv 重算）：240 条 ramp 中 97 条达到 clamp；84 条**物理不可饱和**
  （0.98·μ·Fz_rear > max_brake_force，即高 μ/低 brake_scale 下刹车执行器先到顶——
  对这类车"全力刹车安全"本身就是辨识结论）；59 条可饱和但车先停。
- 公式校验（JSON `theory_check_long`）：超调(满量程) ≈ τ/|da/db| + 3·dt·rate，
  预测中位 0.0558 vs 实测 0.048。**τ 项不随爬坡速率变化**——实测超调满量程
  0.038→0.049（速率 ×8 只涨 29%），印证"快爬坡几乎不多付超调、只省时间"。

### 3.2 横向：检测延迟（240 ramp episodes，30 m 宽赛道 harness）

JSON `lateral.per_rate`：

| 爬坡速率 | n / 真值起始 / 检出 | 延迟中位 (步=ms) | 延迟 p90 | 检出时前胎利用率中位 | 超出极限 % 中位 / p90 |
|---|---|---|---|---|---|
| 0.05 | 60 / 19 / 16 | 56.5 = 1130 ms | 287 | 0.988 | 21.5% / 27.2% |
| 0.10 | 60 / 60 / 60 | 20 = 400 ms | 126 | 0.944 | 5.8% / 24.3% |
| 0.20 | 60 / 60 / 60 | 10 = 200 ms | 21 | 0.939 | 7.0% / 26.9% |
| 0.40 | 60 / 60 / 60 | 10 = 200 ms | 43 | 0.966 | 14.8% / 55.2% |

- **误报：0/64 亚极限 episode**（利用率 0.5 稳态保持，含 tanh 已 9% 偏线性的工况）。
- 真值边界是软的（tanh 渐进），"延迟"对 0.90 利用率交叉的定义敏感：低 μ 单元会出现
  负延迟（提前于 0.90 触发，per_cell 表）。更稳的口径是**检出时利用率 0.94–0.99**
  （上表第 5 列）：检测器把车贴到前胎能力的 94–99% 才报警，且亚极限零误报。
- 信号分离：onset+10 步 deficit 中位 0.0278 rad/s = 亚极限标定最大残差（0.0095）的
  **2.9 倍**；注意 JSON `lateral.signal_validation.separation_ratio_median_over_p99`
  =0.64 用的是"同 episode 饱和前最大信号"做分母，因 tanh 渐进该分母已被接近极限的
  样本污染，不宜引用。
- 漏报 3/199，全部 off_track 截断型。
- **原生 5 m 赛道 lead 测量**（JSON `lateral_native_track`，40 episodes）：40 条全部
  off_track 终止；真值起始先于冲出的 20 条中检出 16 条，**检测先于 off_track 中位 39 步
  （780 ms），p10 8 步（160 ms）**——反射层（v4/v5 肌肉记忆救车）有出手窗口。

### 3.3 超调深度表（爬坡速率 × μ 段 → 超出极限 %，中位）

JSON `longitudinal.per_cell` / `lateral.per_cell`（n/onset/det 详表在 JSON；
"—" = 该单元真值饱和事件 <3，无统计）：

纵向（v0=8 m/s 原生入速）：

| rate \ μ | [0.25,0.45) | [0.45,0.65) | [0.65,0.85) | [0.85,1.15) |
|---|---|---|---|---|
| 0.05 | 13.4% (4/6 检出) | — (0 onset) | — | — |
| 0.10 | 9.7% (11/14) | — (3 onset, 停车截断) | — | — |
| 0.20 | 11.4% (16/16) | 7.0% (14/14) | — (1/3) | — |
| 0.40 | 12.5% (14/14) | 8.3% (14/14) | 5.4% (6/7) | 5.2% (2/6) |

横向（30 m harness）：

| rate \ μ | [0.25,0.45) | [0.45,0.65) | [0.65,0.85) | [0.85,1.15) |
|---|---|---|---|---|
| 0.05 | 21.6% | 17.9% (2/5) | — | — |
| 0.10 | 26.7% | 14.9% | 7.6% | 0.3% |
| 0.20 | 38.9% | 19.5% | 8.4% | 1.6% |
| 0.40 | 62.2% | 26.7% | 14.4% | 3.5% |

横向低 μ 单元的高百分比主因是分母小（低 μ 下 0.90 利用率对应的转角小），绝对超调
（满量程 0.04–0.08，`overshoot_frac_median`）与纵向同量级。

## 4. actor-visible 检测器规格（供测量 B / 未来策略复用）

- 实现：`scripts/feasibility_audit/slip_onset_detectability.py::SlipOnsetDetector`
  （纯 obs72 流函数，无特权、无动作输入——只用执行器态通道 ch5/ch8）；机器可读规格
  含全部公式与常数：JSON `detector_spec`。
- 常数：warmup 10 步；armed 需 ≥15 次更新且激励跨度（ch8 ≥0.04 / steer·vx ≥0.30）；
  更新门 signal < 0.5τ（单边）；触发 signal > τ 连续 3 步；τ_long=0.15 m/s²、
  τ_lat=0.03 rad/s（floor 生效，标定见 `calibration`）。
- 注意 armed 的激励要求意味着检测器**只在动作爬坡中有效**——这正是范式要求：不动手
  就没有手感。

## 5. 推断（与实测分开）

1. **延迟-超调权衡由 τ/增益主导，快爬坡近乎免费**：超调(力的满量程) ≈ τ·mass/F_max +
   3·dt·rate，第一项与速率无关（实测 0.038→0.049 跨 8 倍速率）。推断：策略侧应该用
   **快爬坡（≥0.2 满量程/s）+ 反射救车**而非慢爬坡省超调；慢爬坡在 5.7 s 任务窗内
   还放不下（rate 0.05 仅 16.7% 饱和事件落在 285 步内）。
2. **8 m/s 入速下纵向辨识只在低/中 μ 有"题"可答**：35%（84/240）episode 刹车执行器
   先于轮胎到顶（高 μ × brake_scale 随机化），此时 threshold braking 的正确输出是
   "全力刹车安全"——这与任务结构吻合：B2K2 的 VoI 恰好集中在低/中 μ 段（μ-相关障碍
   距离），高 μ 段全力刹/常规绕已可行。
3. **漏报本质是停车截断而非信号缺失**：漏报集中在可用窗极短的 episode（15 个漏报中
   12 个 onset 后可用窗 ≤16 步，全部 ≤33 步）。对任务策略含义：threshold
   braking 应在还有速度余量时启动（reveal 前贴边），而不是临停前。
4. **横向"贴边"语义应以利用率口径表述**：检出时利用率 0.94–0.99、亚极限零误报，
   说明 obs72 足以支撑"把前胎用到 ~95% 再交给反射层"的横向贴边控制；0.90 交叉
   延迟口径受 tanh 软边界影响，不建议作为 spec 指标。
5. **反射层衔接可行**：原生赛道上检测中位领先 off_track 780 ms（39 步），大于 v4/v5
   反射层的动作时延（单步直接动作），推断"检测→反射救车"闭环在时间上闭得上。
6. 局限：观测无噪声（τ 落在 floor 上，真实噪声下 τ 与延迟会同步抬高——τ 项超调
   线性放大）；tire_stiffness/actuator_tau 仍按 B2K2_final 钉死；刺激为开环爬坡，
   闭环策略下激励谱不同；横向延迟统计用了 30 m 宽赛道 harness。这些都不改变信号
   定义，但量级外推需测量 B 验证。

## 6. 产物

- `scripts/feasibility_audit/slip_onset_detectability.py`（含 SlipOnsetDetector 规格类）
- `experiments/feasibility_audit/slip_onset_detectability.json`（全部聚合 + 检测器规格 + 标定）
- `runs/feasibility_audit/slip_onset_detectability/episodes.csv`（648 行逐 episode）
- `runs/feasibility_audit/slip_onset_detectability/traces/*.csv`（8 条逐步信号轨迹）
