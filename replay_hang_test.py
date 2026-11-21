import argparse, json, subprocess, sys, os, glob
from pathlib import Path
from diagnostics import fen
os.environ.setdefault("MAKEFUN_ENV_URL","http://x")
parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int, default=0, help='maximum positions (0 tests all saved positions)')
parser.add_argument('--budget', type=int, default=150000)
args = parser.parse_args()
FILES = glob.glob("/root/.makefun/trials/tiny-chess-01/*/trial-*/state/transcript.ndjson")
def positions(fen0, moves):
    yield fen0
    import engine as e
    s = e.pf(fen0)
    for u in moves:
        l = e.lm(s)
        mm = None
        for m in l:
            if e.mu(m)==u: mm=m;break
        if mm is None: raise SystemExit(f"illegal {u} in {e.fen(s) if hasattr(e,'fen') else '?'}")
        e.ai(s,mm)
        yield fen(s)
def worker(fen, budget):
    code = f'''
import os,sys
os.environ.setdefault("MAKEFUN_ENV_URL","http://x")
sys.path.insert(0,{str(Path(__file__).resolve().parent)!r})
import engine as e
e.NL={budget}
s=e.pf({fen!r})
m=e.sr(s,{{e.mu(m) for m in e.lm(s)}},{{s.h:1}})
print("done", e.mu(m) if m is not None else "0000")
'''
    r = subprocess.run([sys.executable,"-P","-c",code],capture_output=True,text=True,timeout=15)
    return r.returncode, r.stdout.strip(), r.stderr.strip()[-200:]
tot=0; hangs=0
for f in FILES:
    for line in open(f):
        ev=json.loads(line)
        if ev.get("kind")!="start": continue
        moves=[]
        # reconstruct move sequence from this transcript: collect this game's house/our moves via ply ordering
    # simpler: state.json games
    sj = f.replace("transcript.ndjson","state.json")
    try: st=json.load(open(sj))
    except Exception: continue
    for g in st.get("games",[]):
        mv=g.get("moves") or []
        start=g.get("start_fen") or "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        # replay on the fly to get FEN per ply
        import engine as e
        s=e.pf(start)
        for i,u in enumerate(mv+[]):
            tot+=1
            current_fen = fen(s)
            rc,out,err=None,None,None
            try:
                rc,out,err=worker(current_fen,args.budget)
            except subprocess.TimeoutExpired:
                hangs+=1
                print("HANG at", f, "game",g.get("game"),"ply",i, "fen", current_fen)
            if rc is not None and (rc!=0 or not out.startswith("done")):
                hangs+=1
                print("FAIL", f, "game",g.get("game"),"ply",i,"rc",rc,"out",out,"err",err, "fen",current_fen)
            # apply move
            for m in e.lm(s):
                if e.mu(m)==u: e.ai(s,m); break
            else:
                raise SystemExit(f"illegal saved move {u} in {current_fen}")
            if args.limit and tot >= args.limit:
                print("total",tot,"hangs/fails",hangs)
                raise SystemExit(bool(hangs))
print("total",tot,"hangs/fails",hangs)
raise SystemExit(bool(hangs))
