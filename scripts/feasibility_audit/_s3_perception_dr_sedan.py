"""S3 LEVER (surgical + reversible): perception-DR fine-tune of ONLY the Sedan avoid head to robustify
small-reveal avoid under obstacle-perception noise. Student acts on NOISY obstacle perception; oracle labels
on the CLEAN true state; BC the Sedan avoid head on (noisy_obs -> clean-oracle-action). Everything else
(trunk, FiLM, drift head, UAZBUS/BMW avoid heads) is FROZEN -> those stay bit-identical to the capstone."""
import sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle_conditioned as cond
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
from autodrift.observation_degradation_wrapper import DEFAULT_NOISE_SEED_STREAM, GEOMETRY_NOISE_SEED_SUBSTREAM
RUN=Path('runs/feasibility_audit/phase4_f2')
OBST_PRESENT=[44,51,58,65]; OBST_CONT=np.array([45,46,47,48,52,53,54,55,59,60,61,62,66,67,68,69])
SEDAN_IDX=film.VEHICLES.index("sedan"); SED_OH=cond._vehicle_onehot("sedan")

def degrade_obstacle(obs, rng, gn):
    obs=np.asarray(obs,np.float32).copy()
    if gn<=0: return obs
    noise=rng.normal(0.0,gn,len(OBST_CONT)).astype(np.float32)
    for si,pb in enumerate(OBST_PRESENT):
        if obs[pb]<=0.5: noise[si*4:si*4+4]=0.0
    obs[OBST_CONT]+=noise
    return obs

def dagger_perc_episode(client, model, sp, gn):
    """Student acts on noisy obstacle perception; oracle labels on clean true state.
    Stores (noisy_obs72 -> clean_oracle_action)."""
    reveal,mu,seed=float(sp["reveal"]),float(sp["mu"]),int(sp["seed"])
    oracle=f2.make_avoidance_teacher(reveal=reveal, mu=mu).factory()
    rng=np.random.default_rng([DEFAULT_NOISE_SEED_STREAM,seed,0,GEOMETRY_NOISE_SEED_SUBSTREAM])
    obs,reset_reply=client.reset(sp["scenario"], episode_id=str(sp["scenario"]["scenario_id"]), seed=seed)
    obs=np.asarray(obs,np.float32); info=dict(reset_reply.get("info",{}))
    frames=[]; targets=[]; steps=0; term=trunc=False; coll_any=False
    maxs=int(sp["scenario"]["max_steps"])
    while not (term or trunc) and steps<maxs:
        noisy=degrade_obstacle(obs, rng, gn)
        revealed=f2._obstacle_visible(obs, info)
        if f2._finite_obs72(obs) and (revealed or not f2.AVOIDANCE_BC_REVEAL_POST_ONLY):
            oracle_a=np.clip(np.asarray(oracle(steps, obs),dtype=np.float32),-1.0,1.0)  # oracle on CLEAN
            frames.append(np.concatenate([noisy.astype(np.float32), SED_OH],0))           # store NOISY obs75
            targets.append(oracle_a)
        else:
            _=oracle(steps, obs)
        action=np.clip(model.act(np.concatenate([noisy.astype(np.float32),SED_OH],0)),-1.0,1.0)  # student on NOISY
        obs,term,trunc,_st,info=client.step(action); obs=np.asarray(obs,np.float32); info=dict(info)
        coll_any=coll_any or bool(info.get("collision",False)) or str(info.get("termination_reason",""))=="obstacle_collision"
        steps+=1
    return (np.stack(frames).astype(np.float32) if frames else np.zeros((0,75),np.float32),
            np.stack(targets).astype(np.float32) if targets else np.zeros((0,3),np.float32))

def collect(clients, model, specs):
    res=[None]*len(specs); nW=min(len(clients),len(specs)); nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; c=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            res[i]=dagger_perc_episode(c, model, specs[i], specs[i]["gn"])
    with ThreadPoolExecutor(max_workers=nW) as ex:
        for fut in [ex.submit(worker,w) for w in range(nW)]: fut.result()
    F=[r[0] for r in res if r is not None and r[0].shape[0]>0]
    T=[r[1] for r in res if r is not None and r[1].shape[0]>0]
    return (np.concatenate(F,0) if F else np.zeros((0,75),np.float32),
            np.concatenate(T,0) if T else np.zeros((0,3),np.float32))

# ---- load capstone ----
ck=torch.load(RUN/'distill_final_integrated_policy.pt', map_location='cpu')
sd=ck['state_dict'] if isinstance(ck,dict) and 'state_dict' in ck else (ck.get('model',ck) if isinstance(ck,dict) else ck)
model=film.FiLMAvoidActorCritic(obs_dim=75); model.load_state_dict(sd); model.eval()
# snapshot OTHER heads to PROVE they don't move
import copy
orig_sd=copy.deepcopy(model.state_dict())

# ---- build Sedan perception-DR collection specs (emphasis small reveal; DR over gn) ----
avoid_all=INT._load_avoid_cells()
d3v._install_vehicle("sedan")
# weight small reveals heavier (they are the susceptible cells)
GN_DR=[0.0,0.04,0.08]; SEEDS=4
specs=[]
for cell in avoid_all:
    rv=cell["reveal"]
    nseed = SEEDS if rv<=12.0 else 2   # more data on the susceptible small-reveal cells
    for gn in GN_DR:
        for s in range(nseed):
            seed=int(f2._seed_for("s3percDR","sedan","avoid",int(rv*10),s,round(gn,3),round(cell["mu"],4),cell["geometry"]))
            sc=INT._avoid_scenario("sedan", cell, seed)
            specs.append({"reveal":rv,"mu":cell["mu"],"seed":seed,"scenario":sc,"gn":gn})
print(f"collecting {len(specs)} Sedan perception-DR DAgger episodes (gn in {GN_DR})...", flush=True)
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_s3dr_w{w}_stderr.log') for w in range(8)]
t0=time.time()
try:
    X,Y=collect(clients, model, specs)
finally:
    pass  # keep clients for re-measure
print(f"collected {X.shape[0]} recovery labels in {time.time()-t0:.0f}s", flush=True)

# ---- freeze all but Sedan avoid head; BC fine-tune ----
for p in model.parameters(): p.requires_grad=False
for p in model.avoid_heads[SEDAN_IDX].parameters(): p.requires_grad=True
opt=torch.optim.Adam(model.avoid_heads[SEDAN_IDX].parameters(), lr=1e-3)
Xt=torch.tensor(X); Yt=torch.tensor(Y); N=X.shape[0]; BS=512
model.train()
print("fine-tuning Sedan avoid head (trunk/drift/other-heads FROZEN)...", flush=True)
for ep in range(1200):
    idx=torch.randint(0,N,(BS,))
    pred=model.actor_forward(Xt[idx])   # squashed mean
    loss=((pred-Yt[idx])**2).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if ep%300==0 or ep==1199:
        print(f"  ep {ep:4d}  bc_mse={loss.item():.4e}", flush=True)
model.eval()
# PROVE other params unchanged
new_sd=model.state_dict(); moved=[]
for k in orig_sd:
    if not torch.equal(orig_sd[k], new_sd[k]): moved.append(k)
print("PARAMS THAT MOVED (should be ONLY sedan avoid head idx0):", moved, flush=True)
torch.save({"state_dict":model.state_dict()}, RUN/'distill_final_perceptionDR_policy.pt')

# ---- re-measure Sedan perception ladder (vs capstone) ----
sys.path.insert(0,'scripts/feasibility_audit')
import importlib.util
spec=importlib.util.spec_from_file_location("s3perc","scripts/feasibility_audit/_s3_perception.py")
# reuse eval logic inline instead of importing (it runs on import); replicate quickly:
from concurrent.futures import ThreadPoolExecutor as TPE
def eval_perc(model, vehicle, av_sub, gn, label):
    specs=INT._select_specs(vehicle, [], av_sub, n_drift=0, n_avoid=4, namespace="s3percDRcheck")
    res=[None]*len(specs); nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; c=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]
            base=INT._cond_policy(model, vehicle)
            rng=np.random.default_rng([DEFAULT_NOISE_SEED_STREAM,int(sp["seed"]),0,GEOMETRY_NOISE_SEED_SUBSTREAM])
            def pol(step,obs,_r=rng,_g=gn):
                return base(step, degrade_obstacle(obs,_r,_g))
            r=f2.run_episode(c, sp["scenario"], "avoidance", pol, seed=int(sp["seed"]),
                             mu=float(cell["mu"]), reveal=float(cell["reveal"]))
            res[i]={"s":bool(r["success"]),"rev":round(cell["reveal"],1)}
    with TPE(max_workers=8) as ex:
        for fut in [ex.submit(worker,w) for w in range(8)]: fut.result()
    av=[x["s"] for x in res if x]; byr={}
    for x in res:
        if x: byr.setdefault(x["rev"],[]).append(x["s"])
    brk=" ".join(f"r{k}={np.mean(v):.2f}" for k,v in sorted(byr.items()))
    print(f"  [{label}] avoid={np.mean(av):.3f}({sum(av)}/{len(av)}) | {brk}", flush=True)
    return float(np.mean(av))

d3v._install_vehicle("sedan")
av_sub=[]
allmu=sorted(c['mu'] for c in avoid_all); midmu=allmu[len(allmu)//2]
for rv in sorted(set(c['reveal'] for c in avoid_all)):
    cs=[c for c in avoid_all if abs(c['reveal']-rv)<1e-6]
    if cs: av_sub.append(min(cs,key=lambda c:abs(c['mu']-midmu)))
print("\n=== Sedan perception ladder: perception-DR head vs capstone(0.875 harsh) ===", flush=True)
out={}
for name,gn in [("P1_clean",0.0),("P3_moderate",0.04),("P4_harsh",0.08)]:
    out[name]=eval_perc(model, "sedan", av_sub, gn, f"DR/{name}(gn={gn})")
for c in clients:
    try: c.close()
    except Exception: pass
Path(RUN/'_s3_perception_dr_sedan.json').write_text(json.dumps(out,indent=2))
print("\nDONE. perception-DR Sedan ladder:", out)
