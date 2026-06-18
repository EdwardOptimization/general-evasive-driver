"""Clean RMA-DAgger v2: separated pools (teacher FRAMES vs phi SEQUENCES -> no window pollution) + best-round
selection + LEAVE-ONE-VEHICLE-OUT (--holdout). The killer test: train on 2 vehicles, deploy on the unseen 3rd via
phi-inferred z_hat. The one-hot structurally cannot drive an unseen vehicle; continuous self-ID can (if it generalises)."""
import sys, json, time, threading, argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); SEQ=RUN/'selfid_avoid_seqs'; ALLVEH=["sedan","uazbus","bmw"]
W=M.AdaptationMLP().window; ZD=M.RICH_Z

def load_base():
    out={v:[] for v in ALLVEH}
    for v in ALLVEH:
        d=np.load(SEQ/f'avoid_{v}.npz', allow_pickle=True)
        for obs,act,succ in zip(d["obs"],d["act"],d["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(succ): out[v].append((obs,act))
    return out

def frames_from(TF, vehs):
    OBS=[];EX=[];ACT=[]
    for v in vehs:
        ex=M.vehicle_extrinsics(v)
        for obs,act in TF[v]:
            OBS.append(obs); ACT.append(act); EX.append(np.tile(ex,(obs.shape[0],1)))
    return (torch.tensor(np.concatenate(OBS,0)), torch.tensor(np.concatenate(EX,0).astype(np.float32)),
            torch.tensor(np.concatenate(ACT,0)))

def windows_from(PS, vehs, stride=3):
    XS=[];EX=[]
    for v in vehs:
        ex=M.vehicle_extrinsics(v)
        for obs,act in PS[v]:
            T=obs.shape[0]; prev=np.zeros_like(act); prev[1:]=act[:-1]; step=np.concatenate([obs,prev],1)
            for t in range(1,T,stride):
                lo=max(0,t-W+1); ch=step[lo:t+1]
                if ch.shape[0]<W: ch=np.concatenate([np.zeros((W-ch.shape[0],75),np.float32),ch],0)
                XS.append(ch.reshape(-1)); EX.append(ex)
    return torch.tensor(np.stack(XS)), torch.tensor(np.stack(EX).astype(np.float32))

def train_teacher(TF, vehs, *, epochs, enc=None, film=None, lr=1e-3):
    OBS,EX,ACT=frames_from(TF,vehs); N=OBS.shape[0]
    enc=enc or M.ExtrinsicsEncoder(z_dim=ZD); film=film or M.FiLMZActorCritic(z_dim=ZD)
    opt=torch.optim.Adam(list(enc.parameters())+list(film.parameters()), lr=lr); enc.train(); film.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(512,)); z=enc(EX[idx]); X=torch.cat([OBS[idx],z],1)
        loss=((film.actor_forward(X)-ACT[idx])**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    enc.eval(); film.eval(); return enc,film,float(loss.item())

def train_phi(PS, vehs, enc, *, epochs, phi=None, lr=1e-3):
    X,EX=windows_from(PS,vehs); N=X.shape[0]; phi=phi or M.AdaptationMLP(z_dim=ZD)
    with torch.no_grad(): Z=enc(EX)
    opt=torch.optim.Adam(phi.parameters(), lr=lr); phi.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(1024,)); loss=((phi(X[idx])-Z[idx])**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    phi.eval(); return phi,float(loss.item())

class PhiDeploy:
    def __init__(self, film, phi, oracle=None):
        self.film=film; self.phi=phi; self.oracle=oracle; self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
        self.obs_log=[]; self.lab=[]; self.seq=[]
    def __call__(self, s, obs):
        obs=np.asarray(obs,np.float32); step_in=np.concatenate([obs,self.prev]); self.hist.append(step_in); self.seq.append(step_in.copy())
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zh=self.phi(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        if self.oracle is not None and f2._obstacle_visible(obs,{}):
            self.obs_log.append(obs.copy()); self.lab.append(np.clip(self.oracle(s,obs),-1,1).astype(np.float32))
        a=self.film.act(np.concatenate([obs,zh.astype(np.float32)])); self.prev=a; return a

def run_cells(clients, v, builder, specs, kind, collect=False):
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock(); R_obs=[];R_lab=[];seqs=[]
    shared=builder(v) if kind=="stateless" else None
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]
            if kind=="stateless": pol=shared
            else:
                orc=f2.make_avoidance_teacher(reveal=float(cell["reveal"]),mu=float(cell["mu"])).factory() if collect else None
                pol=builder(v,orc)
            r=f2.run_episode(c,sp["scenario"],"avoidance",pol,seed=int(sp["seed"]),mu=float(cell["mu"]),reveal=float(cell["reveal"]))
            res[i]=bool(r["success"])
            if collect and isinstance(pol,PhiDeploy):
                with lock:
                    if pol.obs_log: R_obs.append(np.stack(pol.obs_log)); R_lab.append(np.stack(pol.lab))
                    if len(pol.seq)>=2:
                        sq=np.stack(pol.seq); seqs.append((sq[:,:72].copy(),sq[:,72:75].copy()))
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    return float(np.mean([x for x in res if x is not None])), (np.concatenate(R_obs,0) if R_obs else None, np.concatenate(R_lab,0) if R_lab else None), seqs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--holdout",default="",help="vehicle to LEAVE OUT of training")
    ap.add_argument("--rounds",type=int,default=2); ap.add_argument("--teacher-epochs",type=int,default=1500); ap.add_argument("--phi-epochs",type=int,default=2000)
    a=ap.parse_args(); torch.manual_seed(0)
    TRAIN=[v for v in ALLVEH if v!=a.holdout]; tag=a.holdout or "all3"
    print(f"holdout={a.holdout or 'NONE'}  TRAIN={TRAIN}  (validate on ALL {ALLVEH})", flush=True)
    avoid_all=INT._load_avoid_cells(); mus=sorted(set(round(c['mu'],3) for c in avoid_all))
    val_cells=[c for c in avoid_all if round(c['mu'],3) in {mus[1],mus[2]}]
    base=load_base(); TF={v:list(base[v]) for v in TRAIN}; PS={v:list(base[v]) for v in TRAIN}
    clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_rmav2_w{w}_stderr.log') for w in range(8)]
    log={"holdout":a.holdout,"train":TRAIN,"rounds":[]}; best={"score":-1}; t0=time.time()
    try:
        enc=film=phi=None
        for rd in range(a.rounds+1):
            enc,film,bl=train_teacher(TF,TRAIN,epochs=a.teacher_epochs,enc=enc,film=film)
            phi,pl=train_phi(PS,TRAIN,enc,epochs=a.phi_epochs,phi=phi)
            row={"round":rd,"phi":{}}
            for v in ALLVEH:
                d3v._install_vehicle(v)
                vs=INT._select_specs(v,[],val_cells,n_drift=0,n_avoid=3,namespace=f"v2val{tag}{rd}")
                ph,_,_=run_cells(clients,v,lambda vv,orc=None:PhiDeploy(film,phi),vs,"perep")
                row["phi"][v]=ph
            train_score=float(np.mean([row["phi"][v] for v in TRAIN]))   # select on TRAIN vehicles only
            hold = row["phi"].get(a.holdout) if a.holdout else None
            row["train_score"]=train_score; row["holdout_score"]=hold
            print(f"ROUND {rd}: phi avoid={ {k:round(x,3) for k,x in row['phi'].items()} } | train={train_score:.3f}"
                  + (f" | HELD-OUT {a.holdout}={hold:.3f}" if a.holdout else "") + f"  [{time.time()-t0:.0f}s]", flush=True)
            log["rounds"].append(row)
            if train_score>best["score"]:
                best={"score":train_score,"round":rd}
                torch.save({"enc":enc.state_dict(),"film":film.state_dict(),"phi":phi.state_dict(),"round":rd,"holdout":a.holdout},
                           RUN/f'selfid_rma_v2_holdout_{tag}.pt')
            if rd==a.rounds: break
            for v in TRAIN:    # DAgger only on TRAIN vehicles (held-out stays UNSEEN)
                d3v._install_vehicle(v)
                ds=INT._select_specs(v,[],avoid_all,n_drift=0,n_avoid=2,namespace=f"v2dag{tag}{rd}")
                _,(ro,rl),sseq=run_cells(clients,v,lambda vv,orc:PhiDeploy(film,phi,oracle=orc),ds,"perep",collect=True)
                if ro is not None: TF[v].append((ro.astype(np.float32),rl.astype(np.float32)))  # recovery (obs,ORACLE act) -> teacher frames
                PS[v].extend(sseq)   # student trajectories -> phi history ONLY (their action is the STUDENT's, not the oracle's -> must NOT train the teacher)
    finally:
        for c in clients:
            try: c.close()
            except Exception: pass
    log["best"]=best
    Path(RUN/f'_selfid_rma_v2_{tag}.json').write_text(json.dumps(log,indent=2))
    br=log["rounds"][best["round"]]
    print(f"\nDONE {time.time()-t0:.0f}s. BEST round {best['round']}: phi avoid={ {k:round(x,3) for k,x in br['phi'].items()} }"
          + (f"  HELD-OUT {a.holdout}={br['holdout_score']:.3f}" if a.holdout else ""))
if __name__=="__main__": main()
