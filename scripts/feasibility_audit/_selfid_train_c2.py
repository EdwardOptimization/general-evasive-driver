"""STEP C2: train the GRU self-ID avoid policy by BPTT BC on pooled 3-vehicle sequences. NO vehicle label —
the GRU must infer the vehicle from the (obs72, prev_action) history. Input per step = [obs72_t | act_{t-1}]
(teacher-forced prev action during BC); target = oracle action_t. Padded/masked variable-length sequences."""
import sys, json, time
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); SEQ=RUN/'selfid_avoid_seqs'
VEH=["sedan","uazbus","bmw"]

def load_episodes():
    eps=[]
    for v in VEH:
        d=np.load(SEQ/f'avoid_{v}.npz', allow_pickle=True)
        for obs,act,succ in zip(d["obs"], d["act"], d["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(succ):   # only successful oracle demos
                eps.append((obs,act,v))
    return eps

def make_batch(eps, idx):
    B=len(idx); T=max(eps[i][0].shape[0] for i in idx)
    X=np.zeros((B,T,75),np.float32); Y=np.zeros((B,T,3),np.float32); Mk=np.zeros((B,T),np.float32)
    for b,i in enumerate(idx):
        obs,act,_=eps[i]; t=obs.shape[0]
        prev=np.zeros_like(act); prev[1:]=act[:-1]      # teacher-forced prev action (prev_0 = 0)
        X[b,:t]=np.concatenate([obs,prev],1); Y[b,:t]=act; Mk[b,:t]=1.0
    return torch.tensor(X), torch.tensor(Y), torch.tensor(Mk)

def main():
    torch.manual_seed(0)
    eps=load_episodes()
    print(f"loaded {len(eps)} successful avoid demo sequences "
          f"({ {v: sum(1 for e in eps if e[2]==v) for v in VEH} })", flush=True)
    g=M.GRUSelfIDActorCritic(); opt=torch.optim.Adam(g.parameters(), lr=5e-4)
    N=len(eps); BS=32; EPOCHS=400; t0=time.time()
    g.train()
    for ep in range(EPOCHS):
        perm=np.random.permutation(N); tot=0.0; nb=0
        for s in range(0,N,BS):
            idx=perm[s:s+BS]
            X,Y,Mk=make_batch(eps, idx)
            pred=g.forward_seq(X)
            loss=(((pred-Y)**2).sum(-1)*Mk).sum()/Mk.sum().clamp(min=1)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(g.parameters(),5.0); opt.step()
            tot+=loss.item(); nb+=1
        if ep%50==0 or ep==EPOCHS-1:
            print(f"  ep {ep:4d}  bc_mse={tot/nb:.4e}  ({time.time()-t0:.0f}s)", flush=True)
    g.eval()
    torch.save({"state_dict":g.state_dict(),"arch":"GRUSelfIDActorCritic"}, RUN/'selfid_c2_gru_policy.pt')
    print("saved selfid_c2_gru_policy.pt", flush=True)
if __name__=="__main__": main()
