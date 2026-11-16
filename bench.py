#!/usr/bin/env python3
import os, sys, time

os.environ.setdefault("MAKEFUN_ENV_URL", "http://bench.invalid")
import engine as e

FENS = [
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r1bq1rk1/pp2ppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ - 0 1",
    "rnbq1rk1/ppp1bppp/4pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 1",
    "2rq1rk1/pp1bppbp/3p1np1/8/2BNP3/2N1BP2/PPPQ2PP/2KR3R w - - 0 1",
]


def run(budget, reps=2):
    e.NL = budget
    rows = []
    for f in FENS:
        s = e.pf(f)
        legal = {e.mu(m) for m in e.lm(s)}
        ap = {e.fk(s): 1}
        best = None
        for _ in range(reps):
            t0 = time.perf_counter()
            m = e.sr(s, legal, ap)
            dt = time.perf_counter() - t0
            if best is None or dt < best[0]:
                best = (dt, e.ND, None if m is None else e.mu(m))
        dt, nodes, mv = best
        rows.append((f, nodes, dt, nodes / dt if dt else 0, mv))
    tn = sum(r[1] for r in rows)
    tt = sum(r[2] for r in rows)
    print(f"budget={budget} reps={reps}")
    for f, n, dt, nps, mv in rows:
        print(f"  {n:7d} nodes {dt:7.3f}s {nps:10.0f} nps  {mv}  {f}")
    print(f"  TOTAL   {tn:7d} nodes {tt:7.3f}s {tn/tt:10.0f} nps  avg {tt/len(rows):.3f}s/move")
    return tn / tt, tt / len(rows)


if __name__ == "__main__":
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    nps, avg = run(budget, reps)
    print(f"nps={nps:.0f} avg_move={avg:.3f}s budget={budget}")
